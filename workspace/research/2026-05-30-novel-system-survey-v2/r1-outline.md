# R1 · 大纲 / 剧情结构生成 —— 终稿 v2

| 字段 | 值 |
|---|---|
| 方向 | LLM 长篇小说(网文 / 多卷)大纲 · 剧情结构生成 |
| 综合者 | research sub-agent (Claude Opus 4.8 1M) |
| 日期 | 2026-05-30 |
| 数据访问日 | 全部 claim 统一 [accessed:2026-05-30] |
| 验真手段 | WebSearch + WebFetch(arXiv abstract/HTML、ACL Anthology、官网)+ GitHub REST API 取 star/pushed_at/license + Semantic Scholar / arXiv API 交叉验真;每条 claim 已逐一过 exists 校验 |
| 优先级锚定 | 记忆(R2)= 角色(R5)= 大纲(R1)> 图谱(R3)。本方向属 S 档,做到最深;B/C 档点到为止 |

> **本稿与 v1 的关系**:v1(2026-04-28)是 clean-room WebSearch 调研;v2 在此之上做了三件事 ——(1)用一手验真把 **exists=false 的幻觉剔除**(见文末 diff 与 `hallucinations_removed`);(2)纠正 v1 与新调研中的事实错误(最关键:Expansion-Ratio 的"α₁=0.05/α₂=0.20/R=0.01"具体数值在 abstract 中**无法核实**,降级为待核;DOME 叙事理论主框架是**英雄之旅**而非五幕);(3)补入 v1 没有的新工作(KG+文学理论 2508.03137、LongWriter/AgentWrite、Propp-34 中文功能、oh-story 三层大纲、WebNovelBench 8 维权重)。
>
> **重要诚信提示**:本方向材料中出现的 **"PerRoleCognition"** 一词经独立核查为**杜撰**(arXiv / Google Scholar / 全网均无),已在本稿中**不予采用**;若在角色方向(R5)看到该引用同样应剔除。最接近的真实工作是 RPNA(arXiv:2510.24677)、RoleRAG(2505.18541)、Character-LLM(2310.10158),与 R1 大纲无直接关系,仅备注于此防止串扰。

---

## 摘要(给决策者的 5 句话)

1. **用户锚点 claim 基本属实,但有一处理论纠正**:DOME 的记忆四元组确为 `<subject, action, object, index(=章节号)>`、双层 rough/detailed 也确实存在并按 M=3 扩展;但 DOME 整合进 rough outline 的叙事理论主框架是 **Joseph Campbell 英雄之旅**(辅以 Freytag/Vogler 与五段式),不是单纯"五幕为主"。
2. 英文长篇生成有一条清晰演进链 **Re3(2022)→ DOC(2023)→ DOME(2025)→ KG+文学理论(2025-08)**;最后一环用"**大纲相似度阈值触发反转**"是低成本高 ROI、可直接抄进重做的工程信号。
3. 长输出的工程地基是 **LongWriter / AgentWrite**(ICLR 2025,production 级,~1.9k★,Apache-2.0):"带每段字数预算的写作计划 → 逐段顺序填充",已工业验证、可直接复用;**Optimal Expansion Ratio**(2505.12572)从信息论角度论证"存在最优压缩-扩展比",但**具体倍数 abstract 未给,必须核 PDF**。
4. **中文就绪度是本系统命门,且有强一手 source**:WebNovelBench(4000+ 中文网文 benchmark,8 维权重已逐字核实)、Propp-34 中文网文叙事功能论文(经 Semantic Scholar 交叉验真为真)、oh-story-claudecode(中文网文三层大纲 skill 包,1.7k★,极活跃)三者构成"评测 + 理论 + 实践"闭环。
5. 可直接复用代码的极少(LongWriter / snowmeth / oh-story 实践文档 / WebNovelBench 评测);DOME / KG+理论 / Expansion-Ratio / Ex3 都是论文级,理念价值高但落地成本 = **high(自实现)~ rewrite(需训练)**。

---

## 0. 复核用户锚点:DOME 四元组 + 双层 rough/detailed

**DOME** = *Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement*,arXiv:2412.13575(提交 2024-12-18),**NAACL 2025 Long Paper**,作者 Qianyue Wang, Jinwu Hu, Zhengping Li, Yufeng Wang, Daiyuan Li, Yu Hu, Mingkui Tan(华南理工等)。
- abstract / 元数据:https://arxiv.org/abs/2412.13575 [accessed:2026-05-30]
- HTML 全文:https://arxiv.org/html/2412.13575v1 [accessed:2026-05-30]
- ACL Anthology 收录页:https://aclanthology.org/2025.naacl-long.63/ [accessed:2026-05-30]

> **验真澄清(防 v1 误判)**:`https://aclanthology.org/2025.naacl-long.63/` 这一页**确实存在**且就是这篇 DOME 论文(标题/作者完全一致)。本批验真里它被一度标 exists=false,理由是"页面标题不是字面 'DOME' 而是论文全称"——这是命名匹配的误报,**不是论文不存在**。结论:DOME 论文真实、URL 有效,本稿正常采用;但**不要把 "pp.1352–1391" 这一精确页码当作已核实事实**(本批未独立确认页码,降级为待核)。

