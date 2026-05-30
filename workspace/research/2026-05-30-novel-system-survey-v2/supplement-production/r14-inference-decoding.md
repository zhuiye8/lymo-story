# R14 · 推理服务 + 解码期干预 — 生产级终稿

> 调研日期 / accessed：全部为 2026-05-30
> 立场：从 0 构建、面向生产、**绝不质量妥协**。判断标准不是"能不能先跑起来"，而是"这是不是生产级最优、值不值得从第一天就做对"。明确拒绝"先用 X 凑合、以后换 Y"的埋雷式分期。
> 方法：clean-room 调研 + 对抗式引用验真（`exists=false` 已剔除，见 §9）+ 对齐两项地基锚点（R11 模型路线 / R15 对白天花板是否 binding）。

---

## 0. 一句话结论（与地基锚点对齐后）

**这个方向不是"要不要自建推理栈"的开放选择题——R11 模型路线已经替它定了调：内核必须建在能碰 raw logits、能改权重的自托管开源底座上（Qwen3-235B-A22B 为目标，起步可 Qwen3-32B 稠密），因此自建推理栈是 binding 的地基，不是可选升级项。** 硬核理由：解码期干预里唯一"对症且经同行验证"的反 slop 手段（Antislop 回溯 / FTPO）**结构上要求本地 raw logits**，而点名要用的闭源 API（Kimi 官方）连 `logit_bias` / `logprobs` 都不提供——纯 API 路线在产出散文的主路径上**根本没有解码干预的入口**。

**在"必须自建"这个已定前提下，本方向的生产级取舍是：**
1. **推理底座选 SGLang**（RadixAttention 把连载的"书级稳定前缀"自动变 KV 命中 + xgrammar 结构化最强 + 有 custom logits processor 钩子可挂自研干预）；vLLM 是合格的通用次优；**TensorRT-LLM 不达标，本阶段排除**（编译期 + NVIDIA 锁定的"重"不转化为质量，只转化为迭代摩擦，并让自研采样器几乎不可行）。
2. **guided / constrained decoding（xgrammar）第一天全量上**，覆盖除 Writer 外的全部结构化 agent——少数"提质 + 不掉速"的干预，生产级最优。
3. **反 slop 用真·回溯（Antislop / FTPO），不做"前瞻 mask 近似"凑合**——近似不达标（见 §2.5）。关键红利：你的 Writer 是 background 章节生成、**延迟容忍度高**，所以"为质量牺牲吞吐跑回溯采样"不是妥协，而是把质量放回它本就该在的离线位置，**可以从一开始就做对**。
4. **角色对白区分度（R15 痛点）不靠未经验证的自造词 "split-softmax"**，而靠"选对底座 + per-character 强结构化控制 + activation steering（有论文背书）+ 离线 stylometry 评测闭环"。这同样是从第一天就做对的工程，而非地基期就训模型。

---

## 1. 推理栈三选一（生产可行性判断，非"能否 demo"）

### 1.1 三者基本盘（repo 验真，[accessed:2026-05-30]）

| 框架 | 验真状态 | license | 定位 |
|---|---|---|---|
| **vLLM**(vllm-project/vllm) | ✅ exists，~81.4k stars，活跃，2000+ contributors | Apache-2.0 | 通用高吞吐，生态最大，事实标准 |
| **SGLang**(sgl-project/sglang) | ✅ exists，~28.5k stars，LMSYS 维护，活跃 | Apache-2.0 | 结构化生成 + 前缀复用最强 |
| **TensorRT-LLM**(NVIDIA/TensorRT-LLM) | ✅ exists，~13.8k stars，最新 v1.2.1(2026-04-20)，活跃 | Apache-2.0 | NVIDIA 官方，编译期极致优化，NVIDIA-only |

> 三者均为活跃项目，无弃坑风险。注：验真返回的 star 数（vLLM 81.4k / SGLang 28.5k / TRT-LLM 13.8k）比调研初稿引用的数字更高、更新，以验真为准。

### 1.2 性能基准的诚实判断

**没有一份"2026 全新、三方同台、含中文长上下文"的权威基准可查** [no-source-found：搜 "vLLM SGLang TensorRT-LLM 2026 benchmark H100 head to head"]。可核实的分散基准**版本普遍陈旧（2024 量级）**，各家在自己擅长场景报喜，**不可作最终选型依据**：

