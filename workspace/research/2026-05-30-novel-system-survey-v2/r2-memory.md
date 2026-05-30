# R2 · 长程记忆系统 — 终稿 (v2)

> **调研日期 [accessed:2026-05-30]。** 本稿在 clean-room 重做基础上综合而成:所有存活 claim 的引用 URL 均已逐条独立验真(verdict=exists:true),并应用了三项基础事实核查结论。
> **场景锚定:中文 + 长篇连载小说连续性**(几十~几百章,角色/世界/伏笔跨章一致)。这与主流"agent/chatbot 个性化记忆"场景有本质差异,下文逐方案按此差异打分。
> **用户优先级:记忆(R2) = 角色(R5) = 大纲(R1) > 图谱(R3)。** 故 S 档方案写到可落地深度;B/C 档点到为止;图谱机制只借不上 Neo4j 全家桶。

---

## 〇、场景错位警告(先看,决定全文取舍)

主流记忆系统(Mem0 / Letta / Zep / MemoryOS / MemOS…)几乎都为**对话式 agent 的"用户画像 + 多 session 召回"**优化,其基准(LoCoMo / LongMemEval)也都是 user-assistant 聊天记录。小说生成的记忆需求与之重叠但**不等价**:

| 维度 | Agent 对话记忆(主流优化目标) | 长篇小说记忆(我们的需求) |
|---|---|---|
| 记忆主体 | 单一 user 的偏好/事实 | 多角色,每角色独立记忆 + 关系网 |
| 时间模型 | wall-clock 真实时间戳 | **章节序号(逻辑时间)**,非真实时间 |
| 写入来源 | 用户随口说的话(噪声大) | **我们自己生成的正文**(可控、可结构化抽取) |
| 核心痛点 | "记住用户上次说什么" | **不能自相矛盾**(伏笔回收、人设漂移、世界规则) |
| 遗忘 | 旧偏好可衰减遗忘 | **伏笔绝不能遗忘**,但要能"按当前章节"过滤可见性 |

**结论:没有任何一个开源系统能开箱即用。** 最贴合的反而是 ① Generative Agents 的 memory-stream 打分思想、② 时序知识图谱(bi-temporal)的"事实失效"机制、③ 专门做长篇小说的 **DOME**——后者的记忆 schema 几乎就是我们需要的。建议:**不照搬单一系统,在现有 `LayeredMemory` + `KnowledgeGraph` 上组合"经验证的机制"**。

---

## 一、S 档方案(最高价值,写到可落地深度)

### 1. DOME — 唯一直击"长篇小说"的 temporal-KG 记忆增强,schema 与我们同构 ⭐ 核心蓝本

- **论文**:*Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement*,arXiv:2412.13575。https://arxiv.org/abs/2412.13575 [accessed:2026-05-30]
- **正式收录**:**NAACL 2025 Long Papers**(Proceedings of the 2025 Conference of NAACL-HLT, Vol.1: Long Papers, pp.1352–1391)。aclanthology PDF:https://aclanthology.org/2025.naacl-long.63.pdf [accessed:2026-05-30]
  > **验真补充**:arXiv 抽象页本身未声明 NAACL;但 ACL Anthology 官方记录确认其收录于 2025 NAACL-HLT 长文卷,**NAACL 2025 venue 成立**(此前 v1 阶段曾对 venue 存疑,现已坐实)。
- 作者:Qianyue Wang, Jinwu Hu, Zhengping Li, Yufeng Wang, Daiyuan Li, Yu Hu, Mingkui Tan(华南理工系)。提交 2024-12-18。
- **记忆架构(关键,直接抄)**:Memory-Enhancement Module(MEM)用**时序知识图谱**存已生成正文,核心是**四元组 `<subject, action, object, chapter_index>`**——逐句 LLM 抽三元组再附章节号,忽略副词/修饰等"非重要信息"。检索为实体级四元组查找 + LLM 侧语义过滤(主语/宾语/动作相似度 + 事件相关性 + "潜在写作价值")。配 **Temporal Conflict Analyzer**:按规则分组四元组 + LLM-as-judge 判时序/语义冲突,定义冲突率 `CR = m/N`。
- **效果**:MEM 把冲突率大幅压低(论文报告冲突率较"无 MEM 的 DOME"下降约 −87.6%,较 Re3 下降约 −27%);DHO 在 Distinct/Entropy-2 等多样性指标上提升;人评 5 维(plot completeness / coherence / relevance / interestingness / expression)全第一。基线对比 Re3 / DOC。生成长度 ~7,100 词 vs 基线 ~3,900 词。
- **模型**:用 **Qwen1.5-72B-chat** 跑(并验证 Llama-3-70B-Instruct / Yi1.5-34B-chat 可迁移)→ 全部中文友好。数据集为 DOC 的 20 个**英文** premise。
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2024 末 / 2025,**新**。
  - 鲁棒性:学术 prototype,无现成生产库;但方法清晰、可自实现;**未用中文数据集** `[no-source-found:DOME 中文数据集/中文实验]`。
  - 可行性:**medium**(需自实现,但 schema 与我们现有 `knowledge_triples` 几乎同构,改造成本低)。