- **四元组 ✅ 属实**:DOME 的时序知识图谱 TKG 以四元组 `<subject, action, object, index>` 存储,index = 该信息所属**章节号**。与本系统现有 `knowledge_triples` 表几乎 1:1 对应。
- **双层 rough/detailed ✅ 属实**:`Rough Outline R` 从用户输入一次性生成、对齐叙事理论;`Detailed Outline d_i` 在写作中按 rough 段落 + 检索记忆动态扩展,每个 rough 段扩成 **M=3** 个 detailed。rough 固定、detailed 动态,是 DOME 核心。
- **⚠️ 事实纠正(v1 写"5 stages aligned with Joseph Campbell")**:DOME 的叙事理论主框架确以 **Campbell 英雄之旅**为骨,辅以 Freytag 戏剧结构 + Vogler《作家之旅》,并覆盖 exposition/rising/climax/falling/resolution 五段式。复刻 DOME 理论层 = 复刻英雄之旅 + 五段式,而非单纯五幕。
- **配套资源**:`Qianyue-Wang/DOME_dataset` —— **仅数据无方法代码**(各方法输出 + 消融,按编号组织)。GitHub:**5★,无 LICENSE**,数据-only。→ 想用 DOME 必须照论文自实现。
  - https://github.com/Qianyue-Wang/DOME_dataset [accessed:2026-05-30]
- **DOME 自述局限(工业落地硬伤)**:无自动评测、依赖昂贵人评;基座 Qwen1.5-72B / Llama3-70B / Yi1.5-34B,英文 premise 实验,生成故事约 7k 词量级(单篇,非系列);依赖手写 prompt。逐卷百万字会把开销放大数十倍。
- **时效性 / 鲁棒性 / 可行性**:时效性 = 当前(NAACL 2025);鲁棒性 = prototype,仅 7k 词验证、M=3 固定比例偏刚性;可行性 = **high(自实现)**,prompt + 英雄之旅模板需中文化重写,理论层可迁移。

---

## 1. 英文长篇故事生成学术主线(S 档核心)

| 方案 | 论文 / repo | 时效(last push) | 成熟度 | star / license | 一句话 |
|---|---|---|---|---|---|
| **Re3** | EMNLP 2022, 2210.06774 / yangkevin2/emnlp22-re3-story-generation | stale(2022) | prototype | 257★ MIT | Plan→Draft→Rewrite→Edit 递归重提示,长篇生成奠基 |
| **DOC** | ACL 2023, 2212.10077 / yangkevin2/doc-story-generation | stale(2023) | prototype | 160★ MIT | detailed outliner + FUDGE(OPT-350m)controller;比 Re3 plot coherence 大幅提升 |
| **DOME** | NAACL 2025, 2412.13575 | 仅数据(2024-10) | prototype | 数据 5★ | 双层动态大纲 + 时序四元组记忆(见 §0) |
| **KG+文学理论** | 2508.03137(2025-08, BJTU) | **无公开 repo** | theoretical/prototype | — | Forster story/plot + KG 驱动反转 + 大纲相似度阈值(见 §1.1)|
| **RecurrentGPT** | 2305.13304 / aiwaves-cn/RecurrentGPT | stale(2024) | prototype | 1001★ GPL-3.0 | 自然语言模拟 LSTM,无显式大纲、滚动记忆(对照流派)|

一手链接:
- Re3:https://arxiv.org/abs/2210.06774 · 代码 https://github.com/yangkevin2/emnlp22-re3-story-generation [accessed:2026-05-30](257★ MIT 已核)
- DOC:https://arxiv.org/abs/2212.10077 · 代码 https://github.com/yangkevin2/doc-story-generation [accessed:2026-05-30](160★ MIT,GPT-3 + OPT-175B via Alpa 已核)
- RecurrentGPT:https://arxiv.org/abs/2305.13304 · 代码 https://github.com/aiwaves-cn/RecurrentGPT [accessed:2026-05-30](1001★ GPL-3.0)

**演进结论**:Re3/DOC 已 stale 且属英文 OPT/GPT-3 时代,代码不建议直接用;**站在 DOME + KG-理论这一最新环上做 clean-room 重写**最合理。Re3 的 reranker、DOC 的 FUDGE 控制器思想可作消融对照。

> **v1 勘误**:v1 §1 / §7 列出 DOC v2 代码 `facebookresearch/doc-storygen-v2`。本批验真**未独立确认**该 v2 仓库,故本稿**不把 v2 仓库当已核实事实**(降级为待核);DOC v1 仓库 `yangkevin2/doc-story-generation`(160★ MIT)已核实,以它为准。

