# R16 · 生产级质量保障体系 — 生产级终稿

> 调研日期 / accessed：全部为 2026-05-30
> 立场：从 0 构建、面向生产、**绝不质量妥协**。判断标准不是"能不能先跑起来 / 能不能 demo"，而是"这是不是生产级最优、值不值得从第一天就做对"。明确拒绝"先用 X 凑合、以后换 Y"的埋雷式分期；不兼容旧系统；宁可前期重，也要一步到位。
> 方法：clean-room 调研 + 第三方对抗式引用验真（`exists=false` 已剔除，见 §10）+ 对齐两项地基锚点（R11 模型路线 / R15 对白天花板是否 binding）。

---

## 0. 一句话结论（与地基锚点对齐后）

**质量保障体系不是"要不要做"的开放选择题——R11 已把生成内核定在"自托管开源权重 + 解码层自控 + 针对性微调"上，这条决定直接把判分与门禁也拉成必须自建、必须独立于 Writer 的一等公民工程。** 在"绝不质量妥协"的立场下，本方向的取舍可以一句话收敛：

**判分内核必须是"会写理由的评审"（带推理链的 generative critic），不是"打个分的标量头"；门禁必须"分维度 + 多评委 + 确定性硬规则 + ECDF 真实分布锚定"四层叠加，不是单模型打 1–5 分；reject-and-regenerate 必须建在"独立验证器 + best-of-N"上，绝不能建在"同模型自评"上。** 这四条都不是"以后再补"的优化项，而是第一天就必须做对的地基——因为最强的反向证据（标量 RM 在中文/主观写作偏好上准确率 52.7%、单 LLM judge 53.9%，等同抛硬币）已经把"朴素单模型打分当生产门禁"这条路彻底判死。

四个被文献钉死、不可妥协的结论：

1. **朴素"单模型 LLM-as-judge 打整体分"作生产硬门禁 = 不达标。** 创意写作恰是判分最弱领域：序列 RM 52.7%、zero-shot judge 53.9%（≈随机）；唯一有效形态是带显式推理链的 generative RM，同基准 81.8%（+30pt）。
2. **reject-and-regenerate 用"同模型自我批判" = 不达标。** LLM 内在自我纠错在推理上不仅不涨反掉分（GPT-4 GSM8K 95.5%→89.0%）。必须独立验证器 + best-of-N + 确定性规则。
3. **确定性硬门禁（中文 slop / repetition / 段落结构退化 / 知识图谱事实冲突）是零判分成本、不可被偏见污染的最可靠 gate，必须第一天进 CI 与逐章实时门禁。**
4. **质量回归监控（golden 集 + 全套度量在 CI block merge）ROI 最高、技术最成熟，无理由不在第一天做对。**

---

## 1. 判分内核：超越 SEQR 的生产级形态

> 对齐 R11：内核已是自托管开源底座（Qwen3-235B-A22B 为目标、起步 Qwen3-32B 稠密），所以"自托管中文 generative critic 省 API、可控、可微调到网文域"是可达的——这正是放弃纯 API 主路径换来的能力，应吃满。

### 1.1 WebNovelBench —— 中文网文唯一对口的学术基准（强烈建议吸收方法论）

- 来源：**WebNovelBench: Placing LLM Novelists on the Web Novel Distribution**，arXiv:2505.14818（Liangtao Lin / Jun Zheng / Haidong Wang），2025-05-20；已被 **EACL 2026 Findings** 收录（aclanthology.org/2026.findings-eacl.94，pp.1828–1847，DOI 10.18653/v1/2026.findings-eacl.94）。
  - https://arxiv.org/abs/2505.14818 [accessed:2026-05-30]
  - https://arxiv.org/html/2505.14818v1 [accessed:2026-05-30]
  - https://aclanthology.org/2026.findings-eacl.94/ [accessed:2026-05-30]
- **Repo / 数据集（验真已更正）：** 调研初稿写的 `github.com/OedonLestrange42/webnovel-bench`（带连字符）**返回 404、不存在**；**正确 repo 是 `github.com/OedonLestrange42/webnovelbench`（无连字符）**。数据集 HF `Oedon42/webnovelbench` exists=true，**license = CC-BY-NC-SA-4.0**（非商用、需署名、相同方式共享）——**这是生产采用的硬约束：数据集本身不可直接商用，只能吸收"方法论"（8 维 rubric / PCA 加权 / ECDF 锚定）自建，不能把它的语料/分数直接搬进商业产品。**
  - https://github.com/OedonLestrange42/webnovelbench [accessed:2026-05-30]
  - https://huggingface.co/datasets/Oedon42/webnovelbench [accessed:2026-05-30]
- **数据：** 4000+ 部中文网文（2013–2020，每部 >10000 读者），从 >10000 部清洗。题材：东方玄幻 1281、现实 1255、西幻 670、历史 234 等。
- **8 个中文叙事维度（PCA 权重，可直接抄进判分 / Consistency agent）：**
  1. 文学手法运用（0.1304）2. 感官细节丰富度（0.1160）3. 角色存在感平衡（0.1152）4. 角色对白辨识度（0.1171）5. **人物塑造一致性（0.1377，最高权重、区分力最强）** 6. 氛围与主题契合（0.1290）7. 上下文恰当性（0.1281）8. 场景间连贯性（0.1263）。