- **对我们的价值(最高)**:`<主语, 动作, 宾语, 章节号>` + 冲突分析器,正是我们 `KnowledgeGraph`(temporal triples + `valid_from/valid_to` chapter)该长成的样子。**作为 R2 核心方法蓝本。**

### 2. Generative Agents — 记忆流检索公式(recency / importance / relevance)⭐ 必抄

- **论文**:Park et al., *Generative Agents: Interactive Simulacra of Human Behavior*,arXiv:2304.03442,**UIST 2023 Best Paper**。https://arxiv.org/abs/2304.03442 [accessed:2026-05-30]
- **ACM 全文**:https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763 (DOI 10.1145/3586183.3606763) [accessed:2026-05-30]
- **开源**:https://github.com/joonspk-research/generative_agents [accessed:2026-05-30]
- **分层记忆 / 重要性评分 / 时间衰减三件套的源头**。检索打分(因 arXiv PDF >10MB 抓取失败,公式从二手权威源核实——上方 ACM 全文,以及 Frontiers in Psychology 2025 *Enhancing memory retrieval in generative agents through LLM-trained cross attention networks* https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1591618/full [accessed:2026-05-30],后者逐字复述了原公式三项):
  - **recency**:指数衰减,decay factor **0.995**,按"距上次被检索的小时数"
  - **importance**:LLM 直接打分 **1–10**(prompt 评"多 poignant/重要")
  - **relevance**:query 与 memory embedding 的 **cosine**
  - **最终分** = 三项各归一化到 [0,1] 后**加权相加**(原论文 α 全取 1,即等权)
  - **reflection**:周期性把底层观察聚合成高层洞见,reflection 本身作为高 importance 记忆回写(类比小说"阶段性人物弧光 / 世界状态快照")
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2023,**机制 evergreen,不算 stale**(几乎所有后续系统都引此公式)。
  - 鲁棒性:范式级,被广泛复现;原文公式因 PDF 体积只能二手核实 `[no-source-found:2304.03442 PDF 原文公式直引]`(二手源已交叉一致)。
  - 可行性:**low**(一个打分函数 + 一次 importance 评分;我们 `LayeredMemory.L1` 已在做类似选择)。
- **对我们的价值(最高)**:把 recency 的"小时数"换成"章节号差",importance 用来**保护伏笔/核心人设**(高分永不衰减/挤出),relevance 做场景召回。**作为记忆检索打分默认骨架。**

### 3. Graphiti / Zep — bi-temporal 图谱,"事实失效"最贴小说 ⭐ 只借机制

- **repo**:https://github.com/getzep/graphiti — **26.7k stars,Apache-2.0,v0.29.1 @ 2026-05-21** [accessed:2026-05-30]
- **论文**:*Zep: A Temporal Knowledge Graph Architecture for Agent Memory*,arXiv:2501.13956(2025-01-20)。https://arxiv.org/abs/2501.13956 [accessed:2026-05-30];解读页 https://graphrag.com/appendices/research/2501.13956/ [accessed:2026-05-30]
- **核心机制(对小说极有价值)**:**双时间(bi-temporal)**——每条边记"事件发生时间(valid time)"+"写入时间(transaction time)"两套区间;**信息变化时旧事实被 invalidate 而非删除**(节点/边带 `valid_at` / `invalid_at`),可查"现在为真 / 任意时刻为真";事实可溯源到 episode。增量实时更新,无需批量重算。
- **后端**:需图数据库(Neo4j 5.26+ / FalkorDB / Kuzu / Amazon Neptune)+ 全文检索后端。
- **跑分**:论文称在 DMR 上 Zep 94.8% vs MemGPT 93.4%;LongMemEval 上 vs full-context 准确率 +18.5%、延迟 −90%。⚠️ 注意 Mem0↔Zep 跑分公案(见第四节),官方数字慎信。
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2026,**极活跃**。
  - 鲁棒性:**production**(配套商业 Zep);**中文支持未明确** `[no-source-found:Graphiti 官方中文支持声明]`,中文实体抽取(人名/门派/法宝别名归一)准确率需实测。
  - 可行性:**medium–high**(要运维图库)。
- **对我们的价值(高,只借机制)**:R3(图谱)与 R2 在此合流。`valid_from / valid_to + invalidate 不删除` 几乎是小说"角色状态变更 / 伏笔生效区间"的标准答案。**用户把图谱(R3)排在记忆/角色/大纲之后 → 只借 bi-temporal 失效语义,在现有 SQLite `knowledge_triples` 上实现,不上 Neo4j 全家桶。** 我们的 `KnowledgeGraph` 已是 temporal triples,正好升级为 bi-temporal。