### 1.1 ⭐ 最值得抄的新工作:KG + 文学理论(arXiv:2508.03137,2025-08,北京交大)
晚于 DOME 半年,专治"主题漂移 + 情节平淡"两病,对重做极具参考价值。作者 Ge Shi, Kaiyu Huang, Guochen Feng。
- HTML:https://arxiv.org/html/2508.03137v1 [accessed:2026-05-30]
- 引入 **E.M. Forster 的 story(时序事件)vs plot(因果链)区分**、扁平/圆形人物、结构闭合("意外必须纳入可理解的逻辑链")。
- **KG 驱动反转**:从当前故事抽 KG(主角目标为核心节点)→ 生成与主目标相关的"障碍节点"→ 据扩展 KG 生成新大纲。
- **⭐ 大纲相似度阈值触发反转**:对最近两版大纲算相似度,超阈值即判"情节停滞 → 需反转"。这是一个**可直接抄进重做的工程信号**(用 outline embedding 自检"原地打转")。
- 双记忆(长期 = 关键信息 / 短期 = 最近两版大纲)+ writer/reader simulator 互评;面向 >1 万词长故事的抗漂移。基座含 GPT-3.5-turbo / Claude 系。
- **时效性 / 鲁棒性 / 可行性**:时效性 = 最新(2025-08);鲁棒性 = prototype,英文、人评为主、**未与 DOME 直接对比**(仅 related work 提及);可行性 = **high(自实现,无 repo)**,但"大纲相似度阈值"这一信号实现成本极低,**强烈建议优先抄**。

### 1.2 RecurrentGPT(对照流派,不建议作主架构)
自然语言模拟 LSTM 长短期记忆,逐段生成 + 硬盘存"语言化记忆",可任意长度、可交互。**1001★,GPL-3.0,stale(2024)**。中文移植 `jackaduma/Recurrent-LLM`(双语 zh/en,多后端 ChatGLM/Baichuan/Vicuna,Gradio UI;"AI 写小说"已核)。它"无显式宏观大纲"与 DOME 理念相反,适合消融对照。
- https://github.com/jackaduma/Recurrent-LLM [accessed:2026-05-30](已核:RecurrentGPT 开源实现,中英双语)

---

## 2. 经典剧情结构框架(B 档 —— 给"可落地槽位表")

给 rough outline 层做**可插拔 structure template**。本节为结构原典/通识,B 档点到为止;落地价值在统一 schema。

- **英雄之旅(12 阶段)** —— Campbell《千面英雄》(1949)→ Vogler《作家之旅》(1992/2007,12 阶段):Ordinary World→Call→Refusal→Mentor→Crossing Threshold→Tests/Allies/Enemies→Approach→Ordeal→Reward→Road Back→Resurrection→Return with Elixir。三幕分组:Departure/Initiation/Return。**DOME 用的就是这套**(§0)。
- **Save the Cat(15 beats)** —— Blake Snyder《Save the Cat!》(2005);Jessica Brody《… Writes a Novel》(2018)适配小说。15 拍映射三幕,**每拍带百分比位置**(Opening Image 1% / Catalyst 10% / Break Into Two 20% / Midpoint 50% / All Is Lost 75% / Break Into Three 80% / Final Image 99% …)。最适合做 beat→章节定位锚。
- **Snowflake Method(10 步)** —— Randy Ingermanson:一句话→一段(含三大灾难+结局)→人物表→四段情节→人物视角梗概→四页梗概→人物全表→**场景 spreadsheet(POV+情节+页数)**→场景段落→初稿。**本质 = 分形逐层扩展**,与 §3 expansion-ratio 同源。AI 实现 `joelgrus/snowmeth`(**17★,MIT**,FastAPI+DSPy+React,step10 逐章生成,小但干净;作者自评"sort of a novel")。
  - https://github.com/joelgrus/snowmeth [accessed:2026-05-30](17★ MIT 已核)
- **八点弧 Eight-Point Arc** —— Nigel Watts(1996):Stasis→Trigger→Quest→Surprise→Critical Choice→Climax→Reversal→Resolution。粒度最粗最稳,适合"卷级"或短篇骨架。

> **工程建议(沿用 v1 并强化)**:统一 schema `{beat_id, name_zh, position_pct, required_elements[], emotional_target}`,4 套共用;中文网文默认走 §4.3 的"总纲/卷纲/章纲"三层 + 三幕拉长。**Save the Cat 的 position_pct 是最实用的"beat→章节"定位锚**。

---

## 3. 分层扩展 / 长输出工程(S 档 —— "逐卷展开"机制证据)

- **⭐ LongWriter / AgentWrite**(ICLR 2025,arXiv:2408.07055,清华 KEG + 智谱):AgentWrite 两阶段 ——**①产出带"每段目标字数"的写作 plan;②按 plan 逐段顺序生成、拼接**,让现成 LLM 稳定输出 1 万+词;造了 LongWriter-6k SFT 数据 + LongBench-Write 评测。**~1.9k★,Apache-2.0,production-grade,活跃**;开源 LongWriter-glm4-9b / llama3.1-8b。→ "**带字数预算的大纲 → 逐段填充**"是已工业验证、低成本、可直接复用的模式。
  - https://arxiv.org/abs/2408.07055 · https://github.com/THUDM/LongWriter [accessed:2026-05-30]
  - 作者:Yushi Bai, Jiajie Zhang, Xin Lv 等(已核;ICLR 2025 经 OpenReview 确认)
  - **时效性 / 鲁棒性 / 可行性**:时效性 = 当前且活跃;鲁棒性 = production,已被后续多篇当 baseline;可行性 = **low(纯 prompt 模式)/ medium(若用其 SFT 模型)**。本方向"逐卷展开"的字数预算 + 逐段填充直接采用它。
