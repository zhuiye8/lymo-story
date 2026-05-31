# Phase 1 实施清单（施工图）

> **状态：✅ 全部里程碑完成（2026-06-01）。** M1-M5 已落地：DB/记忆地基、初始化与章节管线、质量闸、分层语义记忆、伏笔闭环、管理端 UI 全部实现并通过 56 单测 + 10 章压测（冲突 0、composite~8）。本文为施工依据，实现以代码为准。
> 配套：`phase1/00-architecture.md`；运行指引见根 `CLAUDE.md`
> 原则：现有 `backend/` 原地重写（Q1）；先建尺子再建生成（§9 落地顺序）；每步有验收点，不达标不进下一步

---

## 0. 现有 backend 处置总表（原地重写的"留/改/弃"）

> Q1 = 原地重写。下表是逐文件裁决，避免"重写"变成"乱删"。

### 留（plumbing，几乎不动）
| 文件/模块 | 处置 |
|---|---|
| `llm/client.py` | **改**：底层接 Instructor（见 Step 3），对外接口尽量保持 |
| `llm/logger.py` | 留（LLM 调用日志：token/cost/latency） |
| `llm/model_registry.py` | 留 + 扩（per-agent 模型绑定，加 v4-pro/v4-flash/MiMo） |
| `llm/providers/deepseek.py` | 留 + 扩（加 prefix-completion / FIM / logprobs 封装） |
| `storage/sqlite_store.py` | **大改**：删旧表定义，建 §6 新 schema |
| `storage/vector_store.py` | 留（ChromaDB 分层记忆） |
| `config.py` / `deps.py` / `main.py` | 留 + 微调（注册新 agent/graph/路由） |
| `api/llm_admin.py` | 留（模型管理 UI 后端） |
| `api/quality_admin.py` | 留（质量曲线 4 图表 backend，Phase 0 已验收；schema 对齐后救活） |
| `progress.py` / `services/task_registry.py` | 留（生成进度/后台任务） |
| `api/stories.py` `api/chapters.py` `api/control.py` `api/public.py` | 留 + 改（接新 graph） |

### 改/重写（核心逻辑）
| 模块 | 处置 |
|---|---|
| `agents/*` | **重写**：留 `base.py`（升级支持 Instructor）；agent 集合按 §4 重组 |
| `prompts/*` | **重写**：全部 prompt 按新 agent + anti-slop 负指令重写 |
| `graph/*` | **重写**：init_graph（5 节点）+ chapter_graph（含质量闸循环） |
| `models/*` | **重写**：Pydantic schema 按 §4/§6 新定义 |
| `quality/*` | **重写**：slop_detector → 频次感知 + logprobs；新增 critic_room；rubric 对齐 WebNovelBench |
| `memory/*` | **改**：knowledge_graph → DOME 四元组；layered_memory 留；context_builder 改 |

### 弃（删除）
| 文件 | 原因 |
|---|---|
| `storage/json_store.py` | 旧 per-story JSON 文件存储，新架构全进 SQLite |
| `agents/director.py`（若存在遗留）/ `outline_parser.py` | 旧 init 流程，被新 5-agent 管线取代 |
| `agents/scene_*.py`（splitter/writer/consistency） | 旧 scene 拆分逻辑，新架构 scene_plan 内置 |
| `memory/plot_dedup.py` / `world_book.py` | 旧机制，被 DOME 四元组 + 记忆层取代（如有用逻辑则吸收） |
| `services/regeneration.py` | 旧重生成逻辑，被质量闸闭环取代 |
| Phase 0 `data/story.db` | C2：旧数据弃用，归档为 `data/story.db.archive_pre_phase1` 后建空库 |

> 注：删除前一律先 `git mv` 到 `backend/_deprecated/` 或直接删（git 历史可回溯），不物理丢失。

---

## Step 1 · 评测质量层 + slop 词表（先建尺子）

> 没有尺子不知道改得对不对。这步先行。

### 1.1 中文 slop 词表（第 1 层种子）
- 文件：`backend/quality/slop_lexicon_zh.py`
- 内容：tier1 烂喻（频次感知）/ 套话 / fiction-tell / 结构套路，~100-200 条
- 来源：Phase 0 `TIER1_BANNED_ZH` + Antislop 中文化 + 已知 LLM 套话
- **关键改进**：`仿佛/犹如/宛如/如同` 改频次感知（单次不扣，≥2/段才扣）

### 1.2 slop_detector 重写
- 文件：`backend/quality/slop_detector.py`
- 检测：词表命中 + 正则结构（句长 CV / 破折号 / 段首转折）+ logprobs 异常段
- 输出：`SlopReport{findings[], penalty, flagged_spans[]}`（flagged_spans 给 Step 6 局部重写定位）