### 4. MemoryOS(BAI-LAB) — 三层 OS 记忆 + EMNLP Oral + 原生中文 ⭐ 中文链路现成

- **论文**:Kang et al., *Memory OS of AI Agent*,arXiv:2506.06326(提交 2025-05-30,**EMNLP 2025 Oral**,Proceedings 2025 EMNLP pp.25961–25970)。https://arxiv.org/abs/2506.06326 [accessed:2026-05-30]
- **repo**:https://github.com/BAI-LAB/MemoryOS — **~1.4k stars,Apache-2.0** [accessed:2026-05-30]
- **架构**:**三层(STM 短期 / MTM 中期 / LPM 长期个人记忆)+ 四模块(Storage / Updating / Retrieval / Generation)**;STM→MTM "对话链 FIFO",MTM→LPM "分段分页(segmented paging,heat-based)"——把 OS 分页思想用于记忆晋升。
- **跑分**:LoCoMo(GPT-4o-mini)**F1 +49.11%、BLEU-1 +46.18%**(vs baseline)。
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2025,**新鲜活跃**。
  - 鲁棒性:prototype→渐近 production;**中文就绪度高**——中文 README(`readme_cn.md`),首类支持 **Qwen3 / DeepSeek-R1 / vLLM / Llama-Factory**,embedding 默认 **BGE-M3 / Qwen**;有 MCP / ChromaDB / Docker / Playground。
  - 可行性:**low–medium**(可当库用,但"中期记忆"分页语义为对话设计,需把粒度改为章/卷)。
- **对我们的价值(高)**:三层分页 + 中文链路现成;与我们已有 L0–L3 分层同源,可对标其 Updating 晋升/合并逻辑。**Chinese-native,是本调研里对中文最友好的工程参考之一。**

### 5. Mem0 — 生态最大/生产级,但 ADD-only 与小说不全契合 ⭐ 做抽取/召回基线

- **repo**:https://github.com/mem0ai/mem0 — **~57k stars,Apache-2.0,2026 持续更新** [accessed:2026-05-30]
- **论文**:Chhikara et al., *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*,arXiv:2504.19413。https://arxiv.org/abs/2504.19413 [accessed:2026-05-30]
- **架构**:对话中**动态抽取→合并→检索**;变体 **Mem0g** 加图记忆。2026-04 新算法:**single-pass ADD-only 抽取**(一次 LLM 调用,不做 UPDATE/DELETE,只累加不覆盖)+ 多信号检索(语义 + BM25 + 实体)+ 时间感知检索。三 scope(user / session / agent)。
- **跑分(官方,慎信)**:LoCoMo 91.6、LongMemEval 94.8、BEAM(1M)64.1;响应比 full-context 快 ~91%、token 省 ~90%。⚠️ **第三方测 LongMemEval 仅 49.0%**(见第四节)。
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2026,**最活跃**,生态最大($24M 融资)。
  - 鲁棒性:**production**(云 + 自托管 + 库);**官方中文评测未明确** `[no-source-found:Mem0 官方中文评测]`,可换 Qwen / bge-m3 embedding,抽取 prompt 默认英文。
  - 可行性:**low**(API 极简,框架无关,可直接落进现有 LangGraph + ChromaDB)。
- **对我们的价值(中)**:做"角色记忆抽取 + 向量召回"基线很好;但 **ADD-only / 不覆盖** 对小说是双刃——好处是不会误删伏笔,坏处是"A 死了 / 秘密被揭穿"这类**旧事实失效无法表达**,会与正文矛盾。若用 Mem0,需叠加 Graphiti 式失效层(见第六节 Open Q2)。

### 6. MemoryBank / SiliconFriend — 唯一原生中文 + 艾宾浩斯遗忘曲线 ⭐ 遗忘公式可抄

- **论文**:Zhong et al., *MemoryBank: Enhancing Large Language Models with Long-Term Memory*,arXiv:2305.10250,**AAAI 2024**。https://arxiv.org/abs/2305.10250 [accessed:2026-05-30]
- **repo**:https://github.com/zhongwanjun/MemoryBank-SiliconFriend(MIT)[accessed:2026-05-30]
- **机制**:三层(In-Depth 全量对话 / Hierarchical Event Summary 日级摘要 / Dynamic Personality 用户画像);检索用双塔 DPR + FAISS。核心是基于**艾宾浩斯遗忘曲线**的指数衰减:
  > `R = e^(-t/S)`,R=保持率,t=流逝时间,S=记忆强度(初始 1,被召回 +1,完全遗忘归 0)
  这是"时间衰减 + 重要性强化"最直接的闭式工程参考。
