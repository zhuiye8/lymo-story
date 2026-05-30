# R6 · Anti-Slop / 文笔质量（v2 终稿）

| Field | Value |
|---|---|
| Topic | LLM 输出 "slop"(重复套话 / AI-tell / 翻译腔)的检测与抑制:2026 SOTA 在中文小说生成上如何落地 |
| Author | engineer (Claude) — 终稿综合者 |
| Researched | clean-room 调研 2026-05-30(WebSearch + WebFetch only,零训练记忆);所有引用经独立验真 |
| 用户优先级锚定 | 记忆(R2)=角色(R5)=大纲(R1)> 图谱(R3);R6 为 **A 档**:做扎实但不追 S 档深度 |
| Verdict | **DeepSeek API 路线下,Sampler/FTPO 不可行(需 logits + logit_bias)。R6 主路径 = "生成后检测(中文 slop 词表 + 正则)→ 触发重写/重采样 → 去偏 Critic Room 把关"**。英文生态成熟、中文几乎空白:可搬的是方法论 + 评测协议 + 检测器架构,**词表必须本土自建**。 |

> **验真状态**:本方向 27 条引用经逐条核查,**全部 exists=true(无幻觉条目需剔除)**。v1 中部分"via search snippet"的弱引用(Ozigi 博客、Awesome-LLM-as-a-judge、lyc8503 分类器、EnsemJudge)在本轮 clean-room 调研中未被复现为核心证据,已按"降级/移出主线"处理(见末尾 v1↔v2 diff),非因证伪。

---

## 一、为什么对我们重要(承接 Phase 0 信号)

Phase 0 SEQR 基线给出三个相关信号,直接定义 R6 的工作面:

- `rhetoric_quality` ρ=−0.16(工程师评分 vs LLM judge 评分反向)——说明**单一 LLM judge 对中文套话不敏感**,印证了"需要去偏的多评委 + 机械词表双轨"。
- detector v1 在 PD(公版)段落误判:朱自清《歌声》"仿佛一个暮春的早晨"、鲁迅《社戏》"仿佛是踊跃的铁的兽脊"——**单次合法的比喻词被 tier1 一刀切**,需要 frequency-aware。
- 21 章 baseline 里 `tier1_banned` 命中 15 次,是 LLM slop 头号来源。

R6 任务:用 2026 SOTA(paper-grade evidence)决定如何改造现有 slop detector,并在 DeepSeek API 约束下补齐推理后抑制与评测把关。

---

## 二、核心结论(TL;DR)