- **判分内核（可直接复用）：** judge 用 DeepSeek-V3，**direct scoring（逐条独立 1–5）而非 pairwise，刻意规避位置 / 长度偏见**；PCA 第一主成分（解释 75.6% 方差）作权重聚合；ECDF 映射到 4000 部真实分布的百分位；同配置重复 11 轮 IQR<0.05、方差<0.001（稳定性证据）。
- **结果锚点：** 24 模型；Qwen3-235B-A22B 居首（norm 5.21），DeepSeek-R1、Gemini-2.5-Pro 第一梯队。**这与 R11 锚点完全咬合**——R11 正是据此（开源 Qwen3 中文最强、闭源开源 gap 很窄）判定从 0 选自建开源底座。

**生产可行性判断 — R16 判分层的最佳起点，值得第一天就做对。** 三大设计（中文 8 维 rubric / PCA 数据驱动加权 / ECDF 百分位锚定）正补 SEQR 类抽象打分"分数无现实意义"的最大短板。**三个必补缺口：**
- ① 它只用单 judge，作者自己在 Limitations 承认应上多 judge——生产门禁**必上评委团**（§1.4）。
- ② 它是"重写"任务（把 10 章压成梗概再重写），与你"长程连载自动生成"不同构，**百分位须用你自己的章节重拟分布**。
- ③ 它单章 ~800–1200 字、样本 4096 token，**不测长程退化**（你最痛痛点），须叠加长程退化度量（§1.3）。
- ④ 数据集 CC-BY-NC-SA-4.0，**只吸收方法、不搬数据/分数进商业产品**。

### 1.2 LLM-as-judge 偏见账本与去偏 recipe（CALM）

- 来源：**Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge**，arXiv:2410.02736（Jiayi Ye 等，Notre Dame / IBM / 北大），2024-10-03。
  - https://arxiv.org/abs/2410.02736 [accessed:2026-05-30]
- **12 类可量化偏见：** 位置、啰嗦 / 长度、同情消退、从众、分心、谬误疏忽、权威、情感、身份、CoT、**自我增强（偏好自己生成内容）**、Refinement-Aware。
- **量化（Robustness Rate，越高越不偏）：** Claude-3.5 最稳（位置 0.832 / 啰嗦 0.952）；GPT-4o（0.776 / 0.977）；ChatGPT 弱（0.566 / 0.900）。**对齐类数据偏见显著重于事实类；位置偏见在"多选项"下急剧恶化**——创意判分天然多选项 / 开放式，位置偏见风险最高。
- **去偏 recipe（可落地）：** ① **绝不用同一模型既生成又判分**；② 顺序随机化 + A/B+B/A 平均；③ prompt 显式"忽略身份 / 长度"+ 防注入（judge 也会被攻击，见下）；④ 按你的偏见敏感维度挑鲁棒 judge；⑤ CoT 对部分模型 +7%，但 WebNovelBench 反例（分类打分无 CoT 反更稳）——**须按任务实测，不可照搬**。
- **judge 也会被 prompt 注入攻击：** **Optimization-based Prompt Injection Attack to LLM-as-a-Judge**，arXiv:2403.17710（JudgeDeceiver，ACM CCS 2024）——攻击者可在候选响应里注入序列让 judge 必选它。https://arxiv.org/abs/2403.17710 [accessed:2026-05-30]

**生产可行性判断 — 把 CALM 当判分门禁的"对抗测试套件"，第一天纳入。** 每次升级 judge / prompt 跑 CALM 式扰动量化 Robustness Rate，作为 judge 准入条件。**judge 的 prompt 必须做注入防御**（生成内容里可能混入诱导 judge 的文本）。

### 1.3 长程退化与"slop"——网文自动生成最致命、最易忽视的塌方

- **EQ-Bench Creative Writing v3**（eqbench.com/creative_writing.html，验真 exists=true）：32 prompts×3=96 篇；judge 现为 **Claude Sonnet 4.6**；rubric→Glicko-2→ELO；位置偏见 A/B+B/A 平均、长度偏见截断；约 **$10/模型**。**两个可做成确定性硬门禁的自动度量：① Repetition（高频词 / bigram / trigram 频率和）；② Slop Score（对照 GPT-isms 主表）。** 含 Slop / Repetition / Style / Length 维度。**但 32 prompts、主要面向英文，无明确中文赛道。**
  - https://eqbench.com/creative_writing.html [accessed:2026-05-30]
  - repo：https://github.com/EQ-bench/creative-writing-bench （106 stars，MIT）[accessed:2026-05-30]
- **EQ-Bench Longform**（eqbench.com/creative_writing_longform.html，验真 exists=true）：规划→修订→**连续 8 次 1000 字写作**、14 维评估，judge 已升级 Claude Sonnet 4.6（2026-02）。**唯一公开、直接对标"多章连载是否退化"的基准，与你核心痛点同构。**
  - https://eqbench.com/creative_writing_longform.html [accessed:2026-05-30]
  - repo：https://github.com/EQ-bench/longform-writing-bench （MIT）[accessed:2026-05-30]
- **slop-forensics**（sam-paech/slop-forensics，验真 exists=true，**MIT**，~332 stars——初稿写 369，验真为 332）：量化过度用词与低词汇多样性的取证工具，可借鉴方法论。
  - https://github.com/sam-paech/slop-forensics [accessed:2026-05-30]