- **中文就绪度:最高**。10 天模拟史 / 15 虚拟用户 / 194 探测题(97 EN + **97 ZH**),自带 **38K 中文心理对话数据集**,base 模型含 **ChatGLM / BELLE**,demo `--language=cn`。
- **时效性 / 鲁棒性 / 可行性**:
  - 时效性:2023,repo 活跃度低,**疑似 stale** `[no-source-found:MemoryBank repo 精确 last-commit]`。
  - 鲁棒性:学术 prototype,无活跃生产实现。
  - 可行性:**medium**(从论文实现)。
- **对我们的价值(中,谨慎)**:遗忘曲线公式 + 中文落地经验值得抄;但"遗忘"在小说要慎用——日级摘要粒度对章节粒度偏粗;只用于**次要 NPC 记忆衰减 / 旧无关场景降权**,**绝不真删主线伏笔**。

---

## 二、B 档方案(点到为止)

### Letta(原 MemGPT)— 自编辑记忆 + 上下文虚拟分页
- 论文:Packer et al., *MemGPT: Towards LLMs as Operating Systems*,arXiv:2310.08560(2023-10,v2 2024-02)。https://arxiv.org/abs/2310.08560 [accessed:2026-05-30]
- repo:https://github.com/letta-ai/letta — Apache-2.0,2026 活跃 [accessed:2026-05-30]。(MemGPT 2024-09-23 更名 Letta;"MemGPT" 现指设计范式,"Letta" 指框架。)
- 机制:**virtual context management**——上下文=主存、外部存储=磁盘,LLM 用 function call 自主换入/换出;main context(系统指令 + 核心记忆 blocks + FIFO 队列)vs external(recall 全史 + archival 向量库);**记忆 blocks 可被 agent 自编辑**;新增 **sleep-time compute("dreaming")**——空闲时由独立 sleep-time agent 整合/重写核心记忆(主 agent 自己不带改核心记忆的工具,结构性避免冲突)。
- 时效性 2026 活跃;成熟度 production;**中文未明确** `[no-source-found:Letta 中文支持]`;可行性 **high**(整套"有状态 agent 运行时",绑定重,迁移成本高)。
- **价值(中低)**:"LLM 自编辑核心记忆 + 上下文分页 + sleep-time 离线整合"思想可借鉴(例如离线维护"当前在场上下文"块);**整框架太重,抄思想即可,不建议整体采用。**

### MemOS(MemTensor / IAAR-Shanghai)— 中文团队,记忆即可编辑图
- 论文:*MemOS: A Memory OS for AI System*,arXiv:2507.03724。https://arxiv.org/abs/2507.03724 [accessed:2026-05-30]
- repo:https://github.com/MemTensor/MemOS — **~9.5k stars,Apache-2.0** [accessed:2026-05-30]
- 机制:MemCube 封装(内容 + 元数据),整合 plaintext / activation / parameter 级记忆;多层 + 混合检索(全文 + 向量);35.24% token 节省。**记忆是"可检视可编辑的图"非黑盒 embedding。**
- 中文就绪度高(中国团队,双语文档,Qwen/DeepSeek)。
- **价值(中)**:与 MemoryOS 定位重叠;"记忆即可编辑图"+ 中文链路是亮点。⚠️ **MemOS(MemTensor)≠ MemoryOS(BAI-LAB),是两个不同项目,选型别搞错 repo。**

### A-MEM(Agentic Memory,Zettelkasten)— v1 携带,本轮未重新验真
- 论文:arXiv:2502.12110(Wujiang Xu et al.,NeurIPS 2025 poster);两个 repo:`agiresearch/A-mem`(多数页面指向的 canonical)与 `WujiangXu/A-mem`。MIT。
- 机制:每条记忆笔记含 原文+时间戳 / LLM 关键词 / 标签 / 上下文描述 / 链接邻居 / 向量;新笔记触发 top-k 相似 → LLM 判"有意义的连接";**memory evolution** 会回写历史笔记。
- **价值(中)**:graph-of-notes 很贴"角色出场→召回其关联记忆";但 evolution 回写历史**无版本史、buggy 即破坏性**(对伏笔危险)。
- ⚠️ **说明**:本条来自 v1,**不在本轮 clean-room 验真批次内**——arXiv:2502.12110 是已知真实论文,但其精确 star/venue/repo 状态本轮未独立复核,采用前请人工补验。

### Cognee — graph+vector 的轻量记忆控制面(C 档一句话)
- https://github.com/topoteretes/cognee — **17.6k stars,Apache-2.0** [accessed:2026-05-30]。`remember / recall / forget / improve` 四操作,graph+vector 双层,poly-store(Neo4j/Kuzu/NetworkX + Qdrant/Weaviate/Redis)。README 多语含中文。**对我们价值低**:通用 RAG/记忆框架,无小说/时序特化。

