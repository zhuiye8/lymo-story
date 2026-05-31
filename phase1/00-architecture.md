# 狸梦 Story Engine — 全新架构方案（从 0 重建）

> **状态：✅ 已实现并验证（2026-06-01）。** 本文为设计依据；实现以代码为准（`backend/**/phase1*`），权威运行指引见根 `CLAUDE.md`。
> 实现增量（相对本设计）：
>   - DOME 冲突检测根因修复——四元组只存**状态事实**（受控谓语词表 `backend/memory/predicates.py`），事件归摘要；单值谓语 + object 兼容性 + 写入去重，消除误报（10 章压测冲突 51→0）。
>   - 分层记忆 L0-L3 接入管线（`layered_memory.py`），嵌入选定本地 **ollama + Qwen3-Embedding-4B**（中文 SOTA，GPU）。
>   - 伏笔埋坑/填坑闭环落地；MiMo 第二评委须关 thinking（`enable_thinking=false`）。
> 日期：2026-05-30（设计）／2026-06-01（实现完成）
> 前置依据：`workspace/research/` 三轮调研（全部 source-verified）+ DeepSeek/MiMo 官方 API 逐字核实

---

## 0. 不可动摇的约束（地基公理）

这些是用户拍板、不再讨论的前提。所有设计都必须服从。

| # | 约束 | 来源 |
|---|---|---|
| C1 | **从 0 构建，面向生产，绝不质量妥协**。拒绝"先用 X 凑合、以后换 Y"的埋雷式分期 | 用户 2026-05-30 |
| C2 | **不兼容旧数据**。Phase 0 的 `story.db`、SEQR 评分数据全部弃用，从空库开始 | 用户 2026-05-30 |
| C3 | **API-only，不租 GPU**。不能自托管、不能微调、不能改权重、拿不到全量 raw logits | 用户 2026-05-30 |
| C4 | **DeepSeek 为唯一长期依赖（骨架）**；MiMo 仅订阅期（剩 ~1 月）机会性利用，架构零依赖 | 用户 2026-05-30（方案 A+C） |
| C5 | **无监督协议**。你我直接定，不走 workspace 审批 | 用户 2026-05-30 |

---

## 1. DeepSeek API 能力集（逐字核实，2026-05-30）