- **Judgemark v2.1**（eqbench.com/judgemark-v2.html，验真 exists=true，repo `EQ-bench/Judgemark-v2`）：量化"某模型当 judge 有多可靠"，三维 = Stability（迭代间 Kendall τ）、Separability（Kruskal-Wallis + CI99 重叠，权重 4×）、Human Correlation（对 LMSys Arena 创意写作类 Kendall τ）；公式 `(stability + human_corr + 4×separability)/6`。**具体模型分数页面动态加载未渲染 `[需深验]`。**
  - https://eqbench.com/judgemark-v2.html [accessed:2026-05-30]

**生产可行性判断 — Repetition + Slop + 段落结构退化是"零判分成本、确定性、被偏见污染概率为零"的硬门禁，必须第一天进 CI 与逐章实时门禁，是 reject-and-regenerate 最可靠触发器。** 关键本地化工程：**GPT-isms 表是英文，直接套失效——中文 slop 词表必须自建**（与 R6 反 slop、R14 解码层"中文 slop 度量"是同一块基建，三方向共用，第一天建一次）。judge 选型不该拍脑袋，**应先跑 Judgemark v2.1 选 separability + human-corr 最高者**。

### 1.4 评委团 / PoLL —— 去自我偏好的关键架构

- 来源：**Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models**，arXiv:2404.18796（Pat Verga 等，Cohere），2024-04。
  - https://arxiv.org/abs/2404.18796 [accessed:2026-05-30]
- **构成与聚合：** 3 个异族模型（原文 Command R 35B + Claude Haiku + GPT-3.5）；二元判定 max-voting，连续分 average pooling。
- **收益（精确）：** 人类相关性 Cohen's κ —— NQ 0.763 vs 单 GPT-4 0.627、TriviaQA 0.906 vs 0.841、HotpotQA 0.867 vs 0.830；Chatbot Arena Pearson **0.917 vs 0.817**、Kendall τ 0.778 vs 0.667；**成本低 7–8 倍**；**降自我偏好**（评委团方差 2.2 vs 单评委 6.1；并消除"GPT-4 给自家变体打虚高分"）。

**生产可行性判断 — 应作判分层默认架构，与 CALM"别用同模型自判"一致。** 生产做法：judge 用 **2–3 个不同厂商中文强模型**（如 DeepSeek-V3 + Qwen + 一个 Claude/Gemini 级），各 direct-scoring，取中位 / 加权，顺序随机化。同时缓解 self-enhancement 与单点偏见。**代价是判分成本 ×N、延迟上升——但 PoLL 证明"多小模型评委团反而比单大 judge 便宜 7–8 倍"，所以这条对"绝不妥协"立场不仅不是负担，还是省钱的（反直觉、对你有利）。** 且你的 Writer 是 background task、延迟容忍高，评委团延迟不影响用户可感知体验。

### 1.5 reward model 路线在创意写作上的硬天花板与转机（关键证据）

- **WritingPreferenceBench / Beyond Correctness: Evaluating Subjective Writing Preferences Across Cultures**，arXiv:2510.14616（Shuangshuang Ying / Yunwen Li 等，ByteDance Seed + M-A-P），2025-10-16：1800 对人工验证偏好对（**英 1200 + 中 600**），8 题材 / 51 类，**两条响应在语法 / 事实 / 长度上对齐**以隔离纯主观质量。
  - https://arxiv.org/html/2510.14616v1 [accessed:2026-05-30]
  - https://WritingPreferenceBench.github.io/ [accessed:2026-05-30]
  - **结果（决定判分内核选型的核心数字）：序列 RM 52.7%、zero-shot LLM judge 53.9%（≈随机）；带显式推理链的 generative RM 81.8%（+30pt，榜首 RM-R1-Qwen2.5-7B）；Doubao-1.5-Pro 68.7%。** 存在"灾难性题材失效"（18.2%–81.8%，std 10–14%）；27B 不比 8B 稳——靠表面启发而非可泛化美学。
- **RewardBench**，arXiv:2403.13787（Allen AI/UW/Harvard），2024-03：四域 = Chat / Chat-Hard / Safety / Reasoning，**不含创意写作**。**直接含义：现成 RewardBench 高分 RM 与你需求几乎无关，不能直接 gate 网文。**
  - https://arxiv.org/abs/2403.13787 [accessed:2026-05-30]
- **2025 generative RM 路线（已验真 exists=true，可进观察 / 实验，非观望）：**
  - **RLMR: Reinforcement Learning with Mixed Rewards for Creative Writing**，arXiv:2508.18642 https://arxiv.org/pdf/2508.18642 [accessed:2026-05-30]
  - **Writing-Zero: Bridge the Gap Between Non-verifiable Problems and Verifiable Rewards**，arXiv:2506.00103（Self-Principled Critique + Bootstrapped Relative Policy Optimization，CC-BY-4.0）https://arxiv.org/abs/2506.00103 [accessed:2026-05-30]
  - **Rewarding Creativity: A Human-Aligned Generative Reward Model for Reinforcement Learning in Storytelling**，arXiv:2601.07149（阿里，RLCS 框架）https://arxiv.org/html/2601.07149 [accessed:2026-05-30]