- **SqueezeBits《vLLM vs TensorRT-LLM》**(blog.squeezebits.com，[accessed:2026-05-30])：H100-80GB / Llama-3-8B。结论——默认配置两者相当；TRT-LLM 充分调优后峰值更高但配置成本显著更大；vLLM 胜在易用。**版本为 vLLM 0.5.3 / TRT-LLM 0.11.0，已过时，仅供方向参考。**
- **BentoML 多后端基准**(bentoml.com，2024-06，[accessed:2026-05-30])：A100-80GB / Llama-3 8B-70B。LMDeploy(TurboMind) decode 吞吐最强（8B 100 并发 ~4000 tok/s）且 TTFT 最低；vLLM 最均衡；TGI 高并发 OOM。**2024 数据。**
- **LMSYS RadixAttention blog**(lmsys.org/blog/2024-01-17-sglang，[accessed:2026-05-30])：共享前缀类 workload 最高 **5x**（vs Guidance、vLLM），加速高度依赖 cache 命中率。
- **SGLang v0.4**(lmsys.org/blog/2024-12-04-sglang-v0-4，[accessed:2026-05-30])：零开销 batch scheduler 最高 +1.1x；cache-aware load balancer 最高 +1.9x 吞吐 / cache 命中率 +3.8x；**结构化输出(xgrammar)最高比其它开源方案快 10x、JSON 解码近零开销**。
- **vLLM V1**(blog.vllm.ai/2025/01/27/v1-alpha-release，[accessed:2026-05-30])：相对 V0 最高 **+1.7x 吞吐**；**prefix caching 默认开启、命中率 0% 时也近零开销**。
- **NVIDIA 基准指南**(developer.nvidia.com，[accessed:2026-05-30])：只给方法论（TTFT/ITL/TPS/goodput），无三方硬数字。

**生产判断**：选型**不据此拍板**，须以自有中文底座 + 真实连载 prompt 自测 goodput 为准。但**架构特性匹配 workload（下节）是可以现在就判定的硬依据**。

### 1.3 架构特性 × 小说连载 workload（这才是选型依据）

| 维度 | vLLM | SGLang | TensorRT-LLM |
|---|---|---|---|
| 自动前缀缓存 | V1 默认、近零开销 | **RadixAttention（radix-tree+LRU），自动复用最强** | 有 KV 复用但配置/灵活性弱 |
| 结构化/受限解码 | xgrammar(默认)/guidance/outlines | **xgrammar 深度集成，近零开销，最高 10x** | 支持但不灵活 |
| 自定义 logits processor | V1 batch-level 接口（仅当前步，见 §2） | **有 custom logit processor 钩子** | 几乎不可行（编译期固定） |
| 长上下文 / 大 KV | PagedAttention | 同级 + DP-attention 省 KV | 强，但需重编译 |
| 量化 | AWQ/GPTQ/FP8/INT8 | 支持 | **FP8 内核级最优** |
| 上手 / 迭代速度 | **易** | 中 | **难（换模型/改采样即重编 engine）** |
| 生态 / 文档 | **最大** | 大且增长快 | NVIDIA 官方 |

**生产可行性判断 — 推理栈：**

- **SGLang = 连载场景生产级最优默认，值得从一开始就做对。** 连载的本质是同一本书的 Story Bible + 角色记忆 + 已写章节被反复当前缀喂入，RadixAttention 把这种复用做成自动 cache 命中，砍掉重复 prefill；六个 agent 大量产 JSON，xgrammar 结构化是 SGLang 强项；且它有 custom logit processor 钩子——这是 R11 选定的"必须能碰 logits"路线的落点。**这三条恰好命中本项目全部核心 workload。**
- **vLLM = 合格的通用次优，不是埋雷选择。** 生态最大、文档最全、V1 prefix cache 已默认零开销、V1 也有 batch-level logits processor 接口（RFC #17799 在推进可扩展性）。若团队更看重"招人好招、长期最稳"，vLLM 是生产级合格底座。**它与 SGLang 都不达标的地方是同一处：原生批量架构不支持回溯采样（见 §2.5），这点二者无差别。**
- **TensorRT-LLM = 不达标，明确排除（不是"以后再用"，而是这个项目阶段就不该用）。** 它的"重"是编译期 + NVIDIA 锁定 + 每次换模型/改采样都要重走 engine 流程的运维重，**这种重不转化为质量，只转化为迭代摩擦**。对一个还在快速迭代解码策略、且要挂自研 logits processor 的从 0 系统，TRT-LLM 的编译期固定特性几乎让自定义采样器不可行——这与本方向核心目标直接冲突。它只在"模型 + 采样策略全部冻结、纯 NVIDIA 集群榨最后 15% 性能"的终局才值得，而那不是"绝不妥协地从 0 做对"该有的起点。

---

## 2. 解码期质量干预：逐项生产可行性（本方向核心）

> 对齐 R11：内核已定为自托管开源底座，所以下列"需要本地 raw logits"的手段在本项目里**是可达的**——这正是放弃纯 API 主路径换来的能力。对齐 R15：角色对白区分度是真问题，但正解是底座+结构化+steering+评测，而非自造采样器。

### 2.1 logit_bias — ✅ 可用但能力有限，**不能当反 slop 主力**