> 全部来自 [api-docs.deepseek.com](https://api-docs.deepseek.com) 官方文档 + 多源交叉。这是整个架构能用的"原材料清单"——不在此表内的能力一律不假设存在。

### 1.1 模型与价格

| 模型 | 上下文 | 输出上限 | 输入 miss | 输入 hit | 输出 | 用途定位 |
|---|---|---|---|---|---|---|
| **deepseek-v4-pro** | 1M | 384K | $0.435/M | $0.003625/M | $0.87/M | **散文主力**（Writer / Critic 生成侧） |
| **deepseek-v4-flash** | 1M | 384K | $0.14/M | $0.0028/M | $0.28/M | **批量/检测/结构化**（大纲、记忆抽取、slop 检测、best-of-N 打分） |

- `deepseek-chat` / `deepseek-reasoner` = v4-flash 的非思考 / 思考别名（将弃用，不用别名）
- **context caching**：cache hit ≈ miss 的 1/10。**长篇连载的命门**——世界设定/角色卡/前文摘要走缓存复用，大幅压成本。

### 1.2 可用的控制能力（决定 anti-slop 怎么做）

| 能力 | 状态 | 我们怎么用 |
|---|---|---|
| `logprobs` / `top_logprobs`（0-20） | ✅ | slop 段检测、候选打分、best-of-N 选优 |
| `logit_bias`（−100~100，token-id） | ✅ | 压制已知套话起手 token |
| **Chat Prefix Completion**（`/beta`，末条 assistant 设 prefix） | ✅ | 强制开头/语气、控文风、局部续写重写 |
| **FIM 填中**（`/beta`，prefix+suffix） | ✅ | "挖空重写"式精修 slop 段 |
| `response_format: json_object` | ✅（需 prompt 也声明 JSON） | 结构化 agent 输出 |
| `tools`（function calling，≤128） | ✅ | agent 编排可选 |
| `stop`（≤16 序列） | ✅ | 截断控制 |

### 1.3 明确的限制（设计必须绕开）

| 限制 | 影响 |
|---|---|
| ⚠️ **thinking 模式下 logprobs/logit_bias 失效** | slop 的 logits 级控制只能在**非 thinking 模式**做 |
| ❌ `frequency_penalty` / `presence_penalty` 已废弃 | 防重复不能靠这俩，得靠检测+重写 |
| ❌ 无严格 `json_schema` | 结构化输出靠 Instructor 的"校验+reask"补 |
| ❌ 无全量 raw logits / 不能改权重 | 做不了 Antislop 完整回溯 Sampler、做不了 FTPO 微调 → anti-slop 走"外挂检测-重写"而非"权重级根治" |

### 1.4 MiMo（机会性，非依赖）

- **MiMo-V2.5-Pro**：1.02T/42B MoE，1M 上下文，主打 Agent+Coding（**非文笔标杆**）
- OpenAI + Anthropic 双兼容协议；订阅制，剩 ~1 月
- logprobs/logit_bias **官方文档未提及** → 当黑盒用，不做 logits 级控制
- **定位**：订阅期内当"白嫖额度"做离线重活（批量评测、合成数据），或 Critic Room 第二评委（异源去偏）。**1 月后消失架构不受影响。**

---

## 2. 核心设计哲学

> 三轮调研收敛出的、适配 API-only 的三条主线。

### 2.1 控制不靠权重，靠"外挂闭环"
不能微调/改权重 → 质量控制全部做成**生成后的检测—重写—选优闭环**：
- 用 logprobs 检测 slop 段 / 给候选打分
- 用 prefix-completion / FIM **局部重写**命中段（不整章重生成，省钱省时）
- 用 best-of-N + 异源 Critic 选优

### 2.2 "编辑部"多 agent 分工（不是单 prompt 怪兽）
Phase 0 的教训：Director 一次吐整本 bible（max_tokens 12288）质量不稳。新架构把**每个认知任务拆成专注的小 agent**，每步产出小、可校验、可缓存。

### 2.3 长程一致性靠"结构化记忆地基"，不靠模型记忆
DOME 四元组 + 分层记忆 + 大纲全部落 SQLite，**显式管理**世界状态/角色状态/伏笔债，不指望模型在 1M 上下文里自己记住。

---

## 3. 总架构（数据流）

```
┌─────────────────────────────────────────────────────────────────────┐
│  初始化管线（一本书开始时跑一次）                                          │
│                                                                       │
│  用户输入(题材/设定/主角)                                                │
│       ↓                                                               │
│  ConceptAgent ──→ WorldBuilder ──→ CharacterDesigner ──→ OutlinePlanner│
│  (立意/基调)      (世界观/规则)      (角色卡/关系)         (DOME 双层大纲) │
│       └──────────────┴──────────────┴──────────────┘                  │
│                          ↓                                            │
│              StoryBible(完整) + 初始 知识四元组 + 初始 记忆            │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  章节生成循环（每章跑一次，LangGraph 固定 DAG）                            │
│                                                                       │
│  load_context ──→ outline_advance ──→ scene_plan ──→ retrieve_memory  │
│  (取大纲+前文摘要+   (推进到本章细纲)    (本章分镜/beats)  (DOME四元组+    │
│   缓存命中)                                              分层记忆检索)   │
│       ↓                                                               │
│  write_chapter (DeepSeek v4-pro 散文主力, 角色卡注入 + prefix 控文风)   │
│       ↓                                                               │
│  ┌─ 质量闸（外挂闭环）─────────────────────────────────┐               │
│  │ ① 确定性检测: 中文slop词表 + 正则 + logprobs异常段     │               │
│  │ ② 一致性检测: 知识四元组冲突 + 角色状态冲突            │               │
│  │ ③ 局部重写: 命中段用 prefix-completion/FIM 重写       │               │
│  │ ④ 异源Critic(MiMo/v4-flash)打分 + best-of-N选优      │               │
│  └──────────────────┬──────────────────────────────────┘               │
│       ↓(过)                    ↓(不过, 回 ③ 重写, 上限N次)              │
│  extract_memory ──→ save                                              │
│  (抽本章新四元组/                                                       │
│   角色状态变化/伏笔)                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent 拓扑与职责

> 全部用 **Instructor (`from_litellm`)** 包结构化输出（Pydantic 校验 + reask 自愈）；唯一例外是 Writer/Critic 的散文生成走纯文本 `_call_text()`。

### 4.1 初始化管线（5 agent）

| Agent | 模型 | 输入 | 输出（Pydantic schema） | 缓存 |
|---|---|---|---|---|
| **ConceptAgent** | v4-flash | 用户题材/要求/书名 | `Concept{title, genre, tone, one_line, synopsis, special_ability}` | — |
| **WorldBuilder** | v4-flash | Concept | `WorldSetting{background, factions[], power_system, world_rules[]}` | — |
| **CharacterDesigner** | v4-flash | Concept+World | `Characters{protagonist, antagonist, supporting[]}`（每个含 voice_profile 对白指纹） | — |
| **OutlinePlanner** | v4-pro | Concept+World+Chars | `Outline{volumes[], rough_5stage, narrative_func_tags[]}`（DOME 双层 + Propp-34 中文叙事功能标签） | — |
| **assemble_bible** | 无 LLM | 上面全部 | `StoryBible`（完整 V3）+ 初始知识四元组 + 初始记忆 | — |

### 4.2 章节生成循环（LangGraph 节点）

| 节点 | 模型 | 职责 |
|---|---|---|
| `load_context` | 无 LLM | 取大纲位置 + 前文摘要 + **走 context cache** |
| `outline_advance` | v4-flash | 把 rough 段推进展开成本章 detailed 细纲（DOME 动态展开） |
| `scene_plan` | v4-flash | 本章分镜/beats + 选 POV + 可见事件过滤 |
| `retrieve_memory` | 无 LLM | DOME 四元组查询（按章号有效区间）+ 分层记忆语义检索 |
| `write_chapter` | **v4-pro** | 散文主力。角色卡 voice_profile 注入 + prefix 控开头文风 |
| `quality_gate` | v4-flash + Critic | 见 §5 anti-slop 闭环 |
| `extract_memory` | v4-flash | 抽本章新四元组 / 角色状态变化 / 新伏笔债 |
| `save` | 无 LLM | 落库 |

---

## 5. Anti-slop 检测—重写—选优闭环（API-only 的核心创新）

> 这是整个"不妥协质量"在 API 约束下的落地形态。分四层，全部不碰权重。

### 5.1 ① 确定性检测（零成本，不可被模型偏见污染）
- **中文 slop 词表**（自建，移植 autonovel `evaluate.py` 思路 + Antislop 词表中文化）
  - tier1 烂喻：`仿佛/犹如/宛如/如同`（**频次感知**：单次合法不扣，≥2/段才扣——修 Phase 0 已知误判）
  - 套话：`心底深处/命运的齿轮/千丝万缕/不仅仅是…更是`
  - fiction-tell：`瞳孔紧缩/嘴角勾起/心脏漏跳`
- **正则结构检测**：句长 CV、破折号密度、段首转折比例
- **logprobs 异常**：用 top_logprobs 找"模型高自信吐出的陈词"（slop 往往是低熵高频）

### 5.2 ② 一致性检测（对长程质量）
- **知识四元组冲突**：本章新四元组 vs 已有有效区间（死人复活、设定矛盾）
- **角色状态冲突**：角色当前位置/状态 vs 本章动作

### 5.3 ③ 局部重写（省钱的关键）
- 命中段落**不整章重生成**，用 **Chat Prefix Completion / FIM**：
  - prefix completion：给"干净的开头" + stop 控制，强制模型避开 slop 重写该段
  - FIM：把 slop 段挖空，prefix+suffix 让模型填中
- `logit_bias` 压制已知 slop 起手 token

### 5.4 ④ 异源 Critic + best-of-N
- **best-of-N**：write_chapter 出 N 个候选，用 logprobs + Critic 打分选最优
- **异源 Critic Room**：
  - 主评委：DeepSeek v4-flash（确定性 + 便宜）
  - **第二评委：MiMo**（订阅期内，异源去偏；过期后降级为单评委 + 确定性规则兜底）
  - rubric：WebNovelBench 8 维（已逐字核实）

> 戒律（调研结论）：**判官必须与生成模型异源**——Writer 用 v4-pro 生成，Critic 不能也用 v4-pro 自评（self-correction 在推理上会掉分）。这正是 MiMo 在订阅期的最高价值。

---

## 6. 数据库 Schema（全 SQLite，零新基础设施）

> 不引图数据库（GraphRAG 对生成是负 ROI，已验证）。DOME 四元组用扁平表 + 章号有效区间即可。

### 6.1 知识四元组（DOME，长程一致性地基）
```sql
CREATE TABLE knowledge_quads (
    id INTEGER PRIMARY KEY,
    story_id TEXT NOT NULL,
    subject TEXT NOT NULL,        -- 主体（角色/物/地点）
    predicate TEXT NOT NULL,      -- 谓词（动作/关系/属性）
    object TEXT NOT NULL,         -- 客体
    valid_from INTEGER NOT NULL,  -- 起始章号
    valid_to INTEGER,             -- 失效章号（NULL=仍有效；invalidate-not-delete）
    source_chapter INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
```

### 6.2 角色（含对白指纹 voice_profile）
```sql
CREATE TABLE characters (
    story_id TEXT, character_id TEXT,
    name TEXT, role TEXT,
    profile_json TEXT,        -- 完整人设
    voice_profile_json TEXT,  -- 对白指纹: 口头禅/句式/语气/禁用词 —— 对白区分度的抓手
    PRIMARY KEY (story_id, character_id)
);

CREATE TABLE character_states (
    story_id TEXT, character_id TEXT, chapter_num INTEGER,
    location TEXT, status TEXT, emotional_state TEXT,
    relationships_json TEXT,  -- 对其他角色的态度（随章演变）
    PRIMARY KEY (story_id, character_id, chapter_num)
);
```

### 6.3 大纲（DOME 双层）
```sql
CREATE TABLE outline_rough (    -- 5 段英雄之旅/Freytag
    story_id TEXT, stage_num INTEGER, stage_name TEXT,
    summary TEXT, chapter_start INTEGER, chapter_end INTEGER,
    PRIMARY KEY (story_id, stage_num)
);
CREATE TABLE outline_detailed ( -- 动态展开的细纲
    story_id TEXT, chapter_num INTEGER,
    beats_json TEXT, narrative_func_tags TEXT,  -- Propp-34 中文功能标签
    word_budget INTEGER,        -- LongWriter 字数预算
    expanded_at TEXT,
    PRIMARY KEY (story_id, chapter_num)
);
```

### 6.4 分层记忆 + 章节
- `memories`（L0 身份核心 / L1 关键记忆按情感权重 / L2 场景相关 / L3 深搜）→ ChromaDB 向量 + SQLite 元数据
- `chapters`（正文 + POV + 字数 + 质量分快照）
- `slop_findings`（每章 slop 检测留痕，喂质量曲线）

---

## 7. 评测质量层（定义"好"，最先建）

> Phase 0 的 SEQR 思路保留，但对齐 WebNovelBench，数据从 0。

- **8 维 rubric** = WebNovelBench 逐字 8 维（Literary Devices / Sensory Detail / Character Presence Balance / Dialogue Distinctiveness / Characterisation Consistency / Atmospheric & Thematic / Contextual Appropriateness / Scene-to-Scene Coherence）
- **slop_penalty**：§5.1 确定性检测产出
- **Composite** = mean(8 维) − slop_penalty
- **异源 Critic**：见 §5.4
- **质量曲线 UI**：复用 Phase 0 已验收的 4 图表 backend（trend/dimension/heatmap/distribution）—— 这部分代码可救活（schema 对齐后）

---

## 8. 技术栈

| 层 | 选型 | 依据 |
|---|---|---|
| 编排 | **LangGraph 固定 DAG** | 2026 实测最优；不引 supervisor/swarm |
| 结构化 I/O | **Instructor `from_litellm`** | 官方零改造接 LiteLLM gateway；DeepSeek 无严格 json_schema 靠 reask 补 |
| LLM 网关 | **LiteLLM**（已有） | 统一 DeepSeek + MiMo |
| 存储 | **SQLite + ChromaDB**（已有） | 零新基础设施；不引图数据库 |
| 后端 | **FastAPI**（已有） | — |
| 前端 | **Next.js 16**（admin + reader，已有） | — |

---

## 9. 落地顺序（先建什么）

> 原则：先建"定义好坏的尺子"和"长程地基"，再建生成，最后接质量闸。

1. **评测质量层**（§7）— 先有尺子才知道改得对不对；含中文 slop 词表自建
2. **数据库 schema + 记忆地基**（§6）— DOME 四元组 + 角色 voice_profile + 大纲表
3. **Instructor 接入 + LiteLLM 双模型配置**（§8）— 打通 DeepSeek v4-pro/flash + MiMo
4. **初始化管线 5 agent**（§4.1）— 能产出一本书的 bible + 大纲
5. **章节生成循环**（§4.2）— 不含质量闸先跑通
6. **anti-slop 检测-重写-选优闭环**（§5）— 接上质量闸
7. **前端串联**（创建/生成/阅读/质量曲线）

---

## 10. 决策记录（用户 2026-05-30 拍板）

| # | 问题 | **决定** |
|---|---|---|
| Q1 | 现有 backend/ 重写 vs 全新 package | ✅ **现有 `backend/` 原地重写**（保留可复用 plumbing：LiteLLM 网关 / SQLite+Chroma 存储 / FastAPI / 前端 / Phase 0 质量曲线 4 图表 backend；重写 agents / graph / prompts / quality / schema） |
| Q2 | MiMo 订阅期用途 | ✅ **当第二评委**（异源去偏；过期降级为单评委 + 确定性规则，不伤架构） |
| Q3 | best-of-N 的 N | ✅ **N=2~3**，关键章可调高 |
| Q4 | 先做哪个题材 | ✅ **先做一个题材打通全链路，再扩** |
| Q5 | 中文 slop 词表语料基线 | ✅ **混合策略，见 §11**（规避版权地雷：种子词表 day-1 可用 + 统计层用"自家 DeepSeek 输出 vs 合法语料"，绝不爬版权网文） |

---

## 11. 中文 slop 词表语料策略（Q5 展开）

> **授权前提（用户 2026-05-30 确认）**：本项目是**有授权的合作项目**，语料获取（含网文）已获授权，可直接采集。下方"全程不碰版权网文"的保守约束**已解除**。但保留两条工程纪律：① 涉及具体语料来源/平台/合规边界时，**有验证需求直接找用户确认**（不擅自假设授权范围）；② 词表的**统计方法**（自产 vs 基线对比）仍是最优路径——授权只是把"基线/语料池"扩大，不改变"slop = model-specific 高频"这个本质。

> **核心原则**：slop 词表是"检测用对比基线"，不是"训练语料"——目标是找出 **DeepSeek 模型特有的高频套话**（model-specific slop），不是囤一堆文本。

### 三层混合（day-1 可用 + 持续自扩）

**第 1 层 · 种子词表（day-1 硬编码，立即可用）**
- 来源：① Phase 0 已验证的 `TIER1_BANNED_ZH` 等中文词表（这是我们自己写的，无版权问题）② Antislop / autonovel 的英文 slop 词表**中文化映射**（开源 MIT，方法可借）③ 工程师 + 调研已知的中文 LLM 套话（`仿佛/犹如/心底深处/命运的齿轮/瞳孔紧缩…`）
- 规模：~100-200 条起步，**今天就能用**，不依赖任何爬取

**第 2 层 · 自产对比统计（核心，零版权风险，自动扩充）**
- 机制：**用我们自己生成的章节**（DeepSeek 输出，我们拥有）跑词频统计 → 找出"DeepSeek 异常高频"的 n-gram
- 对比基线 = **合法可得的人写中文文本**：
  - ✅ **公版文学**（鲁迅/朱自清/老舍等，作者死后 50 年，我们 Phase 0 已从 wikisource 验证过抓取流程）
  - ✅ **维基/新闻/政府公开语料**（CC 授权或公开）
  - ✅ 用户自有授权的任何文本
- 工具：slop-forensics（开源）中文化（jieba 替换 NLTK），跑"DeepSeek 输出 vs 公版基线"的词频差 → model-specific slop 自动浮现
- **这是可持续的**：系统跑得越多，自家输出越多，统计越准，词表自动长大——不需要爬任何版权内容

**第 3 层 · 上网补充（已获授权，我来做）**
- 我可以上网收集的：
  - ✅ 开源 slop 词表 / anti-AI-detection 词表（GitHub，记录 license）
  - ✅ 学术论文公布的中文 LLM 套话清单（Creative Convergence 34 功能、WebNovelBench 附录等；数据集 CC-BY-NC-SA 仅约束"再分发数据集"，取方法/词表无碍）
  - ✅ 公版文学全文（wikisource，已验证流程）+ **授权范围内的网文语料**（作对比基线/题材模板，规模更大基线更准）
- **协作纪律**：遇到"这个来源在授权范围内吗 / 这个平台能不能爬 / 这批数据怎么用"这类**边界判断**，我**直接找你确认**，不擅自假设。

### 落地
- **day-1**：第 1 层种子词表硬编码进 `backend/quality/slop_lexicon_zh.py`，检测立即可用
- **持续**：第 2 层统计脚本（`scripts/mine_slop.py`）跑"自家 DeepSeek 输出 vs 授权语料基线"，人工 review 后把高置信词加入词表
- **采集工作**：第 3 层开源词表 + 学术清单 + 授权语料，作前两层的扩充。**具体采哪些站/哪批数据，开工前我列清单找你点头**

---

## 附：与三轮调研的对应关系（可追溯）

| 本方案设计 | 调研依据 |
|---|---|
| DOME 四元组 + 双层大纲 | v2 R1 + R3（spot-verified） |
| 分层记忆 | v2 R2（MemoryOS/Mem0 思想，无开箱即用，自建） |
| 角色 voice_profile + 异源 Critic | v2 R5 + supplement R15（对白区分度正解=底座+角色工程+评测闭环） |
| Instructor `from_litellm` | v2 R10（官方零改造，已核实） |
| anti-slop 检测-重写 | v2 R6 + supplement（Antislop 思想；API 无 raw logits 故走外挂） |
| LangGraph 固定 DAG | v2 R7 |
| 不引图数据库 | v2 R3（GraphRAG 负 ROI） |
| DeepSeek 能力集 | 2026-05-30 官方文档逐字核实 |
| MiMo 机会性定位 | 2026-05-30 官方文档 + 用户 A+C 决策 |