### SillyTavern Lorebook / Vectorization — 实战派"世界书 + 关键词激活"(模式参考,非选型)
- repo:https://github.com/SillyTavern/SillyTavern(AGPL-3.0)[accessed:2026-05-30]。
- World Info:条目=关键词 + 内容 + 插入顺序/位置/概率;**关键词触发激活**、递归激活、显式 **token 预算**;作用域 Character/Persona/Chat/Global。Chat Vectorization:消息后台 embedding,ChromaDB per-chat,query=末 2 条 → top-K(≥25% 相关)临时插入。
- **价值(高,仅作模式源,不 vendor)**:**长篇 roleplay 社区日用、久经实战**;关键词激活 + token 预算的工程模式极清晰,可在我们 FastAPI 后端重实现。AGPL 不可 vendor,借模式即可。

---

## 三、关键基准(选型必看,别迷信单一分数)

- **LoCoMo**:*Evaluating Very Long-Term Conversational Memory of LLM Agents*,arXiv:2402.17753(Snap,ACL 2024)。https://arxiv.org/abs/2402.17753 ;repo https://github.com/snap-research/locomo [accessed:2026-05-30]。35 session / ~300 turn / 平均 ~9K token 的对话 QA。**几乎人人报此分,但难度偏低**(对话长度落在现代 LLM 上下文窗口内),对"几十万字小说"参考有限。**英文。**
- **LongMemEval**:*Benchmarking Chat Assistants on Long-Term Interactive Memory*,arXiv:2410.10813,**ICLR 2025**。https://arxiv.org/abs/2410.10813 ;repo https://github.com/xiaowu0162/LongMemEval(MIT)[accessed:2026-05-30]。**500 题,考 5 能力:信息抽取 / 多 session 推理 / 时序推理 / 知识更新 / 拒答**;_S ~115K token、_M ~1.5M token。**比 LoCoMo 更硬、更接近长篇**(尤其"知识更新"=角色状态变更、"时序推理"=章节先后)。三段式 indexing/retrieval/reading 优化(session 分解、fact-augmented key、time-aware query 扩展)**直接可借鉴到我们的检索**。**英文。**
- **BEAM / Beyond a Million Tokens**:arXiv:2510.27246,**ICLR 2026**。https://arxiv.org/abs/2510.27246 ;repo https://github.com/mohammadtavakoli78/BEAM [accessed:2026-05-30]。100 对话 / 128K–10M token / 2,000 验证题,考 **10 项记忆能力(含更新信息 / 解决矛盾 / 时序)**;配 LIGHT 框架(episodic + working + scratchpad 三记忆)。**供持续跟踪。**(v1 阶段曾把 BEAM primary paper 标为 `[no-source-found]`,**v2 已定位并验真**。)
- ⚠️ **ConStory-Bench**(叙事一致性 taxonomy,**强相关但非记忆基准、非中文**):*Lost in Stories: Consistency Bugs in Long Story Generation by LLMs*,arXiv:2603.05890(2026-03,ACL 2026,Microsoft + SUTD,作者 Junjie Li, Xinrui Guo, Yuhao Wu, Roy Ka-Wei Lee 等)。https://arxiv.org/abs/2603.05890 ;repo https://github.com/Picrew/ConStory-Bench [accessed:2026-05-30]。2,000 prompts × 4 任务,目标 8000–10000 词,**5 类错误 × 19 子类**:① 时间线&情节逻辑(时序矛盾/因果违背/弃坑伏笔)② 人物刻画(记忆不一致/能力波动/遗忘技能)③ 世界规则(规则违背/地理矛盾/社会规范)④ 事实细节(外貌/称谓/数量)⑤ 叙事风格(视角/语气/文风)。配 ConStory-Checker(四阶段 LLM-as-judge + 引文取证);**发现错误多发于中段、高 token 熵段、事实&时序维度最多**。→ 这是**设计我们记忆系统该防什么**的 taxonomy。
- ⚠️ **中文小说基准缺口**:**未检索到任何"中文长篇小说记忆/一致性"专用基准** `[no-source-found:中文长篇小说记忆一致性专用基准]`。最近的中文**文笔质量**基准是 **WebNovelBench**(下节);叙事一致性 taxonomy 只有英文 ConStory。**意味着我们大概率要自建中文小说连续性评测集**(可复用项目已有 SEQR v0,commit ff1f4db;直接套 ConStory 5 类 19 子类 + DOME 的 Conflict Rate)。