- vLLM 原生支持 `logit_bias`(token_id→bias)（docs.vllm.ai/structured_outputs 及采样参数，[accessed:2026-05-30]）；SGLang 同级。
- **致命局限（被 Antislop 论文实证）**：中文 slop 绝大多数是**多 token 词组**（"嘴角勾起一抹""空气仿佛凝固"），单 token 的 logit_bias **对症无效**。Antislop(arXiv:2510.15061, ICLR 2026，[accessed:2026-05-30]) 逐字："previous per-token logit biasing approaches are ineffective since most slop words & phrases are more than one token"。
- **生产判断**：仅用于压个别高频虚词/标点癖好，**不是反套话主力**。

### 2.2 guided / constrained decoding — ✅ 生产级最优，**第一天就全量上**

- vLLM：`guided_json`(JSON Schema/Pydantic)、`guided_regex`、`guided_choice`、`guided_grammar`(EBNF)、`structural_tag`；后端 xgrammar(默认)/guidance/outlines/lm-format-enforcer（docs.vllm.ai/structured_outputs，[accessed:2026-05-30]）。注意 v0.12.0 起旧 `guided_*` 参数已迁移，落地按当前文档的 `structured_outputs` 形态写。
- SGLang：xgrammar 深度集成，结构化输出**近零开销、最高 10x**（lmsys，[accessed:2026-05-30]）。
- xgrammar 本体(mlc-ai/xgrammar)：✅ exists，独立活跃项目，~1.7k stars，贡献者含 xAI/DeepSeek/NVIDIA/Meta/Google（[accessed:2026-05-30]）。
- **生产判断**：Director / World / Planner / Camera / Consistency 五个 agent 大量产结构化输出（Bible JSON、事件图、一致性结果），**全部走 guided_json 强约束 schema = 提质零成本、生产级最优**。**只有 Writer 产散文时关掉约束**（散文不能被语法绑死）。这是少数"既提质又不掉速"的干预，**必须从第一天就做对**。
- **与 R11 呼应**：WebNovelBench 八维里最高权重的痛点是"角色塑造一致性"(0.1377)、"对白区分度"(0.1171)、"文学手法"(0.1304)——这些**不是 schema 能解决的散文层质量**，所以 guided decoding 管结构、反 slop + steering 管散文质量，二者分工互补。

### 2.3 contrastive decoding（对比解码）— ⚠️ prototype 级，**不进热路径**

- 原论文：*Contrastive Decoding: Open-ended Text Generation as Optimization*(arXiv:2210.15097, ACL 2023，[accessed:2026-05-30])：用大"专家"模型 log-prob 减小"业余"模型 log-prob，放大并抑制退化（重复/不连贯/跑题），配 plausibility constraint。
- 后续：*Contrastive Decoding Improves Reasoning in LLMs*(arXiv:2309.09117，[accessed:2026-05-30]) 证明对推理任务亦有效。
- **致命成本**：需**同跑两个模型**（专家+业余，同 tokenizer），推理成本与显存近翻倍；业余模型选择敏感；原文主验英文，**中文创作有效性无公开证据** [no-source-found：搜 "contrastive decoding Chinese creative writing"]；vLLM/SGLang 均无内置实现。
- **生产判断 — 不达标作主力**：为文笔多样性把成本翻倍、效果在中文未验证、又无现成生产实现——性价比差。**定位为离线实验/蒸馏手段**（用 CD 跑高质量样本做对照或蒸馏教师），**绝不放进在线/批量生成热路径**。这不是"以后再上"，而是它本质属于离线研究层，不属于服务层。

### 2.4 split-softmax（角色区分）— ❌ 公开文献查无此技术，**不放进生产热路径**

- WebSearch 精确匹配 "split-softmax"/"split softmax" 在 LLM 采样/角色区分语境下**零结果** [no-source-found：搜 "split-softmax LLM sampling persona"、"split softmax character differentiation decoding"]。判断：**极可能是团队内部自造词**，无现成实现、无第三方验证、无论文背书。
- 概念相邻且**有真实研究**的是 **activation steering / persona steering**：
  - *Steering Llama 2 via Contrastive Activation Addition*(aclanthology 2024.acl-long.828, ACL 2024 Outstanding Paper，[accessed:2026-05-30])
  - *Steering Language Models With Activation Engineering*(arXiv:2308.10248，[accessed:2026-05-30])（注：调研初稿误称其为 "Activation Addition: Steering Language Models Without Optimization"，实际标题为 *Steering Language Models With Activation Engineering*，已据验真更正）
  - **Anthropic《Persona vectors》**(anthropic.com/research/persona-vectors)：明确 "prompt/RAG-based signals can be diluted in long dialogues, leading to drifting persona"，activation steering 比纯 prompt 更稳——**这正是长篇叙事 persona 漂移的对症点**。
