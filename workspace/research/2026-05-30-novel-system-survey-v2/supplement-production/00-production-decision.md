# 生产级模型路线 — 总决策综合

> 综合材料:R11 模型路线锚点 + R15 天花板 binding 性 + 四方向 production 终稿(R12 微调 / R13 语料 / R14 推理解码 / R16 质量保障)
> 用户立场(贯穿全文):从 0 构建、面向生产、**绝不质量妥协**;明确拒绝"先用 X 凑合、以后再换 Y"的埋雷式分期;不兼容旧系统;宁可前期重,也要一步到位做最好的。
> 评估准绳:每个方案的问题不是"能不能先跑起来",而是"**这是不是生产级最优、值不值得从一开始就做对**"。
> 日期:2026-05-30

---

## 1. 执行摘要 — 最终路线推荐

**推荐:混合路线(Hybrid),且以"自托管开源权重 + 解码层自控 + 针对性微调"为生成内核、闭源 API 仅作蒸馏教师 / 质量天花板对照 / 周边结构化 agent 可选执行器。**

一句话理由:**用户两大点名痛点(对白区分度、中文 slop)在 2026 年的证据下只有"能碰 raw logits + 能改权重"的自托管开源底座能治本——闭源 API(Kimi 官方文档逐字确认)连 `logit_bias`/`logprobs` 都不给,在产出最终散文的主路径上结构性无解;而文笔已被开源追平甚至中文反超,选闭源 API 的唯一旧理由已经消失。**

为什么是"混合"而不是纯自建,也不是纯 API:

- **不是纯 API**:纯 API + prompt 路线(NovelCrafter 模式)可商用出货,但它把 anti-slop / 对白区分度 / 解码控制全部交给黑盒,在"绝不妥协"立场下结构性达不到顶——这是被 Antislop(arXiv 2510.15061, ICLR 2026)的"slop 多为多 token、单 token logit_bias 无效、必须回溯重采样或改权重"硬结论判死的。
- **不是纯自建**:把闭源旗舰彻底排除是浪费。Kimi K2.6 / DeepSeek-V3.2 是当前最强中文写作模型之一,作为**蒸馏教师**(R13 合成语料的 teacher)和**质量天花板对照**(R16 评测锚)价值极高;周边结构化 agent(World/Planner/Camera/Consistency 的 JSON 产出)用闭源 API 当可选执行器也完全合理。彻底不用 = 自废武器。
- **所以是"内核自建、周边可混"的混合**:生成最终散文的 Writer 内核必须自托管开源(碰 logits + 改权重);闭源 API 退到教师 / 对照 / 周边可选执行器位置,**绝不充当产出最终散文的主路径**。

> 命名提示:本推荐在材料语境里等价于 R11 的"从 0 就选 B"。称其为"混合"是为了如实反映闭源 API 仍在系统里承担教师 / 对照 / 周边角色,而非被清零;但**生成内核 100% 自建**这一点不容妥协。若用户更习惯用"自建训练路线"来指代,二者指向同一架构。

---

## 2. 地基锚点结论(R11 + R15)

### 2.1 R11 — 模型路线(binding,作为全局地基)

**结论:从 0 就把生成内核建在"能碰 logits、能改权重"的自托管开源底座上。** 六条支撑:

1. **决定性(B 独占)**:Antislop(2510.15061)证明 slop 多为多 token,单 token `logit_bias` 无效,必须回溯重采样(解码侧)或 FTPO 改权重才能 85–92% 压制且质量损失 <1%;这要求本地 raw logits。Kimi 官方 API 文档逐字:"the Kimi chat API does not support logprobs, top_logprobs, or logit_bias parameters." → A(纯 API)在主路径上根本无解码干预能力。
2. **文笔已追平 / 中文反超**:WebNovelBench(4000+ 中文网文)开源 Qwen3-235B-A22B 拿全场最高 5.21;hskstory 中文写故事横评 Kimi K2 第一、DeepSeek V3.2 第二;EQ-Bench v3 最强开源 Kimi K2.6 Elo 1808,仅落后 Opus 约 19%。→ "选 A 的唯一旧理由(文笔)消失"。
3. **微调可顶天花板**:32B 开源创意写作微调可 75% 胜出闭源。
4. **许可就位**:Qwen3 全系 Apache2.0 且放出 Base;DeepSeek/GLM 均 MIT;Kimi K2.6 Modified MIT 仅在 MAU>1 亿或月营收>2000 万美元时需标注 → 对本用户等于免费可商用可微调。
5. **成本可控**:Qwen3-235B-A22B(22B 激活)小激活底座大幅降推理成本;微调仅 $10–500/次;自托管 break-even 约 10B tokens/月。
6. **长篇一致性是真问题但支持 B**:须靠自有 memory / 解码控制治理,而非寄望 API 黑盒。

底座阵型:**首选 Qwen3-235B-A22B**(中文最强 + Apache2.0 + 256K~1M + 22B 激活),**起步 Qwen3-32B 稠密**;DeepSeek-V3.2 作对照,GLM-4.6/4.7 作长上下文补充;Kimi K2.6 作蒸馏教师与天花板对照。

### 2.2 R15 — "对白区分度天花板"是否 binding(关键纠错)

**结论:这条"刹车"约束方向半真,但不足以支撑"必须从 0 扛整套自建 + 训练";且用户记忆里的关键论据是张冠李戴的错引,绝不能当地基决策依据。**

- **致命纠错**:arXiv **2510.24677** 真身是《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》(医疗 LLM 神经元消融,RPNA = RP-Neuron-Activated Evaluation Framework),研究的是医疗问答里临床角色 prompt 是否改变推理通路,结论是 role prompt "primarily affect surface-level linguistic features"。它**与 chat-roleplay / 叙事小说对白区分度毫无关系**。用户把结论挂在了错误的 paper id 上。讽刺的是,它"role prompt 只动表层语言风格"的发现若外推,反而站在"prompt 确实能改变对白表层风格"那一侧。
- **天花板有没有证据**:没有任何一篇干净实证钉死"第三人称长篇小说对白区分度上限";同号误配的 2510.20266 实为图像去雾论文《GUSL-Dehaze》,据此构造的"Stylometry of Maintaining Character Voice"引用已整条剔除。但有多条**间接证据**指向"纯 prompt 维度确有同质化倾向"(RPG 会话语言学 2503.20623;persona 漂移 / Anthropic persona vectors;实践者共识"AI tends to homogenize speech patterns")。
- **武器侧**:CMU 2025 证明 LLM 间风格 97% 可辨;2301.05659 / 2401.16968 证明人类小说角色 voice 可被 stylometry 量化区分 → 给了**现成离线评测武器**。
- **真实生产系统三态并存**:纯 API+prompt 可出货(NovelCrafter);做到顶级有人自训(Sudowrite Muse,盲测偏好度 2× Claude 3.7);中文网文有专训(阅文妙笔、字节番茄)。但第三方评测反指 Claude Opus 在"角色像不同的人"上更强 → **自研 ≠ 对白区分度自动天下第一,选对底座本身就能打。**

**R15 对本决策的净影响:对白区分度是真问题,但它的正解是"底座选型 + 角色级工程 + 离线 stylometry 评测闭环",而把"微调 / 自研对白模型"定位为"三层跑满仍不达标、且评测证明 gap 来自模型本身才触发的、有数据支撑的升级项",而不是地基期盲目背整套训练。** 这一定位贯穿下文 R12 阶段 D、R13 偏好对、R14 LoRA 三处。

---

## 3. API 路线 vs 自建训练(混合内核)路线 — 正面对比

