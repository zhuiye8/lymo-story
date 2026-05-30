# R12 · 微调管线终稿(SFT / LoRA / DPO / GRPO / FTPO)

> 方向:2026 中文网文 / 创意写作系统的**生产级微调管线**配方。
> 立场锚定:从 0 构建、面向生产、**绝不质量妥协**。拒绝"先用 X 凑合、以后再换 Y"的埋雷式分期。不兼容旧系统。宁可前期重,也要一步到位做最好的。
> 全部来源 accessed = 2026-05-30。引用经第三方对抗验真;凡 `exists=false` 的 claim 已剔除,凡身份/标签被验真推翻的,已在文末 `身份纠错` 与正文就地标注。
> 数据完整性:本轮调研 WebFetch 中途降级(arxiv 全文 / OpenReview PDF / EQ-Bench 动态榜多次超时),无法从原文核出的精确数字标 `[no-source-found:...]`。

---

## 0. 先给结论(命中用户立场)

**没有任何单一微调方法能同时解决你的两个核心痛点(角色对白区分度天花板 + 系统性中文 slop)。生产级最优是一条四阶段正交管线,而不是"挑一个最强方法"。**

四阶段(每一步都选"不留迁移债"的那条路,架构第一天就按此搭、不留分期口子):

```
阶段 A 领域风格 SFT(bf16 高秩 LoRA,rank 128–256,含 MLP/all-modules;改底座 AI 腔则全参)
  → 阶段 B 多样性保持型偏好优化(deviation-DPO / DORPO,严禁裸 DPO)
    → 阶段 C 中文 slop 外科手术(自建中文 slop 词典 + FTPO,推理期叠 Antislop Sampler 兜底)
      → 阶段 D(破天花板)GRPO + 中文"对白区分度 / 人物一致性"生成式奖励模型
```

底座结论与地基锚点 **R11 模型路线** 完全一致:**自托管开源权重 + 解码层自控 + 针对性微调**是生成内核,闭源 API 只做蒸馏教师 / 质量天花板对照。主力 **Qwen3-32B-Base**(单卡 80G 可 bf16 LoRA);追极致用 **Qwen3-235B-A22B**(22B 激活)或 **GLM-4.6**(多卡)。

**最反直觉、最命中立场的发现**:2026 最新受控实验证明——**裸 SFT 会"启动"叙事扁平化,裸 DPO 会进一步"放大"它**(角色趋同、情感压平、文风收窄)。这恰恰就是你要消灭的"对白区分度天花板"与"slop"的训练侧根源。所以"先裸 SFT/DPO 凑合,以后再优化"在本方向上是**最典型的埋雷**——它不是中性起点,而是主动制造你后面要花更大代价去逆转的损伤。必须从第一天就用多样性保持型方案。

---

## 1. 五类方法逐一 · 存活 findings + 生产可行性判断

### 1.1 全参 SFT vs LoRA / QLoRA(领域适配层)

**事实(全部 exists=true,已验真):**

- **《LoRA Learns Less and Forgets Less》**(Biderman 等,与 Databricks Mosaic AI Research 合作;**TMLR 2024 Featured Certification**)。核心:全参学到的扰动 rank 比典型 LoRA **高 10–100 倍**;**继续预训练(20B token)即使高 rank,LoRA 仍追不平全参**;但**指令微调(~100K 对)场景高 rank LoRA 可追平全参**。LoRA "遗忘更少",比 weight decay / dropout 更能防遗忘且保留生成多样性。
  - https://arxiv.org/abs/2405.09673 `[accessed:2026-05-30]`
  - https://github.com/danbider/lora-tradeoffs (21 star) `[accessed:2026-05-30]`
- **《LoRA vs Full Fine-tuning: An Illusion of Equivalence》**(Shuttleworth, Andreas, Torralba, Sharma):LoRA 即便指标追平也会生成 "intruder dimensions",谱结构与全参不同,影响持续学习鲁棒性。
  - https://arxiv.org/abs/2410.21228 `[accessed:2026-05-30]`
- **《A Comparative Analysis of LLM Adaptation: SFT, LoRA, ICL in Data-Scarce Scenarios》**(Bohnet 等,2025-10):结论 "LoRA provides the most effective balance, successfully instilling new skills with minimal impact on the base model's general knowledge"。
  - https://arxiv.org/abs/2511.00130 `[accessed:2026-05-30]`
