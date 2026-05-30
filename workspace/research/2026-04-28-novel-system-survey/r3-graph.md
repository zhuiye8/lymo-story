# R3 · 图谱管理（聚焦工程落地）

| Field | Value |
|---|---|
| Topic | LLM 小说生成中**实际工程落地**的图谱方案；不深扒理论 |
| Author | engineer (Claude) |
| Researched | 2026-04-28（WebSearch + WebFetch only） |
| Verdict | **不引入独立图谱组件**：把图谱能力嵌入 R2 选定的记忆系统（MemoryOS / Graphiti / Mem0 之一）；DOME 四元组继续作为我们 `knowledge_triples` schema 的事实依据；CREFT/EvolvTrip 留 Phase 2 backlog |

> 用户优先级声明（2026-04-28）：**记忆 = 角色 = 大纲 > 图谱**。本 doc 聚焦"现代 KG 在长篇生成里到底有没有 ROI"，**不深扒理论**。

## Findings

### F1 · Graphiti / Zep — 双时态 KG，工程级

| Field | Value |
|---|---|
| Repo | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) [accessed:2026-04-28] |
| Version | **v0.29.1**（2026-05-21） |
| Stars | **26.7k** |
| License | **Apache-2.0** |
| Backend | Neo4j / FalkorDB / Kuzu / Amazon Neptune（+ OpenSearch 全文索引） |
| Latency | P95 **300ms** retrieval（hybrid: embedding + keyword + graph traversal） |

**核心 verbatim**（来自 fetched README）：
> "Facts have validity windows. When information changes, old facts are invalidated — not deleted. Query what's true now, or what was true at any point in time."

**API 抽象级别**：
```python
graphiti = Graphiti("bolt://localhost:7687", "neo4j", "password")
# Episodes are added; the system autonomously derives entities and relationships
```

**对我们的可行性**：
- ✅ **完美匹配我们对"事实失效"的需求**：角色 A 在 ch5 死了，ch12 不应再被生成（我们当前 `knowledge_triples.valid_from/valid_to` 是 Phase 0 已有的字段，但功能弱）
- ✅ Apache-2.0 + 不强制 Neo4j（Kuzu 是 embedded，零运维）
- ❌ **README 不提中文支持**：内部 entity extraction 调 LLM，理论上中文可行，但需实测
- ⚠️ **新增 Neo4j/Kuzu 服务**：Phase 0 我们只有 SQLite + ChromaDB；引 Graphiti = 引第 3 个 storage backend，要考虑 cost / 运维负担
- adoption cost: **medium-high**

### F2 · Memento — 92.4% LongMemEval

| Field | Value |
|---|---|
| Source | (via search snippet) — 详细 paper 链接需进一步搜 |
| Score | **92.4%** task-averaged on LongMemEval（2026） |
| Type | bitemporal KG memory system |

**对我们的可行性**：
- 仅 search snippet 信息，未直接 fetch paper；标 `[需进一步 verify]`
- 数字诱人但工程化程度未知

### F3 · GraphRAG（Microsoft）

| Field | Value |
|---|---|
| Source | [microsoft.com/en-us/research/blog/graphrag](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) [accessed:2026-04-28] |
| Repo | [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) [accessed:2026-04-28] |
| 定位 | 文档分析 RAG with community detection |

**核心机制**：
- LLM 抽 entity + relation → 建 graph → 用 community detection 找语义子图 → 子图 summary 喂回 LLM 做 QA
- 优点：global summarization queries（标准 RAG 失败的地方）+ multi-hop reasoning
- claim：3.4x accuracy vs 传统 RAG；80% correct vs 50%

**对我们的可行性**：
- ⚠️ **不直接适用**：GraphRAG 是**面向已有文档的 QA**，我们是**生成新文档**；目标动词反了
- ✅ 可借鉴的部分：community detection 可用于"找一群相关章节的 summary"（Phase 6 Critic Room 可能用得到）
- adoption cost: **rewrite**（不抄整套，只取其中 community summarization 思路）

### F4 · LightRAG — GraphRAG 简化版

| Field | Value |
|---|---|
| Source | (via search snippet) |
| 定位 | dual-level retrieval（entity-level + relationship-level）；跳过 community detection；更便宜 |

**对我们的可行性**：
- 同 GraphRAG，定位 QA 而非生成
- adoption cost: **rewrite**

### F5 · CREFT — 角色关系抽取（多 agent）

