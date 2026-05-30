# R5 · 角色扮演 / 角色一致性 — 深度调研 v2(终稿)

> **方向**:面向中文 LLM 小说生成系统的「角色扮演 / 角色一致性 / 多角色辨识度」重构。
> **本稿性质**:在 v1(`2026-04-28-novel-system-survey/r5-character.md`,880 行)基础上做复核 + 验真后的终稿。v1 本身已是"每条 claim 配 WebSearch/WebFetch"的高质量稿;本稿 = **保留 v1 深度与可操作性 + 套用本轮 31 条引用验真表 + 套用三项基础事实核查 + 删除被证伪的幻觉**。
> **优先级锚定**:本系统中 记忆(R2) = 角色(R5) = 大纲(R1) > 图谱(R3)。R5 属 **S 档**,做到最深;S 档条目给「时效性 / 鲁棒性 / 可行性」三维,B/C 档点到为止。
> **靶心问题(承自 v1)**:SEQR 评测里 `dialogue_distinct`(对白区分度)是弱维(ρ=−0.16)。本方向核心是回答"为什么角色都一个腔调,怎么修"。
> **验真标注约定**:
> - ✅ 本轮验真清单已确认存在(arxiv abstract / repo 身份核对一致)。
> - 🔶 v1 已查证但**不在本轮验真清单内** → 标 `[v1-sourced, 本轮未复验]`,引用前建议再 verify id。
> - ⛔ 经核查为不存在 / 杜撰 → 已删除或仅留"勿引"说明。
> 访问日期:✅ 复核条目标 `[accessed:2026-05-30]`;🔶 条目沿用 v1 的 `[accessed:2026-04-28]`。

---

## 0. 三件必须先讲清楚的事(关键纠偏)

### 0.1 术语澄清:RPNA(真) vs PerRoleCognition(假)—— 与 v1 一致,经基础事实核查确认

v1 引入两个关键术语,本轮三项基础事实核查对它们分别下判决,结论与 v1 **一致**:

