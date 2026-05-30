# R9 · 中文网文专属 深度调研(v2 终稿)

> 调研日期 [accessed:2026-05-30]。本方向 = 优先级 **B 档**(用户锚点:记忆 R2 = 角色 R5 = 大纲 R1 > 图谱 R3;S 档最深,B/C 档点到为止)。
> 本稿在 clean-room 调研稿基础上,经独立引用验真(逐 URL fetch + 全网交叉搜索)与三项基础事实核查后定稿:**剔除 4 处幻觉/不实链接、纠正 1 处选型证据链(EVY 聚合分数)、补入 RPNA/RoleRAG/Character-LLM 角色认知交叉指针**。所有"存活"结论均可经真实页面复核;被剔除项见文末 `## v1 ↔ v2 diff`。
> R9 的定位:**它不是要造新算法,而是给已有的 6-agent 流水线做"选型 + 评测 + 题材模板"三件事**——产出主要喂给 Planner(大纲层 R1)与 Writer/Consistency(质量层),不喧宾夺主、不引入重构级改造。

---

## 一、可借鉴清单(逐项 + 三维评判:时效性 / 鲁棒性 / 可行性)

### 1. WebNovelBench(网文专属生成评测基准)★ 本方向最高优先级,证据已坐实

- **是什么**:面向"长篇网文生成"的评测基准,把任务框成 **synopsis→story(梗概到正文)**。底层数据集 = **4000+ 部中文网文**(从 10000+ 部 2013–2020 出版网文中,经去重 [相似度>0.9 剔除]、章节解析 [≥10 章 regex]、剔除尾部作者干扰筛得)。题材覆盖:东方玄幻 1281 / 现实 1255 / 西方奇幻 670 / 历史 234 / 科幻 / 悬疑 / 言情。用 **Doubao-pro-32k** 为每部连续 10 章生成梗概(主角/关键情节/重要场景),共约 40000 对梗概-正文,测试集 1000 条(取自 100 部代表作)。
  - 来源(均验真为真):
    - arXiv 摘要 https://arxiv.org/abs/2505.14818 [accessed:2026-05-30]
    - arXiv HTML 全文 https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]
    - ACL Anthology(Findings of EACL 2026,pp.1828–1847)https://aclanthology.org/2026.findings-eacl.94/ [accessed:2026-05-30]
  - 作者署名小注:arXiv 作 "Leon Lin",ACL Anthology 作 "Liangtao Lin"(同一人,NTU;另有 Jun Zheng、Haidong Wang,中山大学)——引用以 ACL Anthology 正式版为准。

- **8 个叙事质量维度(LLM-as-Judge,PCA 加权)** —— 经基础事实核查逐字核对 Table 1,可直接做我们 Consistency/质量 agent 的评分骨架:
  1. 文学手法运用 Use of Literary Devices(w=0.1304)
  2. 感官细节丰富度 Richness of Sensory Detail(0.1160)
  3. 角色出场平衡 Balance of Character Presence(0.1152)
  4. 对话辨识度 Distinctiveness of Character Dialogue(0.1171)
  5. **人设一致性 Consistency of Characterisation(0.1377 — 权重最高)**
  6. 氛围与主题契合 Atmospheric and Thematic Alignment(0.1290)
  7. 情境合理性 Contextual Appropriateness(0.1281)
  8. 场景间连贯 Scene-to-Scene Coherence(0.1263)
  来源:https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30](维度名 + 权重经独立核查确认逐字一致)

- **关键发现**:能有效区分"人类名著 / 流行网文 / LLM 生成"三档;24 个 SOTA 模型横评中,**Qwen3-235B-A22B 最高(归一化 5.21)**,DeepSeek-R1、Gemini-2.5-Pro 同属第一梯队;GPT-4o、DeepSeek-V3 居中;GLM-4-9B-chat、LLaMA-3-8B 偏低(结果呈现为 Figure 3 热力图,非完整数值表)。来源:https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]