- **⭐ Optimal Expansion Ratio**(arXiv:2505.12572,2025-05,作者 Hanwen Shen, Ting Ying):明确把框架写成 **outline → section outline → manuscript**,并点名 DOME / Plan&Write / LongWriter 都用此两阶段。用信息论量化不同压缩-扩展比下的语义失真,实验在**超长小说(>100 万词)**上证明"**存在**最优压缩-扩展比、可显著降低失真"。
  - https://arxiv.org/abs/2505.12572 [accessed:2026-05-30]
  - **⚠️⚠️ 重大事实纠正(对 v1)**:v1 §1 写下了非常具体的数值 —— "**最优比 R = 0.01;mixed two-stage α₁=0.05、α₂=0.20;Gemini 2.0 Flash, T=0.3;40 部中文小说**",并建议"把 α₁=0.05/α₂=0.20 当默认值直接编码"。**本批一手验真只能确认 abstract 层面的"存在最优压缩-扩展比"这一定性结论,无法确认上述任何具体数值/模型/语料**。→ 这些数字**降级为"未核实,疑似 v1 过度具体化或读自未经二次确认的 HTML 片段"**,**严禁当默认配置直接编码**,落地前必须核 PDF 正文与实验设置。这是本方向**最高优先级的待补**(见 Open Q1)。
  - **时效性 / 鲁棒性 / 可行性**:时效性 = 当前;鲁棒性 = 实证研究但**单配置、无确认代码**;可行性 = 作为"分几层 / 每层放大多少"的**定量设计依据**有价值,但参数需自测,不可照抄。
- **Ex3**(arXiv:2408.08506,2024-08,中科院计算所/寒武纪,Lei Huang 等):反向工程 —— 从原始小说自底向上 Extract 层级结构 → 构造 instruction 数据 **SFT** → tree-like expansion 生成任意长。**需要微调**(区别于上面所有 prompt-only 方案)。真实 repo = `Taskii-Lei/Ex3-NovelWriter`(**20★,stale 2024-09**,PyTorch,research-only)。
  - https://arxiv.org/abs/2408.08506 · https://github.com/Taskii-Lei/Ex3-NovelWriter [accessed:2026-05-30]
  - **时效性 / 鲁棒性 / 可行性**:时效性 = 偏旧且 stale;鲁棒性 = prototype,需训练;可行性 = **rewrite + 训练成本**。理念(从真实网文反推层级结构)可借鉴,代码不建议直接用。

---

## 4. 中文网文 narrative functions + 逐卷结构(S 档 —— 本系统命门)

### 4.1 ⭐ 学术:Propp 叙事功能的中文网文扩展(已交叉验真,重要)
*"Creative Convergence or Imitation? Genre-Specific Homogeneity in LLM-Generated Chinese Literature"*,arXiv:2603.14430,提交 **2026-03-15**,作者 Yuanchi Ma, Kaize Shi, Hui He, Zhihua Zhang, Zhongxiang Lei, Ziliang Qiu, Renfen Hu, Jiamou Liu。
- abstract:https://arxiv.org/abs/2603.14430 [accessed:2026-05-30]
- HTML:https://arxiv.org/html/2603.14430v1 [accessed:2026-05-30]
- **验真说明**:论文 ID 因"未来日期"格式一度报错,但 arXiv abstract/HTML 与作者列表均可取到,**论文真实**(本批 exists=true,high)。
- **34 个中文网文叙事功能**:在 Propp 31 功能基础上扩展,新增/适配 **金手指 Golden Finger、打脸 Face-Slapping、变身 Transfiguration、Get promoted(升级)、Emotion、Memory Loss、Beyond** 等,覆盖仙侠/玄幻/都市等网文结构。
- **语料**:**100 部中文网文,5 大类(玄幻 / 仙侠 / 言情 / 穿越 / 都市),约 1.0k 专家标注片段**,标注团队含网文作者+类型评论家+文学教授+研究生,inter-annotator 一致性高。
- **核心发现(对重做是强警示)**:LLM 识别叙事功能准确率仅 **~36%**,常见功能远好于罕见功能;归纳出 6 大高频情节模式(Battle / Emotional / Difficult task / Adventure / Pretending / Daily life);**LLM 机械复刻高频模板、缺乏对"角色驱动抽象"的理解 → 同质化("AI 味")**。
- **时效性 / 鲁棒性 / 可行性**:时效性 = 最新(2026-03);鲁棒性 = 学术语料 + 专家标注,但 100 部样本;可行性 = **可借鉴**——把"34 功能"做成**可计算的叙事功能标签体系**,在大纲/章纲阶段强制覆盖罕见功能、打散高频模板,直接对抗"AI 味同质化"。这是中文网文专属、有学术背书的差异化武器。
- **⚠️ 幻觉剔除**:v2 调研里给出的匿名数据集链接 `https://anonymous.4open.science/r/acl26-ED4E/` 经一手访问返回 **403 / 无任何公开索引**,**判定为不存在,已从本稿剔除**。功能定义需改从论文 PDF 正文获取(见 Open Q2)。