**生产可行性判断 — 不要把"标量 reward model 当生产绝对质量门禁"作主路线，创意质量上仅 52.7%，这条路明确不达标。** 标量 RM **仅适合 best-of-N 相对排序**（同 prompt 选较好者，弱信号也有用）。**生产级最优 = 带推理链的 generative judge（81.8% 路线）+ 多维 rubric（WebNovelBench 式）+ 评委团 + 确定性 slop/repetition 门禁 + 人审校准。** generative RM 是已被验证有效的方向，不是观望项。**与 R12 微调管线呼应：R12 阶段 D 正是用 GRPO + 中文"对白区分度 / 人物一致性"生成式奖励模型破天花板——R16 判分内核与 R12 训练奖励是同一个 generative critic 的两面，应统一建设、互相喂养（判分产出的偏好对回流去训 critic）。**

### 1.6 中文专用判分模型（可自托管，省 API、可控、可微调到网文域）

- **WritingBench: A Comprehensive Benchmark for Generative Writing**，arXiv:2503.05244（阿里 X-PLUG）：1000 query、6 域 100 子域、**中英双语**；**query-dependent：每条 query 动态生成 5 条实例专属 criteria**（比固定维度更贴网文多样性）；训练了 **7B critic 模型**，与人类相关性达到 / 超过 GPT-4o，**数据与模型均开放**。repo `X-PLUG/WritingBench`，**Apache-2.0**，~181 stars（初稿写 207，验真 181）。
  - https://arxiv.org/abs/2503.05244 [accessed:2026-05-30]
  - https://github.com/X-PLUG/WritingBench [accessed:2026-05-30]
- **CritiqueLLM**，arXiv:2311.18702（清华 THU-CoAI / 智谱，ACL 2024）：**中英双语**，**6B / 12B / 66B**，支持 pointwise + pairwise，66B 系统级相关性匹敌 / 超 GPT-4；模型 / 数据 / 代码开放。repo `thu-coai/CritiqueLLM`，~148 stars（初稿写 100，验真 148），HF `thu-coai/CritiqueLLM-6B`。
  - https://arxiv.org/abs/2311.18702 [accessed:2026-05-30]
  - https://github.com/thu-coai/CritiqueLLM [accessed:2026-05-30]
- **G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment**，arXiv:2303.16634（CoT + form-filling 打分范式，summarization Spearman 0.514）——judge prompt 设计的方法论参考。
  - https://arxiv.org/abs/2303.16634 [accessed:2026-05-30]

**生产可行性判断 — WritingBench 的 criteria-aware（按桥段动态生成评判标准）+ 开放 Apache-2.0 的 7B critic，是最具生产吸引力的中文方向之一。** 与 R11 路线完全同向：自托管中文 critic 省 API 成本、可控、可微调到网文域。**生产做法（不是分期妥协，是两条腿一起站）：判分内核 = 自托管中文 generative critic（WritingBench 7B / CritiqueLLM 微调，Apache-2.0 可商用，跑量省钱）+ 通用大模型评委团（高价值章节交叉校验、做校准锚）双轨并行。** 注意 CritiqueLLM repo 无 SPDX license 标注，商用前须确认许可 `[需深验]`。

> **§1.6 重要剔除：** 调研初稿曾把 **arXiv:2510.13705（"DEMO / 长程细节忠实度"）** 列为长程忠实度证据——经验真，该 arXiv ID 实际指向《VC-Dimension vs Degree: An Uncertainty Principle for Boolean Functions》（Boolean 函数复杂度，与故事生成无关），**该论文不存在，已整条剔除**（详见 §10）。长程退化 / 忠实度证据改由 EQ-Bench Longform（§1.3，验真 exists=true、直接对标多章连载）独立承载，结论不受影响。

---

## 2. 人审环（HITL）在生产中怎么嵌

- **核心模式：** 置信度路由——judge 高置信自动过 / 拒，**低置信 / 高风险 / 评委分歧 / slop 临界样本进人审队列**；人审专注边界 case、申诉、新失败模式，决策回流。
- **生产级 HITL 设计（网文落点）：**
  1. **校准锚（第一职责）：** 定期人工标注一批章节作 ground truth，算 judge 与人类相关性（Spearman / Kendall / Cohen κ），偏出阈值就重标定。CALM 明确要求 "continuous calibration against human experts"。
  2. **分层抽审 + 全审边界：** ECDF 落灰区（如 40–60 百分位）/ 评委团分歧大 / slop-repetition 临界 → 强制人审；高分高置信抽审（防系统性高估）。
  3. **回流闭环：** 人审标签 → 修正 judge prompt / few-shot；累积偏好对喂 generative critic 训练（与 §1.5 / R12 阶段 D 同一管线）；更新 golden 回归集。
  4. **借用网文编辑传统但结构化：** 起点上架靠付费用户人工推选 + 编辑——把编辑判断结构化成可量化标签（对齐 8 维 + 完读率预期），才能回流。

**生产可行性判断 — HITL 不是兜底，是判分层可信度的根基，第一天嵌入，但形态是"校准 + 边界审 + 回流"，不是"人海逐章审"。** 纯人审不可规模化做实时门禁；纯自动判分不可信（52.7% 那条线）。生产级最优 = 自动跑量 + 人审校准锚 + 置信 / 分歧路由边界审。**judge-人类相关性必须被持续测量，而非假设。**

---

## 3. A/B 测试与读者留存代理指标（retention proxy）