| 术语 | 判决 | 处理 |
|---|---|---|
| **PerRoleCognition** | ⛔ **杜撰**。arXiv / Google Scholar / 全网零结果(基础事实核查确认;v1 §3 也独立得出同结论)。 | **从重构文档彻底移除**,仅留"勿引"说明。它像是把 "Role Cognition" + "per-role" + "Cognition" 三个真实片段拼出的伪术语。 |
| **RPNA** | ✅ **真实**。指 **RP-Neuron-Activated Evaluation Framework**,出自《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》(arxiv [2510.24677](https://arxiv.org/abs/2510.24677) [accessed:2026-05-30])。用**神经元消融**研究医学 LLM 的角色认知。 | **保留**。v1 一直把 RPNA 正确当作这篇论文的简称(见 §1.A),本稿沿用。 |

> ⚠️ 注:若某下游材料把 "RPNA" 误当成"角色扮演叙事分析(role-play narrative analysis)"——**那个含义查无此物**,已删除。RPNA 唯一正确所指就是上面这篇神经元消融论文。若你想表达的是"长篇掉人设 / persona drift",对应 §1.B 的 2402.10962,**不是 RPNA**。与 RPNA / PerRoleCognition 语义最近、且真实可引的奠基工作是 **Character-LLM**(EMNLP'23,arxiv [2310.10158](https://arxiv.org/abs/2310.10158) ✅)。

### 0.2 "prompt 治不了一致性、必须 SFT" —— v1 用 RPNA+Narrative Flattening 证"结构性弱"是对的,但**不能滑向"必须 SFT"**

v1 的核心论点(强且正确):**角色 prompt 只改表层措辞、不改底层认知** —— 两条互证:

| 论文 | 实际结论 | 对"必须 SFT"的关系 |
|---|---|---|
| **RPNA / 神经元消融**(2510.24677,✅) | 消融"角色敏感神经元"后:角色 prompt *"primarily affect surface-level linguistic features, with no evidence of distinct reasoning pathways"* —— 模型把所有角色接到**同一套推理回路**,只在词汇层微调。这是 `dialogue_distinct` 弱维的**机理级解释**。 | 说明"给每个角色发 system prompt"会**触顶**,但**没说**只能靠 SFT 解决。 |
| **Narrative Flattening**(2605.27878,✅) | 4 个 OLMo-32B checkpoint(Base/SFT/DPO/RLVR)逐级压缩主题/情感/风格多样性 —— **post-training 本身是"扁平化"的病因**。 | **反向**:它把 SFT/RLHF 列为**病因**;不能拿它论证"需要 SFT"。 |

本轮额外补强的**反向证据**(说明 prompt/检索/解码层能拿大部分收益,不必非训练不可):
- **2402.10962**(✅,真实标题见 §1.B):提出 **split-softmax** —— **training-free / 参数-free 的解码期干预**;并测了 SPR、CFG 两条纯 prompt 基线"可用"。
- **PersonaEval**(arxiv [2508.10014](https://arxiv.org/abs/2508.10014) [accessed:2026-05-30],COLM'25):*"Fine-tuning LLMs with role-play data does not improve performance and can even degrade it"* —— 角色扮演 SFT 数据在"判断谁在说话"上反而**有害**。
- **Talk Less, Call Right**(arxiv [2509.00482](https://arxiv.org/abs/2509.00482) [accessed:2026-05-30],EMNLP'25 Wordplay):纯结构化 prompt(RRP/CSC)0.523→0.571,**零微调**。

**正向证据(SFT/RL 确能涨,但是"第二阶段大招"):** CoSER(✅ ICML'25)、PsyMem(✅ TACL)、Character-R1(✅ RLVR)、PCL(✅ ACL'25 Findings)。

> **修正版结论(取代 v1 任何"必须 SFT"暗示,可直接采纳):**
> 角色一致性是**谱系问题**,按成本递增四档:
> ① **结构化角色卡 + 硬约束 prompt**(low) → ② **解码期干预**(split-softmax 类,low 但需 logits/attention,**闭源 API 用不了**) → ③ **RAG / 知识边界检索**(RoleRAG/AMADEUS/RPNA-boundary 思路,medium) → ④ **SFT/RL**(CoSER/PsyMem/Character-R1,high/rewrite)。
> 对 **prompt-driven 中文小说系统**:**①+③ 性价比最高且中文就绪**;④ 仅当你愿意自建中文角色对话数据集才考虑。
> **但 RPNA 的机理结论要诚实带上**:即便做到 ①+③,纯 prompt 路线对 `dialogue_distinct` 有**结构性上限**(同一回路问题);要突破,要么 ②(改解码,需开源模型)、要么 ④(改权重)、要么换"扁平化更轻"的基座(§0.3)。**这是 v1 最有价值的洞见,本稿保留并强化。**

### 0.3 模型选型(中文文笔 / 扁平化)的事实层 —— v2 新增

本系统经 LiteLLM 网关可任意切基座。结合 §0.2 的"Narrative Flattening = post-training 压平"与"split-softmax 需开源模型",基座选择直接决定 R5 的上限。2026-03~05 实测对比(数据访问 2026-05-30,源自第三方评测/官方参数聚合,属**软性参考**,非一手 benchmark):

- **Kimi K2.6**:创意写作 + 挑战性角色扮演双榜居前,长篇风格连贯性强;**上下文 2M**(最长),**单价最高**。→ 利于多角色口吻区分,但仍带正向/扁平偏置。
- **DeepSeek V4-Pro**:中文知识/推理强(SimpleQA 高),**1M 上下文**,性价比极高;**专项文笔评测数据少**(强项在知识)。
- **GLM-5.1 / Qwen 3.6-Plus**:通用强、创意非主打;**Qwen 完全开源(Apache-2.0)、C-Eval ~93%、单价最低** → **唯一能跑 split-softmax(②档解码干预)的现实通道**。

> **对 R5 的三条直接启示:**
> ① 主力若是 Kimi/DeepSeek 等**闭源 API**,§1.B 的 split-softmax **用不了**,R5 护栏只能落在 **prompt + RAG 边界**(①+③)。
> ② 若想保留 ②档,需在 LiteLLM 后挂一条 **本地 Qwen3.6** 路径。
> ③ **Writer agent 的基座选择 = `dialogue_distinct` 上限的一部分**:越"少 post-training / 风格越散"的基座,角色辨识度天花板越高(Narrative Flattening 的直接推论)。

---

## 1. 可借鉴清单(S 档展开;B/C 档点到为止)

> 每条给:来源 URL + 验真状态 + 对本系统的价值。S 档额外给"时效性/鲁棒性/可行性"。

### 1.A 角色认知的"结构性上限"证据(R5 的理论地基)【S】

**RPNA — Dissecting Role Cognition in Medical LLMs via Neuronal Ablation** — arxiv [2510.24677](https://arxiv.org/abs/2510.24677) [accessed:2026-05-30] ✅
- **机理(可直接抄进设计论证)**:识别"角色敏感神经元"(跨层激活差)→ 选 top-K 层(通常 4)→ 消融每层 top 5% → 对照随机消融。数据集 MedQA/MedMCQA/MMLU-Med。结论:角色 prompt 只动**表层语言特征**,无独立推理通路。
- **时效性**:2025-10,新。**鲁棒性**:有消融对照,机理证据较硬;但**领域是医学**,推广到"小说人物腔调"是合理外推而非直接证明。**可行性**:NA(它是"告诫/边界",非方法)。
- **对你的价值**:这是 `dialogue_distinct` ρ=−0.16 的**机理级解释**,也是论证"为什么不能只靠角色 prompt、要叠 RAG 边界 / 解码干预 / SFT"的最强论据。**保留为 R5 设计的开篇论据。**

**Narrative Flattening** — arxiv [2605.27878](https://arxiv.org/abs/2605.27878) [accessed:2026-05-30] ✅
- 4 个 OLMo-32B checkpoint(Base/SFT/DPO/RLVR)在 StoryStar/TMAS/The New Yorker 上做匹配续写:**post-training 单调压缩**主题/情感/风格多样性,与专业文学差距最大。
- **对你的价值**:扁平化是系统性的;角色辨识度低 = 扁平化在"人物"维的投影。**这是 R5 与 R1(大纲)、R6(反 slop)共同的敌人**,选基座/调温度/显式注入冲突都因它而起(§0.3、§2.4)。

### 1.B Persona drift 测量与控制 —— 对"长篇连载掉人设"最直接【S】

**Measuring and Controlling Instruction (In)Stability in Language Model Dialogs** — arxiv [2402.10962](https://arxiv.org/abs/2402.10962) [accessed:2026-05-30],repo [likenneth/persona_drift](https://github.com/likenneth/persona_drift) ✅(repo)
> ⚠️ **标题纠错(本轮验真发现)**:该 arxiv id 真实标题是 *"Measuring and Controlling **Instruction (In)Stability** in Language Model Dialogs"*(作者 Kenneth Li 等),**不是** v1 写的 *"...Persona Drift..."*。论文内容确实讲 persona/instruction drift + split-softmax,**repo 名仍叫 `persona_drift`** —— 这正是 v1 误记标题的来源。**论文真实存在,按"纠正标题"处理,不删除。**
- **三个可直接抄的自动指标**:prompt-to-line / line-to-line / Q&A consistency(persona 自洽度)。v1 实测引述:LLaMA2-70B persona 服从度从第1轮 ~0.8 跌到第8轮 ~0.4。
- **split-softmax**:解码期把 attention 重新加权偏向 system/persona token,**training-free**(`attn_sys *= π_k/π`,`attn_other *= (1-π_k)/(1-π)`,超参 k∈[0,1])。
- **时效性**:2024-02(略旧但仍是该问题标准引用)。**鲁棒性**:指标语言无关、可进 CI;split-softmax 需 **logits/attention 访问**。**可行性**:指标 **low**;split-softmax **medium 且仅限本地开源模型**(§0.3)。

**Examining Identity Drift in Conversations of LLM Agents** — arxiv [2412.00804](https://arxiv.org/abs/2412.00804) [accessed:2026-05-30] ✅【B】
- 关键告诫:**更大的模型漂移更多**;**只发 persona prompt 不能阻止漂移**;9 个 LLM 实测。→ 印证"纯 prompt 侧 persona 工程救不了最大模型"。

**Persistent Personas?**(extended interactions)— arxiv [2512.12775](https://arxiv.org/abs/2512.12775) [accessed:2026-05-30] ✅【B】
- EACL'26;*persona fidelity 随对话退化,目标导向对话尤甚* —— 长程一致性直接佐证。

**Nautilus Compass**(production drift detection)— arxiv 2605.09863 🔶 `[v1-sourced, 本轮未复验]`【B】
- 黑盒:BGE-m3 把"当前文本"与"behavioral anchor"做 cosine,加权 top-k 均值作漂移分;v1 记 ROC-AUC 0.83、复现成本 ~$3.50。**对你的价值**:Consistency agent 可加一条"每章 vs 角色锚文本"的廉价漂移检测(BGE-m3 中文原生)。**引用前复验 id。**

### 1.C 知识边界 / 人设崩塌(character hallucination)—— 小说系统刚需【S】

**RoleRAG** — arxiv [2505.18541](https://arxiv.org/abs/2505.18541) [accessed:2026-05-30] ✅(作者 Yongjie Wang, Jonathan Leung, Zhiqi Shen)
- **机理**:语义实体归一(把"Anakin"和"Vader"并成一个规范实体,省 LLM 调用 `|N|/k`)+ **boundary-aware retriever**,三种检索模式:**越界拒答 / 指定实体检索 / 1-hop 邻域**。在 Harry Potter、**RoleBench-zh**、Character-LLM 数据上,知识暴露/幻觉/未知拒答均超基线。作者自述:多轮一致性仍 open。
- **时效性**:2025-05。**鲁棒性**:明确在 **RoleBench-zh** 上测过(中文已验)。**可行性**:low-medium —— 实体归一可复用你的 `knowledge_triples`;边界检索是 memory L3 之上的薄层。本轮**未找到稳定 repo/star**(no-source-found:RoleRAG repo)。
- **对你的价值(核心)**:这正是 R3 图谱 + R2 记忆的"角色侧"用法——**用图谱约束"该角色此刻能知道什么"**,与你 KnowledgeGraph(`valid_from/valid_to`)+ Camera agent(过滤可见事件)天然同构。

**TimeChara** — arxiv [2405.18027](https://arxiv.org/abs/2405.18027) [accessed:2026-05-30] ✅
- **point-in-time character hallucination**:角色不该知道剧情时间线之后的事;benchmark 10,000+ 实例;Narrative-Experts 方法。
- **时效性**:ACL'24 Findings。**鲁棒性**:专测时间维幻觉,定义清晰。**可行性**:medium;**英文,需中文化** ⚠️。
- **对你的价值(强烈建议)**:小说连载"角色提前知道未来章节"是高频崩塌点——**把它做成 Consistency agent 的一条检查项**,直接挂 `valid_from/valid_to`。

**RoleFact**(Mitigating Hallucination in Fictional Character Role-Play)— arxiv [2406.17260](https://arxiv.org/abs/2406.17260) [accessed:2026-05-30] ✅【A,可实操】
- 用**预校准置信阈值**调制参数化知识:对抗性问题**事实精度 +18%、时间幻觉 −44%**;**代码与数据公开**(EMNLP'24 Findings)。即插即用,降幻觉性价比高。

**RoleBreak** — arxiv [2409.16727](https://arxiv.org/abs/2409.16727) [accessed:2026-05-30] ✅【B】:把角色幻觉当 **jailbreak 攻击**分析,提 "Narrator Mode" 防御。

**RAIDEN-R1 / Role-Cognition Boundary** — arxiv 2505.10218 🔶 `[v1-sourced, 本轮未复验]`【B】
- v1 记:VRAR 可验证奖励(STV/MTDP),其 benchmark 含 **"Role-Cognition Boundary"** 指标——可借作"角色认知边界"的现成评测目标。**引用前复验 id。**

**IJCAI 2025 Tutorial** — [ijcai-roleplay.github.io](https://ijcai-roleplay.github.io/) [accessed:2026-05-30] ✅:**从幻觉视角的角色扮演完整 taxonomy**,这块最好的"地图"。

**AMADEUS / Dynamic Context Adaptation** — arxiv 2508.02016 🔶 `[本轮未独立验真,引用前复核]`
- 思想(可借):training-free RAG,三阶段(切分 persona 文档 / 检索可推断 chunk / 利用结果),角色缺知识时仍 in-character 不乱编。若属实则 low-medium,最适合 prompt-driven 系统。**v1 曾自述一度误搜到错误 id;本稿降级为待确认。**

### 1.D 对白区分度 / 角色辨识度(dialogue distinctness)—— SEQR 弱维正解【S】

**核心可操作 metric(training-free,可进 CI)**:把生成章节里**去掉说话人标签的对白**,喂给分类器/LLM 猜"谁说的";**猜对率↑ = 区分度↑**。理论支撑:

**PersonaEval** — arxiv [2508.10014](https://arxiv.org/abs/2508.10014) [accessed:2026-05-30] ✅,repo [maple-zhou/PersonaEval](https://github.com/maple-zhou/PersonaEval) ✅(MIT)
- 证明"识别谁在说话"是真实难点:**最强 LLM 仅 ~68.8% vs 人类 ~90.8%**。→ 直接给"去标签猜说话人"这个自研指标背书。

**WebNovelBench 的两维**(基础事实核查锚定)— arxiv [2505.14818](https://arxiv.org/html/2505.14818v1) [accessed:2026-05-30] ✅(经基础事实核查抽出 Table 1 八维)
- 八维里有两条**正是 R5 靶心**:**Distinctiveness of Character Dialogue**(对白区分度)、**Consistency of Characterisation**(人物刻画一致性)。
- (其余六维:Use of Literary Devices / Richness of Sensory Detail / Balance of Character Presence / Atmospheric and Thematic Alignment / Contextual Appropriateness / Scene-to-Scene Coherence。)
- **建议**:把这两维做成 Consistency agent 评分 rubric,与中文 benchmark(§1.F)互补,直接对接 SEQR `dialogue_distinct`。

**Distinct-1 / Distinct-2**:廉价词汇多样性基线,可同时跑(v1 已列)。

🔶 v1 另引 **SA-LLM**(2503.08842,speaker-attributed encoding)、**MIMIC**(EACL'26,speaker stylistic transfer 做数据增强)、**Constella**(CHI'25,每角色 panel-agent 的 COMMENTS 模式可用于创作期测区分度)、**From stage to page / bootstrap distinctiveness**(2301.05659,语言无关的对白区分度自助统计)—— 均 `[v1-sourced, 本轮未复验]`,作为**思路**保留。核心 metric 不依赖它们(已由 PersonaEval + WebNovelBench 承接)。

### 1.E 情感 / 关系追踪(R2 记忆 × R5 角色的交叉)【S — 因 R2=R5 同为最高优先级】

**Signed Character Networks(关系真实性)** — arxiv 2510.18932 🔶 `[本轮未独立验真,引用前复核]`
- 思路:故事人物关系建成**带符号(正/负)网络**,大样本对比 LLM vs 人类。硬核发现(若属实):LLM 故事**强烈偏"紧密+正向"**,密度/聚类更高、彼此趋同;人类更分散。
- **价值**:① 关系追踪 + 关系多样性的评测法;② 量化"LLM 把所有人都写成关系好"——R5 要对抗的具体扁平化模式。

**SCORE — Dynamic State Tracking** — arxiv 2503.23512 🔶 `[v1-sourced, 本轮未复验]`【借实现思路】
- v1 记:每角色/物体符号状态 `S(t)∈{active,lost,destroyed}` 建成 **Markov 链,destroyed/lost 为吸收态** + 分层 episode 摘要 + 混合检索(FAISS+TF-IDF+情感过滤)。
- **对你的价值**:吸收态思路**直接对应你的 `valid_from/valid_to`**,可防"死人复活/能力凭空消失"。**引用前复验 id。**

🔶 **CHARET / SoCP**(角色情感状态追踪 / 多角色独立情感线)、**CREFT**(2505.24553,多 agent 抽人物关系三元组,可 seed 你的 `knowledge_triples`)—— `[本轮未独立验真]`,作为"角色状态机 + 多情感线 + 关系抽取"的实现思路参考。**C 档。**

### 1.F 评测基准(中文优先)【S — 评测闭环是 R5 落地底座】

| Benchmark | 语言 | 规模 | 维度/亮点 | 验真 | 成熟度 |
|---|---|---|---|---|---|
| **CharacterEval**([2401.01275](https://arxiv.org/abs/2401.01275)) | **中文** ✅ | 1,785 多轮 / **23,020 examples** / 77 角色(中文小说+剧本)+ 百度百科人设 | 4 维 13 指标(对话力/角色一致性/扮演吸引力/人格回测)+ **CharacterRM 奖励模型**(论文称中文上比 GPT-4 更贴人类) | ✅ 论文+[repo](https://github.com/morecry/CharacterEval) 身份核实 | **production 评测** |
| **CharacterBench**([2412.11912](https://arxiv.org/abs/2412.11912),AAAI'25) | **双语** ✅ | **22,859 标注 / 3,956 角色 / 25 类** | 6 aspect 11 维;**Boundary Consistency** 对应知识隔离,**Attribute/Behavior Consistency** 对应区分度 + CharacterJudge | ✅ 论文+[repo](https://github.com/thu-coai/CharacterBench) 身份核实 | prototype/eval |
| **InCharacter**([2310.17976](https://arxiv.org/abs/2310.17976),ACL'24) | 多语 | 32 角色 × 14 心理量表 | **用心理访谈测人格保真度**,SOTA ~78.9% | ✅ 论文+[repo](https://github.com/Neph0s/InCharacter) 身份核实 | prototype/eval |
| **PersonaEval**([2508.10014](https://arxiv.org/abs/2508.10014),COLM'25) | 多语 | 人类原创对话 | **"谁在说话"识别**:LLM ~68.8% vs 人类 ~90.8% | ✅ 论文+repo, MIT | prototype/eval |
| **PersonaGym**([2407.18416](https://arxiv.org/abs/2407.18416),EMNLP'25) | 多语 | persona agent 动态评测 | **PersonaScore**(基于决策理论的自动指标) | ✅ 论文核实 | eval |
| **CharacterRM** | 中文 | — | 角色扮演专用 reward model(随 CharacterEval,Baichuan2-13B base) | ✅(同上 repo) | 可复用 |

补充(✅ 已验真,**B 档**):**TimeChara**(时间维知识边界,§1.C)、**Moral RolePlay / "Too Good to be Bad"**(arxiv [2511.04962](https://arxiv.org/abs/2511.04962) [accessed:2026-05-30]:安全对齐 LLM **演不好反派**,四级道德对齐量表 —— "反派/灰色角色辨识度"的直接靶子)。
🔶 v1 另列 **ConStory-Bench**(2603.05890,5维×19子型错误 taxonomy,其中 **Characterization 4 子型**:记忆矛盾、知识矛盾、技能波动、能力遗忘)、**LifeState-Bench**(2503.23514)、**RAIDEN benchmark** —— `[v1-sourced, 本轮未复验]`。其中 **ConStory 的 Characterization 4 子型**是很好的 QA 失败模式清单,建议复验后采用(见 §5)。

### 1.G 训练/模型类方案(若将来走 SFT 路线)【B — 点到为止】

| 方案 | 语言 | 方法 | 数据/模型 | 验真 |
|---|---|---|---|---|
| **CoSER**([2502.09082](https://arxiv.org/abs/2502.09082),ICML'25) | **双语(英主)** | Given-Circumstance Acting:**一个场景里顺序扮演多个角色** + SFT | **17,966 角色/771 书**;CoSER-8B/70B(LLaMA-3.1)+ 数据全开放 | ✅ 论文/[repo](https://github.com/Neph0s/CoSER)/[HF 数据集](https://huggingface.co/datasets/Neph0s/CoSER)/[70B 模型](https://huggingface.co/Neph0s/CoSER-Llama-3.1-70B) **全核实**。**production** |
| **PsyMem**([2505.12814](https://arxiv.org/abs/2505.12814),TACL) | **英文** ❌ | **26 项心理指标**(Big5×5+Schwartz×10+Zimbardo×6+TKI×5)+ 两阶段 memory-alignment 训练(Nano-GraphRAG,α=20 上权重) | ~5,400 角色/~39,000 对话;PsyMem-Qwen(7B);fidelity ~82.6%(超 CoSER-70B/GPT-4o) | ✅ 论文核实;**未见公开 repo**(no-source-found)。**theoretical/prototype** |
| **PCL**([2503.17662](https://arxiv.org/abs/2503.17662),ACL'25 Findings) | 英文 | Persona-Aware Contrastive Learning + Role Chain 自问(annotation-free) | 黑/白盒 LLM | ✅ 论文核实;repo 未确认。**theoretical** |
| **Character-R1**([2601.04611](https://arxiv.org/abs/2601.04611),2026-01) | 未明 | **RLVR**:认知一致(非表层模仿),针对 OOC | — | ✅ 论文核实;repo 未确认。**theoretical** |
| **Character-LLM**([2310.10158](https://arxiv.org/abs/2310.10158),EMNLP'23) | 英 | 可训练单角色 agent(奠基);**一角色一模型,30+ 角色不可扩展** | — | ✅(基础事实核查确认)。**prototype** |

🔶 v1 另列 **RoleLLM**(2310.00746,产出 RoleGLM 中文)、**OpenCharacter**(2501.15427,20k 合成角色 + LLaMA-3 8B 权重)、**CharacterGLM**(EMNLP'24 中文)、**ChatHaruhi**(2308.09597,32 角色 / 54k 对话 + Haruhi-MBTI)、**CharacterBot/CharLoRA**(2502.12988 鲁迅)、**Pygmalion-3 / Mistral-NeMo RP 变体**(开源 RP 基座)—— 均 `[v1-sourced, 本轮未复验]`。**若走 SFT,这些是数据/基座候选**,但**中文高质量开放训练集仍是缺口**(见 §6)。

### 1.H 多角色"社会模拟"式生成(与你的多 agent 架构最贴)【S】

**BookWorld** — arxiv [2504.14538](https://arxiv.org/abs/2504.14538) [accessed:2026-05-30] ✅,repo [alienet1109/BookWorld](https://github.com/alienet1109/BookWorld) ✅(身份核实,官方 "[ACL 2025] ... From Novels to Interactive Agent Societies")
- **架构(v1 抓得很细,保留)**:**role agents(每角色)** 静态属性(性别/年龄/性格)+ 动态属性(目标/状态/记忆),**双层记忆 STM/LTM**;**world agent** 生成"冲突丰富的事件" + 环境响应;每次输出 JSON 含 action_type/target/**visibility** + 文学化叙述(含思想/言语/动作)。对前序方法 win rate 75.36%。
- **时效性**:ACL'25,repo 在维护。**鲁棒性**:静/动属性分离 + STM/LTM + 可见性过滤,是被验证过的清晰设计。**可行性**:low-medium —— 你已有 World agent + Camera agent(可见性)。**支持中文**(`language:zh`,可转 SillyTavern 卡)。
- **对你的价值(核心)**:这几乎是你"六 agent + LangGraph"的**角色侧参考实现**——role-agent 的 memory/status/goal 更新循环 + world-agent 总控,可**对照借鉴架构**(不必照搬代码)。直接呼应 R2(LayeredMemory)、R1(总控)。

🔶 **Character.AI 生产架构**(MQA + 跨层 KV 共享 + **生成后 affective ranking 二次排序** + 会话级记忆缓冲)、**MRPrompt / Memory-Driven RP**(2603.19313,4 段记忆能力 anchor/select/bound/enact + Magic-If 协议,**有中文 split**,Qwen3-8B+MRPrompt 持平闭源大模型)—— 均 `[v1-sourced, 本轮未复验]`。其中 **Character.AI 的"生成后情感排序二次 pass"** 与你 Consistency agent 门控同构;**MRPrompt 的分层记忆**贴近 LayeredMemory L0-L3。

### 1.I SillyTavern Character Card V2 + Lorebook(数据 schema 参考)🔶【B】
- v1 抓的 V2 字段(`description/personality/scenario/first_mes/system_prompt/post_history_instructions/character_book(lorebook: keys/content/priority/position/scan_depth)`)是成熟的**角色卡数据结构**;实践模式"角色卡管核心人设(800-1200 token)+ lorebook 按关键词触发细节"。`[v1-sourced, 本轮未复验]`
- **对你的价值**:Story Bible 角色卡可对齐 V2 字段以互通;你的 `knowledge_triples` 可驱动类 lorebook 的关键词触发检索。

---

## 2. 综合判断

**2.1 最该投入的不是"训练角色模型",而是"角色一致性护栏 + 评测闭环"。** 对 prompt-driven 中文小说系统,ROI 排序:
- **(A) 知识边界护栏**:RoleRAG/TimeChara/RoleFact 思路 + 你已有 `valid_from/valid_to` —— 消灭"角色提前知道未来""乱编不该知道的事"。low-medium,中文就绪。
- **(B) 评测闭环**:接 **CharacterEval(中文)** 做回归;加两个 training-free 自研指标——**去标签猜说话人**(源自 PersonaEval)+ **persona 自洽三指标**(prompt-to-line/line-to-line/Q&A,源自 2402.10962);把 **WebNovelBench 的 Distinctiveness/Consistency 两维**做成 rubric。
- **(C) 关系/情感追踪**:用 signed-network 思路监控"是不是把所有人都写成关系好"(此条依赖未复验论文,作为**思路**采纳);用 SCORE 吸收态思路防"死人复活"。

**2.2 不要被"必须 SFT"带跑偏,但要诚实承认结构上限。** PersonaEval 显示角色 SFT 数据可能损害判别;结构化 prompt(RRP)+ 检索/解码已能拿大部分收益。**但 RPNA 证明纯 prompt 对 `dialogue_distinct` 有同一回路上限** —— 要真正突破,需 ②解码干预(开源模型)/④SFT/换基座三选一。SFT(CoSER/PsyMem/Character-R1)是第二阶段大招,**前提是自建中文角色对话数据集**(缺口,见 §6)。

**2.3 "角色一致性"与 R2(记忆)、R3(图谱)高度耦合,应合并设计**(三者同为高优先级,R3 支撑):
- 角色**认知边界** = 图谱在某章节号下对该角色可见的三元组子集(R3 × R5);
- 角色**记忆** = LayeredMemory 里该角色的 L0–L3(R2 × R5);
- RoleRAG / BookWorld / SCORE 共同印证"角色 = 受时间/视角约束的知识检索 + 状态机",与你 Camera agent(过滤可见事件)+ KnowledgeGraph 天然契合。

**2.4 扁平化是系统性、跨维度的。** Narrative Flattening(✅)证主题/情感/风格被 post-training 压平;RPNA(✅)证角色推理通路被压成同一回路;signed-network(🔶)若属实则关系也被压成"紧密+正向"。**纯换 prompt 难根治,但可缓解**(选扁平化更轻的基座、提温度、显式注入冲突/负向关系、角色卡强约束)。**这是 R5 与 R1、R6 联手对抗的核心敌人**;Moral RolePlay(✅)的"演不好反派"是其极端表现。

---

## 3. Top 候选方案(给重构直接选型)

| 排序 | 方案 | 用途 | 为什么 | 成本 | 中文 | 验真 |
|---|---|---|---|---|---|---|
| ⭐1 | **CharacterEval + CharacterRM** | 中文角色一致性**评测底座** | 唯一成熟中文角色扮演 benchmark + 专用 reward model;repo 身份已核实 | low | ✅ 原生 | ✅ |
| ⭐2 | **RoleRAG 范式 + 你的 KnowledgeGraph** | 角色**知识边界护栏**(防崩塌) | training-free,复用已有图谱;消灭最高频崩塌;RoleBench-zh 已测 | medium | ✅ | 论文✅/repo缺 |
| ⭐3 | **去标签说话人识别(PersonaEval 思路) + 2402.10962 三指标 + WebNovelBench 两维** | **对白区分度 + 持续一致性**自动指标(直击 SEQR `dialogue_distinct`) | 无需训练、可进 CI;PersonaEval/WebNovelBench 背书 | low | ✅ | ✅ |
| ⭐4 | **BookWorld 架构** | 多角色 agent 的 **memory/status/goal 循环 + 可见性**参考 | 与你 LangGraph 六-agent 同构,支持中文;repo 身份已核实 | medium | ✅ | ✅ |
| ⭐5 | **TimeChara 时间点知识边界** | Consistency agent 新增检查项 | 卡"角色知道未来"——连载刚需 | medium | ⚠️需中文化 | ✅ |
| ⭐6 | **RoleFact 置信阈值调制** | 降幻觉(事实+18%/时间−44%) | 代码公开、效果量化、即插 | medium | ⚠️ | ✅ |
| 备选A | **PsyMem 26 项心理指标做角色卡 schema** | **不训练也能用**:让人设立体可区分 | Big5+Schwartz+Zimbardo+TKI,low-cost 提升对白区分度的杠杆 | low | ⚠️ schema 可中文化 | ✅(论文) |
| 备选B | **CoSER 数据集/模型 / GCA 评测法** | 若走 SFT 的数据构造 + 评测 | 最大开放真实小说对话集(英为主) | high | ⚠️英主 | ✅ |
| 备选C | **split-softmax(2402.10962)** | 解码期防漂移 | training-free,但**需本地开源模型**(Qwen3.6) | medium | ✅ | ✅ |

> **机理诚实提示(承 RPNA)**:⭐3 的指标能**测**出区分度差,但纯 prompt 改不动同一回路上限;要让分数有上限突破,需配 备选C(解码) / 备选B(SFT) / 或 §0.3 换基座。

### 3.1 落地路径(承 v1 的三候选,按本系统现状改写)

v1 把方案分成三档并给了具体工程量,本稿沿用并按"prompt-driven + 闭源 API 为主"现状调整顺序:

- **第一波(1–2 周,直击 `dialogue_distinct`,纯 prompt)**:Writer agent prompt 引入 **CSC(Voice/Action 分离,源自 Talk Less Call Right ✅)** + **PsyMem 26 项心理指标子集**(Big5×5 + Schwartz×10 + Zimbardo 3–5 维 ≈ 18–20)写进 Story Bible 角色卡 + 生成前 **Magic-If 检索(anchor→select→bound→enact,源自 MRPrompt 🔶)**;同步上 ⭐3 的两个 training-free 指标做回归。**风险**:RPNA 提醒——这只拿中段提升,非根治。
- **第二波(并行,架构)**:⭐2 知识边界护栏。具体 delta(承 v1):① `knowledge_triples` 加实体归一 pass(~1 天);② 检索前加 boundary-check(~2 天,每查多一次 LLM 调用);③ 加 `valid_from/valid_to` 吸收态校验(schema 已有);④ Writer agent 包成 role-agent + BookWorld JSON 输出(action_type/target/visibility/narrative)。
- **第三波(若前两波触顶,4–8 周,大招)**:走 SFT —— CoSER 的 GCA 目标 + PsyMem 两阶段 memory-alignment,基座选 **本地 Qwen2.5/3.6**(LoRA,单卡 A100 数天),用 CharacterEval 评测。**前提**:自建中文角色对话数据集(§6);**风险**:安全对齐可能损害反派刻画(Moral RolePlay ✅),需保留可控道德机制。

---

## 4. 失败模式清单(角色一致性崩塌的具体形态;承 v1 §7,标注验真)

1. **跨轮 persona 漂移** — LLaMA2-70B 第1轮 ~0.8 → 第8轮 ~0.4;更大的模型漂移更多(2402.10962 ✅ / 2412.00804 ✅)。
2. **记忆/知识矛盾** — ConStory Characterization 最常见错误(知识矛盾/技能波动/能力遗忘)(🔶)。
3. **认知边界越界** — 角色知道不该知道的事(RoleRAG ✅ 专治)。
4. **"助手音"泄漏** — 道德说教 / 出戏拒答,被记为 RP-LLM 头号敌人(Moral RolePlay 2511.04962 ✅ + 中文 RP 实践经验)。
5. **反派对齐坍塌** — 安全训练压过角色,演不出真恶(Moral RolePlay ✅)。
6. **风格扁平化** — post-training 后收敛到窄默认风格(Narrative Flattening 2605.27878 ✅),直接拉低 `dialogue_distinct`。
7. **中段错误聚集** — 错误集中在叙事中段 / 高熵段(ConStory 🔶)。
8. **角色复活 / 状态违例** — 吸收态(死/毁)实体凭空回归(SCORE 2503.23512 🔶 可标记)。
9. **跨角色知识串味** — 角色 X 展示只有 Y 才有的知识(CharacterBench Boundary Consistency ✅)。
10. **同一回路无独立认知** — RPNA(2510.24677 ✅)证 prompt 诱导的人设共用同一推理回路 = 纯 prompt 方法的结构上限。

---

## 5. Open Questions(承 v1 §8,删除已被证伪项,标注验真状态)

1. **中文细分文风(正式度/古白话/方言标记)能否扛住基座扁平化?** Narrative Flattening 只在英文 OLMo 上证过,无中文复现;直接影响 `dialogue_distinct`。
2. **有没有可直接用的中文 CoSER/PsyMem 等价数据集?** ChatHaruhi(32)+ CharacterEval(77)+ CharacterGLM 数据是最近的,但都到不了 CoSER 的 17,966 角色规模。[本轮 no-source-found:中文 CoSER 类训练集]
3. **split-softmax 能否用纯 prompt 的 attention 偏置近似?**(如 attention-sink token、"记住你是 X"插入)未见论文测过纯 prompt 设定,值得做受控消融。
4. **SEQR `dialogue_distinct` ρ=−0.16,瓶颈在模型还是评测本身?** CharacterBench 指出 Attribute/Behavior Consistency 是需定向查询的 sparse 维 —— 你的指标可能没测在对的线索分布上。
5. **CharacterRM/CharacterJudge 能否直接当 Consistency agent 评分器?** 现有 reward model 都在**多轮对话**上训,迁到**长篇小说章节**(叙事体)可能 OOD,需实测。
6. **CSC 的 scene-contract 在章节长度下的合适粒度?** Talk Less Call Right 面向短轮工具 agent,搬到章节级需重定义 "Voice/Action",无现成工作。
7. **关系扁平化的可控对抗** — 若 signed-network 属实,如何在生成端注入合理负向/紧张关系而不破坏连贯,尚无成熟方案。
8. **RPNA 的医学→小说外推** — 在你自己的 SEQR 上做一次消融式验证(同一基座、有/无角色卡,看 `dialogue_distinct` 是否真触顶),是"训练 vs prompt"之争最干净的实验。
9. **一批 v1 条目需复验 id** — 标 🔶 `[v1-sourced, 本轮未复验]` 的(Nautilus 2605.09863、RAIDEN-R1 2505.10218、SCORE 2503.23512、ConStory 2603.05890、LifeState 2503.23514、MRPrompt 2603.19313、CREFT 2505.24553、OpenCharacter 2501.15427、RoleLLM 2310.00746、ChatHaruhi 2308.09597、CharacterGLM、CharacterBot 2502.12988、SA-LLM 2503.08842、MIMIC、Constella 2507.05820、bootstrap distinctiveness 2301.05659、Pygmalion-3、Character.AI blog、Signed Network 2510.18932、AMADEUS 2508.02016)—— 写进最终重构文档前应逐条 verify。**这些大多是 v1 已查证、只是不在本轮验真批次里,可信度中高,但需复核 id。**

---

## v1 ↔ v2 diff

### 新增(v2 相对 v1)
- **§0.1 术语判决表**:把基础事实核查结论落地——**PerRoleCognition=杜撰(删)**、**RPNA=真实(2510.24677,保留)**。v1 §3 本就独立判过 PerRoleCognition 是幻觉,本稿与之一致并补强;并澄清"RPNA≠角色扮演叙事分析"那种错误含义。
- **§0.3 模型选型事实层(全新)**:接入 2026 中文模型实测(Kimi K2.6 文笔居前 / DeepSeek V4-Pro 知识强文笔少 / Qwen3.6 开源利于本地 split-softmax),并与"split-softmax 需开源模型""Narrative Flattening=基座越 post-trained 越扁平"串成**选型决策链**。
- **WebNovelBench(2505.14818)八维**:新增并锁定 **Distinctiveness of Character Dialogue / Consistency of Characterisation** 两维作 R5 rubric(§1.D / §3 ⭐3),与 SEQR `dialogue_distinct` 直接对接。
- **PersonaEval / PersonaGym / Persistent Personas / Moral RolePlay / Character-R1**:新增本轮已验真条目(评测/长程/反派/RLVR 四块)。
- **每条 S 档显式补「时效性/鲁棒性/可行性」**,并给全表加验真状态标记(✅/🔶/⛔)。

### 纠正(v2 相对 v1)
- **2402.10962 标题纠错**:v1 写成 *"Measuring and Controlling **Persona Drift**..."*;本轮验真确认真实标题是 *"Measuring and Controlling **Instruction (In)Stability** in Language Model Dialogs"*(repo 名 `persona_drift` 是误记来源)。论文真实存在,按"纠正标题"处理,**不删论文**。
- **把 v1 隐含的"必须 SFT"明确改写为"谱系四档"**(§0.2):用 PersonaEval(SFT 数据有害)、2402.10962(解码 training-free)、Talk Less Call Right(纯 prompt 提分)三条反向证据封死;同时**保留 v1 最强洞见**(RPNA+Narrative Flattening 证纯 prompt 有结构上限),不滑向任何一端。
- **RoleRAG 成熟度据实下调**:明确**未找到稳定 repo/star**(no-source-found),标 论文✅/repo缺,而非 v1 略偏"可直接用"的语气。
- **v1 大量 2025-2026 条目降级为 🔶 `[v1-sourced, 本轮未复验]`**:它们**不在本轮验真批次**(是"未复核"而非"被判假"),包括 Nautilus、RAIDEN-R1、SCORE、ConStory、LifeState、MRPrompt、CREFT、OpenCharacter、RoleLLM、ChatHaruhi、CharacterGLM、CharacterBot、SA-LLM、MIMIC、Constella、bootstrap distinctiveness、Pygmalion-3、Character.AI blog、Signed Network、AMADEUS。引用前需逐条复验 id(§5.9)。
- **把 v1 偏英文工程细节(Character.AI 的 MQA/KV 共享、Mistral-NeMo 变体列表等)压缩为 B/C 档点到为止**:对一个 prompt-driven 中文系统,聚焦中文就绪 + training-free 的 S 档。

### 删除(剔除幻觉 / 失真)
- **PerRoleCognition** ——⛔ 杜撰(基础事实核查 + v1 §3 双重确认),从正文/候选**彻底移除**,仅留"勿引"说明。
- **"RPNA = 角色扮演叙事分析(role-play narrative analysis)"这一错误含义** —— 删除;RPNA 仅保留其真实所指(神经元消融论文 2510.24677,与 v1 一致)。
- **2402.10962 的错误标题 "Persona Drift"** —— 作为失真事实删除/替换(见"纠正")。
- **说明**:本轮针对 R5 的**论文级验真清单(31 条)中没有任何 exists=false 的"论文不存在"条目**——唯一 exists=false 的是 2402.10962 的**标题不符**(论文本身存在,已按纠正处理)。真正"杜撰需删"的是 **PerRoleCognition** 与 **RPNA 的错误含义**,二者来自三项基础事实核查,而非引用验真表。