### WebNovelBench — 中文网文质量基准(评测维度可直接对标)
- arXiv:2505.14818(ACL Findings 2026)。https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]。4,000+ 中文网文,以 25 位茅盾奖得主作上界锚;24 个 SOTA 模型;LLM-as-judge + PCA 加权 + ECDF 百分位。
- **Table 1 的 8 个评测维度(经基础事实核查逐字确认)**:
  1. Use of Literary Devices(文学手法运用)
  2. Richness of Sensory Detail(感官细节丰富度)
  3. Balance of Character Presence(角色出场平衡)
  4. Distinctiveness of Character Dialogue(角色对白辨识度)
  5. Consistency of Characterisation(**人物刻画一致性** ← 与 R2/R5 直接相关)
  6. Atmospheric and Thematic Alignment(氛围与主题契合)
  7. Contextual Appropriateness(语境恰当性)
  8. Scene-to-Scene Coherence(**场景间连贯性** ← 与 R2 直接相关)
- 用法:其中维度 5、8 正好是"记忆系统该撑住的连续性指标",可直接纳入我们自建评测的打分项。

---

## 四、跑分可信度警告(强烈建议读)

**Mem0 vs Zep 的"SOTA"互撕公案 + 全行业刷分乱象**,直接影响选型时对官方数字的信任:

- Zep 公开质疑 Mem0 论文(*Is Mem0 Really SOTA in Agent Memory?*,Daniel Chalef / Preston Rasmussen,2025-05 起)https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/ [accessed:2026-05-30]:称 Mem0 把 Zep **配错了**(双方都标 user 角色、时间戳塞进 message 而非用 `created_at`、串行检索致延迟虚高);Zep 改正后自报更高 J-score,并指"**Mem0 自己结果里 full-context baseline 反而打赢 Mem0**"。
- **LongMemEval(更硬基准)上差距更真实**:第三方测 **Mem0 ~49.0% vs Zep ~63.8%**(GPT-4o,~115K token),约 15 分差距反映"向量召回 vs 图谱+时序"的真实架构差异。
- 行业刷分失控:LoCoMo 头部数字从 ~65% 到接近 100%,但**各家用不同 answer 模型 / judge 模型 / judge prompt,不可直接比**。
- **结论:任何单一 LoCoMo/LongMemEval 数字别全信,尤其厂商自报。选型应自己在中文小说样本上小规模复测。**

---

## 五、综合判断 & Top 候选

**总策略:不照搬任何单一开源系统,在现有 `LayeredMemory` + `KnowledgeGraph` 上组合"经验证机制"。** 理由:① 成熟系统全为对话场景优化,小说场景(章节逻辑时间 + 多角色 + 自生成可控正文 + 伏笔不可遗忘)无一开箱即用;② 中文就绪度参差,真原生中文只有 MemoryBank / MemoryOS / MemOS;③ 跑分不可全信需自测。

**Top 候选(按"借鉴价值 × 落地成本"排序):**

1. **DOME 的章节四元组 + 冲突分析器(最高价值,medium cost)** — `<主语,动作,宾语,章节号>` 逐句抽取 + Temporal Conflict Analyzer(分组 + LLM 判时序/语义冲突 + Conflict Rate 指标)。**离我们最近、schema 最契合,作为 R2 核心方法蓝本**,直接升级 `backend/storage/sqlite_store.py:knowledge_triples` → 加 `chapter_index`。
2. **Generative Agents 检索公式(必做,low cost)** — `score = w1·relevance(cosine) + w2·importance(LLM 1-10) + w3·recency(指数衰减)`;recency 时间维改为**章节距离**,importance 高分**保护伏笔/核心人设**永不挤出。在 `ChapterExtractor` 抽取时打 importance。作为记忆检索打分默认骨架。
3. **Graphiti 的 bi-temporal "失效不删除"(高价值,medium cost,只借机制)** — 借 `valid_from/valid_to + invalidate` 表达**角色状态变更 / 世界规则演进**(章节号当逻辑时间),在 SQLite 上实现。**不上 Neo4j 全家桶**(契合"图谱优先级最低")。
4. **MemoryOS / MemOS 的分层晋升 + 中文链路(low–medium cost)** — 对标短/中/长晋升与分页,完善 L0–L3;中文 embedding 直接用 **BGE-M3 / Qwen**。二选一(MemoryOS 更轻、MemOS 更图谱化)。
5. **MemoryBank 艾宾浩斯遗忘曲线(medium cost,谨慎)** — 仅用于次要 NPC 记忆衰减 / 旧无关场景降权,**非真删伏笔**;中文数据集经验可参考。
6. **Mem0 抽取/召回作基线(low cost)** — 可快速搭"角色记忆抽取 + 向量召回";但须叠加失效层补 ADD-only 短板。

**评测层(必做):** 自建**中文小说连续性评测集** = ConStory 的 5 类 19 子类 taxonomy + DOME 的 Conflict Rate + LongMemEval 的"知识更新/时序推理"维度 + WebNovelBench 的维度 5/8,复用项目 SEQR 框架,作为 R2 回归基准。