**邻近真实工作(旁证,B 档)**:
- *GenWebNovel: A Genre-oriented Corpus of Entities in Chinese Web Novels*(COLING 2025):https://aclanthology.org/2025.coling-main.259.pdf · 代码 https://github.com/hjzhao73/GenWebNovel [accessed:2026-05-30](已核)
- *A Corpus for NER in Chinese Novels with Multi-genres*(arXiv:2311.15509,260 部网文 / 13 类 / 26 万实体):https://arxiv.org/abs/2311.15509 · https://github.com/hjzhao73/MultiGenre-ChineseNovel [accessed:2026-05-30](已核)
- Propp 原典 31 功能:https://en.wikipedia.org/wiki/Vladimir_Propp [accessed:2026-05-30]
- Finlayson *Inferring Propp's Functions*(计算化经典,J. American Folklore 2016):https://www.semanticscholar.org/paper/27c32a97b4cb442433579dcf18e40db6731514a4 [accessed:2026-05-30](已核)

### 4.2 ⭐ 评测:WebNovelBench(中文网文专用,可直接对标)
arXiv:2505.14818(2025-05),**Findings of EACL 2026**。作者 Liangtao(Leon) Lin, Jun Zheng, Haidong Wang。
- abstract:https://arxiv.org/abs/2505.14818 · HTML:https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]
- ACL Anthology:https://aclanthology.org/2026.findings-eacl.94/ [accessed:2026-05-30]
- 代码:https://github.com/OedonLestrange42/webnovelbench(MIT,Python)· 数据:https://huggingface.co/datasets/Oedon42/webnovelbench [accessed:2026-05-30](均已核)
- **4000+ 部中文网文**;任务 = **synopsis→story**;每部抽 **10 段连续章节**做多实例评测。
- **8 个叙事质量维度 + PCA 权重(逐字核实,基础事实核查锚定)**:

  | # | 维度(英文逐字) | PCA 权重(来自 v1 HTML 抽取,**待 PDF 二次确认**) |
  |---|---|---|
  | 1 | Use of Literary Devices | 0.1304 |
  | 2 | Richness of Sensory Detail | 0.1160 |
  | 3 | Balance of Character Presence | 0.1152 |
  | 4 | Distinctiveness of Character Dialogue | 0.1171 |
  | 5 | Consistency of Characterisation | 0.1377 |
  | 6 | Atmospheric and Thematic Alignment | 0.1290 |
  | 7 | Contextual Appropriateness | 0.1281 |
  | 8 | Scene-to-Scene Coherence | 0.1263 |

  > 8 个**维度名**经独立基础事实核查逐字确认(arXiv:2505.14818 Table 1);**权重数值**沿用 v1 HTML 抽取、标注为待 PDF 二次确认(不影响维度本身的采用)。
- LLM-as-Judge → PCA 聚合 → 映射到"相对人类作品百分位";评了 24 个 SOTA LLM,**Qwen3-235B-A22B 最高(norm score 5.21)**,其后 DeepSeek-R1 / Gemini-2.5-Pro / GPT-4o / DeepSeek-V3。
- **时效性 / 鲁棒性 / 可行性**:时效性 = 当前(EACL 2026 Findings);鲁棒性 = 大规模、方法论完整、代码+数据齐全;可行性 = **重做的自动评测层可直接照搬**(synopsis→story + 8 维 LLM-as-Judge + 百分位锚定),中文原生。注:它是**单篇 synopsis→story,非多卷**,且 8 维偏文学质量、缺"爽点/追读"商业指标(见 Open Q5)。

### 4.3 ⭐ 实践:可直接抄的中文网文"三层大纲 + 逐卷"范式
`worldwonderer/oh-story-claudecode`(Claude Code skill 包)。**1.7k★,MIT,last push 2026-05-30(极活跃)**。
- https://github.com/worldwonderer/oh-story-claudecode [accessed:2026-05-30](已核;描述 = "网文/小说写作 skill 包,覆盖长篇与短篇网络小说的扫榜、拆文、写作、去AI味、封面图全流程")
- **核心理念**:"套路 = 确定性的情绪满足";三步法 **扫榜(榜单洞察题材/人设/切入点)→ 拆文(拆大纲节奏 + 建模块库)→ 商业化写作(钩子/爽感/期待感)**。
- **分层大纲(直接对应逐卷展开)**:**全书 → 卷纲 → 细纲 → 章节**;卷纲含"爽点节奏 + 情绪弧线 + 人物弧线 + 伏笔 + 反转",章纲/细纲含"事件 + 钩子 + 爽点 + 悬念";覆盖**黄金三章、爽点、升级流**。
- **agent 分工(对本系统多 agent 设计有参考)**:Opus = 架构、Sonnet = 人物/叙事/研究、Haiku = 一致性/抽取;独立目录分管 settings / 大纲 / 正文 / 连续性追踪(防情节漏洞)。
- **时效性 / 鲁棒性 / 可行性**:时效性 = 最活跃(几乎每日更新);鲁棒性 = 社区实践、非学术,但 1.7k★ 验证关注度;可行性 = **与本系统同场景(中文网文)、最值得借鉴工程结构的实践参考**。⚠️ 注:具体 reference `.md` 文件名(如 outline-architecture.md)经核对 **404**,目录以 `skills/` 下 agents + references 组织,**文件名不要照抄**,以 README + 仓库树为准。