- **生产判断 — 与 R15 锚点严格对齐**：R15 已核实，"纯 prompt 对白区分度有天花板"这条约束**半真**（弱设定下大概率真实，但没有任何证据硬到"必须自建/微调才能跨过"），且用户记忆里的关键论据 RPNA / arXiv:2510.24677 是**张冠李戴的错引**（见 §9）。因此：
  - **不把未经验证的自造采样器 split-softmax 放进"质量绝不妥协"的生产热路径**——那是研究赌博。
  - **对白区分度的生产正解（R15 四步）**：①底座选型优先（多源证据显示对白区分度强烈 model-dependent）；②per-character 强结构化控制（角色卡 / style sheet / 逐角色生成 / few-shot 对白范例 / 解码期 persona 控制）；③activation steering（有论文+开源实现）+ 你已有的 LayeredMemory L0 身份核注入；④离线 stylometry 量化（Burrows' Delta / 引文归属分类器，见 §2.6）。
  - **何时才上更重手段**：仅当 ①②③ 跑满、且离线评测证明 gap 来自模型本身，才上 LoRA/微调。届时它是"有数据支撑的天花板加层"，**不是埋雷、不是凑合后换**。

### 2.5 Antislop 回溯反套话 — 机制与批量推理栈结构性冲突，**但本项目恰好能吃下真回溯**

- repo：sam-paech/antislop-sampler，✅ exists，Apache-2.0，**工作已被 ICLR 2026 接收**，~345 stars（[accessed:2026-05-30]）。论文 arXiv:2510.15061。
- 机制：维护禁止短语列表；**检测到禁止序列时回退(backtrack)到该短语首 token，下调其概率并重采样**——因此能处理 logit_bias 搞不定的**多 token 词组**。FTPO（fine-tune 变体）achieving **85–92% 压制、写作质量损失 <1%**；DPO 则质量退化显著且压制更弱（arXiv:2510.15061，[accessed:2026-05-30]）。
- repo 明确："需 raw logits access + 缓存历史 logits 回溯；**Commercial APIs typically lack these capabilities, making them incompatible**"（[accessed:2026-05-30]）——**这正是 R11 判 A（纯 API）出局、必须自建的决定性一锤**。
- **关键技术冲突（务必想清楚）**：vLLM V1 的 custom logits processor 接口**只作用于当前解码步、无法 rewind 已采样 token**（接口为 batch-level 的 `is_argmax_invariant`/`update_state`/`apply`，`apply()` 只见当前步 batched logits，无回退机制）（docs.vllm.ai/custom_logitsprocs，[accessed:2026-05-30]）。SGLang 的 custom logit processor 同理。**结论：antislop 的真·回溯无法以原生方式跑在 vLLM V1 / SGLang 的高吞吐批量服务里。**
- 旁证：DRY/XTC 等创作向 stateful 采样器在 vLLM 长期是 open feature request（vLLM issue #8581，[accessed:2026-05-30]），maintainer 明确这类采样器**难以在批量架构里向量化**，落后于 ExLlamaV2/TabbyAPI、llama.cpp 等单机引擎。

- **生产判断 — 本方向最重要的取舍，立场是"做对"而非"凑合"**：

  - ❌ **不接受"前瞻式 n-gram mask 近似"作为最终方案。** 近似（当 token 串即将触发禁止短语时提前压制下一 token、不回退）只能挡"短语尚未起头"的情况，对"短语首 token 已落地"无能为力，效果弱于真回溯。Antislop 的 85–92% 压制 + <1% 质量损失正是**靠真回溯/改权重拿到的**——退到近似就是退掉了这条手段的核心价值，**对"绝不妥协"不达标**。它最多作为在线草稿阶段的廉价兜底，不算"做对"。

  - ✅ **接受"为真回溯牺牲吞吐"，因为这在本项目不是妥协。** 关键红利：**你的 Writer 是 background 章节生成，不是低延迟聊天**——延迟容忍度天然高。所以"单请求 / 异步批量跑 antislop 回溯采样（transformers/GGUF 后端），吞吐与并发下降"在本项目是**可接受且正确**的工程取舍。把"绝不妥协的质量"放回它本就该在的离线/异步位置，不牺牲任何用户可感知体验。**这一点显著改变了 antislop 的可行性结论：对小说连载，牺牲吞吐换真回溯反套话，可以从一开始就做对。**

  - ✅ **更强的"做对"路线 = FTPO 改权重，把反 slop 烧进模型本身。** Antislop 论文证明 FTPO（fine-tuning 变体）能在 raw logits 上做到 85–92% 压制、质量损失 <1%，**且改权重后正常吞吐推理即可享受**——与 R11"针对性微调可顶天花板"完全同向。生产终态应是：**底座微调（FTPO 量级）把高频中文 slop 烧进权重 → 在线/批量用 SGLang 正常高吞吐生成 → 仅对残留套话密集段落用单请求回溯采样局部精修**。这条路线既不牺牲在线吞吐、又拿到真回溯级质量，是"重但一步到位"的生产级最优，而**不是**"先近似后真回溯"的分期妥协。

  - **架构落点**：自托管 SGLang（R11 已定）→ 在线/批量走 xgrammar 结构化 + FTPO 微调后的底座（正常吞吐）→ 离线精修阶段挂 antislop 单请求回溯后端。三段都在自有栈内，无 API 黑盒依赖。