> 说明:"自建训练路线"一列指本决策推荐的**混合路线之生成内核**(自托管开源 + 解码自控 + 针对性微调);"API 路线"指纯闭源 API + prompt orchestration(NovelCrafter 模式)。

| 维度 | API 路线(纯闭源 + prompt) | 自建训练路线(自托管开源内核) | 裁决依据 |
|------|---------------------------|------------------------------|---------|
| **中文文笔上限** | 高(Kimi K2 / DeepSeek V3.2 顶级),但封顶于供应商当前版本 | **同级或更高**(WebNovelBench 开源 Qwen3-235B 全场 5.21 最高;微调可 75% 胜出闭源) | R11 证据 B/C |
| **对白区分度可控性** | 低 — 只能靠 prompt;persona 长对话被稀释、无法解码期干预 | **高** — 底座选型 + per-character 结构化 + activation steering + GRPO/GenRM 可触发加层 | R15 + R12 阶段 D + R14 §2.3 |
| **anti-slop 可控性** | **结构性无解** — Kimi 官方 API 连 logit_bias 都不给,单 token bias 对多 token slop 也无效 | **高** — FTPO 烧权重(85–92% 压制 <1% 质量损失)+ 离线单请求真回溯采样 | R11 证据 A + R12 阶段 C + R14 §2.2 |
| **数据可商用风险** | 低(不持有训练数据);但产出受供应商 ToS 约束 | **可控但需主动经营** — 现成中文网文数据集全部不可用(盗版 / 无效 license / 触《暂行办法》第七条),**必须 100% 自建**(公版 + 自有授权 + 合成,全程留证) | R13 §0/§1/§2.2 |
| **总拥有成本量级** | 按量付费,低启动;规模化后单 token 成本固定、无摊薄 | 前期重(8×H200 摊销 ≈ $8k–10k/月);**break-even ≈ 10B tokens/月**,到量后省 60–80% | R11 证据 E |
| **上线速度** | **快**(接 API 即可) | 慢(底座 + 语料 + 微调 + 推理栈 + 评测全要自建) | — |
| **长期可维护性** | 受供应商版本 / 定价 / ToS / 模型下线摆布(R14 已记录 DeepSeek 现售型号已变 v4-flash/v4-pro) | **自主可控** — 模型 / 权重 / 采样器 / 评测全在手,无迁移债 | R11 + R14 §3 |
| **不妥协达标度** | **不达标** — anti-slop / 对白区分度 / 解码控制三项结构性触顶 | **达标** — 唯一能在"绝不妥协"立场下把四个痛点维度全部闭环的架构 | 全局综合 |

**结论:在"绝不质量妥协"这唯一裁决线下,API 路线在 anti-slop 与对白区分度两项上结构性不达标;自建内核(混合)路线是唯一达标解。代价是上线速度慢、前期重——这正是用户已明确接受的取舍("宁可前期重,也要一步到位做最好的")。**

---

## 4. 端到端蓝图(自建训练内核 / 混合路线)