### 3.1 中文网文平台真实质量验收标准（可作对齐信号）

来自番茄 / 起点作者生态公开拆解（知乎 / 澎湃等）。[accessed:2026-05-30]

| 指标 | 定义 | 数值锚点 |
|---|---|---|
| 完读率 | 点击中读完一定字数的占比 | 番茄 10 万字完读率均值 **16–17%**，**>17% 优秀**有扶持；脑洞文 ≥15%、传统文 ≥10% 及格；**30 万字 ≥6% 是继续给量底线，跌破即停** |
| 留存（次/三/七留） | 第 2/3/7 天仍在读比例 | 算法早期"是否继续推"的**最关键权重**；10–20 万字阶段 **七留 >25%** |
| 追更比 / 追读率 | "在读"与追最新章之比；追读率≈三天新增内容阅读总数 / 当天阅读者 | 追更比理想 **2:1**（重在稳定上升）；追更率 **>30%**（10–20 万字阶段） |
| 吸量 | 书名 / 封面 / 简介吸引点击 | 首日阅读 400+ 或点击 300+ 合格（A），500+ 为 SS 级明显倾斜 |
| 均订 / 追订 | 起点上架核心 | 起点上架以**付费用户人工推选 + 订阅量**为核心 |

- **写作工艺锚点（可进 Writer spec）：** 单章 ~2000 字；脑洞 / 同人 1500–2000、每 500 字一小事件、避免连续 >3 段对话；传统文 2500–3500；日更 4000+；验证期前 3 天最关键。
- **推荐机制：** 番茄是"小量测试→达标→逐级放量→回落→停量"的纯数据驱动循环，决定权在实时数据而非编辑。

### 3.2 能否代理为训练 / 评测信号？——双层结构（生产级关键）

- **线上层（终极真值 OEC）：** 完读率 / 留存 / 追读 / 订阅是真金白银，但**事后、群体、有数据延迟**（完读率要到 10 万字才统计准），不能逐章实时 gate。应作 **A/B 北极星 + guardrail**，评判"prompt / 模型 / pipeline 改动是否真让书更好"。
- **离线层（代理 reward）：** 把"高完读 / 高留存的真实人类章节"作正样本、低数据章节作负样本，训**预测完读率 / 留存的代理模型**，给生成章节打"预期留存分"，作 reject-and-regenerate 触发 + best-of-N 排序，把读者验收前移成可实时计算的代理。
- **理论支撑：**
  - **The Surrogate Index**（NBER w26463，Athey / Chetty / Imbens / Kang，验真 exists=true）——用一组短期代理估长期结果，核心假设是 surrogacy（代理需完整中介长期效应）。https://www.nber.org/papers/w26463 [accessed:2026-05-30]；**假设边界对网文是否成立 `[需深验]`。**
  - OEC / 在线受控实验（Kohavi）——选能预测长期价值的 OEC、警惕短期代理误导、配 guardrail `[snippet-only]`。
  - "Success with style"（EMNLP 2013，aclanthology D13-1181）——文体特征预测小说成功（Gutenberg 下载量代理），证明"文体→受欢迎度"可学习，但经典≠网文，迁移性存疑 `[snippet-only]`。

**生产可行性判断 — "双层结构"是生产级最优，且应第一天就规划章节级阅读行为埋点，否则后期无数据训代理——正是"绝不埋雷"的体现。** 风险：① **Goodhart**（优化代理 / judge 分而非真实质量），靠线上 A/B 定期校验代理-真值相关性漂移；② **冷启动无自有读者数据**，可先用番茄 / 起点公开阈值 + 人类网文正负样本 bootstrap，但**绝不能把代理分当唯一真理，必须线上验证**。

---

## 4. 章节级 reject-and-regenerate 闭环

- **最硬戒律：Large Language Models Cannot Self-Correct Reasoning Yet**（Huang 等，Google DeepMind + UIUC，**ICLR 2024**，arXiv:2310.01798，验真 exists=true）：**无外部反馈的内在自我纠错在推理上不仅不涨反而掉分**——GPT-3.5 GSM8K 75.9%→74.7%；**GPT-4 GSM8K 95.5%→91.5%→89.0%**；**Llama-2 CommonSenseQA 64.0%→37.5%→36.5%**；**多智能体辩论 83.2% < self-consistency 85.3%**（等算力下）。根因：模型无法可靠判断自身正确性。**只有 oracle / 外部 verifier 才有效。**
  - https://arxiv.org/abs/2310.01798 [accessed:2026-05-30]
- **对照：Self-Refine: Iterative Refinement with Self-Feedback**（arXiv:2303.17651，NeurIPS 2023，验真 exists=true）在部分任务（含对话 / 写作）用自反馈→自改有改善，但有效性与"是否有可靠反馈信号"强相关。https://arxiv.org/abs/2303.17651 [accessed:2026-05-30]

> **§4 重要剔除：** 调研初稿曾引 **DReSS / arXiv:2510.21304**（"多智能体草稿→多维评审→精炼循环"）佐证 reject-and-regenerate——经验真，该 arXiv ID 实际指向《Arbitration-Free Consistency is Available (and Vice Versa)》（分布式存储一致性，与故事生成无关），**该论文不存在，已整条剔除**（详见 §10）。reject-and-regenerate 设计改由"self-correction 戒律 + Self-Refine + best-of-N + 独立验证器"承载，结论不受影响、反而更干净。