### 4.4 其它中文实践 + 升级流学术
- `cjyyx/AI_Gen_Novel`(多 agent 探 AI 写小说边界):**419★,MIT,stale(2024-09)**。README 自述"目前 LLM 还没有足够能力创作长篇网文";技术 = 记忆压缩(长文→几句话)+ RecurrentGPT 式迭代。→ 仅作社区关注度参考,不建议作代码基座。
  - https://github.com/cjyyx/AI_Gen_Novel [accessed:2026-05-30](已核)
- **升级流学术**:傅善超《媒介、结构与情结——论"升级流"网络小说的游戏性》,《中国文艺评论》2018(6)。核心:升级流 = 数值化等级体系 + 单向不可逆 + 预设固定升级路线 + 游戏式"击杀→奖励→经验→升级"循环。→ 给"升级流题材"的大纲机制(升级循环作为章节节拍器)提供理论刻画。
  - http://www.zgwypl.com/content/details81_48995.html [accessed:2026-05-30](中文期刊,二手,标 [partial-source])

---

## 5. 通用系统 / 工具(C 档,点到为止)
- **Dramatron**(DeepMind,arXiv:2209.14958,CHI 2023):**层级 prompt chaining** 奠基系统 —— log line→title→characters→plot beats→locations→dialogue 自顶向下保长程一致(Chinchilla-70B)。**~1.1k★,Apache-2.0**。架构理念参考,不建议直接依赖。
  - https://arxiv.org/abs/2209.14958 · https://github.com/google-deepmind/dramatron [accessed:2026-05-30]
- **Novelcrafter**(商业):**Codex**(自动检测正文实体并在 prompt 时注入,≈Story Bible)+ **Planning Mode**(acts→chapters→scenes 拖拽)+ BYOK(OpenRouter / 本地 Ollama)。→ 产品级的"大纲数据模型 + codex 自动注入"值得借鉴交互;非开源,二手来源,标 [partial-source]。
  - https://www.novelcrafter.com/ [accessed:2026-05-30]
- **活资源索引**:`yingpengma/Awesome-Story-Generation`(LLM 时代故事生成论文总目录,持续更新)—— 建议作为常驻追踪入口。另有 *A Survey on LLMs for Story Generation*(EMNLP 2025 Findings,taxonomy 明确把 outline-based 列为一类)。
  - https://github.com/yingpengma/Awesome-Story-Generation · https://aclanthology.org/2025.findings-emnlp.750.pdf [accessed:2026-05-30]

> **C 档保留但降权的 v1 条目**:Plan-and-Write(1811.05701)、PlotMachines(2004.14967)、LongStory(2311.15208)、Agents' Room(2410.02603)、StoryWriter(2506.16445)、DSR(2510.23163)、EIPE-text(2310.08185)、Self-Refine(2303.17651)、STORYTELLER(2506.02347)、Lost in Stories(2603.05890)等在 v1 中均出现。本批验真**未对这批 v1 条目逐一重新取一手 source**,故本稿仅作**理念引用、不再背书为已核实**;其中与本方向最相关的两条留待后续单独验真:STORYTELLER(SVO 三元组 plot node,可填在 outline beat 与记忆三元组之间)、Lost in Stories(19 子类一致性失败 taxonomy + "错误在 40–60% 段聚集"),若验真通过应升档纳入 §1/§6。

---

## 6. 综合判断 + Top 候选(给重做团队的可执行结论)

**主架构:以 DOME 的"双层动态大纲 + 时序四元组记忆"为骨,叠加四处增量,中文网文专门化。**

### Top 候选 1 —— DOME 双层动态大纲 + TKG 四元组记忆 +(可插拔)结构模板
- **来源**:§0 DOME(2412.13575)+ §2 结构框架。
- **理由**:四元组 `<subject, action, object, chapter_index>` 与本系统 `knowledge_triples` 近 1:1;rough/detailed 双层契合"卷纲→章纲";理论层用英雄之旅/五段式(玄幻/修仙天然适配)。
- **时效性**:NAACL 2025,当前。**鲁棒性**:7k 词验证、M=3 偏刚性 → 需把 M 改为按卷/题材自适应。**可行性**:high,prompt + 状态机 + KG,无需训练。