- **《Continual Learning via Sparse Memory Finetuning》**(Jessy Lin 等,2025-10):学新事实后 NaturalQuestions F1 全参掉得最狠、LoRA 次之、稀疏记忆微调最少——侧证**全参灾难性遗忘远重于 LoRA**。
  - https://arxiv.org/pdf/2510.15103 `[accessed:2026-05-30]`
  - 注:findings 初稿给出的"全参掉 89% / LoRA 掉 71% / 稀疏 11%"为搜索摘要交叉值,原文未逐字核到 → `[no-source-found:精确百分比]`,趋势方向可信。

**生产判断(中文网文):**

- 中文网文风格化 = **中等域漂移**(底座已会中文,要改的是文风 / 节奏 / 对白习惯),对应论文"指令微调"档 → **高秩 LoRA(rank 128–256、alpha 256、含 MLP / all-modules)可追平全参且遗忘少**,还能保住你多 Agent 一致性校验依赖的长程推理能力。**✅ 生产级首选。**
- 若要注入**亿级 token 网文语料做继续预训练**(真正改写底座"AI 腔"语言分布),属 continued-pretraining 档 → **LoRA 追不平,需全参或超高秩**,成本约 LoRA 8–16×。
- **生产铁律:不要用 QLoRA(4bit)做主力。** 4bit 量化对"文笔细腻度"是隐性减分,与"绝不质量妥协"直接冲突。主力 **bf16 LoRA 或全参,QLoRA 仅限早期消融**。这条不能让步——QLoRA 主力路线**不达标**。

### 1.2 Narrative Flattening 警告(本方向最重要的一篇)

- **《Narrative Flattening: How Post-Training Compresses Thematic, Affective, and Stylistic Variation in LLM Fiction》**(Zehan Li, Yutong Zhu, Siyang Wu, Honglin Bao, **James A. Evans @ University of Chicago Knowledge Lab**;2026-05-27)。用 **OLMo-32B 同源四检查点(Base→SFT→DPO→RLVR)** 隔离后训练效应,Qwen2.5-32B / Llama-3.1-8B / Gemma-3-12B base/instruct 交叉验证。
  - https://arxiv.org/abs/2605.27878 `[accessed:2026-05-30]`(exists=true,标题 / 作者 / 日期 / 机构均验真)
- 精确数字(findings 称已从全文核出,但本轮 WebFetch 降级未能逐字复核全文,按"作者自报"采信,落地前亲验):
  - **主题运动**:句间语义跳变 CV 从人类 ~0.105 → RLVR 0.081(**−22.2%**);分阶段 Base→SFT −8.0%、SFT→DPO 累计 −15.1%、→RLVR −22.2%。
  - **情感**:冲突类从 base ~47% **崩到 RLVR ~7.5%**;惊奇-好奇 33%→13%;中性涨到 ~45%(人类 ~29%)。
  - **文风**:StyleDistance MMD 从 Base 0.24 → DPO/RLVR **0.52–0.53**;跨故事文风方差**坍缩到人类的 0.5–0.55×**;跨域文风差异被抹掉 **>90%**;专业文学(纽约客)受损最重(情感掉 ~21pp)。
- 论文给的**设计方向**(非现成药方):① 域条件化奖励模型(校准到源语域而非池化偏好);② 分布匹配目标(保跨故事方差而非只优化点态质量);③ 从"文学长尾"而非"多数偏好续写"采偏好数据;④ 把扁平化指标本身当诊断工具。原文明确:"创意写作助手可能需要与通用助手不同的对齐目标"。

**生产判断:** 这篇是整条管线的**理论地基**。它把"裸 SFT 启动扁平化 / 裸 DPO 放大扁平化"做成了同源受控证据,直接定性了"先裸 SFT/DPO 凑合"=主动制造痛点。落地动作:① 偏好层从第一天用多样性保持变体(1.3);② 把**扁平化三指标(主题运动 CV / 情感分布 / StyleDistance MMD + 跨故事方差)接入评测闭环做长期回归监控**——这是你的"质量不妥协"护栏。