- **代码/数据**(均验真为真):
  - repo https://github.com/OedonLestrange42/webnovelbench(**MIT**,star 15;验真描述为 "Official PyTorch implementation for the paper")[accessed:2026-05-30]
  - 数据集 https://huggingface.co/datasets/Oedon42/webnovelbench(标题 "Web Novel and Famous Novel Benchmark Dataset";含 raw novel data + chapter-level component extractions + scoring results;**license = CC-BY-NC-SA-4.0**)[accessed:2026-05-30]
  - **坑**:打分管线强耦合**火山方舟 Volcengine Ark batch inference**(`python novel_gands_pipeline.py --config config.json`),需自改解耦;且数据集 **CC-BY-NC-SA-4.0 = 非商用**,落地前注意许可。

- **三维评判**:
  - 时效性 = **新鲜**(2025-05 发布,EACL 2026 Findings 已录用)。
  - 鲁棒性 = **prototype**(star 15;打分耦合火山 API;LLM-judge 量表稳定性未充分披露)。
  - 可行性 = **low–medium**——"借范式不借代码":8 维量表 + synopsis→story 范式与我们"分场景生成 + Consistency 校验"链路天然对齐,可作内部自动评测蓝本;中文就绪度满分。**这是 R9 里最该抄的东西。**

### 2. Creative Convergence:34 个中文网文 narrative functions ★ 大纲/情节理论支撑

- **是什么**:把 Propp 的 31 个叙事功能**扩展/改写为 34 个**适配现代中文网文(其中约 15 个为新增或改写),用于诊断 LLM 生成的"同质化/套路化"根因。
  - 来源(论文本体验真为真):
    - arXiv 摘要 https://arxiv.org/abs/2603.14430 [accessed:2026-05-30]
    - arXiv HTML 全文 https://arxiv.org/html/2603.14430v1 [accessed:2026-05-30]
  - 题目 "Creative Convergence or Imitation? Genre-Specific Homogeneity in LLM-Generated Chinese Literature";核心贡献即 "a taxonomy of 34 narrative functions customized for contemporary online literature";作者 Yuanchi Ma 等 8 人;2026-03-15 提交。

- **34 功能(本次抓到约 20 个符号)**:核心单元 = 初始情境(A)、禁止(B)、加害(H)、离开(L)、斗争(Q)、胜负(S)、归来(U);**网文专属新增** = **金手指/晋级(O)、打脸/揭穿(De)、易容(Fa)、失忆(Lo)、设定(Fr)、变身(Ch)、情感(Em)**。这套"打脸/金手指/失忆/晋级"符号化功能可直接做 Planner(章节 beat 规划)的**功能标签词表**。来源:https://arxiv.org/html/2603.14430v1 [accessed:2026-05-30]

- **关键发现**(对"反套路"极有用):
  - 6 大套路范式 = **战斗 / 情感 / 任务 / 冒险 / 扮猪吃虎 / 日常**;LLM 续写机械重复 "A-Lo-E-Q-P-S" 这类序列(≥60% 频率即判定套路)。
  - 模型**根本读不懂叙事功能语义**:Qwen3-32b / Doubao 最高也只有 **accuracy 0.364**;常见功能识别率约 60%,冷门功能 ≤33.3%;论文结论"没有任何 baseline 能准确理解该功能框架"。
  - 同质化根因是"**理解缺陷**而非语言能力限制"——人类作者用的功能种类明显更广;用 BERT-score 度量内容同质化。评测覆盖:GPT-4o/4o-mini、Qwen3(8b/32b)、Doubao-pro、DeepSeek-V3/R1、轩辕(Xuanyuan)、千帆(Qianfan)、Kimi-v1。来源:https://arxiv.org/html/2603.14430v1 [accessed:2026-05-30]
  - **语料**:1.0k 条人工标注,取自 100 部代表网文,5 题材 = 奇幻/仙侠/言情/穿越/都市;两位专家(职业网文作者 + 类型评论者)段落级标功能符号,inter-annotator κ≈0.83;140 个种子用 DeepSeek-R1 扩写后专家复核。
  - **数据可得性已变更(重要)**:clean-room 稿曾引用匿名数据 repo `anonymous.4open.science/r/acl26-ED4E/` —— **该链接经验真为不可确认(HTTP 403 + 全网无证据该 ID 下存在本项目),已从本稿剔除**。即:论文与 34 功能框架可信,但**配套数据/代码目前没有可复核的公开入口**;若要落地为可训练约束,需向作者索取或等正式 repo。