### 1.3 SEQR rubric（对齐 WebNovelBench）
- 文件：`backend/quality/rubric.py`
- 8 维逐字对齐 WebNovelBench；Composite = mean(8) − slop_penalty
- 文件：`backend/quality/critic_room.py`（异源评委，Step 6 用，先留接口）

### 1.4 质量曲线 backend 救活
- `api/quality_admin.py` 已验收的 4 图表，schema 对齐新表后接通

**验收点 S1**：给一段已知含 slop 的中文文本，detector 正确标出 flagged_spans + penalty；rubric 能对一章打 8 维分。

---

## Step 2 · 数据库 schema + 记忆地基

### 2.1 建表
- 文件：`backend/storage/sqlite_store.py`（重写建表段）
- 表：§6 全部——`knowledge_quads` / `characters`(含 voice_profile) / `character_states` / `outline_rough` / `outline_detailed` / `memories` / `chapters` / `slop_findings` / `stories`
- 旧库归档：`data/story.db` → `.archive_pre_phase1`，建空库

### 2.2 DOME 四元组读写层
- 文件：`backend/memory/knowledge_quads.py`（重写 knowledge_graph.py）
- 接口：`add_quad` / `query_valid_at(chapter_num)` / `invalidate(quad_id, at_chapter)` / `find_conflicts(new_quads)`

### 2.3 分层记忆
- `memory/layered_memory.py` 留 + 接新表；`context_builder.py` 改为从 DOME + 记忆组装上下文

**验收点 S2**：建表无错；四元组能写入、按章号查有效集、检测出"死人复活"式冲突。

---

## Step 3 · Instructor 接入 + 双模型配置

### 3.1 LLM client 升级
- 文件：`backend/llm/client.py`
- `complete_json` 底层换 `instructor.from_litellm(litellm.acompletion)`：返回校验过的 Pydantic 对象 + reask 自愈
- `complete`（纯文本）保持
- 新增：`complete_with_logprobs` / `prefix_complete`（/beta）/ `fim_complete`（/beta）—— anti-slop 闭环要用

### 3.2 BaseAgent 升级
- 文件：`backend/agents/base.py`
- `_call_json` 接受 `response_model: type[BaseModel]`，返回该类型实例（不再裸 dict）

### 3.3 模型绑定
- `llm/model_registry.py` + `config.py`：deepseek-v4-pro（散文）/ v4-flash（批量）/ mimo（第二评委）
- 验证 thinking 模式与 logprobs 互斥的处理（slop 控制走非 thinking）

**验收点 S3**：一个 agent 用 Instructor 调 DeepSeek 返回校验过的 Pydantic 对象；prefix-completion / logprobs 调用各跑通一次。

---

## Step 4 · 初始化管线（5 agent）

### 4.1 Pydantic schema
- 文件：`backend/models/`：`Concept` / `WorldSetting` / `Characters`(含 voice_profile) / `Outline` / `StoryBible`(V3)

### 4.2 5 个 agent + prompt
- `concept` / `world_builder` / `character_designer` / `outline_planner`（DOME 双层 + Propp-34 标签）/ `assemble_bible`（无 LLM）
- prompt 全部含中文 anti-slop 负指令

### 4.3 init graph
- 文件：`backend/graph/init_graph.py`：5 节点线性 → 产出 StoryBible + 初始四元组 + 初始记忆

**验收点 S4**：给一个题材，跑出完整 StoryBible（世界观/角色卡含 voice_profile/DOME 双层大纲），落库。

---

## Step 5 · 章节生成循环（先不含质量闸）

### 5.1 ChapterGraphState + 节点
- `load_context`（含 context cache）/ `outline_advance` / `scene_plan` / `retrieve_memory` / `write_chapter`(v4-pro) / `extract_memory` / `save`

### 5.2 chapter graph
- 文件：`backend/graph/chapter_graph.py`：先跑通"生成一章并落库"，质量闸留空位

**验收点 S5**：从 StoryBible 生成第 1 章正文（2000-4000 字），抽出新四元组/角色状态变化并落库；第 2 章能正确加载第 1 章上下文。

---

## Step 6 · anti-slop 检测-重写-选优闭环（接质量闸）

### 6.1 质量闸节点
- 文件：`backend/graph/nodes.py` 的 `quality_gate`
- ① 确定性检测（Step 1 detector）② 一致性检测（DOME 冲突 + 角色状态）③ 局部重写（prefix/FIM 重写 flagged_spans）④ 异源 Critic + best-of-N（N=2~3）

