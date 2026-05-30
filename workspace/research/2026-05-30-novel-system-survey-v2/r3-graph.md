# R3 · 图谱管理调研(v2 终稿,聚焦工程落地,优先级档位 B)

> accessed 统一为 **2026-05-30**。
> **优先级锚定**:记忆(R2)= 角色(R5)= 大纲(R1)> **图谱(R3,本档 B)**。本档按 B 档处理——聚焦"图谱在长篇生成里到底有没有 ROI、能不能在现有栈上低成本落地",**不深扒图论/图算法理论**,点到为止。
> 验真说明:本方向 23 条引用经独立 fact-check **全部 `exists=true`**(无幻觉 URL 需剔除);幻觉剔除与基础事实纠正详见文末 "v1 ↔ v2 diff"。
>
> **结论先行**:对一个**中文、离线、按章生成**的小说系统,把"全量知识图谱 + 图数据库 + GraphRAG"当核心基础设施是**负 ROI**;但图谱的退化形态——**按章号打标签的四元组事实表(DOME 路线)**——**ROI 为正**,且能在现有 SQLite 上 low-cost 落地。图数据库只在将来做 reader 端"全书问答 / 角色百科"时才考虑(届时选 **LightRAG**,不选原版 GraphRAG)。

---

## 一、核心问题:图谱在长篇生成里有 ROI 吗?(分场景,每条带 source)

### 场景 A:把图谱当"生成时的全局检索器"(GraphRAG 式)—— ROI 存疑,对中文小说大概率为负