- **三维评判**:
  - 时效性 = **最新**(2026-03-15)。
  - 鲁棒性 = **theoretical/prototype**(理论框架 + 1k 标注;**配套数据 repo 链接失效/不可确认**,无 star)。
  - 可行性 = **medium**(把 34 功能落成 Planner 的 beat 模板 + "功能多样性/功能熵"反同质化指标需工程化,概念中文原生,但**不能依赖其匿名数据集**)。
  - **借鉴点**:① 给 Planner 一套网文功能词表;② 把"功能序列多样性"做成大纲层反套路约束;③ **核心警示——别指望模型自发理解金手指/打脸/失忆,必须在 prompt/结构里显式编码功能序列**(这点与 §1 人设一致性权重最高、§3 妙笔单列"打斗描写"互相印证)。

### 3. 阅文妙笔(网文行业大模型 + 作家助手)— 产品形态参照,验真为真

- **是什么**:**国内首个网文行业大模型**,2023-07-19 阅文创作大会发布,基于"二十余年网文创作经验与表达方式"训练,强调更懂网文语言/"梗"/读者互动(对《庆余年》《全职高手》等问答比通用模型更准)。
  - 来源:甲子光年 https://www.jazzyear.com/article_info.html?id=1052(验真标题"阅文发布首个网文行业大模型阅文妙笔…")[accessed:2026-05-30];极客公园 https://www.geekpark.net/news/322057(验真标题"大模型时代,网络文学正在经历「大变革」")[accessed:2026-05-30]
- **作家助手·妙笔版四大功能** = **世界观设定 / 角色设定 / 情景描写 / 打斗描写**(注意:"打斗描写"被单列为一等公民,印证网文对战斗场景的高频刚需,呼应 §2 的"战斗范式")。后续接入 **DeepSeek-R1**,升级智能问答 / 获取灵感 / 描写润色三方面;"智能问答、描写、提取、画师"四功能高频调用。
  - DeepSeek 接入来源:北京日报 https://news.bjd.com.cn/2025/02/05/11057592.shtml(验真:2025-02-05,"阅文率先部署DeepSeek…智能问答、获取灵感、描写润色三大功能升级")[accessed:2026-05-30]
- **产品方向**:不止文本,延伸到**文生图 / IP 构建**(content+platform 生态)。来源:https://www.jazzyear.com/article_info.html?id=1052 [accessed:2026-05-30]
- **三维评判**:时效性 = **活跃**(2023 发布 + 2025-02 接 DeepSeek);鲁棒性 = **production**(商用、调用量大);可行性对我们 = **参照不可复用**(闭源、阅文自有语料)。**借鉴点**:其功能切分(世界观/角色/情景/打斗/提取/润色)几乎就是我们 agent 边界的"市场验证版"——"描写润色""打斗描写""设定提取"可做独立调用能力点;且"先接 DeepSeek-R1 做底座、自家做行业层"的路线,直接为我们**不自训基座、只做网文领域编排层**的策略背书。

### 4. 中文 LLM 文笔/选型(给 Writer agent 选基座)★ 已据基础事实核查重建证据链

> 说明:clean-room 稿原引用的 **EVY 聚合榜中文模型分数**(Kimi K2.6 1807.7 等一串数值)经验真**不成立**——该页面存在,但**并未以"中文模型分数"作为榜单组成项呈现**,所引数值无法复核,**整段已剔除**。同时 **Andrew Mayne "Kimi K2 最强开源创意写作" 博文(2025-07-14)经验真为 HTTP 404,亦已剔除**。下文选型结论改以"可复核的 benchmark + 基础事实核查"重建。

- **创意写作评测方法论(可借来做内部自动评测,均验真为真)**:
  - **EQ-Bench Creative Writing v3**:32 prompt × 3 iter,rubric + 成对 Elo 混合打分;含 Slop / Repetition 等维度。来源:https://eqbench.com/creative_writing.html [accessed:2026-05-30];repo https://github.com/EQ-bench/creative-writing-bench(作者 Samuel J Paech)[accessed:2026-05-30]
  - **EQ-Bench Longform Creative Writing**:从极简 prompt 做规划 → 写多章长文;独有指标 = **Slop(套话,越低越好)/ Repetition(n-gram)/ Degradation(后段质量衰减)**;最新 v1.11(2026-02)用 **Claude Sonnet 4.6** 作 judge。来源:https://eqbench.com/creative_writing_longform.html [accessed:2026-05-30];repo https://github.com/EQ-bench/longform-writing-bench(MIT,作者 S.J. Paech)[accessed:2026-05-30]
  - **这三个指标(slop / repetition / degradation)正是长篇网文最痛的点,强烈建议纳入我们章节质量门禁**(补强现有 `consistency_check` 只查一致性、不查文笔退化的缺口)。