**生产级设计（给你的 Chapter graph，对齐 R11 / R14）：**

1. **门禁信号按可靠性排序：**
   - (a) **确定性硬规则**——中文 slop / repetition / 段落结构退化 / 字数 / 连续对话段数 / 知识图谱事实冲突——**最可靠，优先硬 gate**（与 §1.3、R14 §2.6、R6 共用中文 slop 词表）。
   - (b) **独立判分器**——评委团 8 维 direct-scoring + ECDF 百分位，落灰区触发 regen。
   - (c) **代理留存分**——低于阈值触发 regen / 择优（§3.2 离线层）。
2. **best-of-N 优于"自评 retry"：** 并行写 N 版 → 独立判分器 / 代理分排序 → 取最优，绕开 intrinsic self-correction 陷阱（用外部排序而非自我批判）。**这与 R14 的红利叠加：Writer 是 background task、延迟容忍高，best-of-N 的额外算力 / 延迟不伤用户体验，是"为质量花算力"的正确位置。**
3. **retry 上限 + 升级：** 现有"最多 3 次"应在 3 次后**升级**（换更强模型 / 触发人审 / 降级标记），而非无限重试或静默硬塞。
4. **反馈具体可执行：** 若用 critique 引导 regen，须结构化、定位到具体维度 / 段落（对应 8 维 + 失败模式），而非"写得不好"。

**生产可行性判断 — reject-and-regenerate 必须建在"独立验证 + 确定性规则"上，绝不能建在"同模型自评"上——这是文献最强戒律，也最易被工程图省事违反。** **把 Consistency / 判分做成与 Writer 不同模型 / 不同视角的独立验证器**（R11 已定底座可碰 logits / 权重，独立 critic 完全可达），优先用确定性度量做硬门禁。**与 R15 锚点呼应：reject-and-regenerate 里的"独立验证器"绝不能是"同基座换 persona 的伪独立评审"——R15 已警示这种伪独立收益有限，必须真异构（不同厂商 / 不同底座）。**

---

## 5. 质量回归监控（防退化）

- **核心做法：** 固定 **golden 章节 / prompt 集**，每次 prompt / 模型 / pipeline 改动跑全套（评委团 8 维 + slop + repetition + 一致性 + 代理留存分），与基线 diff，**回归则 block merge**。工具：Braintrust（GitHub Action，PR 贴对比 + 内置 merge blocking）、promptfoo（开源，GitHub Action/CLI）、LangSmith（接 pytest/GitHub）、DeepEval（pytest 式）。社区共识：**轻量 CI gating（DeepEval/promptfoo/RAGAS）+ 回归追踪平台（Braintrust/LangSmith/Arize）双工具组合**。[accessed:2026-05-30]
- **生产级三层监控：**
  - ① **离线回归（CI，merge 前）**：golden 集全套度量超阈即 block；
  - ② **生成时实时门禁（运行时）**：每章过确定性硬规则 + 评委团判分，触发 regen；
  - ③ **线上漂移监控（发布后）**：完读率 / 留存 / 追读分布漂移 + judge-人审分相关性漂移（防 judge 失准）+ 代理-真值相关性漂移（防 Goodhart）。

**生产可行性判断 — ROI 最高、技术最成熟，无理由不在第一天做对。** 你已是 LangGraph / Python 栈：**promptfoo 或 DeepEval 做 gating + 自建 / Braintrust 做回归追踪**；judge 选型先跑 Judgemark 定。需自建的只有**中文 slop 词表**（R6/R14/R16 三方向共用）和**网文 golden 集 + 8 维 rubric 的 eval 实现**（无现成中文工具）。这是把"绝不质量妥协"工程化、可验证的必要地基，值得前期重投入。

---

## 6. Top 推荐配方（生产级最优组合，从 0 一步到位）

> 全部对齐 R11（自托管开源底座、能碰 logits / 改权重）与 R15（对白区分度靠底座 + 结构化 + 评测，不靠错引约束 / 不靠未验证自造技术）。

1. **判分内核 = 带推理链的 generative critic（WritingPreferenceBench 证明 81.8% vs 标量 52.7%）+ WebNovelBench 中文 8 维 rubric × 评委团（2–3 异厂中文强模型，direct-scoring，顺序随机化）× PCA 加权 × ECDF 百分位（锚到你自己的人类网文章节分布，非搬 WebNovelBench 数据）。** 自托管 WritingBench 7B（Apache-2.0）/ CritiqueLLM 微调跑量省钱，通用大模型评委团做高价值章节交叉校验与校准锚。
2. **确定性硬门禁 = 中文 slop score + repetition + 段落 / 对话结构退化 + 知识图谱事实一致性。** 零判分成本、不可被偏见污染、regen 最可靠触发器。**第一天进 CI + 逐章实时门禁。**
3. **闭环 = best-of-N 生成 + 独立验证器排序（非自评 retry，真异构非伪独立）；3 次后升级到人审 / 换模型。** 绕开 intrinsic self-correction 陷阱；利用 Writer background task、延迟容忍高的红利。
4. **HITL = 持续校准 judge（定期人工 ground truth 测相关性）+ 置信 / 分歧路由边界审 + 标签回流（喂 critic、更新 golden 集）。**
5. **读者真值 = 双层（线上完读率 / 留存 / 追读作 A/B 北极星 + guardrail；离线训"预期留存"代理分前移）+ 第一天埋章节级阅读行为点。**
6. **回归监控 = golden 集 + 全套度量在 CI block merge（promptfoo / DeepEval）+ 线上漂移监控（judge 失准 + Goodhart 双防）。**
7. **judge 选型 = 先跑 Judgemark v2.1（选 separability + human-corr 最高者），不拍脑袋。**
8. **统一基建复用：中文 slop 词表 / 自动 slop 评分 / 对白可分性打分是 R6（反 slop）+ R14（解码层）+ R16（判分门禁）三方向共用，第一天建一次、三处复用。** 判分产出的偏好对回流去训 generative critic（与 R12 阶段 D / GRPO 奖励模型同一管线）。