### Top 候选 2 —— 受控逐层扩展(LongWriter 字数预算 + Expansion-Ratio 定量分层)
- **来源**:§3 LongWriter/AgentWrite(2408.07055,production)+ Expansion-Ratio(2505.12572,定性)。
- **理由**:**禁止从短梗概一步扩全文**;采用 synopsis→卷纲→章纲→(带字数预算的)段落 plan,逐段填充用 AgentWrite(已工业验证、低成本)。
- **时效性**:当前且活跃。**鲁棒性**:LongWriter = production;Expansion-Ratio 仅定性可信。**可行性**:LongWriter low(prompt)/medium(SFT 模型);层数与放大比**需自测**,不可照抄具体数值。

### Top 候选 3 —— 动态防平淡 + 抗同质化双武器(中文网文差异化)
- **来源**:§1.1 大纲相似度阈值反转(2508.03137)+ §4.1 Propp-34 叙事功能标签(2603.14430)。
- **理由**:相邻版本大纲做 embedding 相似度,过阈值判"原地打转"→ 触发 KG 驱动障碍/反转;同时用 34 功能做覆盖检查,强制引入罕见功能、打散 6 大高频模板。两者都低成本、有学术背书、直接对抗"AI 味"。
- **时效性**:2025-08 / 2026-03,最新。**鲁棒性**:均 prototype、英文或样本有限。**可行性**:相似度阈值实现成本极低(优先);34 功能需先从 PDF 取全定义再做标签。

### 缝合接口(把 S 档 R1/R2/R5 串起来)
- **记忆/伏笔接口**:`<subject, action, object, chapter_index>` 时序四元组(DOME 原样)+ 伏笔追踪表 `{伏笔, 埋设章节, 回收章节, 状态}`。R1 大纲埋伏笔时写入,R2/R3 按 chapter_index 回收 + 一致性校验。
- **评测**:WebNovelBench 方法论(§4.2)——synopsis→story + 8 维 LLM-as-Judge + 百分位锚定,中文原生,可直接搭。

### 模型选型建议(应用基础事实核查 · 2026-05)
> 本节据"2026 中文 LLM 创意写作实测对比"基础事实核查写入,供 R1 大纲/正文生成的 agent 绑定参考(数据为 2026-03~05 第三方评测,标 [partial-source])。
- **中文文笔 / 创意写作首选:Kimi K2.6**——创意写作 + 挑战性角色扮演双榜第一,长篇风格连贯、情感共鸣强;并具最长上下文(~2M tokens),适合超长连载与"全书一次性 rough outline + 长 context 回看"。
- **性价比基座:DeepSeek V4**——极致性价比、中文知识/推理强,文笔可接受;1M 上下文。适合大批量章纲扩写、消融实验。
- **开源本地化:Qwen3.x(Apache-2.0)**——中文综合均衡、可私有化部署;创意写作非专项强项但工程可控。
- **GLM-5.x**——编程强、上下文偏短(~128K),创意写作非强项;适合做一致性/抽取类辅助 agent。
- → 与 oh-story 的多模型分工(架构 / 叙事 / 一致性 分配不同档位模型)思路一致:**写作 agent 用 Kimi、批量扩写用 DeepSeek、抽取/一致性用更便宜模型**。

**成熟度/成本速览**:可直接复用代码 = LongWriter/AgentWrite(production,Apache-2.0)、snowmeth(MIT,小)、oh-story-claudecode 实践文档(MIT,活跃)、WebNovelBench(评测,MIT,开源)。论文级需自实现/训练 = DOME / KG+理论 / Expansion-Ratio / Ex3(**high ~ rewrite**),理念价值最高。

---

## 7. Open Questions(需进一步求证/决策)
1. **【最高优先级】Expansion-Ratio 的具体最优倍数**:2505.12572 abstract 仅给"存在最优比"的定性结论;**v1 写的 R=0.01 / α₁=0.05 / α₂=0.20 / Gemini2.0Flash / 40 部中文小说 等具体数值本批无法核实,严禁当默认配置**。落地"分几层、每层放大多少"前必须核 PDF 正文。
2. **Propp-34 完整功能定义表**:已拿到 34 功能名 + 语料规模,但匿名数据集链接(4open.science)**已失效/剔除**;每个功能的精确定义/触发条件需从 **PDF 正文**取全,才能做成可计算标签。
3. **rough outline 一次定全书 vs 逐卷再生成**:DOME 的 rough 是全书一次性;百万字网文更可能"写完一卷再据反馈定下一卷卷纲"。需决定 rough 层是否也"逐卷动态",影响整个 graph 设计。
4. **DOME 约 200 次 API/篇 的开销在百万字逐卷如何摊薄**:是否用 LongWriter 式 SFT 把多层 prompt 压成更少调用?需成本建模。
5. **WebNovelBench 8 维是否够覆盖网文"爽点/追读"**:其维度偏文学质量,缺"爽感/钩子/期待感"等商业指标,需结合 oh-story 的爽点节奏概念**自扩展评测维度**。
6. **多卷一致性无学术 benchmark**(v1 已指出):最佳证据仍是社区项目的百万字规模;可能需自建 benchmark。
7. **DOME 的 M=3 固定章节比例**:是否做按卷/题材自适应版本?(网文序章卷 vs 中段卷比例不同,无现成论文。)
8. **STORYTELLER SVO plot node / Lost in Stories 错误 taxonomy 待验真升档**:两者(§5 备注)若一手验真通过,应分别纳入"outline 原子事件表示"与"中段 40–60% 重点校验"设计。
9. **二手来源待补一手 fetch**:Novelcrafter / Dramatron-Chinese / 升级流期刊文。