- **可复核的中文模型创意写作硬数据**:
  - **WebNovelBench(网文专属,最硬)**:Qwen3-235B > DeepSeek-R1 > Gemini-2.5-Pro。来源:https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]
  - **EQ-Bench Creative Writing v3(llm-stats 快照,2026)**:**Qwen3-235B-A22B-Instruct-2507 排第 3(score 0.875)**,Qwen3 系列占据 #4–#9 多席、Qwen3-4B 在 #13。来源:https://llm-stats.com/benchmarks/creative-writing-v3(验真:32 prompt×3 iter、rubric+Elo;Qwen3 名次确认)[accessed:2026-05-30]
  - **基础事实核查(2026 中文文笔实测综合,多源)**:**Kimi K2.6 在中文创意写作 + 挑战性角色扮演双榜第一,实测超 GPT-5**;K2 Thinking 能驾驭微妙文风、长篇保持风格连贯、情感共鸣强、意象生动。**DeepSeek V4-Pro** 中文知识/超长上下文(1M)强、但**缺专项文笔评测数据**;**Qwen 3.6-Plus** 完全开源(Apache-2.0)、C-Eval 93%、性价比最高,综合均衡但创意写作非强项;**GLM-5.1** 编程强、创意写作有能力非强项。来源(基础事实核查转引):知乎 Kimi K2 讨论 https://www.zhihu.com/question/2029714522651272097、苏米客横评 https://www.xmsumi.com/detail/2984、DataLearner DeepSeek-V4-Pro 卡 https://www.datalearner.com/ai-models/pretrained-models/deepseek-v4-pro、TokenMix 2026 中文模型对比 https://tokenmix.ai/blog/best-chinese-ai-models-2026-comparison-guide [accessed:2026-05-30]
  - **SuperCLUE(中文综合基准,验真为真)**:中文大模型"生成创作"成熟度最高;DeepSeek-R1 发布后中外第一梯队中文差距由 15.05%→7.46%。来源:https://www.superclueai.com/、https://github.com/CLUEbenchmark/SuperCLUE [accessed:2026-05-30]

- **Weaver(波形智能 / AIWaves)— 论文可参考,落地不推荐**:
  - 专做创作的基座模型族(Mini 1.8B / Base 6B / Pro 14B / Ultra 34B),写作语料预训练 + 指令合成/对齐 + routing agent 按复杂度分发;原生 RAG + function calling;自带 WriteBench。
  - 来源(已替换为可访问链接):arXiv 摘要 https://arxiv.org/abs/2401.17268 [accessed:2026-05-30];**ar5iv 镜像全文 https://ar5iv.labs.arxiv.org/html/2401.17268** [accessed:2026-05-30]。**注意:clean-room 稿引的 `arxiv.org/html/2401.17268v1` 经验真为 HTTP 404,已替换为 ar5iv 镜像。**
  - 同组开源的是 Agents 框架仓 https://github.com/aiwaves-cn/agents(Apache-2.0,5.9k star,**last activity 2024-06-25 v2.0**,symbolic-learning agent 框架,**非 Weaver 权重**)[accessed:2026-05-30];**Weaver 权重/代码本身未开源**。
  - 评判:时效性 = **stale**(2024-01-30,>2 年);可行性 = **参考论文方法,不建议作落地基座**。

