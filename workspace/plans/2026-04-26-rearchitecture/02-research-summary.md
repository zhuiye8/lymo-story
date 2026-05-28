# 02 · 调研总结（4 路深度调研结果）

> 蓝图列了 11 个外部参考项目。出实施计划前，工程师 Claude 用 4 个并行 agent **真实访问每个项目的 GitHub 仓库、官方文档、论文 PDF**，逐一验证可用性、活跃度、可移植性，避免凭印象规划。本文档是关键发现的浓缩，便于 PM 快速判断技术选型可信度。

## 调研路线总览

| 调研路线 | 覆盖项目 | 核心问题 |
|---------|---------|---------|
| 路线 A · 记忆系统三巨头 | MemPalace / Graphiti+Zep / Mem0 / Letta / LangMem | 用谁替换我们手写的 KG？ |
| 路线 B · 创作系统两标杆 | autonovel / SillyTavern | 编辑闭环和 lorebook 怎么做？ |
| 路线 C · 外部素材接入 | Tavily / Firecrawl / SerpAPI / pytrends / 国内合规渠道 | 蓝图说的"热点雷达"用什么栈？ |
| 路线 D · 叙事规划论文 | StoryWriter / CONCOCT / CreAgentive / DOME / WebNovelBench | 长篇规划学术界最强方法是什么？ |

## 路线 A 关键收获

### MemPalace（蓝图重点推荐项目）