### 1.3 DPO / KTO / SimPO / ORPO + 多样性保持变体(偏好层)

**方法事实(全部 exists=true):**

- **DPO**(Rafailov 等,《Your Language Model is Secretly a Reward Model》):需参考模型,**多样性损伤最大**(被 1.2 同源实验钉死)。
  - https://arxiv.org/abs/2305.18290 `[accessed:2026-05-30]`
- **SimPO**(Meng, Xia, Chen,**NeurIPS 2024**):长度归一化、**无参考模型**,AlpacaEval2 比 DPO +6.4、Arena-Hard +7.5。工程更省,但**不解决多样性**。
  - https://arxiv.org/abs/2405.14734 `[accessed:2026-05-30]`
  - https://github.com/princeton-nlp/SimPO (953 star, MIT) `[accessed:2026-05-30]`
- **KTO**(Ethayarajh 等,**ICML 2024**):**可用非配对二元反馈**(只标 喜欢/不喜欢)。网文场景极友好——线上读者点赞可直接做训练信号。
  - https://arxiv.org/abs/2402.01306 `[accessed:2026-05-30]`
- **ORPO**(Hong, Lee, Thorne,EMNLP 2024):**单阶段**合并 SFT+偏好,无参考模型。
  - https://arxiv.org/abs/2403.07691 `[accessed:2026-05-30]`