- **三维评判(选型整体)**:时效性 = 新鲜;鲁棒性 = DeepSeek/Qwen/Kimi/GLM 均 **production**;可行性 = **low**(我们已是 LiteLLM 多 provider,换基座 = 配置级)。
  - **结论倾向(可复核证据 + 基础事实核查双支撑)**:
    - **Writer(文笔)首选 Kimi K2.6**(基础事实核查:中文创意写作双榜第一、超 GPT-5、低 AI 味);**备选 Qwen3 大杯**(WebNovelBench #1 + EQ-Bench v3 #3,双榜可复核)。
    - **结构/一致性/推理类 agent → DeepSeek-R1 / DeepSeek V4-Pro**(推理 + 1M 长上下文,知识性强)。
    - **judge → Claude(Longform 官方即用 Sonnet 4.6)或 DeepSeek**;注意 judge 与被测同源的潜在偏袒(见 Open Q1)。
    - **不自训、不上已 stale 的 Weaver。**

### 5. 网文题材分布(给 Director/题材模板 + 冷启动选型)— 全部权威源验真为真

- **平台格局(2025 艾媒金榜 IP 平台 TOP10,验真)**:阅文 92.83 > 番茄 83.90 > 黑岩 83.38 > 七猫 > 点众 > 中文在线 > 掌阅 > 磨铁 > 咪咕 > 塔读。阅文聚合海量创作者/作品/200+ 品类;番茄 2 亿+ MAU、免费+AI 听书+短剧;黑岩主打男频(玄幻/悬疑/都市/军事)。来源:https://www.iimedia.cn/c1088/106462.html [accessed:2026-05-30]
- **题材结构(2024–2025 权威报告交叉,均验真)**:
  - **三大头部题材 = 古言/现言、都市职场、玄幻奇幻**,优势仍在扩大。来源:CSSN《2024中国网络文学发展研究报告》 https://www.cssn.cn/wx/tbch/202505/t20250513_5873701.shtml [accessed:2026-05-30]
  - **悬疑推理 = 2024 最受欢迎题材**;历史军事关注度上升;**玄幻奇幻热度逐年下降**。来源:国家新闻出版署 https://www.nppa.gov.cn/xxfb/ywdt/202505/t20250512_894767.html、中国作家网《2024年度中国网络文学发展报告》 https://www.chinawriter.com.cn/n1/2025/0718/c404023-40524796.html [accessed:2026-05-30]
  - **科幻同比增速约 +38.5%(全题材第 2)**;2024 新增现实题材约 17 万部、科幻约 18 万部;现实题材为增速第 2 大品类。来源:https://www.cssn.cn/wx/tbch/202505/t20250513_5873701.shtml [accessed:2026-05-30]
  - **番茄读者性别偏好(可做男频/女频默认)**:男性偏好玄幻/都市修真(>50%)、武侠/科幻/游戏/历史;女性偏好古代言情(>60%)、现代言情,其次玄幻。来源:https://www.donews.com/article/detail/6776/80064.html、https://zhuanlan.zhihu.com/p/598875492 [accessed:2026-05-30](注:此两条为第三方/早期面板,精确占比见 Open Q4)
  - **Z 世代套路化倾向**:2024"00 后"偏好作品中"系统流/穿越重生/甜宠无虐"占比 >85%,深度现实题材 <5%;短剧人设(黑莲花/复仇大女主/马甲大佬/忠犬霸总)在番茄 2024 占比约 61%。来源:CSSN《2025中国网络文学发展研究报告》 https://www.cssn.cn/skgz/bwyc/202604/t20260420_5981165.shtml [accessed:2026-05-30]
  - **起点细分演进**:把"诸天流/无限流"从"科幻"独立为「诸天无限」;95 后现实题材阅读占比约 49%、科幻约 62%。来源:https://www.cssn.cn/skgz/bwyc/202604/t20260420_5981165.shtml [accessed:2026-05-30]
  - **出海题材前五 = 都市/西方奇幻/东方奇幻/游戏竞技/科幻**;古言现言连续多年出海冠军。来源:中国作家网 https://www.chinawriter.com.cn/n1/2025/0206/c404027-40413483.html [accessed:2026-05-30]
- **行业规模(验真)**:网文用户 **5.75 亿**(占网民 51.9%);2024 年度新增作品约 200 万部。来源:国家新闻出版署《2024中国网络文学蓝皮书》 https://www.nppa.gov.cn/xxfb/ywdt/202506/t20250619_900890.html [accessed:2026-05-30]
- **三维评判**:时效性 = **新鲜**(2024–2025 数据);鲁棒性 = **production**(行业权威报告/榜单);可行性 = **low**——可直接把"玄幻/仙侠/都市/科幻/历史/现言/古言/穿越重生/系统流/无限流/悬疑" + 男频/女频性别偏好 + 6 大功能范式(战斗/情感/任务/冒险/扮猪吃虎/日常)做成 Director 的**题材/套路预设模板库**,并据热度设冷启动默认。**注意趋势:玄幻下降、悬疑/现实/科幻上升,默认模板别只押玄幻。**

### 6. (新增交叉指针)角色认知相关真实工作 — 对 R5(角色,高优先级)的转介

> 基础事实核查发现:某些综述中流传的 "PerRoleCognition" **系杜撰**(arXiv / Google Scholar / 全网均无)。**本稿不引用、不依赖该名词**。与"角色一致性/角色认知"真正相关、且已验真存在的工作,转介给 R5 深挖:
- **RPNA(RP-Neuron-Activated)**:《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》 https://arxiv.org/abs/2510.24677(2025-10;神经元消融研究"角色提示是否诱发不同认知过程")。
- **RoleRAG**:《Enhancing LLM Role-Playing via Graph Guided Retrieval》 https://arxiv.org/abs/2505.18541(知识图谱引导检索增强角色扮演——与 R3 图谱亦有交叉)。
- **Character-LLM**:可训练的角色扮演 agent,EMNLP 2023 https://arxiv.org/abs/2310.10158。
- **评判**:本块仅作**指针**(R9 = B 档,点到为止);对 R9 自身,§1 的"人设一致性"维度(权重最高)已足够覆盖网文场景的角色一致性评测需求。

---

## 二、综合判断

1. **R9 是"选型 + 评测 + 题材模板"三件事,不造新算法**。价值是给已有 6-agent 流水线**校准方向**,与用户优先级(记忆/角色/大纲 > 图谱)一致——产出主要喂 **Planner(R1)** 和 **Writer/Consistency(质量层)**。
2. **最高 ROI = 把 WebNovelBench 8 维量表 + EQ-Bench 的 slop/repetition/degradation 三指标,合成我们自己的中文章节质量门禁**。正好补强现有 `consistency_check` 只查一致性、不查文笔/退化的缺口;全部中文就绪,adoption cost = low–medium。**许可提醒**:WebNovelBench 数据集为 CC-BY-NC-SA-4.0(非商用),仅可"借量表范式",勿直接商用其数据。
3. **第二 ROI = 用 34 个中文 narrative functions 给 Planner 做"功能标签 + 反同质化约束"**。核心警示直接指导设计:**模型不会自发理解金手指/打脸/失忆,必须在大纲结构里显式编码功能序列**,并用"功能多样性/熵"防套路(对应 6 大套路范式)。**但其配套匿名数据 repo 链接已失效,落地不能依赖该数据集——只采框架。**
4. **基座选型已据可复核证据 + 实测核查重建**:Writer→**Kimi K2.6**(中文创意写作双榜第一、超 GPT-5)或 **Qwen3 大杯**(WebNovelBench + EQ-Bench v3 双榜可复核);Reasoning/结构类→**DeepSeek-R1 / V4-Pro**;judge→Claude/DeepSeek;**不自训、不采用已 stale 的 Weaver**。LiteLLM 架构使切换 = 配置级。**(已删除原 EVY 聚合分数与 Andrew Mayne 实测两处不实证据)**
5. **题材层**:三大头部(古言现言/都市/玄幻)+ 上升赛道(悬疑/科幻/现实/无限流)+ 男女频性别偏好 + 6 范式,做成 Director 预设模板即可,low-cost;注意"玄幻下降、悬疑/现实/科幻上升"趋势。
6. **产品形态对标妙笔**:"打斗描写""描写润色""设定提取"作为可独立调用能力点——已被商用验证的网文刚需切分;妙笔"接 DeepSeek-R1 做底座 + 自做行业层"的路线为我们背书。

---

## 三、Top 候选(按"该不该抄"排序)

| 排名 | 候选 | 用途 | 成熟度 | adoption cost | 中文就绪 | 备注 |
|---|---|---|---|---|---|---|
| 1 | **WebNovelBench 8 维量表 + synopsis→story 范式** | 内部自动评测 / 质量门禁 | prototype(EACL26 录用,star 15) | low–medium(借范式) | 满分 | 数据集 CC-BY-NC-SA(非商用),只借量表 |
| 2 | **Creative Convergence 34 功能 + 6 范式** | Planner 功能词表 / 反同质化约束 | theoretical(2026-03) | medium | 满分 | **只采框架;配套匿名数据 repo 已失效** |
| 3 | **EQ-Bench slop/repetition/degradation 指标** | 长篇退化检测门禁 | production(开源活跃) | low | 需中文适配量表 | repo 均验真 MIT/可访问 |
| 4 | **选型:Kimi K2.6 / Qwen3 大杯(写)+ DeepSeek-R1/V4-Pro(推)** | Writer / 结构 agent 基座 | production | low(配置级) | 满分 | 证据已重建,弃用 EVY/Mayne 两源 |
| 5 | **2024–25 网文题材+性别偏好+平台数据 → Director 模板库** | 题材预设 / 冷启动默认 | production | low | 满分 | 全部权威源验真 |
| — | Weaver | (不推荐落地:已 stale、权重未开源) | **stale**(2024-01) | rewrite | 论文中文 | URL 已换 ar5iv 镜像 |
| — | 阅文妙笔 | (产品对标,闭源不可复用) | production | n/a | 满分 | 功能切分可借鉴 |

---

## 四、Open questions

1. **WebNovelBench 8 维量表的中文 judge 稳定性**:论文用 LLM-as-Judge,但未充分披露 judge 模型与 prompt;复用需自验 judge 一致性——尤其**用 Kimi/DeepSeek 当 judge 是否偏袒同源生成?**(Longform 官方用 Claude Sonnet 4.6 作 judge,可作中立基线参照)。[需看 PDF 附录 / repo config.json]
2. **34 narrative functions 完整清单与中英符号精确对照**:本次只抓到约 20 个符号(A/B/H/L/Q/S/U/O/De/Fa/Lo/Fr/Ch/Em…);完整 34 个及精确中文定义需查论文表格。**注意原匿名数据 repo(acl26-ED4E)已验真为不可访问,不能作为获取入口**——需等正式 repo 或向作者索取。[no-full-list-extracted + data-repo-dead]
3. **EQ-Bench Longform live 榜的中文模型确切名次**:Longform 页面为 JS 渲染,直接 fetch 拿不到数据行(只拿到方法论);Kimi/DeepSeek 的 slop/degradation 分仍需浏览器或 JSON 接口核实。[partial-source:JS 渲染]
4. **番茄/七猫细粒度题材占比 %**:权威报告给出"三大头部 + 科幻 +38.5% + 性别偏好 >50%/>60%"等,但各题材精确百分比未完全公开;§1.5 引的番茄性别偏好两源(donews/zhihu)为第三方/早期面板,需更新源核实。[partial-source]
5. **是否值得自建中文网文标注集**:Creative Convergence 仅 1k 条、WebNovelBench 测试集 1k 条——若要把 34 功能做成可训练的 Planner 约束,且其匿名数据集不可得,**可能必须自标**。[open-design-question]
6. **数据可商用性双风险**:① WebNovelBench 数据集 = **CC-BY-NC-SA-4.0(非商用)**;② Creative Convergence 配套数据 repo 失效、license 未定。两者落地前都需确认许可,**当前都只能"借方法/框架"而非直接用数据**。[open-license-question]
7. **(新增)中文创意写作选型的"可复核单一榜单"缺口**:WebNovelBench 与 EQ-Bench v3(llm-stats)各自只覆盖部分中文模型,Kimi K2.6 的第一名结论目前主要来自**基础事实核查转引的第三方实测**而非单一权威可复核榜单;建议落地前在我们自己的中文章节质量门禁上小样跑一轮 Kimi K2.6 vs Qwen3 大杯做内部确认。[open-validation-question]

---

## v1 ↔ v2 diff

> **关于 v1**:任务指定的 v1 路径 `C:\Files\work\story\workspace\research\2026-04-28-novel-system-survey\r9-chinese.md` 经核查(Read 工具 + Glob `**/r9*` / `**/*.md` / `**/*novel-system-survey*/**`)**在仓库中不存在**——该方向无历史 v1 文件。因此本节的 diff 以"clean-room 调研稿(findings)"作为 v1 基线,对照本 v2 终稿说明变化。

### 删除(剔除幻觉 / 不实链接 — 共 4 处)
1. **`https://anonymous.4open.science/r/acl26-ED4E/`(Creative Convergence 匿名数据/代码 repo)** — 验真 exists=false(HTTP 403 + 全网无证据该 ID 下存在本项目)。论文本体(arXiv 2603.14430)为真、保留;**仅删除该数据 repo 链接**,并在 §2 与 Open Q2/Q6 显式标注"配套数据不可得,只采框架"。
2. **`https://evy.so/compare/best-llms-for-writing/` 及其全部中文模型聚合分数**(原:Kimi K2.6 1807.7 > DeepSeek V3.2 > GLM-5 > … 一整段排名)— 验真 exists=false:页面虽在,但**未以"中文模型分数"作为榜单组成项**,所引数值无法复核。整段聚合分数已删,选型证据链改用 WebNovelBench + EQ-Bench v3(llm-stats)+ 基础事实核查重建。
3. **`https://andrewmayne.com/2025/07/14/kimi-k2-the-best-open-source-model-for-creative-writing-maybe/`(Andrew Mayne 实测博文)** — 验真 exists=false(HTTP 404)。已删除该"实测背书"引用;Kimi K2.6 的优势改由基础事实核查的多源中文实测支撑。
4. **`https://arxiv.org/html/2401.17268v1`(Weaver HTML 全文)** — 验真 exists=false(HTTP 404,非标准 arXiv HTML 路径)。已替换为可访问的 **ar5iv 镜像 https://ar5iv.labs.arxiv.org/html/2401.17268** + arXiv 摘要(两者均验真为真)。

### 纠正
- **选型证据链重建**:删去 EVY 聚合分数与 Mayne 博文后,Writer 选型(Kimi K2.6 / Qwen3 大杯)结论**不变**,但支撑证据换成"WebNovelBench Qwen3-235B #1 + EQ-Bench v3 llm-stats Qwen3-235B #3(均可复核)+ 基础事实核查多源实测(Kimi K2.6 中文创意写作双榜第一、超 GPT-5)";新增 **DeepSeek V4-Pro(1M 上下文、知识强、文笔数据薄)/ Qwen3.6-Plus(Apache-2.0 全开源、C-Eval 93%)/ GLM-5.1(编程强)** 的实测画像。
- **WebNovelBench 元数据补正**:补入作者署名差异(arXiv "Leon Lin" vs ACL Anthology "Liangtao Lin",同一人)、repo 描述更新为 "Official PyTorch implementation"、**数据集许可 = CC-BY-NC-SA-4.0(非商用)**——后者直接影响落地策略(只借量表、勿用数据商用)。
- **8 维量表逐字核验**:经基础事实核查比对 Table 1,确认 8 个维度名称与权重逐字一致(原稿无误,标注为"已核验")。
- **34 功能数据可得性纠正**:从原稿"匿名 repo 可取"纠正为"**链接失效、数据不可得,落地只能采框架/自标**"。

### 新增
- **§6 角色认知交叉指针**:依据基础事实核查,明确 **"PerRoleCognition" 系杜撰(全网无)**,本稿不引用;并转介三项**已验真存在**的相关工作给 R5/R3——**RPNA**(arXiv 2510.24677)、**RoleRAG**(2505.18541)、**Character-LLM**(2310.10158)。
- **三维评判显式化**:每条候选补齐"时效性 / 鲁棒性 / 可行性"三维标注,并在 Top 候选表加"备注"列标注许可与数据风险。
- **Open Q6 升级为"数据可商用性双风险"**:合并 WebNovelBench(CC-BY-NC-SA 非商用)与 Creative Convergence(数据失效/license 未定)两条许可风险。
- **Open Q7(新增)**:指出中文创意写作"可复核单一榜单"缺口,建议落地前在自有质量门禁上小样实测 Kimi K2.6 vs Qwen3 大杯做内部确认。
- **许可/落地提醒贯穿全文**:WebNovelBench 数据非商用、Creative Convergence 数据不可得、Weaver 权重未开源——三者均明确为"借方法不借资产"。