### 2.6 中文 slop 度量（反套话的闭环基建，**必建**）

- **EQ-Bench Creative Writing v3**(eqbench.com/creative_writing.html，✅ exists，[accessed:2026-05-30])：LLM-judge 评创作，**含 Slop / Repetition / Style 维度 + Elo**，judge=Claude Sonnet 4.6。但 **32 prompts、主要面向英文，无明确中文创作赛道**。R11 锚点引用其分数：claude-opus-4-7=2215.9(#1)、Kimi-K2.6=1807.7(#6，最高开源)、GLM-5=1663.6、DeepSeek-V3.2=1514.4。
- **slop-forensics**(sam-paech/slop-forensics，✅ exists，MIT，~332 stars，[accessed:2026-05-30])："分析 LLM 输出里重复词汇模式"的工具链，可借鉴**方法论**。
- **R15 提供的离线 stylometry 武器**：Burrows' Delta + 引文归属分类器（arXiv:2301.05659《From stage to page》、arXiv:2401.16968《Distinguishing Fictional Voices》，均 [accessed:2026-05-30]），可给生成对白做"角色间可分性"打分。
- **生产判断**：反套话与对白区分度要**可度量才能闭环**。英文 EQ-Bench **不能直接套用**——**必须从一开始自建中文 slop 词典 + 自动 slop 评分 + 对白可分性打分**，作为 Consistency agent 之外的"文体守门员"。否则"绝不质量妥协"无法度量、不可验证，质量目标落空。这是把质量工程化的必要地基，值得前期投入。

### 2.7 解码干预可行性总表（对齐"绝不妥协"立场）

| 干预 | 现成生产实现 | 在自托管 vLLM/SGLang 可行 | 对中文质量有效性 | 生产判断（绝不妥协视角） |
|---|---|---|---|---|
| logit_bias | ✅ 原生 | ✅ | 弱（仅单 token） | 个别虚词用，**非主力** |
| guided/constrained(xgrammar) | ✅ 原生 | ✅ 近零开销 / 最高 10x | 管结构 | **第一天全量上（非 Writer），达标最优** |
| contrastive decoding | ❌ 无内置 | 需自研、双模型成本翻倍 | 中文未验证 | **仅离线实验/蒸馏，不进热路径** |
| split-softmax | ❌ 查无此技术 | 可自研但无背书 | 未知 | **不进热路径**；改走 steering + 记忆 + 评测 |
| Antislop 真回溯 | ✅ prototype(ICLR'26) | ❌ 批量架构冲突；✅ 单请求/离线 | **强（对症，85–92%）** | **离线/异步局部精修跑真回溯（本项目延迟容忍，达标）** |
| FTPO 改权重反 slop | ✅ 论文方法 | ✅ 微调后正常吞吐 | **强（<1% 质量损失）** | **生产终态首选：烧进权重，在线正常吞吐** |
| 前瞻 n-gram mask 近似 | 需自研 | ✅ batch-level | 中（弱于真回溯） | **不达标作终方案**，仅在线廉价兜底 |
| activation steering（对白） | ✅ 有论文+实现 | ✅（改隐空间，不回溯） | 有背书（persona 漂移对症） | **对白区分度的有据路线** |

---

## 3. 长篇连载的 KV-cache / prefix-cache 复用（纯赚，零质量损失，必做对）

这是小说连载相对一般 LLM 服务的**最大结构性红利**。

- **workload 特征**：同一本书每章生成都重复喂入 Story Bible、世界设定、角色卡、相关历史章节/记忆——**前缀高度重叠**。
- **SGLang RadixAttention**（R11 已定底座的核心收益）：radix-tree 存所有请求 KV，LRU 淘汰 + cache-aware 调度，**自动复用共享前缀**，最高 5x（lmsys，[accessed:2026-05-30]）；v0.4 cache-aware load balancer 多节点把 cache 命中率再提最高 3.8x（[accessed:2026-05-30]）。
- **vLLM V1 APC**：prefix caching 默认开启、命中率 0% 时近零开销（docs.vllm.ai/automatic_prefix_caching，[accessed:2026-05-30]）。
- **生产判断**：无论底座是 SGLang 还是 vLLM，**第一性工程是"书级稳定前缀前置"**——把每本书不变的 Bible/角色核放 prompt 最前、易变内容放后，使 prefix-cache 命中率最大化。自建选 SGLang 拿到最强自动复用。这是**纯赚、零质量损失**的优化，从第一天就做对。
- **注**：调研初稿讨论的"API 侧 context caching 显式定价"（DeepSeek/Kimi 的 cache-hit 档）在 R11 定调后**不再是主路径关切**（API 仅作蒸馏教师/对照/可选周边 agent 执行器），故此处只保留自建侧的 prefix-cache 工程结论。

---

## 4. 成本：自建 vs API 的盈亏平衡（R11 已定，本节只校准数字与风险）

> R11 锚点结论：**从 0 就选自建开源底座**，驱动**不是省钱而是"必须能碰 logits + 改权重"**——纯 API 在反 slop/对白主路径上无解码干预入口。因此本节不做"该不该自建"的开放权衡，只校准成本量级、明确风险。

### 4.1 自建成本量级（R11 锚点核实数，[accessed:2026-05-30]）

- **微调成本低**：70B QLoRA "8–12h on H100 ($10–16)"；全量 "8×H100 24–48h, $250–500"（Spheron 2026）。**FTPO 量级反 slop 微调 $10–500/次，可负担**——这让"把反 slop 烧进权重"成为现实可行的生产动作。
- **自托管月成本**（Lushbinary/Spheron，[accessed:2026-05-30]）：Kimi 1T INT4 8×H100 ≈ $14.4k–17.3k/月；DeepSeek 671B FP8 8×H200 ≈ $26k/月；**"~10B tokens/月起，自托管省 60–80%"**。
- **TCO 回本**（sitepoint 2026，[accessed:2026-05-30]）：自购 8×H200 摊销+电+运维 ≈ $7,974–10,224/月 vs 云租 $20,440–35,040/月，**>~14 个月回本**。
- **最小部署单元约束**（vLLM recipe，[accessed:2026-05-30]）：Kimi-K2 FP8 128k seqlen 最小 16 GPU 集群——**这是选底座规模时的硬约束**：起步用 Qwen3-32B 稠密（单/双卡可部署）比直接上千亿 MoE 现实得多，与 R11"起步 Qwen3-32B、规模化 Qwen3-235B-A22B"路线一致。
- **解码是显存带宽瓶颈**（Databricks 2023，[accessed:2026-05-30]）：每 token 约读 2N 字节，batching 是 per-token 成本最大杠杆，量化→更大 batch→更低单价。**这解释了为何 22B 激活的 MoE（Qwen3-235B-A22B）比稠密 235B 推理成本低得多**——R11 选它正是吃这个红利。

### 4.2 成本结论（绝不妥协立场）

- **起步期 token 量小时，自建单 token 成本确实可能高于 API**——但 R11 已判定这**不构成放弃自建的理由**，因为 API 路线**根本拿不到反 slop/对白所需的 logits 干预能力**，"省钱"在这里是伪命题：省下的钱买不回"质量绝不妥协"所必需的解码主权。
- **真正的成本纪律**在于：起步用小激活底座（Qwen3-32B 稠密）压低自托管门槛，**不要为了"一步到位"在 token 量未上规模时就上 16-GPU 千亿 MoE 集群**——那是把"重"花在不转化为质量的地方（同 TRT-LLM 的错误）。底座规模应随真实日均 token 量增长，**这不是质量妥协，是把重资源花在刀刃上**。

---

## 5. Top 推荐配方（生产级，从 0 一步到位）

**给"从 0、面向生产、绝不质量妥协"的中文小说系统的解码层 + 推理栈落地组合：**

1. **推理底座：SGLang（自托管）。**
   - 吃 RadixAttention 的连载前缀复用红利；xgrammar 结构化最强；有 custom logit processor 钩子可挂自研干预。
   - 模型底座对齐 R11：起步 **Qwen3-32B 稠密**（单/双卡可部署），规模化 **Qwen3-235B-A22B**（22B 激活，中文最强 + Apache-2.0）；DeepSeek-V3.2 作对照、GLM-4.6/4.7 作长上下文补充、Kimi K2.6 留作蒸馏教师与质量天花板对照。
   - **明确排除 TensorRT-LLM**（编译期 + 锁定的重不转化为质量，且让自研采样器几乎不可行）。vLLM 为可接受的通用备选。

2. **结构化输出：第一天全量 guided_json(xgrammar)。** 覆盖 Director/World/Planner/Camera/Consistency；Writer 散文关约束。提质零成本，生产级最优。

3. **反 slop（绝不用近似凑合）：**
   - **生产终态首选 = FTPO 量级微调把高频中文 slop 烧进权重**（$10–500/次可负担，85–92% 压制、<1% 质量损失），在线/批量正常高吞吐生成。
   - **离线/异步精修 = 单请求 antislop 真回溯**局部重写残留套话密集段（利用 Writer 是 background task、延迟容忍高的红利）。
   - logit_bias 仅压个别虚词，**不当主力**。

4. **角色对白区分度（R15 痛点，不用 split-softmax）：**
   - ①选对底座（model-dependent，对白区分度强烈依赖底座）；②per-character 强结构化（角色卡/style sheet/逐角色生成/few-shot 对白范例）；③**activation steering（有论文背书）+ LayeredMemory L0 身份核注入**；④离线 stylometry 评测闭环（Burrows' Delta / 引文归属）。
   - 仅当 ①②③ 跑满仍不达标、且评测证明 gap 来自模型本身，才上 LoRA。

5. **KV/prefix 复用：书级稳定前缀前置**，吃满 SGLang RadixAttention 自动命中。纯赚、零质量损失。

6. **中文质量度量基建：自建中文 slop 词典 + 自动 slop 评分 + 对白可分性打分**（英文 EQ-Bench 不直接可用），作为文体守门员，让"绝不妥协"可度量可闭环。

7. **离线层（不进热路径）：** contrastive decoding 仅作蒸馏/对照实验，绝不放在线生成路径。

---

## 6. 决策树（对齐地基锚点后的收敛版）

> R11 已替本方向定调：**内核必须自托管开源底座**（要 logits + 权重），所以传统的"自建 vs API"决策树已坍缩。剩下的是"自建之内怎么做对"：

> - **推理栈** → **SGLang**（连载前缀复用 + 结构化 + 可挂自研干预）。vLLM 次优。**TRT-LLM 排除**（除非模型与采样全冻结的纯 NVIDIA 终局）。
> - **结构化 agent 质量** → **xgrammar guided decoding，第一天全量**。
> - **反 slop** → **FTPO 烧进权重（在线正常吞吐）+ 离线单请求 antislop 回溯精修**；**不退到前瞻 mask 近似**。
> - **对白区分度** → **底座选型 + per-character 结构化 + activation steering + 离线 stylometry**；**不上未验证的 split-softmax**；微调是"有数据支撑的可触发升级项"，非地基期必做。
> - **底座规模** → 起步 Qwen3-32B 稠密压低门槛，随真实 token 量增长到 235B-A22B；**不为"一步到位"过早上 16-GPU 千亿集群**。

---

## 7. 成本 / 风险

- **API 价格与型号不可长期假设（已非主路径但影响蒸馏/对照）**：验真发现 DeepSeek 官方定价页现已是 **deepseek-v4-flash / v4-pro**（含 v4-pro 75% 促销至 2026-05-31），**调研初稿与 R11 锚点引用的 "DeepSeek-V3.1 $0.56/$1.68" 已与现售页面不一致——这些价格须视为过时，落地前以官方控制台实价为准**。Kimi 官方页现为 Kimi K2.6 / Moonshot V1。**结论**：API 成本/型号变动频繁，**双供应商 + 抽象层（已有 LiteLLM gateway）是正确对冲**，但 API 仅作蒸馏教师/对照，不依赖其价格稳定。
- **解码干预 ⟂ 高吞吐批量架构（已核实的根本张力）**：真·回溯反套话无法原生跑在 vLLM V1 / SGLang 批量服务里。**最大踩坑风险是团队误以为"antislop 能直接塞进 SGLang 生产服务"**——必须按"FTPO 烧权重 + 离线单请求回溯精修"设计，不要指望批量服务内回溯。
- **split-softmax 是未验证自造技术**：放进"绝不妥协"热路径是研究赌博。**主路径用有论文的 activation steering + 记忆注入 + 评测闭环**，split-softmax 降级为纯研究分支。
- **R15 错引风险（地基纠错，必须传达）**：用户记忆把"纯 prompt 对白区分度天花板"挂在 **arXiv:2510.24677(RPNA)** 上——经核实该论文是《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》(医疗 LLM 神经元消融)，与对白区分度**毫无关系**；其"role prompt 只动表层语言风格"的发现若硬外推，反而站在"prompt 确实能改对白表层风格"一侧。**不得拿此错引当地基决策依据。** 另 arXiv:2510.20266 是图像去雾论文(GUSL-Dehaze)，据此构造的"Stylometry of Maintaining Character Voice"引用已剔除。
- **中文质量评测真空**：主流 slop/创作基准偏英文，**中文 slop / 对白可分性度量须自建**，否则反套话与对白区分度无法闭环验证。
- **基准数据陈旧**：可查三方推理基准多为 2024 版本，**不可作最终选型依据**，须自测 goodput。
- **TRT-LLM 迭代摩擦**：编译期 + NVIDIA 锁定，在快速迭代解码策略期是负资产，且让自研 logits processor 几乎不可行。
- **最小部署单元硬约束**：千亿 MoE（如 Kimi K2 FP8）最小 16 GPU——**起步勿盲目上大底座**，按 token 量增长。

---

## 8. Open Questions（需进一步定向实测）

1. **FTPO 在中文 slop + Qwen3 底座上的实际压制率与质量损失** —— Antislop 论文数据基于其测试集，**中文 + 本项目底座须自建 A/B 复现**。[落地前必测]
2. **antislop 单请求回溯后端在 transformers/GGUF 上跑 Qwen3-32B/235B 的实际吞吐与精修延迟** —— 决定"离线精修阶段"的批量调度设计。[no-source-found，须 prototype]
3. **SGLang custom logit processor 钩子能挂多重的 stateful 逻辑** —— 确认它能否承载比"当前步改分布"更复杂的状态（虽不能回溯，但 persona steering 等隐空间干预的接入层级需读源码确认）。
4. **activation steering 在中文角色对白上的实际区分度增益** —— 论文主验英文，中文创作场景须自测 Burrows' Delta 可分性提升。[no-source-found]
5. **2026 最新三方推理基准（vLLM 0.10+/SGLang 0.5+/TRT-LLM v1.2+，H200/B200，中文长上下文）** —— 当前无权威来源，建议以自有底座 + 真实连载 prompt 自测。[no-source-found]
6. **各云商 H100/H200 真实租金 + 本项目真实日均 token 量** —— 盈亏平衡需代入自有数字；最小部署单元（16 GPU for 千亿 MoE）是规模化时的硬门槛。[no-source-found]

---

## 9. 引用验真与剔除记录（对抗式）

**已剔除（exists=false，不得作为证据）：**

1. **Persona Steering / Dashboard for Transparency and Control (arXiv:2405.15076)** — 该 arXiv ID 实际指向数论论文《Refined conjectures on Fitting ideals of Selmer groups over $\mathbf{Z}_p^2$-extensions》(Cédric Dion)，**标题+ID 组合不存在**。调研初稿用它佐证 persona steering，**已剔除**；persona steering 论据改由 ACL 2024 CAA(aclanthology 2024.acl-long.828) + arXiv:2308.10248 + Anthropic Persona vectors 承载（均验真 exists=true）。
2. **DeepSeek News — API Pricing Update September 2025 (deepseek.news/...)** — 域名 deepseek.news **不存在/无索引**，fetch 超时、零检索结果。**已剔除**；DeepSeek 定价以官方 api-docs.deepseek.com 为准（且现售型号已变为 v4-flash/v4-pro，见 §7 风险）。
3. **Helicone — Kimi K2 (Moonshot) Pricing Calculator (helicone.ai/llm-cost/provider/moonshot/...)** — URL 返回 **HTTP 404**，Moonshot 不在 Helicone 支持的 provider 列表。**已剔除**；Kimi 定价以官方 platform.moonshot.ai(→platform.kimi.ai) 为准。

**地基锚点错引（来自 R15，须传达；本就不是本方向直接引用，记录以防误用）：**

4. **arXiv:2510.24677 被误当作"对白区分度天花板"论据** — 实为《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》(医疗 LLM 神经元消融)，与对白区分度无关。**不得作地基决策依据。**
5. **arXiv:2510.20266 同号误配** — 实为图像去雾《GUSL-Dehaze》，据此构造的"Stylometry of Maintaining Character Voice"引用**已剔除**。

**已据验真更正的标题：**

6. arXiv:2308.10248 调研初稿误称 "Activation Addition: Steering Language Models Without Optimization"，**实际标题为《Steering Language Models With Activation Engineering》**(Turner et al.)，已更正。

**关键存活引用（验真 exists=true，high confidence，节选）：**

- vLLM / SGLang / TensorRT-LLM GitHub repos（均活跃）
- antislop-sampler (sam-paech) + arXiv:2510.15061 (ICLR 2026)
- xgrammar (mlc-ai) / slop-forensics (sam-paech)
- vLLM 官方文档：structured_outputs / automatic_prefix_caching / custom_logitsprocs；issue #8581(DRY)、#17799(logits processor RFC)
- LMSYS RadixAttention blog / SGLang v0.4 blog / vLLM V1 blog
- SqueezeBits / BentoML / NVIDIA / Databricks 基准与方法论
- arXiv:2210.15097、2309.09117 (contrastive decoding)
- aclanthology 2024.acl-long.828 (CAA) / arXiv:2308.10248 (activation engineering)
- EQ-Bench Creative Writing v3 / arXiv:2301.05659 / arXiv:2401.16968 (stylometry 武器)
- DeepSeek 官方 pricing 页 / Moonshot(Kimi) 官方 pricing 页（型号已更新，价格须现查）