**架构对齐参考(逐项 self-audit)**:*Rethinking Memory in AI: Taxonomy, Operations, Topics, and Future Directions*,arXiv:2505.00675(Du / Huang / Lapata / Wong / Pan,2025-05)。https://arxiv.org/abs/2505.00675 [accessed:2026-05-30]。统一抽象:**3 类记忆**(parametric / contextual-structured 如 KG / contextual-unstructured 如向量库)+ **6 原子操作**——管理类:**consolidation 巩固 / indexing 索引 / updating 更新 / forgetting 遗忘**;利用类:**retrieval 检索 / compression 压缩**。用法:逐项 review 我们 `LayeredMemory` + `ChapterExtractor` + `KnowledgeGraph` 是否覆盖这 6 个(目前疑似缺**显式 updating-失效** 与 **systematic forgetting / compression**)。

**模型层提示(应用基础事实核查·中文文笔实测对比 [accessed:2026-05-30])**:记忆系统的"抽取 / importance 打分 / 冲突判定"都是 LLM 调用,模型选择影响中文质量与成本——
- **中文文笔/创意写作**:**Kimi K2.6** 当前领先(创意写作 + 角色扮演双榜第一,2M token 超长上下文,利于长篇连载),次选 **DeepSeek V4-Pro**(1M 上下文、中文知识强,但文笔专项数据有限)。
- **抽取/判定等结构化任务(性价比)**:**DeepSeek V4**(极致性价比)或 **Qwen 3.6-Plus**(开源、C-Eval 93%、最便宜,可本地部署作 embedding/抽取)。
- 建议:**正文 Writer 用 Kimi/DeepSeek 高质量档;记忆抽取/冲突判定用 DeepSeek/Qwen 性价比档**,与现有 per-agent ModelRegistry 绑定机制契合。

---

## 六、Open Questions(给下一轮 / 人工跟进)

1. **逻辑时间 vs wall-clock**:所有方案的时间衰减/bi-temporal 都基于真实时间。DOME 用 `chapter_index` 证明"章节号当时间轴"可行;但 **Graphiti 是否支持自定义时间字段替换 wall-clock?** 需读其 episode/edge schema 验证后再决定借机制的实现路径。
2. **ADD-only vs 可失效**:Mem0 只增不改对伏笔友好但无法表达"已死/已揭穿"。**最佳组合是否 = Mem0 抽取层 + Graphiti/DOME 失效层?** 需原型验证。
3. **中文实体抽取质量**:Graphiti / Mem0g / Cognee / DOME 抽取 prompt 默认英文,对中文小说**人名/地名/门派/法宝/称号别名**(同角色多称呼)归一化准确率未知 → **必须实测**(可结合 R5 角色方向一起做)。
4. **importance 评分的小说语义**:Generative Agents 的 importance 是"对 agent 的重要性";小说应改为"对主线/伏笔的重要性"——**评分 prompt 怎么写才能让"看似平凡实为伏笔"的句子拿高分?** 这是把通用公式落到小说的关键 prompt 工程问题。
5. **中文小说记忆专用基准缺失** `[no-source-found:中文长篇小说记忆一致性专用基准]` → **是否值得我们开源一个?** 可成项目差异化资产(ConStory taxonomy 中文化 + DOME Conflict Rate + 复用 SEQR)。
6. **未直引的原文**(因 arXiv PDF >10MB / 抓取失败):Generative Agents 公式原文(2304.03442 PDF)、Letta 官方记忆文档细节、A-MEM 本轮未独立复核——建议人工补读原文确认。

---

## v1 ↔ v2 diff

> 对比对象:`workspace/research/2026-04-28-novel-system-survey/r2-memory.md`(v1,2026-04-28,18 节 / 30+ 系统)。

### 删除(尤其幻觉 / 不可验证内容)

- **【删·疑似幻觉】MemPalace(§5)整节删除。** v1 把 MemPalace 描述为"女演员 Milla Jovovich + Ben Sigman 用 Claude Code 打造、~47k–53k stars、LongMemEval 96.6% raw recall@5、AAAK 30× 压缩、170-token 启动"。本轮 clean-room 重做**刻意未纳入** MemPalace;且其全部性能 claim 均为**单一来源/营销材料**(v1 自己已注"not independently reproduced",并引第三方称 AAAK 实测把准确率从 96.6% 降到 ~84.2%),无同行评审论文,"名人造记忆系统"叙事是强幻觉信号。**判定为不可靠 → 从 v2 移除**(详见 `hallucinations_removed`)。
- **【删·验真未覆盖,降级处理】** v1 的若干"通用框架细节"(LangChain/LangGraph memory §7、LlamaIndex Memory Blocks §8、CoALA §13、DOC/Re3 §14 其余、AgentMemoryBench/MemoryAgentBench §15、嵌入与失效模式 §16–17 的部分二手 Medium 来源)在 v2 **不再单列长节**——它们或非小说特化、或来源为非权威博客、或不在本轮验真批次。v2 按"用户优先级 + S/B/C 分档"收敛,只保留经验真的核心方案;CoALA 的 vocabulary、SillyTavern 的工程模式被压缩进 B 档。
- **【删·重复/过期元数据】** v1 大量 `last_commit_date / stars 精确值`(如"Letta 7,464 commits""Cognee v1.1.1.dev0")在 v2 简化为区间值并统一标 [accessed:2026-05-30],避免易腐数字。