### 6.2 best-of-N + Critic Room
- `write_chapter` 出 N 候选 → logprobs + critic_room 打分选优
- critic_room：主评委 v4-flash + 第二评委 MiMo（订阅期）

### 6.3 重写循环
- 不过 → 局部重写 → 重检，上限 N 次；仍不过则标记人工 review

**验收点 S6**：一章含 slop → 闭环检测到 → 局部重写后 slop_penalty 下降 → Critic 分提升；全程不整章重生成。

---

## Step 7 · 前端串联

- 创建故事（选题材）/ 生成控制（stage 进度）/ 章节阅读 / **质量曲线 4 图表**（救活的 quality_admin）
- reader 端（已有）接新 public API

**验收点 S7**：浏览器里从"创建一本书"到"读到生成的章节 + 看质量曲线"全链路通。

---

## 里程碑

| 里程碑 | 含 Step | 标志 |
|---|---|---|
| **M1 尺子就位** | S1+S2+S3 | 能检测 slop、能存四元组、Instructor 通 |
| **M2 能造一本书的骨架** | S4 | StoryBible 完整产出 |
| **M3 能写章（裸）** | S5 | 生成+记忆闭环通，无质量闸 |
| **M4 能写好章** | S6 | anti-slop 闭环生效——**这是"不妥协质量"的兑现点** |
| **M5 端到端可用** | S7 | 浏览器全链路 |

---

## 跨 Step 并行采集任务（我做，不阻塞主线）

- **slop 词表第 2/3 层**：自家输出 vs 授权语料统计（§11）——M3 有自产章节后才有料，先备工具 `scripts/mine_slop.py`
- **授权语料采集**：开工前列"采哪些站/哪批数据"清单找你点头（§11 协作纪律）
- **题材模板**：先做的那个题材（Q4）的设定/桥段参考

---

## 实施层决策（用户 2026-05-30 拍板）

| # | 问题 | **决定** |
|---|---|---|
| I1 | 先做哪个题材 | ✅ **男频系统流** |
| I2 | 删旧文件方式 | ✅ **直接删**（git 历史可回溯） |
| I3 | 里程碑验收节奏 | ✅ **自主执行 + 自我验证**，不逐里程碑找用户点头（用户授权）。每个验收点我自己跑通再进下一步 |
| I4 | 章节字数控制 | ✅ **范围软目标 + 事前分镜预算为主、事后微调为辅**，详见 §字数控制机制 |

### 字数控制机制（I4 展开）

> 目标：稳定产出 3000+ 字/章，但**不让 LLM 操控精确数字**（它做不到）。核心思想：**结构性控制（事前）为主，矫正性控制（事后）为安全网**。

**① 事前分镜预算（主控，LongWriter 方法 arXiv 2408.07055）**
- `scene_plan` 给每章分 N 场景，每场景配字数预算（如 3 场景 × ~1100 = 3300），逐场景生成
- 总字数天然落进范围 → 事后矫正成为罕见例外

**② 范围软目标 + 永不硬切**
- prompt 给范围（"本章约 3200-3800 字"），不给精确数
- `max_tokens` 给足（~6000 token ≈ 4000+ 字），让模型自然收尾
- 落在 **[3000, 4500]** 接受；**绝不在 max_tokens 处中途截断**（半句截断是最差结果）

**③ 事后矫正（安全网，用 prefix/FIM —— 与 anti-slop 局部重写共用引擎）**
- **太短（<3000）** → prefix-completion：整章当 assistant prefix 喂回，扩展**最单薄场景**（不在尾部硬接）
- **太长（>4500）** → **压缩，不截断**：找最冗余场景/段落压缩，**死保章末钩子**（网文命根子）
- **接缝修复** → FIM：prefix=前文 / suffix=后文，填/改中间段（用户原"截断部分左右扩展"思路在此）

**关键协同**：字数矫正与 anti-slop 局部重写共用 prefix/FIM 引擎，无需额外机制。

---

## 我的自主执行模式（基于 I3 授权）

- 按 7 Step 顺序执行，每个验收点（S1-S7）**我自己跑通验证**（compileall / pytest / 实跑 smoke）
- **不逐步找用户点头**；遇到这些情况才主动找你：
  - 授权语料采集的"采哪些站/哪批数据"边界判断（§11 纪律）
  - 架构级方向需要改（与已定方案冲突）
  - 真正卡住、需要你的外部信息
- 阶段性主动汇报进度（如每完成一个里程碑 M1-M5 简报一次），但不阻塞等待