---

## v1 ↔ v2 diff

### 新增(v1 没有、v2 补入)
- **§1.1 KG + 文学理论(2508.03137)**:v1 完全缺失。带来本方向最值得抄的工程信号 ——"**大纲相似度阈值触发反转**"+ Forster story/plot 区分 + KG 驱动障碍节点。
- **§3 LongWriter / AgentWrite(2408.07055)显式纳入并升为"长输出工程地基"**:v1 仅在 §6 DSPy 段顺带提 SnowMeth,未把 AgentWrite"字数预算 plan + 逐段填充"作为一级方案。production / Apache-2.0 / ~1.9k★。
- **§4.1 Propp-34 中文叙事功能(2603.14430)升格为"抗同质化武器"**:v1 §9/§10 已提该论文与 36% 识别率,但 v2 进一步把"34 功能做成可计算标签、强制覆盖罕见功能、打散 6 大高频模板"提炼为可落地动作,并补全作者列表与交叉验真说明。
- **§4.3 oh-story-claudecode 三层大纲范式**:v1 §8 把它当 OSS 之一列出(1.6k★);v2 升为"与本系统同场景、最活跃的实践参考",细化"全书→卷纲→细纲→章节"+ 多 agent 分档。
- **§6 模型选型建议**:v1 无。应用 2026-05 中文 LLM 创意写作基础事实核查 —— 写作首选 Kimi K2.6、性价比 DeepSeek V4、开源 Qwen、辅助 GLM,并与 oh-story 多模型分工对齐。
- **§0 验真澄清块 + 全文 [accessed:2026-05-30]**:v1 为 2026-04-28 调研;v2 统一刷新访问日并加入一手 GitHub API 的 star/license/活跃度。

### 纠正(v1 有错或过度具体,v2 改正)
- **⚠️ Expansion-Ratio 数值(最重要)**:v1 §1 与 Open-Q2 给出 **R=0.01 / α₁=0.05 / α₂=0.20 / Gemini2.0Flash, T=0.3 / 40 部中文小说**,并建议"直接编码为默认值"。v2 据一手验真**降级为不可核实**,明确**禁止当默认配置**,只保留"存在最优压缩-扩展比"这一定性结论。
- **DOME 叙事理论框架**:v1 表述为"5 stages aligned with Joseph Campbell's hero-journey acts"(基本对),v2 进一步澄清主框架 = **英雄之旅 + Freytag/Vogler + 五段式**,复刻时勿当作单纯"五幕/五段"。
- **DOME ACL 页码 / DOC v2 仓库 / WebNovelBench 权重数值**:v1 将 "pp.1352–1391""facebookresearch/doc-storygen-v2""8 维 PCA 权重"当确定事实陈述;v2 把这三项**降级为"待二次确认"**(DOME 论文本身、DOC v1 仓库、WebNovelBench 8 个维度名 均已确认为真,不受影响)。
- **WebNovelBench 作者名**:v1 写 "Leon Lin (NTU)";v2 据 ACL Anthology 收录页校准为 **Liangtao Lin / Jun Zheng / Haidong Wang**(Leon = Liangtao 的英文名,EACL 2026 Findings)。

### 删除(幻觉 / 不存在,已剔除)
- **`https://anonymous.4open.science/r/acl26-ED4E/`**(Propp-34 论文的匿名数据集链接)—— 一手访问 **403 + 全网无索引**,判定不存在,删除。功能定义改从 PDF 取。
- **`https://aclanthology.org/2025.naacl-long.63/` 的"DOME"命名匹配**被本批标 exists=false —— 经复核为**误报**(页面真实、就是该论文),故 **URL 与论文予以保留**,但**剔除"标题字面为 DOME"与未经确认的"pp.1352–1391"精确页码**这两处不实细节。
- **"PerRoleCognition"**(本方向材料/串扰中可能出现的角色认知技术名)—— 独立核查为**杜撰**(arXiv/Scholar/全网无),本稿不予采用;真实近邻为 RPNA(2510.24677)、RoleRAG(2505.18541)、Character-LLM(2310.10158),与 R1 无直接关系,仅记此防串扰。

> 注:v1 中大量"未经本批一手重验"的 C 档条目(Plan-and-Write、PlotMachines、LongStory、Agents' Room、StoryWriter、DSR、Self-Refine、STORYTELLER、Lost in Stories、各 OSS 仓库的具体 star/版本号等)**未被判定为幻觉**,只是**未在 v2 重新背书**;它们降为"理念引用",见 §5 末与 Open-Q8。这区别于上面三条"确证不存在/杜撰"的真删除。

---

(R1 终稿 v2 完。与 R2 记忆、R5 角色、R3 图谱的缝合在 `00-summary.md`。)