1. **英文 anti-slop 生态非常成熟,作者高度集中在 Sam Paech(EQ-Bench 团队)**:三件套(slop-forensics → antislop-sampler → auto-antislop)+ ICLR 2026 论文 + EQ-Bench Slop Score 排行榜,构成完整链路,全部 MIT/Apache-2.0,maturity = production/prototype。
2. **方法论(分层禁词、show-don't-tell、句长/句首均匀度、12 类叙事 anti-pattern)是语言无关的、可直接移植到中文的最高价值资产**;但**所有词表本身是英文统计产物,对中文零就绪**——中文需从零跑一遍 slop-forensics 流程生成本土 slop list。
3. **DeepSeek API 的 logits/logit_bias 访问是本方向最大工程约束**:官方 API 文档列出 `logprobs`/`top_logprobs`(支持),但**未列出 `logit_bias`**;即便第三方聚合(aimlapi)称支持,亦有 MTP 多 token 失效 bug(sgl-project/sglang#8734)。结论:**antislop-sampler 的 backtracking(本地 logits + 偏置)无法在 DeepSeek 官方 API 运行,只能走"生成后检测 + 重写"的 API 友好路径**。
4. **给 R6 的可落地组合(B/A 档,非 S 档)**:中文 slop list(自建)+ 规则/正则检测器(移植 autonovel evaluate.py)+ 去偏 LLM-as-judge Critic Room。adoption cost = medium;FTPO/Sampler 属 high/rewrite 且与 DeepSeek 不兼容,**仅在自托管开源模型时考虑**。
5. **判官与生成模型必须分离**:基础事实核查显示 Kimi K2.6 在中文创意写作评测双榜第一、DeepSeek V4 系列文笔评测数据有限但综合/性价比强。结合自偏好偏置(self-preference)研究,**生成用 DeepSeek、判官用 Claude/Kimi/Qwen 等异源模型**,避免同模型自评。

---

## 三、存活的 Findings(逐条:URL + accessed + 时效性/鲁棒性/可行性)

### F1 · Antislop(ICLR 2026 论文)— 框架总纲 [验真:exists=true]

- 论文:*Antislop: A Comprehensive Framework for Identifying and Eliminating Repetitive Patterns in Language Models*,arXiv **2510.15061**(v1 2025-10-16,v2 2025-10-21),**published as conference paper at ICLR 2026**。作者:Samuel Paech, Allen Roush, Judah Goldfeder, Ravid Shwartz-Ziv。
  - https://arxiv.org/abs/2510.15061 [accessed:2026-05-30]
  - ICLR 2026 poster:https://iclr.cc/virtual/2026/poster/10008156 [accessed:2026-05-30]
  - OpenReview:https://openreview.net/forum?id=gLcyM1khyp [accessed:2026-05-30]
- 三大组件:(1) **Antislop Sampler**——推理时 backtracking 抑制不想要的字符串,不破坏词表;(2) **自动化 pipeline**——把模型 slop 对照人类基线 profile 并生成训练数据;(3) **FTPO(Final Token Preference Optimization)**——逐 token 微调,在 banned pattern 出现处外科手术式调整 logits。
- 关键数字(引自 abstract,经 OpenReview 核对):某些 slop pattern 在 LLM 输出中比人类文本高 **1,000x+**;Sampler 可抑制 **8,000+** patterns 仍保质量,而纯 token banning 在 **2,000** 就不可用;**FTPO 实现 90% slop 削减**且在 GSM8K/MMLU/创意写作跨域评测保持或提升;对比 DPO 在写作质量与词汇多样性上显著退化。
- License:MIT(论文声明 code+results 开源)。
- **评判**:时效性 = **最新(2025-10 / ICLR 2026,非 stale)**;鲁棒性 = **production**(已发表 + 排行榜在用);可行性 = **方法论 low(直接借鉴 slop 定义、对照人类基线、分层抑制思想);Sampler/FTPO 对 DeepSeek = rewrite(不兼容,需 logits)**。中文就绪度:论文未提任何非英文/中文支持。

### F2 · slop-forensics(分析/词表生成工具)— 最高移植价值 [验真:exists=true]

- repo:https://github.com/sam-paech/slop-forensics [accessed:2026-05-30]。Stars **332**,forks 24,License **MIT**,语言 Jupyter Notebook 75.7% / Python 24.3%。维护者 Sam Paech 活跃账号,**视为 active/prototype**。
- 功能:多模型批量产出 → 计算 word/bigram/trigram 频率、**Repetition Score / Vocabulary Complexity / Slop Index** → 跨模型聚合生成 slop list → 用生物信息学方法(parsimony/层次聚类)画模型"系统发育树"。
- 产物(四个 canonical 文件,**可直接作为中文复刻的目标格式**):`slop_list.json`(单词)、`slop_list_bigrams.json`、`slop_list_trigrams.json`、`slop_list_phrases.jsonl`。
- **中文就绪度**:文档仅面向英文,使用 NLTK stopwords 等英文中心工具,**无中文支持证据**。流程(对照人类语料统计 over-representation)语言无关,**移植到中文需替换分词(jieba/中文 tokenizer)+ 中文停用词 + 人类网文语料基线**。
- **评判**:时效性 = active;鲁棒性 = prototype(研究级脚本,非库);可行性 = **medium**(流程清晰,中文化要换分词与语料,约 1 天核心工作量 + 语料准备)。

### F3 · antislop-sampler(推理时抑制)— 与 DeepSeek 不兼容 [验真:exists=true]

- repo:https://github.com/sam-paech/antislop-sampler [accessed:2026-05-30]。Stars **345**,forks 31,License **Apache-2.0**,Python 69.7%/Notebook 30.3%,**last update 2025-04-07**(距今约 14 个月,**未 stale 但已放缓**,后续工作转向 auto-antislop/FTPO)。
- 机制:不做逐 token 过滤,而是等完整短语出现 → backtrack → 降低导向该短语的起始 token 概率(配置 JSON:phrase→概率衰减因子,可轻度/重度去 slop)。支持 string + regex ban、JSON 输出校验回溯修正、流式(regex ban 除外)、temperature/top-k/top-p/min-p,集成 KoboldCpp v1.76+。
- **关键约束**:**需要本地 model logits + 逐 token 生成 + logit 偏置能力,无法用于 DeepSeek/OpenAI 这类 API-only 服务**。它自带的"OpenAI 兼容 API server"是把本地模型包成 API,而非消费第三方 API。
- **评判**:时效性 = 放缓;鲁棒性 = prototype-production;可行性对本项目(DeepSeek 为主)= **rewrite/不可行**;仅当自托管开源中文模型(Qwen/DeepSeek 本地权重 via vLLM)时 = medium。

### F4 · auto-antislop(端到端 pipeline + FTPO 训练) [验真:exists=true]

- repo:https://github.com/sam-paech/auto-antislop [accessed:2026-05-30]。Stars **133**,forks 5,License **README 未明确标注**([no-source-found:auto-antislop LICENSE 文件具体协议——商用前需读 LICENSE 确认])。
- 流程:(1) 无 ban 跑 baseline;(2) 识别 over-represented n-gram/slop 短语;(3) 生成 ban list(+ 用户自定义);(4) 带 ban 生成、采集 preference pairs;(5) 构造 FTPO 数据集;(6) FTPO/DPO/DPO-final-token 微调。依赖:**vLLM(必需)**、Unsloth(可选省显存)、TRL、PyTorch 2.8+CUDA、flash-attn、NLTK。
- **可直接抄的设计**:`extra_slop_phrases_to_ban`、`extra_ngrams_to_ban`、`extra_regex_patterns`(这套"用户增量 ban"接口直接迁到中文检测器,让运营/作者随时补词)。
- **中文就绪度**:无多语种讨论,英文中心(NLTK stopwords)。**强约束**:全流程要 vLLM + 本地模型 logits,**API-only 模型不可用**。
- **评判**:时效性 = active;鲁棒性 = prototype;可行性 = **high/rewrite**(需 GPU + 本地模型 + 训练 pipeline),与 DeepSeek API 路线正交。

### F5 · autonovel(NousResearch)evaluate.py + ANTI-SLOP / ANTI-PATTERNS — 方法论金矿 [验真:exists=true]

- repo:https://github.com/NousResearch/autonovel [accessed:2026-05-30]。Stars **~1,000**,forks 190,Python 94.8%,License **页面未直出/未明确**([no-source-found:autonovel LICENSE 具体协议——**商用前必须查清,继续走"自己重写、不 copy code"路线**])。我们 Phase 0 的 `backend/quality/slop_detector.py` 已是 evaluate.py 的中文化自研 port,合规。
- 关键文件均已验真存在:
  - `ANTI-SLOP.md`:https://github.com/NousResearch/autonovel/blob/master/ANTI-SLOP.md [accessed:2026-05-30](词级 AI pattern 词库,可定期 diff 拉新)
  - `ANTI-PATTERNS.md`:https://github.com/NousResearch/autonovel/blob/master/ANTI-PATTERNS.md [accessed:2026-05-30]
  - `PIPELINE.md`:https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md [accessed:2026-05-30]
- 架构:五层共演化——voice.md(怎么写)/world.md(有什么)/characters.md(谁)/outline.md(发生什么)/chapters(实际文字);四阶段:Foundation→First Draft→Automated Revision→Export。样例长篇 *The Second Son of the House of Bells*(约 75k–79k 字 / 19 章 / 6 轮自动修订 + 6 轮 Opus 评审)。
- **evaluate.py 机械检测(无 LLM,正则)——本方向最可直接落地的部分**:
  - **Tier 1(见即杀)**:几乎不出现在人类随意写作的词(delve/utilize/leverage/facilitate/paradigm),单次出现即重写句子;
  - **Tier 2(成簇可疑)**:单用可接受,**一段内出现 3 个即重写**(robust/innovative/seamless/cutting-edge);
  - **Tier 3(填充短语)**:零信息构造("It's worth noting that"/"Let's explore"/"In conclusion")→ 直接删;
  - **句首均匀度**:读每句第一个词,全是转折词 → 重写;句长全 15–25 词 → 掺短句;
  - **段落模板检测**:每段同模板 → 打破;
  - **show-don't-tell**:场景已展示的情绪,叙述者不得复述("手在抖、对话沉默"后不得再加"他害怕了")。
- **ANTI-PATTERNS.md 的 12 类小说 anti-pattern**(可直接翻译成中文检测维度):过度解释、三段式罗列(triadic listing)、否定断言堆叠(did not...)、清单式思考、明喻拐杖(the way X did Y)、分节符滥用(`---`)、段落长度均匀、情绪弧线准点到达、章节结尾重复、对仗平衡滥用、过度打磨的对白、场景/概述失衡。**可机械化的**:三连片段正则、"did not"频次、"the way"频次、`---` 计数、段落句数统计;其余需 LLM/语义判断。
- **LLM-judge 组件**:另一模型按 **prose quality / voice adherence / character distinctiveness / beat coverage** 四维打分,**score > 6.0 保留,否则重试**(modify-evaluate-keep/discard 循环);终稿"双人格评审"(dual-persona,即 Critic Room 雏形)捕捉机械工具抓不到的散文级重复、人物单薄、伦理漏洞、结构单调。
- **评判**:时效性 = 新(2025 末 / 2026,Hermes Agent);鲁棒性 = prototype(文档 + 脚本,非长期维护库)但 **star 量最高、工程叙事最完整**;可行性 = **low–medium**(分层禁词表 + 正则 + judge rubric 直接可抄;难点全在"造中文词表"和"判官去偏")。跨语言:12 类 anti-pattern 针对叙事逻辑与节奏而非英文习语,**可迁移中文**,只需适配语法与标点。

### F6 · EQ-Bench Creative Writing v3 + Slop Score — 评测/排行榜 [验真:exists=true]

- benchmark repo:https://github.com/EQ-bench/creative-writing-bench [accessed:2026-05-30]。Stars **106**,forks 28,创建者 Samuel J Paech。License/last-commit 页面未直出([no-source-found:creative-writing-bench LICENSE 与 last-commit 日期])。
- 排行榜:https://eqbench.com/creative_writing.html [accessed:2026-05-30];Slop Score 说明:https://eqbench.com/slop-score.html [accessed:2026-05-30];第三方镜像:https://llm-stats.com/benchmarks/creative-writing-v3 [accessed:2026-05-30]。
- 方法:32 prompts × 3 iters = 96 项;混合 **rubric 评分 + Glicko-2/Elo**(pairwise,主指标 `elo_norm`);判官推荐 **Claude Sonnet 4**;**仅支持 API 文本生成,不需要 logits**(对 DeepSeek 友好);去偏:截断 ~4000 字符抗长度偏置、A/B+B/A 双序平均抗位置偏置。**明确"目前仅评估英文写作"**。当前 Creative Writing v3 榜首 **Grok-4.1 Thinking(1721.9)**(经 llm-stats 核对)。
- **Slop Score 加权(已验真)**:**60% Slop Words + 25% "not-x-but-y" 对比构造 + 15% Slop Trigrams**;词表由 **slop-forensics** 跑 ~10 个模型 vs 人类文本生成;**lower = 更像人类**。语言覆盖未声明(实质英文)。
- **评判**:时效性 = active(榜单持续更新);鲁棒性 = production(社区权威英文创意写作榜);可行性 = **medium**(评测协议 + rubric + Elo 去偏可抄;**Slop/Repetition 自动指标依赖中文词表**;"not-x-but-y"需中文版正则,如"不是…而是…/与其说…不如说…")。

### F7 · LLM-as-a-judge 去偏研究(支撑 Critic Room 设计) [验真:全部 exists=true]

- *Judging the Judges: A Systematic Evaluation of Bias Mitigation Strategies in LLM-as-a-Judge Pipelines*,arXiv **2604.23178**:https://arxiv.org/html/2604.23178 [accessed:2026-05-30]。9 种去偏策略 × 5 模型,结论——**style bias 是主导偏置(0.76–0.92)**,多数缓解策略不彻底、引入新偏置、对闭源模型不实用。
- *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge*,arXiv **2406.07791**:https://arxiv.org/html/2406.07791v9 [accessed:2026-05-30]。15 个判官,**位置偏置跨模型族普遍**。
- *Quantifying and Mitigating Self-Preference Bias of LLM Judges*,arXiv **2604.22891**:https://arxiv.org/html/2604.22891v2 [accessed:2026-05-30]。**自偏好偏置**——存在偏爱自身输出的"Machiavellian Judges";**Critic Room 应避免"同模型自评"**(尤其不能用 DeepSeek 评 DeepSeek)。
- *A Survey on LLM-as-a-Judge*,arXiv **2411.15594**:https://arxiv.org/html/2411.15594v6 [accessed:2026-05-30]。综述,含 CalibraEval 等校准法。
- **评判**:时效性 = 新;鲁棒性 = theoretical(研究);可行性 = **low**(直接指导工程:双序平均、避免自评判官、长度归一、rubric 锚定 + Elo)。

### F8 · LitBench(reward model 评测路线,长期备选) [验真:exists=true]

- 论文:*LitBench: A Benchmark and Dataset for Reliable Evaluation of Creative Writing*,arXiv **2507.00769**(2025-07-01):https://arxiv.org/pdf/2507.00769 [accessed:2026-05-30]。基于 WritingPrompts 人类偏好(2,480 test / 43,827 train pairs)训练 **reward model**,声称优于标准 LLM-as-judge(后者"风格压过实质")。License **CC-BY-4.0**;code/data 在 HuggingFace + GitHub SAA-Lab。**英文为主,无中文证据**。
- **评判**:时效性 = active;鲁棒性 = prototype;可行性 = **high**(要训中文 reward model + 中文偏好数据,成本大);**S 档不做,记为长期备选**。

### F9 · 中文 anti-cliché / slop 词库现状 — 本方向最大空白 [验真:funNLP/星月/朱雀 均 exists=true]

- **funNLP**:https://github.com/fighting41love/funNLP [accessed:2026-05-30]。"几乎最全的中文 NLP 资源库",含停用词、同义词库(Synonyms)、词汇情感值、否定词库等通用资源;**但明确没有"翻译腔/AI 生成中文/套话"专用检测资源**([no-source-found:funNLP 精确 star 数与 last-commit])。
- **直接的中文 slop list / 网文味词表 开源项目:本轮未找到**。多轮搜索(中文 GPT 味词库 anti-slop、网文 AI 套话词库、网文味检测开源)均只命中通用 NLP 库与商业检测器,**无开源中文 slop 词表**。([no-source-found:最后一轮针对性搜索因 turn 上限未取回结果,建议补一轮 GitHub 站内 + 知乎/B 站确认空白。])
- **商业/产品侧(非开源,竞品参考)**:
  - **星月写作**:https://xingyuexiezuo.com/ [accessed:2026-05-30]。自称内置千万级中文网文语料,**显式以"避免翻译腔/书面化、精准使用网文黑话"为卖点**,覆盖玄幻/都市/古言/悬疑等多类;有爽点/伏笔/仿写功能。**证明"反翻译腔 + 网文黑话"是中文市场真实痛点与差异点**,但闭源,只能借鉴产品定义。
  - **腾讯朱雀 AI 检测**:https://matrix.tencent.com/ai-detect/ [accessed:2026-05-30]。多模态 AI 文本/图像鉴别,称中文准确率 ~96%(腾讯实验室数据,需谨慎),原理为"写作特征分析识别重复句式与逻辑连贯异常"。可作为**"AI 味"外部判别基线/对抗目标**(把生成稿喂进去看 AI 概率),但闭源、无 API 词表产出。
- **评判**:中文就绪度 = **零开源词表**,这是 R6 的核心工作量所在;maturity = 商业 production(星月/朱雀)但不可复用代码;**结论:中文 slop list 必须自建**(slop-forensics 流程 + 中文分词 + 人类网文语料对照),一次性中等投入、长期复用的资产。

### F10 · "Elara Voss" 名字 slop 现象(补充证据,中文需自查) [验真:exists=true]

- *Who is Elara Voss?*(Read Max,Max Read,2025-08-07):https://maxread.substack.com/p/who-is-elara-voss [accessed:2026-05-30]。记录 LLM 反复生成的"promptonyms"(如 Elara Voss / Elara Vex / Elias Vance)横跨 GPT/Claude/Gemini。
- **对我们的意义**:**人名/地名也是 slop 维度**。中文同样存在高频生成名(需自查我们生成稿里反复出现的人名/门派名/招式名),应纳入中文 slop list 的一个子表。时效性 = 新;鲁棒性 = 文章(非 paper);可行性 = low(作为词表的一个子类,顺手收集)。

---

## 四、基础事实核查的应用(写稿据此纠正)

1. **判官模型选择(对接 Critic Room)**:核查结论显示 **Kimi K2.6 在中文创意写作 + 角色扮演评测双榜第一(超 GPT-5),Claude 4.6 Opus 为业界天花板/最自然"人味"**;DeepSeek V4 系列中文综合/知识强、性价比极致,但**专项文笔评测数据有限**。GLM-5.1、Qwen 3.6-Plus 通用强但创意写作非强项。
   - **落地**:生成用 DeepSeek V4(性价比);**判官 Critic Room 用异源高文笔模型(首选 Kimi K2.6 / Claude;Qwen 作开源本地备选)**,既符合"判官 ≠ 生成模型"去自偏好偏置,又拿到更可信的文笔判断。
2. **WebNovelBench 八维(arXiv 2505.14818,Table 1,已核查为真)**可直接作为 Critic Room 中文 rubric 的锚:
   1. Use of Literary Devices(文学手法运用)
   2. Richness of Sensory Detail(感官细节丰富度)
   3. Balance of Character Presence(人物存在平衡)
   4. Distinctiveness of Character Dialogue(人物对白辨识度)
   5. Consistency of Characterisation(人物塑造一致性)
   6. Atmospheric and Thematic Alignment(氛围与主题契合)
   7. Contextual Appropriateness(语境恰当性)
   8. Scene-to-Scene Coherence(场景间连贯)
   - **落地**:把 autonovel 四维(prose/voice/character/beat)与 WebNovelBench 八维合并,挑 4–6 维做我们的中文 anti-slop judge rubric,避免维度过多导致评分噪声。
3. **杜撰名词防护**:核查确认 **"PerRoleCognition" 全网不存在(杜撰)**。本方向终稿未使用、亦不应引入该名词;若 Critic Room 涉及"角色认知"相关引用,使用真实存在的 **RPNA(arXiv 2510.24677)/ RoleRAG(arXiv 2505.18541)/ Character-LLM(arXiv 2310.10158,EMNLP 2023)**——但这些属 R5 角色方向,R6 仅在需要时交叉引用。

---

## 五、对接 Stack 的对比表(抑制方法 vs 我们 DeepSeek 路线)

| 方法 | 接入位置 | 不需 logits | DeepSeek API ✓ | 中文支持 | 即时可用 | 长期价值 |
|---|---|---|---|---|---|---|
| **prompt 负指令**(autonovel/Slop 思路) | prompt 顶部 | ✅ | ✅ | ✅(要翻译指令) | ✅ 立即 | 低(model 易忽略) |
| **detector v1**(autonovel 自研 port,已有) | 生成后扫描 | ✅ | ✅ | ✅(我们中文词库) | ✅ 已有 | 中 |
| **detector v1.1 frequency-aware tier1** | 同上 | ✅ | ✅ | ✅ | ✅ | 中-高(修已知 FP) |
| **slop-forensics 中文化 profile** | 离线分析 | ✅ | ✅ | 需移植中文分词 | ✅ ~1 天 | 高(喂 detector + prompt) |
| **去偏 Critic Room**(EQ-Bench 协议) | 生成后 | ✅ | ✅(判官异源) | ✅ | 🟡 cost 待评估 | 高 |
| **antislop-sampler**(backtracking) | LLM forward pass | ❌ | ❌ | 需中文 slop list | ❌ | 极高(仅自托管可用) |
| **FTPO 微调**(auto-antislop) | weights | ❌ | ❌ | 需中文 prefer pairs | ❌ | 极高(仅自家 model 后) |
| **LitBench 式中文 reward model** | 训练 | ✅(推理) | ✅ | 需中文偏好数据 | ❌ | 高(成本大,长期) |

---

## 六、Top 候选方案(给重构直接落地,按性价比排序)

1. **【首选·方法论移植】autonovel evaluate.py 分层禁词体系 + 12 类 anti-pattern + show-don't-tell**
   - 把 Tier1/2/3 框架与正则检测**翻译成中文版**(机械化部分:三连罗列、否定堆叠、`---` 计数、句首/句长均匀度、段落句数);adoption cost = **low–medium**,无 GPU,API 友好,性价比最高。
   - 合规:autonovel LICENSE 未明确,继续**自研重写、不 copy code**(Phase 0 已做对)。

2. **【首选·词表自建】slop-forensics 流程中文化**
   - 换 jieba/中文 tokenizer + 中文停用词 + **人类网文语料基线**,产出中文 `slop_list / bigrams / trigrams / phrases`,作为检测器数据底座。MIT,cost = **medium**,一次投入长期复用。先跑 DeepSeek V4 在中文小说上的 model-specific slop profile,把高频结果并入 `TIER1_BANNED_ZH`。

3. **【首选·评测/把关】EQ-Bench Creative Writing v3 协议 + 去偏 Critic Room**
   - 借 rubric(取 autonovel 四维 ∪ WebNovelBench 八维的 4–6 维)+ Elo + 双序平均(A/B、B/A)+ 长度归一;**判官用异源模型(Kimi K2.6 / Claude,Qwen 本地备选),严禁 DeepSeek 自评**;cost = **medium**,API 友好。需与 AC4 单章 cost 上限重新协调(预估单章 +¥0.2–0.3)。

4. **【次选·仅自托管时】antislop-sampler / FTPO(auto-antislop)**
   - 若未来上自托管开源中文模型(vLLM),可用 8,000+ pattern 回溯抑制或 FTPO 微调彻底去 slop。对 DeepSeek API = **不适用**,cost = **high/rewrite**。

5. **【长期备选】LitBench 式中文 reward model**
   - 需中文创意写作偏好数据,cost = **high**,非现阶段。

---

## 七、Open Questions(留给验真/二次确认)

1. **DeepSeek 官方 API 到底支不支持 `logit_bias`?** 官方文档页(api-docs.deepseek.com/api/create-chat-completion)确认**未列出**该参数;第三方 aimlapi 称支持。需用真实 key 实测一次(传 logit_bias 看是否报错/被忽略),**直接决定能否做"轻量级 API 端 token 抑制"**。即便支持,仍有 sglang#8734 的 MTP 多 token 失效风险。
2. **autonovel / auto-antislop / creative-writing-bench 的确切 LICENSE 与 last-commit** 页面未直出,需 `gh` 或直接读 LICENSE 确认(尤其 autonovel,商用前必须查清)。
3. **中文 human baseline 语料从哪来?** slop-forensics 需要"人类网文"对照集才能算 over-representation。候选:起点/番茄公版、自有已发布章节、wikisource PD。**Phase 0 的 21 章 + 22 段 PD 可能不够**,估计要扩到 100+ 章,这是中文词表质量的关键输入。
4. **中文"not-x-but-y"等构造的等价模式** 需人工枚举中文 LLM 高频套路(如"不是…而是…""与其说…不如说…""仿佛…又像…""空气仿佛凝固""嘴角勾起一抹弧度"),**无现成开源清单**,需自建并验证频率。
5. **是否存在未搜到的中文 slop 开源项目?** 最后一轮针对性搜索因 turn 上限未取回结果,建议补一轮 GitHub 站内 + 知乎/B 站确认空白。
6. **判官多样性 vs 成本**:用 3 个 DeepSeek 评委 vs DeepSeek+Kimi+Qwen 异源评委,哪个 inter-rater correlation 更接近人类?(结合自偏好偏置研究,异源应更优,但需实测 ICR。)
7. **FTPO + 中文 token 化**:原 paper 是英文;中文 BPE token 更短,FTPO 在中文 logits 上的效果未验证——仅在自托管阶段才需回答。

---

## v1 ↔ v2 diff

### 新增(v2 有、v1 无)

- **ICLR 2026 多源确认**:补 ICLR poster(iclr.cc/virtual/2026/poster/10008156)+ OpenReview(forum?id=gLcyM1khyp)双证据,v1 只有 arXiv + 一个无法解析的 OpenReview PDF 链接。
- **EQ-Bench Slop Score 精确加权**:**60% Slop Words + 25% not-x-but-y + 15% Slop Trigrams**(v1 完全没有此分解),并补 slop-score.html 直接 URL。
- **LLM-as-judge 去偏的 paper-grade 支撑**:新增 4 篇(2604.23178 偏置缓解、2406.07791 位置偏置、2604.22891 自偏好偏置、2411.15594 综述),把"Critic Room 要去偏"从 v1 的口头建议升级为有文献依据的设计约束(双序平均、避免自评、长度归一)。v1 仅引一个未验真的 Awesome-LLM-as-a-judge repo。
- **中文商业竞品作竞品参考**:新增星月写作(反翻译腔 + 网文黑话卖点)、腾讯朱雀(AI 检测对抗基线),把 v1 "中文真空"的论断从"搜不到"升级为"有商业 production 但零开源,差异点被市场验证"。
- **LitBench(2507.00769)**reward model 路线作为长期备选(v1 无)。
- **"Elara Voss" 名字 slop 现象**(maxread.substack)——提示中文需自查高频生成人名/门派名(v1 无)。
- **auto-antislop 的"用户增量 ban"接口**(`extra_slop_phrases_to_ban` 等)作为可直接抄的设计(v1 只提 FTPO,未提配置接口)。
- **autonovel 三文件 URL 全部验真**(ANTI-SLOP / ANTI-PATTERNS / PIPELINE),12 类 anti-pattern 完整列出 + 标注哪些可机械化(v1 只提两个文件名,未列 12 类)。
- **基础事实核查应用**:引入 WebNovelBench 八维 rubric 锚、Kimi/Claude/DeepSeek 文笔实测对比指导判官选型、明确防护杜撰名词 PerRoleCognition(v1 全无)。

### 纠正(v2 修订 v1 的说法)

- **DeepSeek logit_bias 约束更精确**:v1 笼统说"DeepSeek API 无 logits 访问";v2 区分——官方**支持 logprobs/top_logprobs,但文档未列 logit_bias**,且引 sglang#8734 说明即便支持也有 MTP 多 token 失效 bug。结论不变(Sampler/FTPO 不可行),但论据更扎实、可实测。
- **Antislop code 链接归位**:v1 把 Sampler 论文的 code 标成 auto-antislop;v2 区分三个独立 repo(slop-forensics / antislop-sampler / auto-antislop)各自的 star/license/用途,Sampler 的实现是 antislop-sampler 而非 auto-antislop。
- **判官模型选型**:v1 笼统说"3 个 judge LLM";v2 据文笔实测 + 自偏好偏置研究,明确**生成(DeepSeek)与判官(Kimi/Claude/Qwen 异源)必须分离**。
- **EQ-Bench 相关性数字处理**:v1 写"与人类 preference 相关性 98.6%"(via search snippet,本轮未复现);v2 不再断言该具体数字,改述去偏协议本身(截断抗长度偏置、双序平均抗位置偏置)与可核对的榜首(Grok-4.1 Thinking 1721.9)。
- **autonovel 字数**:v1 写"~1,000 stars";样例长篇字数 v1 未给,v2 补 ~75k–79k 字 / 19 章(注:不同来源 75,000 与 79,456 略有出入,故以区间表述)。

### 删除(v2 移除/降级,尤其幻觉)

- **无 exists=false 幻觉条目需删除**:本方向 27 条引用全部验真为真,无凭空捏造的链接。
- **降级/移出主线的弱引用**(v1 标"via search snippet",本轮 clean-room 未作为核心证据复现,故不进 v2 主线,非证伪):
  - **Ozigi 产品博客**(blog.ozigi.app banned-lexicon-validator)——其 Two-Layer 思路已被 autonovel evaluate.py 的分层禁词覆盖,无独立增量,移出。
  - **Awesome-LLM-as-a-judge**(github.com/llm-as-a-judge/...)——被 4 篇验真的去偏 paper + A Survey on LLM-as-a-Judge 取代。
  - **blog.lyc8503.net LLM-classifier、EnsemJudge(arXiv 2603.27949)**——属"检测人写 vs LLM 写"方向,非"抑制 slop",与 R6 主线正交,移出主线(R6 关注抑制,不关注溯源分类)。
  - **emergentmind FTPO 词条**——FTPO 细节已由验真的 arXiv 2510.15061 + OpenReview 直接覆盖,二手词条移除。
- **"可发表/中文社区影响力"的战略表述弱化**:v1 把"整理 1000+ 中文 slop 词条可发表"作为卖点;v2 保留"自建词表是长期资产"的工程判断,但移除"可发表"这类未经验证的外部价值断言(锚定 A 档:做扎实,不夸张)。