每一环引用对应方向终稿。文件均在 `C:\Files\work\story\workspace\research\2026-05-30-novel-system-survey-v2\supplement-production\`。

### 4.1 底座选型 — R11 + R12 §3 + R14 §3

- **起步**:Qwen3-32B 稠密(Apache2.0、放出 Base、中文强、自托管门槛低)。
- **追极致**:Qwen3-235B-A22B(中文最强、22B 激活、256K–1M)。
- **长上下文补充**:GLM-4.6/4.7(MIT、200K、finetune 生态)。
- **教师 / 对照(混合的闭源一侧)**:Kimi K2.6 / DeepSeek-V3.2,作蒸馏教师与天花板对照,**绝不产出最终散文**。
- **规模纪律(R14 §3)**:按真实 token 量增长再上 235B-A22B,**不为"一步到位"过早上 16-GPU 千亿 MoE 集群**(把重花在不转化为质量处 = 同 TRT-LLM 的错误)。

### 4.2 语料 — R13(全程 100% 自建)

- **法务地基最先锁死**:只用公版(版权过期)+ 自有授权 + 合成,全程留证。现成中文网文数据集全部不可用,任何"先用现成凑合、上线前再换"= 把版权炸弹焊进权重 + 违反《暂行办法》第七条(有 1.35 亿罚没刑案先例),一票否决。
- **合成 pipeline**:Magpie(2406.08464)× PersonaHub(2406.20094)/ OpenCharacter(2501.15427)× Humpback(2308.06259)× LongWriter(2408.07055)。**teacher 必须用旗舰中文写作模型**(Kimi K2.6/DeepSeek-V3.2)——弱 teacher 蒸馏会把弱 slop 固化进权重、自废武功。
- **中文去 slop 体系**:自采基线统计建中文 slop 词表(无现成资源),是竞品最少触及的差异化壁垒,属必做地基(与 R14/R16 共建一次)。
- **专项偏好对**:auto-antislop / FTPO 偏好对,定位为**有评测数据后才触发的升级项**(非盲目地基),架构第一天预留数据口。

### 4.3 微调配方 — R12(四阶段正交管线)

不是"选单一最强方法",而是四阶段叠加(四痛点维度两两正交):

1. **阶段 A 风格 SFT(打底文风)**:bf16 高秩 LoRA(rank 128–256,**含 MLP**),非 4bit QLoRA 主力。SFT 单用会启动叙事扁平化,只是打底。
2. **阶段 B deviation-DPO / DORPO(对抗扁平化)**:偏好信号显式加偏离度 / 多样性项。**严禁裸 DPO** —— 同源受控实验(Narrative Flattening, arXiv 2605.27878)证明裸 SFT 启动扁平化、裸 DPO 放大它(= 用户要消灭的对白趋同 + slop 的训练侧根源)。"先裸 DPO 凑合"是本方向最典型埋雷。
3. **阶段 C 中文 FTPO + Antislop(治套话)**:FTPO(2510.15061,权重侧)+ Antislop Sampler(解码侧 raw logits 回溯);必须自建中文 slop 词典。
4. **阶段 D GRPO + 对白区分度 GenRM(顶天花板,可触发升级项)**:唯一能直接优化主观对白区分度的路径;启动条件 = 底座选型 + 角色级 prompt 工程 + 离线 stylometry 评测三者跑满仍不达标、且 gap 证明来自模型本身(贯穿 R15)。架构第一天预留数据格式(成对对白 / 人物卡 / 章节约束),且与 R16 判分 critic 同源互喂。

> 配方纪律:主力必须 bf16 高秩 LoRA(含 MLP)或全参;QLoRA(4bit)隐性损伤文笔细腻度,仅限早期消融。

### 4.4 推理栈 — R14 §1

- **SGLang(生产级最优默认)**:RadixAttention 吃连载书级前缀复用 + xgrammar 结构化最强 + custom logits processor 钩子可挂自研干预 —— 三项恰好命中本项目全部核心 workload。
- vLLM:合格次优。
- **TensorRT-LLM:排除** —— 编译期 / NVIDIA 锁定,"重"不转化为质量,且编译期固定特性使自研 logits processor 几乎不可行(与本项目核心目标直接冲突);仅在模型 + 采样全冻结的纯 NVIDIA 榨性能终局才值得,那不是从 0 做对的起点。

### 4.5 解码干预 — R14 §2

- **结构化(guided decoding)**:xgrammar **第一天全量上**(Director/World/Planner/Camera/Consistency),Writer 散文关约束。提质零成本。
- **反 slop(两层)**:在线 FTPO 烧权重(正常高吞吐)+ 离线单请求 antislop **真回溯**局部精修残留段(Writer 是 background task,延迟容忍高)。**前瞻 n-gram mask 近似判为不达标作终方案**(弱于真回溯,丢掉 85–92% 压制 + <1% 质量损失核心价值),仅作在线廉价兜底。
- **对白区分度**:底座选型 + per-character 强结构化 + activation steering(CAA / 2308.10248 / Anthropic persona vectors 背书)+ 离线 stylometry 闭环。**split-softmax 查无此技术,不进生产热路径**(未验证自造词 = 研究赌博)。
- **contrastive decoding**:中文无证据 + 双模型成本翻倍 + 无内置实现,**仅离线实验 / 蒸馏,不达标作在线主力**。
- **根本张力(必须传达给团队)**:真回溯反 slop ⟂ 高吞吐批量架构(已核实 vLLM V1 / SGLang custom logits processor 只改当前步、不能 rewind)。误以为 antislop 能直接塞进批量服务会踩大坑 —— 必须按"FTPO 烧权重 + 离线单请求回溯"设计。

### 4.6 质量门禁 — R16

- **判分内核**:带推理链的 **generative critic**(WritingPreferenceBench 实证 generative RM 81.8% vs 标量 RM 52.7% vs 单 LLM judge 53.9% ≈ 抛硬币)。"朴素单模型打 1-5 整体分当硬门禁""标量 RM 当绝对质量门禁"本质不达标,剔除主路径(标量 RM 仅降级用于 best-of-N 相对排序)。
- **门禁四层叠加**:① 确定性硬规则(中文 slop / repetition / 段落退化 / 知识图谱事实冲突,零成本不可被偏见污染)② 评委团(2–3 异厂中文强模型 direct-scoring,顺序随机化;PoLL 证明比单大 judge 便宜 7–8 倍)③ ECDF 真实分布锚定 ④ 人审校准锚。
- **reject-and-regenerate**:建在**独立验证器 + best-of-N**(非同模型自评)。self-correction 戒律(arXiv 2310.01798:同模型自评在推理上反掉分 GPT-4 95.5%→89.0%);验证器必须真异构(R15 警示同基座换 persona 伪独立收益有限);Writer 是 background task → best-of-N 额外算力花在离线刀刃上。
- **第一天就必须做(否则不达标)**:中文 slop / 对白可分性度量自建(英文 EQ-Bench/RewardBench/slop 表套用失效;与 R6/R14 共建一次)、章节级阅读行为埋点(否则后期无数据训留存代理)、judge 选型先跑 Judgemark v2.1 选 separability + human-corr 最高者。
- **许可硬约束**:WebNovelBench 数据集 CC-BY-NC-SA-4.0(非商用),只吸收方法论不搬数据;判分内核可自托管 WritingBench 7B(Apache-2.0)/ CritiqueLLM 跑量省钱;与 R12 阶段 D GRPO 奖励模型同源互喂。

### 4.7 跨方向共用基建(只建一次)

- **中文 slop 词表**:R13(语料去 slop)/ R14(解码反 slop)/ R16(确定性硬规则)三方向共用,**一次建成**。
- **对白区分度评测武器**(Burrows' Delta / 引文归属分类器,2301.05659 / 2401.16968):R15 / R12 阶段 D 触发判据 / R16 门禁 共用。
- **判分 critic ⟷ GRPO 奖励模型**:R16 判分内核与 R12 阶段 D GenRM 同源互喂。

---

## 5. 全局风险 + 待用户最终拍板的决议点

### 5.1 全局风险

| 风险 | 说明 | 缓解 |
|------|------|------|
| **错引污染地基** | 用户记忆里 RPNA/2510.24677、2510.20266 均张冠李戴,若当地基会导出"地基期就盲目自训对白模型"的过度工程 | 已纠正;对白区分度走"底座 + 工程 + 评测闭环",微调作可触发升级项 |
| **法务一票否决** | 训练语料若沾盗版来源 = 版权炸弹焊进权重 + 触《暂行办法》第七条(1.35 亿罚没刑案先例) | 语料 100% 自建(公版 + 自有授权 + 合成),最先锁死,全程留证 |
| **裸 SFT/DPO 训练侧埋雷** | 裸 SFT 启动扁平化、裸 DPO 放大,直接制造对白趋同 + slop | 第一天即用多样性保持变体(deviation-DPO/DORPO);裸 DPO 单用明确判不达标 |
| **真回溯 ⟂ 高吞吐架构冲突** | 误以为 antislop 能塞进批量服务会踩大坑 | 按"FTPO 烧权重 + 离线单请求回溯"设计,Writer 走 background |
| **判分内核选错** | 标量 RM / 单 judge ≈ 抛硬币,当硬门禁会放行劣质章节 | generative critic + 评委团 + 确定性硬规则四层叠加 |
| **未验证技术研究赌博** | split-softmax 查无此技术、contrastive decoding 无中文证据 | 不进生产热路径,仅离线实验 |
| **前期重 / break-even 风险** | 自托管 break-even ≈ 10B tokens/月;若长期达不到该量级,TCO 反不如 API | 起步 Qwen3-32B 稠密压低门槛,按真实 token 量增长;闭源 API 在周边仍可用 |
| **缺一手中文 235B 微调可复现 case** | "微调 75% 胜出"仅通用 32B 二手综述,无中文网文 235B 级可复现实验 | 落地前自建 A/B 验证,不盲信二手名次 |

### 5.2 待用户最终拍板的决议点

1. **混合的"闭源一侧"边界**:闭源 API 是否允许出现在周边结构化 agent(World/Planner/Camera/Consistency 的 JSON 产出)的执行器位置?还是连周边也要 100% 自托管?(本决策默认:周边可混、内核必自建。)
2. **起步底座**:Qwen3-32B 稠密起步 → 235B-A22B 演进,还是直接上 235B-A22B?(TCO vs 一步到位的权衡;R14 建议前者以压低门槛。)
3. **阶段 D 触发线的量化定义**:"底座 + 角色级工程 + 离线 stylometry 三层跑满仍不达标"的具体阈值(Burrows' Delta 角色间可分性达到多少算"达标"、低于多少算"gap 来自模型")需用户 / 团队先定指标,否则升级项触发无依据。
4. **语料种子规模与公版来源清单**:公版 + 自有授权的具体来源、目标体量、留证流程需用户确认(这是法务地基,影响"是否合法存在")。
5. **硬件路线**:自购 8×H200 摊销 vs 云租(R11 证据 E:自购 ≈ $8k–10k/月 / 云租 ≈ $20k–35k/月,回本 >~14 个月)——取决于用户对前期资本支出 vs 现金流的偏好。
6. **闭源教师的合规边界**:用 Kimi/DeepSeek 作蒸馏 teacher 产出合成训练数据,需确认其 ToS 是否允许蒸馏 / 输出用于训练(R13 的合成 pipeline 强依赖此前提)。

---

## 6. 自动拦下的幻觉汇总

> 汇总两项地基锚点 + 四方向终稿全部 `hallucinations_removed`。分两类:**A. 整条剔除(exists=false / 张冠李戴)**;**B. 论文真实但属性被虚构(标签级纠正)**。

### A. 整条剔除(arXiv ID / URL 不存在或张冠李戴)

| 被引内容 | 真身 / 问题 | 来源方向 |
|---------|-----------|---------|
| **arXiv 2510.24677**(被当"RPNA / 纯 prompt 对白区分度天花板"论据) | 实为《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》(医疗 LLM 神经元消融,RPNA=RP-Neuron-Activated Evaluation Framework),与对白区分度无关 | R15 / R12 / R13 / R14(跨方向反复标注防误用) |
| **arXiv 2510.20266**(被构造为"Stylometry of Maintaining Character Voice") | 同号误配,实为《GUSL-Dehaze: A Green U-Shaped Learning Approach to Image Dehazing》(图像去雾);据此构造的角色 voice stylometry 引用整条剔除 | R15 / R13 / R14 |
| **Persona Steering / "Dashboard for Transparency and Control"(arXiv 2405.15076)** | exists=false;该 ID 实为数论论文《Refined conjectures on Fitting ideals of Selmer groups over Z_p^2-extensions》。persona steering 论据改由 CAA(2024.acl-long.828)+ 2308.10248 + Anthropic persona vectors 承载 | R14 |
| **DeepSeek News — API Pricing Update Sep 2025(deepseek.news/...)** | exists=false;域名不存在 / 无索引。定价改以官方 api-docs.deepseek.com 为准(现售型号已变 v4-flash/v4-pro) | R14 |
| **Helicone — Kimi K2 Pricing Calculator(helicone.ai/.../moonshot/...)** | exists=false;URL 返回 404,Moonshot 不在 Helicone provider 列表。定价改以官方 platform.kimi.ai 为准 | R14 |
| **DEMO / "Evaluating Long-form Story Generation by Measuring Detail Faithfulness..."(arXiv 2510.13705)** | exists=false;该 ID 实为《VC-Dimension vs Degree: An Uncertainty Principle for Boolean Functions》。原"长程细节忠实度 / Barthes reality effect"佐证整条剔除,改由 EQ-Bench Longform 承载 | R16 |
| **DReSS / "Multi-Agent Story Generation Framework with Phased Refinement..."(arXiv 2510.21304)** | exists=false;该 ID 实为《Arbitration-Free Consistency is Available (and Vice Versa)》(分布式存储)。原"多智能体草稿→评审→精炼"佐证整条剔除,改由 self-correction 戒律(2310.01798)+ Self-Refine(2303.17651)+ best-of-N + 独立验证器承载 | R16 |

### B. 论文真实但某属性被虚构(标签级纠正,论文本体 exists=true)

| 论文 | 被虚构的属性 | 更正 | 来源方向 |
|------|------------|------|---------|
| **RLMR(arXiv 2508.18642)** | 误标会议归属"(AAAI)" | 实为 arXiv 论文(2025-08),非 AAAI 录用,AAAI 标签剔除 | R12 |
| **DiversityTuning / deviation-DPO(arXiv 2503.17126)** | 误标作者机构为 Midjourney | arXiv 页未列机构,改为不确认机构 | R12 |
| **FTPO / Antislop(arXiv 2510.15061)** | 测试模型家族误写含 Qwen | 实为 Gemma-3-12B / Mistral-Small-3.2 / Llama-3.3-70B | R12 |
| **GEM《Preserving Diversity in SFT》(ICLR 2025)** | OpenReview forum-id 错误(原 pOq9vDIYev) | 正确为 NQEe7B7bSw | R12 |
| **"Activation Addition: Steering Language Models Without Optimization"(arXiv 2308.10248)** | 标题误称 | 实际标题《Steering Language Models With Activation Engineering》(Turner et al.) | R14 |

### C. 验真全数通过(无剔除)的方向

- **R13 语料**:30 条核心引用(数据集 + 支撑论文 / 工具仓)逐条验真**全部 exists=true,无一剔除**(jetaudio/chinese_web_novels、webnovel_cn、Magpie/PersonaHub/OpenCharacter/Humpback/LongWriter/Weaver/LIMA/Antislop/RoleLLM/COIG-CQIA 等)。其列出的 2510.24677 / 2510.20266 仅作跨方向错引校准标注,不在 R13 论证链中。

> 总计:**整条剔除 7 条**(2 条为地基锚点跨方向反复标注的同一对错引 2510.24677 / 2510.20266,5 条为各方向独有的 exists=false 引用)、**标签级纠正 5 处**。所有 production 终稿的论文本体在各自验真中 exists=true。

---

（总决策综合终稿。与 R11 / R15 两项地基锚点、R12 / R13 / R14 / R16 四方向终稿全程对齐。）