**明确不做（现阶段，且不是"以后再做"，是本质不适用 / 不达标）：**
- ❌ **不押注"标量 reward model 当绝对质量门禁"**（创意 52.7%，本质不达标；标量 RM 仅用于 best-of-N 相对排序）。
- ❌ **不照搬英文 RewardBench / 英文 slop 表 / 英文 EQ-Bench 分数**（中文必须自建度量）。
- ❌ **不用同模型自生成自判分，不用同基座换 persona 的伪独立评审**（CALM + self-correction + R15 三重戒律）。
- ❌ **不把单 LLM judge 整体分当唯一真理**（必分维度 + 评委团 + 人审校准）。

---

## 7. 与三方向 / 地基锚点的咬合关系（防重复造轮子）

| 关切 | R16（本方向） | 与其它方向的接口 |
|---|---|---|
| 中文 slop 度量 | 确定性硬门禁的核心（§1.3、§5） | **R6 反 slop / R14 §2.6 同一块基建，建一次三处用** |
| generative critic | 判分内核（§1.5、§1.6） | **R12 阶段 D GRPO 奖励模型同一个 critic 的两面，偏好对互喂** |
| 独立验证器底座 | reject-and-regenerate 的 verifier（§4） | **R11 已定自托管开源底座，可碰 logits / 改权重，独立 critic 可达** |
| 对白区分度评测 | 离线 stylometry 闭环（§2、§3.2 间接） | **R15 提供武器（Burrows' Delta / 引文归属，arXiv:2301.05659 / 2401.16968）** |
| best-of-N 算力 | 闭环排序（§4.2） | **R14 红利：Writer background task、延迟容忍高，算力花在离线刀刃上** |

> **R15 地基纠错传达（必须记录，防误用）：** R15 已核实，用户记忆把"纯 prompt 对白区分度天花板"挂在 **arXiv:2510.24677** 上是**张冠李戴的错引**——该论文实为《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》（医疗 LLM 神经元消融，RPNA = RP-Neuron-Activated Evaluation Framework），与对白区分度毫无关系。**不得拿此错引当任何质量门禁 / 判分设计的地基依据。** 对白区分度的判分落点是"离线 stylometry 可分性打分"（有现成方法），而非寄望某条不存在的"天花板定律"。

---

## 8. 成本 / 风险

**成本（可核实）：**
- EQ-Bench CWv3 判分约 **$10/模型**（Sonnet 4.6，96 篇）；评委团 ×N 倍单次判分成本，**但 PoLL 证明 3 小模型评委团比单 GPT-4 便宜 7–8 倍**——"多评委"对成本反而有利。
- 自托管中文 critic（WritingBench 7B Apache-2.0 / CritiqueLLM 6B）跑量边际成本远低于 API judge，与 R11 自托管底座共用 GPU（R12 锚点：70B QLoRA 微调 $10–16/次，7B critic 微调更廉）。
- WebNovelBench 全量判分成本未披露 `[no-source-found]`；复用方法只需对你自己章节分布拟合，100 部 ×10 = 1000 样本即得稳定排名。

**风险：**
1. **judge 不可靠**（创意质量上接近随机）——靠多维分解 + 评委团 + 人审校准 + 持续测相关性压住。
2. **Goodhart**（优化代理 / judge 分而非真实质量）——靠线上 A/B 校验代理-真值相关性漂移。
3. **中文本地化缺口**（slop 表、网文 golden 集、中文 critic 微调数据均需自建）——这是"绝不妥协"必须前期吃下的工程税。
4. **长程退化单章基准测不出**——须叠加 EQ-Bench Longform 思路 + 确定性退化度量（中文连载退化硬门禁须自建）。
5. **完读率等真值有字数门槛延迟**——只能作离线 / 线上信号，不能实时 gate。
6. **"伪独立"评审**（同基座换 persona）收益有限——judge / verifier 须真异构（不同厂商 / 底座）。
7. **judge 被 prompt 注入攻击**（JudgeDeceiver / arXiv:2403.17710）——judge prompt 须做注入防御，生成内容里可能混入诱导 judge 的文本。
8. **WebNovelBench 数据集 CC-BY-NC-SA-4.0、CritiqueLLM repo 无 SPDX**——商用前须确认许可，只吸收方法、不直接搬非商用数据进产品。

---

## 9. Open Questions（下一轮深验 / 落地前必测）