- **GraphRAG 并非普遍优于向量 RAG,优势高度任务相关。**
  《When to use Graphs in RAG: A Comprehensive Analysis for Graph Retrieval-Augmented Generation》(GraphRAG-Bench,arXiv **2506.05690**,ICLR'26,港理工 + 腾讯优图)。
  https://arxiv.org/abs/2506.05690 [accessed:2026-05-30];repo https://github.com/GraphRAG-Bench/GraphRAG-Benchmark [accessed:2026-05-30](MIT,~429 star / 50 fork)。
  关键:多数 GraphRAG 方法相对 LLM 基线**只提升 1–3 个百分点**(RAPTOR 73.58% vs GPT-4o-mini 70.68%);**在推理 / 开放问答上有帮助,但在多选、数学、填空上反而掉点**("引入冗余或弱相关信息")。小说续写是 **generation 任务、不是多跳问答**,落在"收益薄甚至负"的那一侧。

- **控制评测偏差后,此前报告的增益被显著高估。**
  ① 《How Significant Are the Real Performance Gains? An Unbiased Evaluation Framework for GraphRAG》(arXiv **2506.06331**)https://arxiv.org/abs/2506.06331 [accessed:2026-05-30]——修正 answer position / length / trial 偏差后,GraphRAG 增益"**比此前报告温和得多(much more moderate)**"。
  ② 《RAG vs. GraphRAG: A Systematic Evaluation and Key Insights》(arXiv **2502.11371**,v3 2026-03-04)https://arxiv.org/abs/2502.11371 [accessed:2026-05-30]——结论是"**RAG 与 GraphRAG 各有所长、按任务取舍**"(QA + summarization 标准化对比)。
  ⚠️ **诚实标注**:此前流传的具体数字(NQ −13.4%、时效查询 −16.6%、HotpotQA 多跳 +4.5%、延迟 2.3×)来自检索摘要的**二手转述**,abstract 页未逐条复核 [no-source-found:2502.11371 正文逐条数字一手复核]。引用前需开 PDF 核对。

- **成本侧:** 微软 GraphRAG repo 顶部官方挂"**索引昂贵**"警告(https://github.com/microsoft/graphrag [accessed:2026-05-30]);二手测算全量抽取约 **$20–50 / 百万 token**(https://tianpan.co/blog/2026-04-17-graphrag-vs-vector-rag-knowledge-graphs [accessed:2026-05-30],二手博客)。

> 小结:**场景 A 不做。** 多跳全局综合是小说生成几乎用不上的能力,却要付重抽取成本 + 常态掉点风险。

### 场景 B:把图谱当"局部、外科手术式的结构化注入"—— ROI 为正,最值得借鉴

- **只在"制造冲突 / 转折"环节用图,不当全局记忆。**
  《Long Story Generation via Knowledge Graph and Literary Theory》(arXiv **2508.03137**,北京交通大学,英文,无 code)https://arxiv.org/abs/2508.03137 [accessed:2026-05-30]。
  KG 仅服务 "twist plot generation"——以"主角当前目标"为核心节点,生成"障碍节点"挂接;用相邻 outline 的 cosine 相似度路由 twist / 普通路径。人工评测(20 名母语者 pairwise)显著优于 DOC / RecurrentGPT / EX³(对 DOC:89.1% 无主题漂移、95.8% 相关性)。

- **图谱的真实价值在"可控 / 可编辑",不在"自动质量"。**
  《Guiding Generative Storytelling with Knowledge Graphs》(arXiv **2505.24803**,University of the Arts London / Charismatic.ai,英文,无 code,已发 *Int. J. Human-Computer Interaction* 2025)https://arxiv.org/abs/2505.24803 [accessed:2026-05-30]。
  用户研究关键量化:
  - **KG 对故事质量无整体显著收益(p>0.05)**;
  - **动作型叙事显著变好(p=0.039,角色塑造 p=0.016);内省型叙事反而变差(p=0.07,被评"平淡、结构僵硬")**;
  - 但 **92.9%(13/14)用户偏好"编辑 KG"这种交互**,78.5% 给"掌控感"打 Excellent / Very Good。
  **对我方 admin 后台(人工改剧情)直接参考:图谱当"可视化可编辑的剧情骨架"是赢的,当"全自动质量增强"是输的。**

### 场景 C:把图谱当"防前后矛盾的事实记账本"—— ROI 为正,但四元组扁平表即可拿到大部分收益

详见第二节 DOME。一句话:**收益主要来自"结构化一致性记账 + 局部目标 / 冲突建模",这些用轻量四元组表 + 现有 SQLite 就能拿到;图数据库 + 全量 GraphRAG 的额外收益(多跳全局综合)在小说生成里几乎用不上,却要付重抽取成本与同步运维。**

---

## 二、可借鉴方案逐个点评(时效性 / 鲁棒性 / 可行性)

> star / push 日期取自 GitHub(accessed:2026-05-30)。"中文就绪度"按"模型链路是否在中文模型上验证过 + 是否有中文 prompt/文档"评。

### 1. DOME ⭐⭐(最相关,直接对标我方"知识三元组"系统)

- **是什么**:《Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement》,arXiv **2412.13575**,**NAACL 2025**(华南理工 + 鹏城实验室 + 港理工,英文)。
  论文 https://arxiv.org/abs/2412.13575 [accessed:2026-05-30];官方 ACL Anthology https://aclanthology.org/2025.naacl-long.63/ [accessed:2026-05-30]。
- **这就是用户说的"四元组扁平表"**:记忆模块 **MEM(基于 temporal knowledge graph)**,数据模型 = 四元组 **`<subject, action, object, index>`,index = 章节号**。LLM 逐句抽 triple 后追加章号成四元组;检索 = 实体匹配 + **cosine 相似度(阈值 0.75)** 过滤 + LLM 5 分制相关性打分取 top-k,再以**自然语言**喂给大纲与正文。
  ⚠️ **重要更正(v2)**:数据模型虽是扁平四元组,但**官方参考实现(repo)实际把它存进 Neo4j**(需配 Neo4j 凭据,跑 `1storyline.py` → `DOME.py`)。即"扁平四元组"是**逻辑视图**,**不代表非要图数据库**——我方完全可以用 SQLite 表实现同一逻辑。
- **效果(强证据)**:消融去掉 MEM,冲突率从 **0.56% 飙到 4.52%**(Qwen1.5-72B-Chat);人工评测五项第一。**直接证明"章号标注的事实记账"对长程一致性是刚需。**
- **时效性**:NAACL 2025;repo 提交数少(prototype 级),**not stale**。
- **鲁棒性**:repo `Qianyue-Wang/Generating-Long-form-Story-Using-Dynamic-Hierarchical-Outlining-with-Memory-Enhancement`(https://github.com/Qianyue-Wang/Generating-Long-form-Story-Using-Dynamic-Hierarchical-Outlining-with-Memory-Enhancement [accessed:2026-05-30])——**~19 star,Python,license 未标注**(prototype 级;**license 缺失 = 合规风险,代码不可直接复用,只能照方法复现**)。
- **可行性**:**adoption cost = low**。**中文就绪度极高——实验本身就在 Qwen1.5-72B-Chat 上做**,prompt 体系天然适配中文。
  **本档最高优先级借鉴对象**:把我方现有 `knowledge_triples`(SQLite)升级为 `<主体, 谓词/动作, 客体, 章号>` + `valid_from / valid_to`,检索沿用"实体匹配 + 向量相似 + LLM 打分"三步。**零新基础设施。**

### 2. Graphiti(getzep)—— 双时态、生产级,但定位错配、过重

- **是什么**:开源时序知识图谱引擎(Zep 底座),"Build Temporal Context Graphs for AI Agents"。bi-temporal:每条边带 `t_valid` / `t_invalid`,事实失效是"作废"非"删除",可做时间点查询。
  https://github.com/getzep/graphiti [accessed:2026-05-30];配套论文《Zep: A Temporal Knowledge Graph Architecture for Agent Memory》arXiv **2501.13956** https://arxiv.org/abs/2501.13956 [accessed:2026-05-30]。
- **时效性**:活跃维护(2026 年仍在更新)。
- **鲁棒性**:**~26,741 star / 2,667 fork,Apache-2.0,Python**——**production 级,六者中成熟度最高之一**。
- **可行性**:**adoption cost = high**。支持自定义 Pydantic 实体 / 边(可建 Character / Location / Event,契合我方),LLM 可换 Qwen / DeepSeek;但**必须挂图数据库(Neo4j / FalkorDB / Kuzu / Neptune)**,对我方 SQLite + Chroma 栈是新增重组件。**中文就绪度 = 中**:能处理中文实体 / 事实,但抽取 prompt 是英文、无中文 prompt 包,需自行本地化。
  **定位错配**:Graphiti 为"agent 对话记忆 / 高频增量更新"设计;小说是离线批量按章生成,且**只需单时态(章号),双时态(事件发生时间 vs 摄入时间)在小说里冗余**。
  **结论:抄思想(失效不删除 + 有效区间),不引入框架。**

### 3. Microsoft GraphRAG —— 全局综合强,但成本 / 定位双错配

- **是什么**:"A modular graph-based RAG system",从非结构化文本抽结构化信息的数据管线。https://github.com/microsoft/graphrag [accessed:2026-05-30]。
- **时效性**:活跃维护(2026 年仍在更新)。
- **鲁棒性**:**~33,325 star / 3,523 fork,MIT,Python**——production 级(但官方声明 "demonstration, not officially supported")。
- **可行性**:**adoption cost = high / rewrite**,索引昂贵(官方警告)。中文就绪度:未见官方中文支持 [no-source-found:GraphRAG 官方中文支持]。
  **定位错配**:解决"大语料全局主题综合问答",非"边生成边维一致"。小说生成 **不推荐**。
- **必看替代:LazyGraphRAG**(微软研究院 blog,2024-11-25,Darren Edge 等)https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ [accessed:2026-05-30]:**消除昂贵的前置索引**,索引成本量级≈向量 RAG、延迟抽取。**若将来做"全书问答 / 读者检索",优先考虑 LazyGraphRAG / LightRAG,别上原版全量 GraphRAG。**

### 4. LightRAG(HKUDS)—— 性价比最高的"图 + 向量"折中,中文最友好

- **是什么**:《LightRAG: Simple and Fast Retrieval-Augmented Generation》,arXiv **2410.05779**(HKU,Chao Huang 组),**EMNLP 2025 接收(repo 标注)**。双层检索(low / high-level)+ 图与向量结合。
  https://arxiv.org/abs/2410.05779 [accessed:2026-05-30];repo https://github.com/HKUDS/LightRAG [accessed:2026-05-30]。
- **时效性**:**极活跃(2026 年仍在高频更新)**。
- **鲁棒性**:**~35,969 star / 5,082 fork,MIT,Python**——**六者中 star 最高,production 级**。
- **可行性**:**adoption cost = medium**。支持增量插入、文档删除自动重建 KG;后端可用 Postgres / Mongo / Neo4j / OpenSearch / **JSON-KV(可纯 KV 起步,不强制图数据库)**。**中文就绪度 = 高:官方提供中文 README。**
  **定位**:仍是"检索器"而非"生成时记账";**若做 reader 端"全书智能问答 / 角色百科",LightRAG 是首选**(比 GraphRAG 轻、比纯向量强、中文现成)。**与 R3 生成时记账是两件事,别混用。**

### 5. EvolvTrip —— 角色心理时序图(与 R5 角色强相关,R3 里偏理论)

- **是什么**:arXiv **2506.13641**《EvolvTrip: Enhancing Literary Character Understanding with Temporal Theory-of-Mind Graphs》(曼彻斯特 / KCL / 华为,英文,2025-06)https://arxiv.org/abs/2506.13641 [accessed:2026-05-30]。perspective-aware 时序 ToM 图。
  **schema = (Character, Predicate, Object) + 时间标签**,谓词为 **BelievesAbout / FeelsTowards / IntendsTo / DesiresFor**;例:"(King Lear, BelievesAboutCordelia, Cordelia's silence is defiance)"。**存储是 JSON 结构化文本,非图数据库。** benchmark = LitCharToM。
- **效果**:7B–72B 全尺度一致提升;**Qwen3-14B 58.04%→63.46%(+5.42)、DeepSeek-R1 70.74%→74.44%(+3.7)、GPT-4o 70.86%→73.36%(+2.5)**;**对小模型增益更大**。
- **时效性**:2025-06。**鲁棒性**:repo `Bernard-Yang/EvolvTrip`(https://github.com/Bernard-Yang/EvolvTrip [accessed:2026-05-30])——star/fork 极低、license 不明——**research-only,不可直接商用**。
- **可行性**:**adoption cost = high(自建)**,且面向"理解既有文学"非生成。
  **借鉴点**:"角色 belief / desire / intention 随章节演化"的 4 谓词 schema + JSON 存储,**适合并入 R5 角色记忆**,而非 R3 图谱;它用 Qwen3 / DeepSeek 实验,**中文模型链路已验证**(虽数据是英文经典文学)。**这正好回答 v1 r5-roles 的 open question"belief/desire 随章节变化如何建模"。**

### 6. CREFT —— 多 agent 抽人物关系图(抽取向,非生成向)

- **是什么**:arXiv **2505.24553**《CREFT: Sequential Multi-Agent LLM for Character Relation Extraction》(英文,2025-05,**无公开 code** [no-source-found:CREFT 官方代码仓库])https://arxiv.org/abs/2505.24553 [accessed:2026-05-30]。顺序多 agent:知识蒸馏建基础人物图 → 迭代精炼(人物构成 / 关系抽取 / 角色识别 / 分组),抽 SPO triple,韩剧数据集,显著优于单 agent。
- **时效性**:2505。**鲁棒性**:论文级 prototype,无 repo 可评。
- **可行性**:**adoption cost = medium**,但方向相反——它是"**从已有文本抽关系**",我们要"**生成时维护关系**"。**唯一借鉴点**:多 agent"先抽后校"比单次抽取更准更全,可用于我方 **ChapterExtractor** 的人物关系抽取。中文就绪度:方法语言无关,但实验是韩语,无中文验证。

### 旁路发现:EnigmaToM(实体状态神经知识库)

arXiv **2503.03340**《EnigmaToM: Improve LLMs' Theory-of-Mind Reasoning Capabilities with Neural Knowledge Base of Entity States》(**ACL 2025 Findings**)https://arxiv.org/abs/2503.03340 [accessed:2026-05-30];repo `seacowx/EnigmaToM`(https://github.com/seacowx/EnigmaToM [accessed:2026-05-30],Python,license 需自行确认)。维护"实体状态"知识库构建空间场景图、做 belief tracking,在 ToMi / HiToM / FANToM 上提升 ToM。与 DOME"实体状态记账"同源,可作"角色 / 物品状态随章节变化"建模的第二参考。

---

## 三、综合判断与 Top 候选

**对本系统(中文、离线按章生成、现有栈 = SQLite + Chroma + LangGraph,R3 仅 B 档):**

- **不要**为 R3 引入图数据库(Neo4j / FalkorDB)或全量 GraphRAG。理由:
  (a) 小说生成是 generation 任务,GraphRAG 多跳优势用不上且常掉点(GraphRAG-Bench 2506.05690);
  (b) 增益经偏差修正后被高估(2506.06331);
  (c) 双时态对小说冗余(只需章号单时态);
  (d) 抽取成本 + 图同步运维负担高,而 R3 不是重点(优先级低于 R1/R2/R5)。
- **要**把图谱"降维"成 **DOME 式四元组事实表**,复用现有 SQLite——正 ROI 且 low-cost,是本档核心动作。

**Top 候选(按落地优先级):**

1. **DOME 四元组 schema(首选,立即可做)** —— 现有 `knowledge_triples` → `<主体, 谓词/动作, 客体, 章号>` + `valid_from / valid_to`(章号区间);检索"实体匹配 + 向量相似(阈值起点 ~0.75,中文需重调)+ LLM 相关性打分"三步。零新基础设施,中文现成(Qwen 上验证),消融证明对一致性刚需(冲突率 0.56%→4.52%)。**直接服务 Consistency agent。**

2. **Graphiti 的"双时态思想"(只抄思想,不引框架)** —— 事实失效用"作废 + 有效区间"而非物理删除,支持"第 N 章时世界是什么样"回溯;用 SQLite `valid_to` 字段实现。**直接补上 v1 r2-memory 指出的"章号标注缺失导致无法时间点回溯"这一缺口。**

3. **局部 KG 做"目标-障碍 / 冲突建模"(2508.03137,中期可做)** —— Planner / World 环节以"主角当前目标"为核心节点临时构图、生成转折障碍、用完即弃。轻量按需,正 ROI。**回应 v1 r1-outline 的 open question"转折如何自动生成且不突兀"。**

4. **角色心理 4 谓词 schema(EvolvTrip,并入 R5,不属 R3)** —— belief / desire / intention / feeling + 章号,JSON 存储,小模型增益大;**归到 R5 角色而非 R3 图谱**。

5. **LightRAG(仅当做 reader 端全书问答时)** —— 中文 README 现成、可纯 KV 起步、MIT、最活跃。面向"读者检索 / 角色百科"的最佳折中,**与 R3 生成时记账解耦**;同场景的微软方案选 LazyGraphRAG,不选原版 GraphRAG。

---

## 四、Open Questions(需后续验证 / 决策)

1. **四元组扁平表 vs 真图,在我方"一致性检查(Consistency agent)"上的实测差距?** 现有文献都在 QA / 通用生成上测,**没有"中文网文长篇、章级一致性"这一精确场景的对照实验** [no-source-found:中文网文章级一致性 图谱 vs 扁平表 对照实验]。建议自建小规模 A/B(SQLite 四元组 vs Graphiti)再定。
2. **2502.11371 的具体数字(NQ −13.4% / 时效 −16.6% / HotpotQA +4.5% / 2.3× 延迟)是二手转述**,需打开正文 / PDF 逐条复核后再引用。
3. **DOME repo 无 license + 用 Neo4j** —— 方法可借鉴,代码不可直接复用;且需把它的 Neo4j 存储替换成我方 SQLite。
4. **CREFT 无公开代码** —— 多 agent 关系抽取精炼策略只能照论文复现。
5. **检索阈值 0.75 是 DOME 在英文 / 特定模型下的取值**,中文 + 我方 embedding 需重新调参。
6. **图谱"可控性收益"(2505.24803)依赖 human-in-the-loop 且对内省型叙事会掉点** —— 全自动生成时收益打折;若 admin 后台要"可视化改剧情",价值上升。需结合产品形态决策。
7. **EvolvTrip / EnigmaToM repo 的 license 未确认** —— 若要复用代码须先核实许可。

---

## v1 ↔ v2 diff

> v1 基线 = `workspace/research/2026-04-28-novel-system-survey/`。**该目录只有 r1 / r2 / r4 / r5 / r6 五份,没有 `r3-graph.md`** —— 图谱方向(R3)在 v1 中**根本未独立调研**。因此本 v2 r3-graph.md 整体是**净新增方向**;以下 diff 同时对照 v1 中"散落在 r1/r2/r5 里的图谱相关碎片"。

### 新增(v1 完全没有)
- **整个 R3 方向**:v1 无 r3-graph.md。v2 首次给出"图谱在长篇生成有无 ROI"的分场景结论(A 全局检索 / B 局部注入 / C 事实记账)。
- **GraphRAG 怀疑论证据链**:GraphRAG-Bench(2506.05690)、无偏评测框架(2506.06331)、RAG vs GraphRAG 系统评测(2502.11371)—— v1 完全未涉及,据此明确"全量 GraphRAG 对小说生成负 ROI"。
- **六个可借鉴方案的工程评级**:DOME / Graphiti / Microsoft GraphRAG(+LazyGraphRAG)/ LightRAG / EvolvTrip / CREFT 的时效性 + 鲁棒性(star/license)+ 可行性(adoption cost + 中文就绪度)逐条评分,v1 无此粒度。
- **明确"图数据库不要、四元组扁平表要"的落地决策** + "双时态对小说冗余、只需章号单时态"的判断。
- **旁路发现 EnigmaToM(2503.03340)**、局部 KG 转折建模(2508.03137)、可控性用户研究(2505.24803)—— 均为 v1 没有的新材料。

### 纠正 / 深化(v1 提过但 v1 角度不同或不准)
- **DOME 的角色重定位**:v1 r1-outline 只把 DOME(2412.13575)当"动态分层大纲"的来源。v2 揭示 DOME 的 **MEM 四元组 `<subject, action, object, index=章号>`** 才是与 R3"知识三元组"最直接对标的部分,并补强消融证据(冲突率 0.56%→4.52%)。
- **关键更正:DOME 的"扁平四元组"在官方实现里其实存进 Neo4j**。即"扁平四元组"是逻辑视图,不等于必须图数据库——我方可用 SQLite 复现同一逻辑。(此点若仅看论文数据模型极易误判,v2 据 repo 纠正。)
- **回填 v1 r2-memory 缺口**:v1 r2 指出"knowledge_triples 谓词无章号标注、无法时间点回溯"且列为 open question。v2 给出具体解法(DOME 章号四元组 + Graphiti 式 `valid_from/valid_to` 有效区间,SQLite 实现)。
- **回填 v1 r5-roles 缺口**:v1 r5 的 open question"belief/desire 随章节变化如何建模"——v2 用 EvolvTrip 4 谓词 schema(2506.13641,中文模型已验证)给出答案,并明确**归 R5 不归 R3**。
- **回填 v1 r1-outline 缺口**:v1 r1 的 open question"转折如何自动生成且不突兀"——v2 用局部 KG 目标-障碍建模(2508.03137)回应。

### 删除 / 剔除
- **幻觉 URL 剔除:无**。本方向 23 条引用经独立 fact-check **全部 `exists=true`**,没有 `exists=false` 的伪造链接需要删除。
- **基础事实纠正(跨方向,记录在此以防误用)**:外部材料中出现的 **"PerRoleCognition"** 经核查为**杜撰**(arXiv / Google Scholar / 全网均无此文献)——但该词**本就不出现在 R3 图谱材料里**(属 R5 角色认知话题),故 R3 正文无需删除任何条目;仅在此标注,提醒最接近的真实工作是 RPNA(arXiv 2510.24677)/ RoleRAG(arXiv 2505.18541)/ Character-LLM(arXiv 2310.10158),引用时勿写成 "PerRoleCognition"。
- **降级为"二手待核"而非删除**:2502.11371 的逐条数字(NQ −13.4% 等)在 v2 中**明确标注为二手转述**(见 Open Question 2),未当作一手结论使用——保留但加警示,而非直接引用。

### 与其他方向的边界(避免重复劳动)
- **EvolvTrip(角色心理 4 谓词)→ 交 R5 角色**;R3 只记录、不深做。
- **LightRAG / LazyGraphRAG(检索器)→ 属 reader 端"全书问答"产品功能**,与 R3"生成时一致性记账"解耦,不在本档落地范围内。
- **多 agent 抽取(CREFT)→ 可喂给 R2/ChapterExtractor**,R3 仅点出借鉴点。

---

*（v2 终稿,2026-05-30。优先级 B 档:结论与落地动作已收敛,理论细节按 B 档点到为止,不再扩写。）*