### 纠正

- **DOME venue 坐实**:v1 仅称 arXiv preprint;v2 经 ACL Anthology 确认 **NAACL 2025 Long Papers(pp.1352–1391)**,venue 成立。
- **BEAM 基准补全**:v1 §15 把 BEAM 标 `[no-source-found: BEAM primary paper]`(仅经 mem0 博客间接引用);v2 **定位并验真为 arXiv:2510.27246(ICLR 2026)** + repo,纳入"持续跟踪基准"。
- **ConStory-Bench 元数据更新**:v1 用 `arxiv.org/html/2603.05890v1` 且作者写"Microsoft Beijing + SUTD";v2 确认 arXiv:2603.05890、**ACL 2026**、repo `github.com/Picrew/ConStory-Bench`、作者 Junjie Li / Xinrui Guo / Yuhao Wu / Roy Ka-Wei Lee 等;5 类 19 子类 taxonomy 保留并强化为"自建评测的蓝本"。
- **WebNovelBench 8 维度逐字确认**:v1 只说"八维度";v2 应用基础事实核查,**逐字列出 Table 1 的 8 个英文维度名**,并标出其中维度 5(Consistency of Characterisation)、8(Scene-to-Scene Coherence)与 R2 直接相关。
- **Mem0↔Zep 跑分公案量化**:v1 §17 只泛泛提"不同系统处理 staleness 不同";v2 新增**第四节专门拆解互撕**(配错实现、full-context baseline 反超、第三方 LongMemEval Mem0 49% vs Zep 63.8%),明确"官方数字慎信、需自测"。
- **A-MEM 标注降级**:v1 把 A-MEM 当 S 级证据详写;v2 明确标注其**不在本轮验真批次**,降为 B 档并提示"采用前人工补验"(arXiv:2502.12110 本身是真论文,但 star/venue/repo 状态未本轮复核)。
- **PerRoleCognition 幻觉防护(新增基础事实)**:基础事实核查确认 **"PerRoleCognition" 在 arXiv/Scholar/全网均无 → 杜撰**。v1 r2-memory 未引用此词(它更可能出现在 R5 角色方向),但 v2 在此**显式记录**:若后续任何记忆/角色方案引用 "PerRoleCognition",应判为幻觉;最接近的真实概念是 RPNA(arXiv:2510.24677)/ RoleRAG(arXiv:2505.18541)/ Character-LLM(arXiv:2310.10158)。

### 新增

- **场景错位对照表 + S/B/C 分档**:v1 是平铺 18 节;v2 开篇加"对话记忆 vs 小说记忆"五维对照表,并按**用户优先级(R2=R5=R1>R3)**把方案分 S/B/C 档,S 档写到可落地深度、B/C 点到为止。
- **逐方案"时效性 / 鲁棒性 / 可行性"三标**:v2 每个 S 档方案显式标三项,便于选型。
- **《Rethinking Memory in AI》6 原子操作 self-audit 框架**(arXiv:2505.00675):v1 用 CoALA 做 vocabulary;v2 改用更新的统一抽象,并给出"逐项 review 我们是否缺 updating-失效 / forgetting / compression"的可执行清单。
- **模型层建议(应用 2026 中文文笔实测)**:v2 新增——正文用 Kimi K2.6 / DeepSeek V4-Pro 高质量档,记忆抽取/冲突判定用 DeepSeek V4 / Qwen 3.6-Plus 性价比档,绑到现有 per-agent ModelRegistry。
- **明确 R2↔R3 合流边界**:v2 强调"借 Graphiti bi-temporal 机制但不上 Neo4j",显式呼应用户"图谱优先级最低"。
- **6 条 Open Questions**:v2 收敛出可执行的下一步(逻辑时间字段、ADD-only+失效组合、中文实体抽取实测、importance 小说语义 prompt、是否自建中文基准、补读原文)。

---

*终稿 v2 编制于 2026-05-30。所有存活引用 URL 均经逐条验真(exists=true);幻觉与不可验证内容见上方 diff 与 hallucinations_removed。*