1. `[需深验]` Judgemark v2.1 各模型实际分数（页面动态未渲染）→ 定 judge 选型。webnovelbench repo star / 是否补 SPDX license。
2. `[需深验]` Surrogate Index（NBER w26463）统计假设（surrogacy）对网文完读率 / 留存的适用边界；是否有"预测网文完读率 / 留存"的公开模型 / 论文。
3. `[需深验]` generative RM（Writing-Zero 2506.00103 / Rewarding Creativity 2601.07149 / RLMR 2508.18642）是否到可生产排序 / 可作硬门禁的成熟度；RewardBench 2 是否新增创意域。
4. `[需深验]` EQ-Bench Longform 的退化 / 14 维精确度量公式，以便复刻成中文连载退化硬门禁。
5. `[需深验]` 中文偏好 / RLHF 数据集（CValues 等）能否复用为网文 critic 训练数据；WritingPreferenceBench 的 **600 条中文对**能否直接用作中文 generative critic 的种子（注意其许可）。
6. `[需深验]` CritiqueLLM repo 的实际开源许可（无 SPDX 标注），商用可行性。
7. `[落地前必测]` 自托管 WritingBench 7B critic 在你自己网文章节上的人类相关性——论文相关性基于其测试集，本项目域须自建 A/B 复现。

---

## 10. 引用验真与剔除记录（对抗式）

**已剔除（exists=false，不得作为证据）：**

1. **DEMO / "Evaluating Long-form Story Generation by Measuring Detail Faithfulness in Literary Criticism Framework"（arXiv:2510.13705）** — 验真：该 arXiv ID 实际指向《VC-Dimension vs Degree: An Uncertainty Principle for Boolean Functions》（Fan Chang / Yijia Fang，2025-10，Boolean 函数复杂度），**与故事生成 / 文学评论无关，声称的论文不存在**。调研初稿曾在 §1.6 用它佐证"长程细节忠实度（Roland Barthes reality effect）"，**已整条剔除**。长程退化 / 忠实度证据改由 EQ-Bench Longform（验真 exists=true、直接对标多章连载）承载，方案结论不受影响。

2. **DReSS / "Multi-Agent Story Generation Framework with Phased Refinement and Multidimensional Evaluation"（arXiv:2510.21304）** — 验真：该 arXiv ID 实际指向《Arbitration-Free Consistency is Available (and Vice Versa)》（Hagit Attiya 等，分布式存储一致性模型），**与故事生成无关，声称的论文不存在**。调研初稿曾在 §4 用它佐证"多智能体草稿→评审→精炼"循环，**已整条剔除**。reject-and-regenerate 设计改由 self-correction 戒律（2310.01798）+ Self-Refine（2303.17651）+ best-of-N + 独立验证器承载，结论不受影响、更干净。

**已据验真更正的元数据（不影响结论，但落地须用正确值）：**

3. WebNovelBench repo：初稿 `OedonLestrange42/webnovel-bench`（带连字符）**404 不存在**，正确为 **`OedonLestrange42/webnovelbench`（无连字符）**。
4. WebNovelBench 数据集 `Oedon42/webnovelbench`：license = **CC-BY-NC-SA-4.0（非商用，硬约束）**。
5. star 数更正：slop-forensics 332（非 369）、WritingBench 181（非 207）、CritiqueLLM 148（非 100）。
6. CritiqueLLM 模型规模含 **6B / 12B / 66B**（初稿仅写 6B 与 66B）。
7. EQ-Bench CWv3 / Longform judge 现为 **Claude Sonnet 4.6**（初稿写 Sonnet 4 / 推荐 Claude Sonnet 4）。

**地基锚点错引（来自 R15，须传达；非本方向直接引用，记录以防误用）：**

8. **arXiv:2510.24677 被用户记忆误当"对白区分度天花板"论据** — 实为《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》（医疗 LLM 神经元消融，RPNA = RP-Neuron-Activated Evaluation Framework），与对白区分度无关。**不得作任何质量门禁 / 判分 / regen 设计的地基依据。**

**关键存活引用（验真 exists=true，high confidence）：**

- WebNovelBench：arXiv:2505.14818 / arXiv:2505.14818v1 / aclanthology 2026.findings-eacl.94 / repo `OedonLestrange42/webnovelbench` / HF `Oedon42/webnovelbench`
- CALM：arXiv:2410.02736；JudgeDeceiver：arXiv:2403.17710
- WritingPreferenceBench：arXiv:2510.14616 / WritingPreferenceBench.github.io
- RewardBench：arXiv:2403.13787
- PoLL：arXiv:2404.18796
- self-correction 戒律：arXiv:2310.01798（ICLR 2024）；Self-Refine：arXiv:2303.17651（NeurIPS 2023）
- EQ-Bench CWv3 / Longform / Judgemark v2.1（eqbench.com + repos `EQ-bench/creative-writing-bench`、`EQ-bench/longform-writing-bench`、`EQ-bench/Judgemark-v2`）；slop-forensics（sam-paech）
- WritingBench：arXiv:2503.05244 / repo `X-PLUG/WritingBench`（Apache-2.0）；CritiqueLLM：arXiv:2311.18702 / repo `thu-coai/CritiqueLLM`
- G-Eval：arXiv:2303.16634
- generative RM 路线：RLMR arXiv:2508.18642 / Writing-Zero arXiv:2506.00103 / Rewarding Creativity arXiv:2601.07149
- Surrogate Index：NBER w26463