- **现代共识**(《DPO Isn't Enough》,James Fahey,2025-10):SimPO 求稳 / ORPO 求鲁棒 / KTO 处理风险——是**组合**而非择一。
  - https://medium.com/@fahey_james/dpo-isnt-enough-the-modern-post-training-stack-simpo-orpo-kto-and-beyond-d82e52a1ee6c `[accessed:2026-05-30]`
  - 补充综述:《A Comprehensive Survey of DPO》 https://github.com/Mr-Loevan/DPO-Survey `[accessed:2026-05-30]`

**真正的生产级答案 = 多样性保持变体:**

- **DiversityTuning（Diversified DPO / Diversified ORPO,DDPO/DORPO）**(Chung, Padmakumar, Roemmele, Sun, **Max Kreminski**;2025-03)。在 DPO/ORPO 目标上乘 chosen 样本的 **deviation(δ^w = 同 prompt 下样本间嵌入余弦距离均值,可含语义+文风)**,**给"罕见的高质量"更强梯度,阻止坍缩到高奖励安全模式**。结果:8B 模型**多样性追平人类数据集**、质量持平 GPT-4o / DeepSeek-R1 / Claude-3.5,优于 DivPO 基线。训练:LoRA rank 128 / alpha 256,Llama-3.1-8B + Mistral-7B-v0.3,r/WritingPrompts 42 万对,6×H100。
  - https://arxiv.org/abs/2503.17126 `[accessed:2026-05-30]`
  - https://github.com/mj-storytelling/DiversityTuning (53 star) `[accessed:2026-05-30]`
  - **身份纠错**:findings 初稿曾把作者机构标成 Midjourney,arxiv 页面未列机构,**此处改为不确认机构**(repo 命名 mj-storytelling,仅作线索)。
- 这是**直接对抗 Narrative Flattening 的可训练药方**,可叠在阶段 A 风格 SFT 之上。
- 旁证(可选叠加 / 离线诊断):《Preserving Diversity in SFT (GEM)》(**ICLR 2025**,https://openreview.net/forum?id=NQEe7B7bSw)证明 SFT 阶段本身就能保多样性 → 暗示**阶段 A 也应加多样性约束,不等到偏好层才补**。

**判断:**

- ❌ **裸 DPO 单用不可接受**——它正是 1.2 里"放大扁平化"的元凶,与立场正面冲突,**不达标**。
- ✅ **deviation-DPO / DORPO = 当前最值得一开始就做对的偏好层。**
- ✅ KTO 的非配对优势 → 长期接入读者反馈数据飞轮(把点赞/弃读变成训练信号)。
- ⚠️ SimPO / ORPO 的"无参考模型"只是工程减负,**必须叠 deviation 思想**,不能用其裸形态。

### 1.4 FTPO / Antislop:中文 slop 外科手术刀(强推,中文需自建)

- **《Antislop: A Comprehensive Framework》**(Samuel Paech, Allen Roush, Judah Goldfeder, Ravid Shwartz-Ziv;**ICLR 2026 接收**,2025-10-16)。三件套:① **Antislop Sampler**(推理时回溯抑制,压 **8000+** 模式仍保质量,传统 token-ban 到 ~2000 就崩);② 自动 profiling 管线(部分 slop 在 LLM 输出比人类高 **>1000×**);③ **FTPO(Final Token Preference Optimization)**——**只约束被禁短语首 token 的 chosen/rejected logit,不训练前文上下文**,配 logit 空间两段式 MSE 正则,**保住更宽行为分布与跨域能力**。
  - https://arxiv.org/abs/2510.15061 `[accessed:2026-05-30]`(exists=true,ICLR 2026 + OpenReview + poster 三方验真)
  - https://openreview.net/forum?id=gLcyM1khyp `[accessed:2026-05-30]`
- **效果(findings 核出值)**:FTPO **90% slop 削减**,GSM8K / MMLU / 创意写作持平或提升;**词汇多样性维持基线 95–102%,而 DPO 渐进坍缩到 74–92%**。测试模型家族:**Gemma-3-12B、Mistral-Small-3.2、Llama-3.3-70B**(**身份纠错**:findings 初稿曾误写 Qwen,实为 Gemma/Mistral/Llama)。
- **工程(GitHub API 验真 2026-05-30):**
  - `auto-antislop`(端到端 FTPO 管线,四步:baseline→slop 分析→造偏好对→FTPO;`finetune_mode:"ftpo"`,支持 vLLM + TRL/Unsloth,ShareGPT 格式)— **133 star** — https://github.com/sam-paech/auto-antislop
  - `antislop-vllm`(OpenAI 兼容端点的推理期 slop 抑制)— **31 star** — https://github.com/sam-paech/antislop-vllm
  - `slop-forensics`(slop 统计/取证工具,**MIT**)— **332 star** — https://github.com/sam-paech/slop-forensics
  - 成品 `sam-paech/gemma-3-12b-it-antislop`(基于 google/gemma-3-12b-it,Gemma 许可)— https://huggingface.co/sam-paech/gemma-3-12b-it-antislop
  - 全部 `[accessed:2026-05-30]`,exists=true。

**生产判断(中文适配是关键风险点):**

- ✅ **FTPO 是目前唯一被证明"压 slop 不杀多样性"的专门方法**(对比组 DPO 越压越坍缩),精准命中"系统性压制中文 slop",**强烈推荐放管线末端(阶段 C)**。
- ⚠️ **中文必须自建,不能直接用英文资源。** Antislop 的 slop 词典 / 人类基线默认英文(成品模型 card 明确无中文支持,且只处理"过度出现的词/短语",不处理"主题/文风型 slop")。中文网文 slop(如"嘴角勾起一抹弧度""空气仿佛凝固""不容置疑""深邃的眸子")必须用**中文人类网文语料重新 profile**——一次性重活,正契合"宁可前期重"。`slop-forensics` 可改造做中文统计。
- ✅ Antislop Sampler 可作**推理期兜底**(不微调也能立即压 slop),与微调正交 → 生产双保险。这一点与地基锚点 **R11** 完全咬合:R11 已定"治 slop 必须能碰 raw logits,闭源 API(Kimi 官方文档明确不支持 logit_bias/logprobs)做不到"——本阶段正是把这个能力落到权重侧(FTPO)+解码侧(Sampler)。

### 1.5 GRPO + 生成式奖励模型:冲击"对白区分度"天花板的重武器

- **《Rewarding Creativity: A Human-Aligned Generative Reward Model for RL in Storytelling》**(Zhaoyan Li 等,**Alibaba**;2026-01)。GenRM 两阶段:① ~1400 条带推理链 demo(从 Gemini-2.5-Pro 蒸馏)SFT;② **GRPO** 在 ~4000 故事对(职业编剧标注+多模型共识)精炼,配 **entropy-based reward shaping**。维度含 narrative coherence / creative originality / emotional engagement / outline adherence / **character consistency**。数字:GenRM **68.3% 人类对齐**(优于 Bradley-Terry 54.1%、Gemini-2.5-Pro 60.0%、Claude-4-Sonnet 62.0%);用作奖励后故事生成 **72.4% 胜 SFT 基线、59.1% 胜 Gemini-2.5-Pro**。底座 Qwen2.5-7B/14B/32B(GenRM)、Qwen-72B(30B 故事 token 继续预训练)做生成。
  - https://arxiv.org/abs/2601.07149 `[accessed:2026-05-30]`(exists=true)
- **《DPWriter: RL with Diverse Planning Branching》**(Qian Cao, Yahui Liu, Wei Bi 等,**Renmin University + Kuaishou**;2026-01)。建在 **GRPO** 上:规划阶段分叉 K=32 多样计划 + **group-aware 多样性贡献奖励**(独特 n-gram),奖励 = (1−λ)·质量 + λ·质量·多样性,λ=0.6,**质量过阈才给多样性奖励防坍缩**。数字:WritingBench(Qwen3-4B)质量 6.43 vs GRPO 6.32,嵌入多样性 +15%、n-gram +9.9%。语料 43K(含中文 COIG-Writer)。英文论文但 **Qwen3-4B-Base 底座 + 含中文语料,迁移性好**。
  - https://arxiv.org/abs/2601.09609 `[accessed:2026-05-30]`(exists=true)
- **《RLMR: RL with Mixed Rewards for Creative Writing》**(Jianxing Liao 等;2025-08):**主观写作质量奖励模型 + 客观约束验证模型动态混合**,约束权重按组内写作质量动态调整(违约样本在 GRPO 拿负优势)。数字:IFEval 83.36%→86.65%,WriteEval 人工专家 **72.75% 胜率**;跨 8B–72B 验证。**对你"既要文笔又要守人物卡/章节字数约束"高度对口。**
  - https://arxiv.org/abs/2508.18642 `[accessed:2026-05-30]`(exists=true)
  - **身份纠错**:findings 初稿标注"(AAAI)"会议**错误**——验真确认它是 **arXiv 论文(2025-08),并非 AAAI 录用**。AAAI 标签已剔除。
- 可选解码侧叠加(与微调正交,做推理期多样性兜底):《Avoidance Decoding》(EMNLP 2025,https://arxiv.org/pdf/2509.02170)、《Conformative Decoding》(https://arxiv.org/pdf/2507.20956)、《Diversity via DPP》(https://www.arxiv.org/pdf/2509.04784)、《CD-RLHF》(https://arxiv.org/pdf/2501.11463),均 `[accessed:2026-05-30]` exists=true。

**对"角色对白区分度"的判断(贯穿地基锚点 R15):**

- 这是**唯一能真正突破对白趋同结构性天花板的训练路径**。对白区分度**主观、无单一 ground truth**,SFT/DPO 只能模仿数据里"恰好存在"的区分度,**只有"奖励模型 + RL"能直接优化它**。
- **配方建议**:训一个**中文"角色对白区分度"专项 GenRM**(输入两角色对白 → 奖励 = 文风/用词/句式可区分度 + 人物画像一致性),用 **GRPO** 优化 writer。复用 GenRM 的"带推理链 + entropy shaping"、DPWriter 的"规划分叉 + 分支多样性奖励"、RLMR 的"混合可验证约束(守人物卡/字数)"。
- ⚠️ **成本/风险最高**:GRPO 需在线采样 + 奖励模型同驻,显存与时间数倍于前三阶段,有 reward hacking / 坍缩风险(需 entropy shaping + 多样性约束 + 质量阈控)。**放管线最后**,但**架构第一天就要为它预留数据格式**(成对角色对白、人物卡 JSON、章节约束)——这正是"一步到位做对、不留迁移债"。

**与地基锚点 R15 的对齐(重要,避免在错引地基上过度自建):**

- R15 已纠正:用户记忆里"纯 prompt 对白区分度有天花板"的关键论据 **arXiv 2510.24677(RPNA)是张冠李戴**——它实为《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》,讲医疗 LLM 角色 prompt 神经元消融,与小说对白区分度**毫无关系**。**本终稿不以该错引为地基。**
- R15 的真实结论:对白区分度天花板在"纯 prompt、不挑底座、不做角色级工程"的弱设定下**大概率真实**,但**没有任何干净实证证明它硬到"必须自建/微调才能跨过"**;正解是 **底座选型 + 角色级 prompt 工程 + 离线 stylometric 评测闭环**,**只有当这三者跑满仍达不到目标、且离线评测证明 gap 来自模型本身,才上阶段 D 的 LoRA/GRPO**。
- 因此**阶段 D 在本管线里是"有数据支撑的可触发升级项",不是地基期的无条件必选**。它仍写进管线、架构预留数据口,但**触发条件是"(i)底座选型 +(ii)角色卡/style-sheet/逐角色生成/few-shot 对白 +(iii)Burrows' Delta / 引文归属分类器离线评分 三者跑满仍不达标"**。这既不是"先凑合后换"(它本就是最优架构的一层),也不是为一条错引约束在地基期背整套训练。**离线评测武器现成可用**:《From stage to page》(https://arxiv.org/abs/2301.05659)、《Distinguishing Fictional Voices》(https://arxiv.org/pdf/2401.16968),CMU 模型级风格 97% 可辨。

---

## 2. 开源底座可训性排名(中文网文,贯穿 R11)

**WebNovelBench**(arXiv 2505.14818,EACL 2026 Findings;4000+ 中文网文 synopsis→story,8 维含**第 4 维"对白区分度"权重 0.1171、第 5 维"人物一致性"权重 0.1377(最高)、"文学手法"0.1304**,DeepSeek-V3 当裁判):**榜首 Qwen3-235B-A22B(5.21 norm)**,其后 DeepSeek-R1、Gemini-2.5-Pro。结论:开源已逼近闭源,gap 集中在创意/文风维度(= 微调要补的,= 你三个最痛的维度)。

| 底座 | 判断 | 来源 `[accessed:2026-05-30]` |
|---|---|---|
| **Qwen3(首选)** | ✅ **生产首选**。官方有 `-Base` 检查点(Qwen3-30B-A3B-Base、32B 等),**Apache 2.0** 商用无忧,36T token / 119 语言,中文榜首,工具链(Unsloth / LLaMA-Factory)最成熟。**主力 Qwen3-32B-Base(单卡 80G bf16 LoRA)**;追极致 Qwen3-235B-A22B(22B 激活,降推理成本)。 | huggingface.co/Qwen/Qwen3-32B、Qwen3-30B-A3B-Base;arxiv 2505.09388;github.com/QwenLM/Qwen3 |
| **GLM-4.6 / 4.7** | ✅ 极致质量备选。355B MoE(32B 激活)、200K 上下文、**MIT**、Z.ai,明确"role-play 更自然",HF 上已有 16 个 finetune。8×H100 / 4×H200 可跑;只能高秩 LoRA。 | huggingface.co/zai-org/GLM-4.6 |
| **DeepSeek-V3.x** | ⚠️ 671B MoE,**全参不现实**;MIT、中文强。更适合做**教师蒸馏数据源**而非直接微调底座。 | huggingface.co/deepseek-ai/DeepSeek-V3.1 |
| **Yi-34B / InternLM** | ⚠️ 可训但创意写作生态、更新已不及 Qwen3,**不推荐作 2026 新建生产底座**。 | huggingface.co/01-ai/Yi-34B |
| **Weaver(方法论参考)** | 📖 模型本身偏老(2024-01),但**方法论强烈借鉴**:首创 **instruction backtranslation(从高质量人类文本反推指令)+ Constitutional DPO**,诊断出"专业写作语料 < 0.1% 导致 GPT 腔扁平"。 | arxiv 2401.17268;github.com/aiwaves-cn/weaver |

**Qwen3 微调关键工程坑(贯穿 R11):**

- Qwen3 是 **hybrid thinking/non-thinking**。**创意写作要关 thinking**(`enable_thinking=False`,思维链打断散文流畅度)。注:此为社区经验,缺对照实验论文 → `[no-source-found:thinking 干扰文笔的对照实验]`,建议自做消融。
- 官方创意写作评测用 **presence_penalty=1.5 / deviation 采样** 增多样性,可作解码期基线。
- 微调**用 `-Base` 学文风**(避开 instruct 已有的扁平化先验),或在 instruct 上做 deviation-DPO 纠偏。这与 1.2 的同源实验一致:instruct 检查点已被后训练"扁平化"过,从 Base 起更干净。

**与 R11 的硬对齐**:R11 已用 WebNovelBench / EQ-Bench v3 / hskstory 证明"文笔已追平甚至中文反超 → 选闭源 A 的唯一旧理由消失",且"治 slop / 对白必须碰 logits 与权重,而 Kimi 官方 API 连 logit_bias 都不给 → 只有自托管开源 B 能生产级绝不妥协"。**本 R12 管线就是 B 路线的训练侧落地**——闭源 API 在本系统里仅作蒸馏教师(如 GenRM demo 蒸馏自 Gemini-2.5-Pro 的做法)与质量天花板对照,**绝不产出最终散文**。

---

## 3. Top 推荐:生产级一步到位四阶段配方(完整版)

主力 **Qwen3-32B-Base**;追极致 Qwen3-235B-A22B / GLM-4.6。**从第一天就按此架构,不留迁移债。**

**阶段 A — 风格 SFT**
- 数据:高质量人类中文网文,精筛去 slop、按文风分层。规模:风格适配 1–5 万优质样本起;注入式继续预训练需亿级 token。
- 方法:**bf16 高秩 LoRA(rank 128–256,含 MLP / all-modules)**;若要改底座 AI 腔(继续预训练档)则上**全参**。
- 增益:借 Weaver 的 instruction backtranslation 造指令;参考 GEM(ICLR 2025)在 SFT 阶段即加多样性约束,**不把"防扁平"全压到偏好层**。

**阶段 B — 多样性保持偏好优化**
- 方法:**deviation-DPO / DORPO**(2503.17126 思想),**严禁裸 DPO**。
- 数据:成对网文片段;长期接 **KTO 式读者反馈飞轮**(点赞/弃读 → 非配对二元信号)。
- 护栏:把 Narrative Flattening 三指标(主题运动 CV / 情感分布 / StyleDistance MMD + 跨故事方差)接入评测,做回归监控。

**阶段 C — 中文 slop 外科手术**
- 方法:**自建中文 slop 词典**(slop-forensics 改造 + 中文人类语料 profile),`auto-antislop` 跑 **FTPO**(`finetune_mode:"ftpo"`)。
- 兜底:推理期叠 **Antislop Sampler**(antislop-vllm),与微调正交,生产双保险。
- 这一步把 R11 "必须碰 raw logits"的能力同时落到权重侧(FTPO)与解码侧(Sampler)。

**阶段 D — 破天花板(可触发升级项,非地基无条件必选)**
- 方法:训"对白区分度 + 人物一致性"中文 **GenRM**(带推理链 + entropy shaping + RLMR 式混合可验证约束),**GRPO** 优化 writer,借 DPWriter 分支多样性。
- 触发条件(贯穿 R15):**仅当底座选型 + 角色级 prompt 工程 + 离线 stylometric 评测(Burrows' Delta / 引文归属分类器)三者跑满仍不达标,且离线评测证明 gap 来自模型本身**,才启动。
- 架构动作:**第一天就预留数据格式**(成对角色对白、人物卡 JSON、章节字数/设定约束),使 D 随时可触发而无需返工。

**为何是"最优而非凑合"**:四阶段正交互补——A 学文风、B 防扁平、C 杀 slop、D 破对白天花板;每一步都选不留债的那条路(deviation-DPO 取代裸 DPO、FTPO 取代 token-ban、GenRM-GRPO 取代纯模仿、bf16 取代 QLoRA)。

---

## 4. 成本 / 风险

**成本(量级;精确 GPU-hour 多为 `[no-source-found]`):**

| 阶段 | 量级 | 备注 |
|---|---|---|
| A LoRA-SFT(Qwen3-32B) | 单卡 80G,数小时–1 天/轮,**最低** | 全参约 8–16× LoRA |
| B deviation-DPO/DORPO | 与 SFT 同量级 | 参考 DiversityTuning 6×H100 / 42 万对 |
| C FTPO | **轻量**(单 GPU、数千 token 级偏好样本) | **中文 slop 词典构造是主要一次性人力成本** |
| D GRPO + GenRM | **最贵**(在线采样 + reward model 同驻,数倍时间/显存) | 放最后,触发式启动 |

自托管 TCO(引自 R11):约 **10B tokens/月** 时自托管 break-even;8×H200 摊销 ≈ $7,974–10,224/月 vs 云租 $20,440–35,040/月,约 14 个月回本。微调单次 $10–500。

**风险:**

1. **数据是真瓶颈**——所有方法吃高质量中文网文偏好/区分度数据,**版权 + 清洗是最大隐性成本**(参考番茄/字节因"AI 训练协议"引发作者抵制的前车之鉴)。
2. **中文 slop 词典 / 奖励模型必须自建**——英文资源(Antislop 默认词典、GenRM 英文标注)不能直接用。
3. **GRPO 不稳定**——reward hacking / 坍缩;需 entropy shaping + 多样性约束 + 质量阈控(DPWriter 的"质量过阈才给多样性奖励"是关键防坍缩技巧)。
4. **核心 2026 论文全文未逐字复核**——Narrative Flattening / DPWriter / GenRM 的精确机制本轮 WebFetch 降级未拉到全 PDF,落地前亲验。
5. **LoRA "学不进底座 AI 腔"** → 需升秩或转全参/继续预训练(1.1 已界定档位)。

---

## 5. Open Questions(建议亲验)

1. **FTPO 90% slop 削减是否迁移到中文**——论文只测英文 Gemma/Mistral/Llama,**必须自建中文基线复测**。
2. **deviation-DPO(2503.17126)精确 loss 与中文质量/多样性数值**——repo 已开源(mj-storytelling/DiversityTuning),值得复现。
3. **GenRM(2601.07149)能否改造成中文"角色对白区分度"专项奖励模型**——破核心天花板的关键,值得单独立项。
4. **EQ-Bench Longform / WebNovelBench 逐模型最新排行**——动态页未能稳定抓取(R11 亦记录 longform 页 "TABLE NOT POPULATED"),建议手动看 eqbench.com 确认 Qwen3 / GLM-4.6 实时位次。
5. **Qwen3 thinking 模式对文笔的影响**——目前只有社区经验,缺对照实验,建议自做消融。
6. **"先 SFT 再纠偏" vs "一开始就 deviation-DPO" 在中文上的实测差距**——Narrative Flattening 证明 SFT 已启动扁平化,但能否被后续 deviation-DPO 完全逆转值得验证(决定阶段 A 要不要也加多样性约束;GEM/ICLR 2025 倾向"A 阶段就要加")。
7. **阶段 D 触发阈值的量化定义**——用 Burrows' Delta / 引文归属分类器给生成对白打"角色间可分性"分,设定一个生产可接受阈值,以数据决定是否启动 GRPO。

---

## 身份纠错与引用验真说明

**剔除/纠正的 claim(均为身份/标签错误,论文本体 exists=true):**

- **RLMR(arXiv 2508.18642)**:findings 初稿标注的 **"(AAAI)" 会议归属错误** → 实为 arXiv 论文(2025-08),非 AAAI 录用。AAAI 标签已剔除。
- **DiversityTuning / deviation-DPO(arXiv 2503.17126)**:findings 初稿曾误标作者机构为 **Midjourney** → arxiv 页面未列机构,已改为**不确认机构**(repo 命名 mj-storytelling 仅作线索)。
- **FTPO 测试模型家族**:findings 初稿曾误写含 **Qwen** → 实为 **Gemma-3-12B / Mistral-Small-3.2 / Llama-3.3-70B**,已更正。
- **GEM / Preserving Diversity(ICLR 2025)**:原 OpenReview 链接 forum-id 错误 → 正确为 `NQEe7B7bSw`,已更正。

**未发现 `exists=false` 的引用**——本轮 28 条引用验真**全部 exists=true**,故无"凭空捏造的论文/仓库"需整条删除;以上 4 处为"论文真实但某属性虚构"的标签纠正。

**`[no-source-found]` 清单**:Sparse-Memory 精确百分比、Narrative Flattening 全文逐字数字、Qwen3 thinking 干扰文笔对照实验、各阶段精确 GPU-hour。