- **官方仓库**：[MemPalace/mempalace](https://github.com/MemPalace/mempalace)
- **2026 年新创建**（README 强调有大量仿冒域名，用户提到的 `milla-jovovich/mempalace` 是其中之一）
- **真实代码状态**：架构思想宣传度 >> 实际代码成熟度，自动化测试稀薄
- **可借鉴点**：
  - L0/L1/L2/L3 分层记忆思路
  - wing/room/hall/drawer 范围化 metadata（本质是命名空间过滤）
  - verbatim storage（存原文片段而非只存摘要）
  - agent diary（每个专业 agent 维护长期观察）
- **明确风险**：**不要直接引入代码**，只吸收设计模式

### Graphiti（重点推荐替换我们手写 KG）

- **官方仓库**：[getzep/graphiti](https://github.com/getzep/graphiti)
- **论文**：[arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956)
- **官方文档**：[help.getzep.com](https://help.getzep.com/graphiti/graphiti/overview)
- **关键发现**：**支持 Kuzu 嵌入式图库**（`pip install graphiti-core[kuzu]`）→ 不需要 Neo4j 服务，运维与 SQLite 等价
- **直接替换我们的 `KnowledgeGraph`**：
  - 自动 episode/provenance（每个事实链回章节原文）
  - 自动 fact invalidation（替代手写 valid_from/valid_to）
  - hybrid retrieval（semantic + keyword + graph traversal）
  - 与 LangChain / LangGraph 已有集成
- **维护活跃度**：Zep 团队在持续更新，2026 年 4 月仍有 commit

### Mem0 / Letta / LangMem（备选）

| 项目 | 适用度 | 理由 |
|------|-------|------|
| Mem0 | ❌ 不适合 | 模型抽象是 user/conversation，不是 character/story |
| Letta（原 MemGPT） | ⚠️ 太重 | OS 风格 agent 框架，引入会和我们 LangGraph 冲突 |
| LangMem | ✅ 可试 | 轻量，但能力子集被 Graphiti 覆盖 |

**结论**：选 Graphiti+Kuzu 替换手写 KG。

## 路线 B 关键收获

### autonovel（强烈推荐"借资产"）

- **仓库**：[NousResearch/autonovel](https://github.com/NousResearch/autonovel)
- **真实状态**：2026-03-14 开源，仅 3 commit，**作者基本未维护**
- **依赖极简**：纯 `httpx` 裸调 Anthropic Messages API，无 LangGraph / LangChain / LiteLLM
- **代码组织**：27 个 Python 脚本平铺在仓库根目录，无 package 结构
- **不能 fork**：架构与我们不兼容（无并发 / 无 DB / 无 Web UI）
- **能直接搬的高价值资产**（5 个 markdown）：

| 文件 | 大小 | 内容 |
|------|------|------|
| `ANTI-SLOP.md` | 17 KB | Tier 1/2/3 banned words + 9 个结构性 slop 模式 |
| `ANTI-PATTERNS.md` | 5.7 KB | 12 个小说专属 AI 失败模式（OVER-EXPLAIN 等） |
| `CRAFT.md` | 16 KB | Save the Cat / Story Circle / MICE / Sanderson 三定律 |
| `voice.md` | 7 KB | 文风指纹两层模板 |
| `canon.md` | - | 硬事实 7 大类 schema 模板 |

- **能直接抄的代码**（一个函数）：

```python
# slop_score(text) — 纯正则，0 LLM 调用，秒级出反 AI 味分数
TIER1_BANNED = ["delve","utilize","leverage","facilitate", ...]  # 19 词
TIER2_SUSPICIOUS = ["robust","comprehensive","seamless", ...]    # 24 词，cluster 触发
FICTION_AI_TELLS = [r"a sense of \w+", r"the air was thick with",
                    r"eyes widened", r"heart pounded in (?:his|her|their) chest", ...]
STRUCTURAL_AI_TICS = [r"[Nn]ot (?:just|merely|simply) .{3,40}, but ", ...]
# 数学特征：句长变异系数 CV<0.3 罚分、em-dash 密度、转折词比例、show-vs-tell
```

→ **直接照搬函数结构，banned words 替换为中文 LLM 俗套**："宛如…一般" / "不仅仅是…更是" / "千丝万缕" / "深深地" / "在心底深处" 等。

- **能直接借的 4 个 agent 设计**：
  1. `AdversarialEditor` — 让模型"切 500 字"，输出分类切割表（FAT/REDUNDANT/OVER-EXPLAIN/GENERIC/TELL/STRUCTURAL）
  2. `ReaderPanel` — 4 personas（编辑/类型读者/作家/普通读者），关键设计**"找分歧"而非"找共识"**
  3. `BriefGenerator` — 整合 reader_panel + critique + slop → 自动生成修订指令
  4. `OpusReviewer` — 双重人格（critic + professor）整本评审

- **关键 prompt 校准技巧**（autonovel 的 evaluate.py FOUNDATION_PROMPT）：

> "9-10: Could not improve this with a month of focused editorial work. Reserve 10 for work that SURPRISES you. Err toward lower scores."

强制每个维度先输出 `(a) gap (b) actionable improvement` 才能给分（防虚高分）。

### SillyTavern（强烈推荐借 schema）

- **仓库**：[SillyTavern/SillyTavern](https://github.com/SillyTavern/SillyTavern)
- **不能引入代码**（JS 单页应用，运行时和我们完全不同）
- **能直接抄的两件宝**：

#### (1) World Info / Lorebook 完整 schema（30+ 字段）

| 字段 | 用途 |
|------|------|
| `key + keysecondary + selectiveLogic` | 4 元逻辑：AND_ANY / NOT_ALL / NOT_ANY / AND_ALL |
| `constant / keyed / vectorized` 三态 | 主角永远在(蓝)、配角按需(绿)、远古传说语义召回(链) |
| `position + depth + order` | 精确插入位置控制 |
| `group + groupWeight + groupOverride` | **同组互斥**避免重复堆叠（我们目前 L2 没有！） |
| `sticky / cooldown / delay` | 时序控制（伤口触发后强制保留 N 章） |
| `excludeRecursion / preventRecursion / delayUntilRecursion` | 防 lore 雪崩 |
| `probability + useProbability` | 罕见事件低概率触发，避免确定性千篇一律 |

→ 我们当前 WorldBook 只有 5 字段，差距巨大。

#### (2) Prompt Inspector（最值钱的可观测性工具）

每次生成后能看到**完整的 prompt 拼装树**：每个 slot 占多少 token、按什么顺序拼、哪个 marker 被填什么内容。

→ 我们当前调 prompt 全靠盲猜，加这个能让调优速度 ×10。

## 路线 C 关键收获（彻底翻盘原蓝图）

### 蓝图的推荐实测都不能直接用

| 蓝图原推荐 | 实测结论 |
|-----------|---------|
| pytrends | **2023-04 最后 commit，已死** |
| 抓起点番茄 | **反爬 + 法律双风险** |
| 抓 B 站第三方 API | 2026-01 律师函风险 |
| Tavily | ✅ 国外搜索可用（1000 次/月免费），但中文场景有限 |
| Firecrawl | ✅ 提取可用，但收费偏高 |
| SerpAPI | ✅ 可用，按次付费 |

### 替换方案（中文场景实测）

| 用途 | 推荐栈 | 成本 | 备注 |
|------|--------|------|------|
| 中文热点聚合 | **DailyHotApi（自托管 Docker）** | 0 元 | 聚合微博/B 站/抖音/知乎等 50+ 中文站点 |
| 中文搜索 | **博查 BoChaAI** | 0.02 元/次 | 国内合规，无需海外 IP |
| 海外搜索 | **Tavily** | 1000 次/月免费 | 适合做对照、找趋势 |
| 网页提取 | **Jina Reader（500 RPM 免费）+ trafilatura（兜底）** | 0 元 | 把网页转 LLM-ready markdown |

→ 月成本估算：**0-60 元**（取决于搜索调用量）

## 路线 D 关键收获（找到了客观评测基线 + 一篇必抄论文）

### WebNovelBench（**头等收获，直接定为我们的评测公约**）

- **数据集**：4000 篇起点中文网文（玄幻/现实/西幻/历史四类）
- **8 维度评分**：D1 流畅度 / D2 词汇丰富度 / D3 情节连贯 / D4 角色塑造 / D5 对话区分度 / D6 主题深度 / D7 创新性 / D8 整体可读性
- **评委 LLM**：DeepSeek-V3
- **当前 SOTA**：**Qwen3-235B 5.21 分** > DeepSeek-R1 > Gemini-2.5-Pro > GPT-4o
- **HNES 综合分**：QLS = (Sq + Sl) / 2，长篇不衰减证据
- **价值**：直接给我们一套**论文级别的客观评测**，避免凭感觉

### CreAgentive（**最值得借鉴的工程论文**）

- **论文**：[arxiv.org/abs/2509.26461](https://arxiv.org/abs/2509.26461)
- **核心创新 1：Dual Knowledge Graph**
  - Role Graph（角色关系）+ Plot Graph（情节因果），两个 Neo4j 图分开存
  - 我们可以用 Graphiti+Kuzu 实现等价方案
- **核心创新 2：Per-Role Limited Cognition**
  - **每个角色一个轻量 agent**，只能访问自己相关的 prototype 和记忆
  - 这是解决"角色都说同一种话"的根本方法
- **核心创新 3：PlotWeave**
  - 多 Role Agent 接力贡献情节
  - 角色离开主角视野后仍有自己的行动逻辑
- **证据**：千章稳定不衰减，baseline 在 8 章后崩坏

### DOME（NAACL 2025 · 直接证据）

- **核心**：DHO（Dynamic Hierarchical Outline）+ MEM（时序 KG）
- **硬证据**：加 MEM 模块后**章节冲突率从 4.52 降到 0.56（8 倍下降）**
- 我们当前 KG 已有 valid_from/valid_to，**只差 conflict detection 这一步**

### CONCOCT / StoryWriter（参考但不必抄）

- CONCOCT：长篇 pacing 评估方法（"事件具体度"指标）
- StoryWriter：event-based outline + 非线性叙事（NLN）
- 都是值得读的论文，但不是核心借鉴对象

## 关键技术选型一览（调研后的最终建议）

| 方向 | 蓝图原计划 | 调研后建议 | 决策依据 |
|------|-----------|-----------|---------|
| KG / 记忆 | 自研 temporal graph | **Graphiti + Kuzu** | 嵌入式无运维，提供我们做不到的 provenance |
| Lorebook | 借鉴 SillyTavern | **直接抄 30+ 字段 schema** | 现成最完整的设计 |
| 反 AI 味 | 不在原蓝图 | **抄 autonovel slop_score 中文化** | 0 LLM 调用，秒级出分 |
| 评测基线 | 自定义评分表 | **WebNovelBench 8 维度** | 论文级客观 baseline |
| 修订循环 | 蓝图 §4.11 | **照抄 autonovel 4 agent** | adversarial / reader panel / brief / opus review |
| Per-Role | 蓝图 §4.4 | **CreAgentive PlotWeave** | 论文已证明能解决角色雷同 |
| Conflict 检测 | 蓝图未细化 | **DOME 时序 KG conflict** | 论文证据：8 倍下降 |
| 外部素材 | pytrends + 抓起点 | **DailyHotApi + 博查 + Jina** | pytrends 已死，反爬法律风险 |
| MemPalace | 蓝图重点推荐 | **只借思想，零代码** | 仓库太年轻、宣传 >> 实测 |
| Mem0/Letta | 候选 | **不引入** | 抽象错位 / 太重 |

## 引用清单

所有结论可追溯到下面的真实链接：

**autonovel**：
- [autonovel/PIPELINE.md](https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md)
- [autonovel/ANTI-SLOP.md](https://github.com/NousResearch/autonovel/blob/master/ANTI-SLOP.md)
- [autonovel/evaluate.py](https://github.com/NousResearch/autonovel/blob/master/evaluate.py)
- [autonovel/adversarial_edit.py](https://github.com/NousResearch/autonovel/blob/master/adversarial_edit.py)

**SillyTavern**：
- [SillyTavern world-info.js 源码](https://github.com/SillyTavern/SillyTavern/blob/release/public/scripts/world-info.js)
- [SillyTavern PromptManager.js 源码](https://github.com/SillyTavern/SillyTavern/blob/release/public/scripts/PromptManager.js)

**Graphiti**：
- [getzep/graphiti](https://github.com/getzep/graphiti)
- [Graphiti 论文 (arxiv 2501.13956)](https://arxiv.org/abs/2501.13956)

**论文**：
- WebNovelBench
- [CreAgentive (arxiv 2509.26461)](https://arxiv.org/abs/2509.26461)
- DOME (NAACL 2025)
- [CONCOCT (arxiv 2311.04459)](https://arxiv.org/abs/2311.04459)
- [StoryWriter (arxiv 2506.16445)](https://arxiv.org/abs/2506.16445)

**外部素材**：
- DailyHotApi
- 博查 BoChaAI（国内合规中文搜索）
- Tavily / Firecrawl / Jina Reader / trafilatura