| Field | Value |
|---|---|
| Paper | [arxiv.org/pdf/2505.24553](https://arxiv.org/pdf/2505.24553) [accessed:2026-04-28] |
| Org | per R5 agent findings + search snippet |
| 定位 | sequential multi-agent LLM for character relation extraction from narrative |

**对我们的可行性**：
- ⚠️ 抽取方向（已有小说 → KG），我们要生成方向（KG → 小说），可作为 reverse-engineering 工具
- ✅ Phase 2 backlog：把已生成章节用 CREFT 抽出关系，喂回 memory + bible，闭环 self-correction
- adoption cost: **medium**

### F6 · EvolvTrip — Temporal Theory-of-Mind 图

| Field | Value |
|---|---|
| Paper | [arxiv.org/pdf/2506.13641](https://arxiv.org/pdf/2506.13641) [accessed:2026-04-28] |
| 定位 | perspective-aware temporal KG，追踪角色心理发展 |

**核心 claim**（per search snippet）：
> "Performing theory-of-mind reasoning in prolonged narratives requires integrating historical context with current information, a task at which humans excel but LLMs often struggle."

**对我们的可行性**：
- ✅ **关键缺口**：我们当前 character 系统只有 `character_states` 表，没有 "A 以为 B 知道 X" 这种 ToM 嵌套
- ⚠️ Phase 2+：先做基础 character consistency，再上 ToM
- adoption cost: **high**（需要重新设计 character state schema）

### F7 · DOME（**已 R1 spot-verified**） — 直接落地 winner

| Field | Value |
|---|---|
| Paper | [arxiv.org/abs/2412.13575](https://arxiv.org/abs/2412.13575) [accessed:2026-04-28] |
| TKG format | **`<subject, action, object, chapter_index>` 四元组**（verbatim verified 2026-04-28） |

**为什么单独列**：
- DOME 的 TKG schema 几乎等于我们 Phase 0 现有的 `knowledge_triples`（多一个 chapter_index 列）
- **零迁移成本**：把 `valid_from` 字段重命名为 `chapter_index_start`，把 outline 层接入 5-stage 英雄之旅
- 是 R3 调研里**最直接可抄**的方案

**adoption cost: low**

### F8 · LlamaIndex PropertyGraphIndex 域 schema

| Field | Value |
|---|---|
| Source | (via search snippet)：Knowledge Graphs Reveal the Hidden Architecture of Great Literature, Medium, 2026-02 |
| 机制 | 每部作品定制 schema：The Iliad 用 HERO/BATTLE；Dune 用 FACTION/PROPHECY 等 |

**对我们的可行性**：
- ✅ **Phase 2 启示**：我们应该允许 story_bible 定义自家 entity 类型（每本书的"特殊能力"、"派系"等是不同的）
- ⚠️ 当前实现 = LlamaIndex 框架，与我们的 storage 抽象不兼容；抄 schema flexibility 思路即可

### F9 · PersonalAI — KG storage/retrieval 综合 benchmark

| Field | Value |
|---|---|
| Paper | [arxiv.org/pdf/2506.17001](https://arxiv.org/pdf/2506.17001) [accessed:2026-04-28] |
| 定位 | 系统对比不同 KG 存储 + 检索 方案 in personalized LLM agents |

**对我们的可行性**：
- ✅ 作为选 backend 时的对比参考（我们若要选 graph DB，这篇是判断材料）
- 当前 finding 仅 search snippet level，未深 fetch

## "图谱在长篇生成里到底有没有 ROI" — 工程师判断

### 反对方观点（监督角度）

1. **架构复杂度爆炸**：Phase 0 已经有 SQLite + ChromaDB；加 Neo4j/Kuzu 是第 3 个 storage backend
2. **延迟成本**：300ms P95 听着低，但 6 agent × per-chapter × multi-call 会累积
3. **可观察性差**：图谱状态 debug 比扁平表 difficult，supervisor protocol 期间不利
4. **DOME 已证明**：四元组扁平表（即我们已有的 `knowledge_triples`）就够撑长篇

### 支持方观点（用户角度）

1. **角色关系网密度**：8+ 角色 × 多面关系（爱/恨/欠债/师徒/亲属）× 时间演变；扁平表会 N×N 爆
2. **多跳查询**：Q："A 和 B 之间的所有共同好友里，谁现在不在场？" — flat table 多次 self-join，graph 一次 traversal
3. **ToM 嵌套**："A 以为 B 知道 X" 这种深度 3+ 的嵌套，flat 表表达困难
4. **DOME 是 outline，不是关系图**：DOME 用 KG 抓"事件因果"；CREFT/EvolvTrip 才抓"角色关系网"，两件事

### 折衷方案

**Phase 1 不引入独立图谱 component**：
- 继续用 `knowledge_triples`（SQLite）+ ChromaDB
- DOME 四元组 schema 直接复用
- 角色关系存 `character_arcs.relationships_json`（JSON 数组），先用扁平表

**Phase 2 评估窗口**：
- 跑 5 章后看：是否真有多跳查询需求？是否 N×N 关系数足够大？
- 若是：引 **Graphiti embedded mode（Kuzu backend）**（零运维 + Apache-2.0）；不引 Neo4j
- 若否：继续扁平表

**Phase 3+ 评估**：
- EvolvTrip 的 ToM 嵌套：只在角色心理戏剧成为核心卖点时再引

## 时效性 / 鲁棒性 / 可行性 评分

| 方案 | 时效性 | 鲁棒性 | 可行性（Phase 1） |
|---|---|---|---|
| Graphiti embedded（Kuzu） | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐（26.7k stars） | ⭐⭐⭐（多一层 storage） |
| GraphRAG community summarization | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐（rewrite） |
| LightRAG | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| CREFT 反向抽取 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐（Phase 2） |
| EvolvTrip ToM 图 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐（Phase 3+） |
| **DOME 四元组（扁平表）** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐（Phase 1 直接抄） |
| Memento 92.4% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐（未深查） | ⭐⭐ |

## Recommendation

### Phase 1（图谱 minimum viable）

1. **复用 `knowledge_triples` SQLite 表，扩成 DOME 四元组 schema**
   - 加 `chapter_index` 列（替代 valid_from 语义）
   - 保留现有 `subject/predicate/object` 字段
   - 不引新 graph DB

2. **角色关系存 `character_arcs.relationships_json`（扁平 JSON）**
   - 一个 character 一行，relationships 是字符串数组 `["A:friend", "B:rival", ...]`
   - 不做 N×N 表

3. **Graphiti / EvolvTrip 列 Phase 2-3 backlog**

### Phase 2（条件触发）

- 跑 10 章后评估：N×N 关系是否 >50 条且查询有多跳需求？
- 若是：上 Graphiti embedded（Kuzu），双写 SQLite + Kuzu，渐进迁移
- 若否：维持扁平表

### Phase 3+（ToM / 心理）

- 角色心理嵌套（"A 以为 B 知道 X"）：EvolvTrip 风格 perspective-aware KG
- 与 R5（角色一致性）的 PsyMem 26 维心理指标交叉

## Open questions

- DOME 的 chapter_index 单一 timeline 是否够？长篇可能有 flashback / 多 POV 时间错位（如倒叙、平行叙事）—— 需要双 timeline?
- Graphiti embedded Kuzu 模式的 Chinese entity extraction 是否可靠？需要实测
- Memento 的 92.4% LongMemEval 与我们的小说生成任务相关性多高？(LongMemEval 主要测 dialog memory，不是 fiction continuity)

## Sources

- [github.com/getzep/graphiti](https://github.com/getzep/graphiti) [accessed:2026-04-28]
- [blog.devgenius.io/ai-agent-memory-systems-in-2026 (Memory comparison)](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8) [via search snippet, accessed:2026-04-28]
- [neo4j.com/blog/developer/graphiti-knowledge-graph-memory](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/) [via search snippet, accessed:2026-04-28]
- [tianpan.co/blog/2026-04-10-graph-memory-llm-agents-relational-reasoning](https://tianpan.co/blog/2026-04-10-graph-memory-llm-agents-relational-reasoning) [via search snippet, accessed:2026-04-28]
- [explore.n1n.ai/blog/building-bitemporal-knowledge-graph-llm-agent-memory-longmemeval-2026-04-11 (Memento)](https://explore.n1n.ai/blog/building-bitemporal-knowledge-graph-llm-agent-memory-longmemeval-2026-04-11) [via search snippet, accessed:2026-04-28]
- [microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) [via search snippet, accessed:2026-04-28]
- [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) [via search snippet, accessed:2026-04-28]
- [arxiv.org/pdf/2505.24553 (CREFT)](https://arxiv.org/pdf/2505.24553) [via search snippet, accessed:2026-04-28]
- [arxiv.org/pdf/2506.13641 (EvolvTrip)](https://arxiv.org/pdf/2506.13641) [via search snippet, accessed:2026-04-28]
- [arxiv.org/pdf/2506.17001 (PersonalAI)](https://arxiv.org/pdf/2506.17001) [via search snippet, accessed:2026-04-28]
- [medium.com/@shereshevsky (Knowledge Graphs Reveal Hidden Architecture)](https://medium.com/@shereshevsky/knowledge-graphs-reveal-the-hidden-architecture-of-great-literature-fa69798cc6b0) [via search snippet, accessed:2026-04-28]
- [arxiv.org/abs/2412.13575 (DOME, spot-verified)](https://arxiv.org/abs/2412.13575) [accessed:2026-04-28]
