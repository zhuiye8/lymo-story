# R6 · Anti-Slop / 文笔质量

| Field | Value |
|---|---|
| Topic | LLM 输出 "slop"（重复套话 / AI-tell）的检测与抑制：当前 2026 SOTA 在小说生成上如何应用 |
| Author | engineer (Claude) |
| Researched | 2026-04-28（WebSearch + WebFetch only；零训练记忆） |
| Verdict | **三层防御**：(1) Phase 1 立即接 Antislop Sampler 做推理时抑制；(2) detector v1.1 frequency-aware tier1（Phase 0 backlog 兑现）；(3) Phase 3+ 评估 FTPO 微调（如果我们有自家 model） |

## Why this matters for us

Phase 0 SEQR 数据点出三个相关信号：
- `rhetoric_quality` ρ=−0.16（工程师 vs LLM judge 评分反向，说明 LLM judge 对中文套话不敏感）
- detector v1 在 PD 段落（朱自清《歌声》"仿佛一个暮春的早晨"等）误判，因为单次使用 `仿佛` 被 tier1 一刀切扣 1.5 分
- 21 章 baseline 里 `tier1_banned` 命中 15 次，是 LLM slop 头号来源

R6 任务：找 2026 年的 SOTA，特别是 paper-grade evidence，决定 Phase 1 怎么改造现有 slop detector + 加新的推理时抑制层。

## Findings

### F1 · Antislop（ICLR 2026 paper） — 决定性 SOTA

| Field | Value |
|---|---|
| Paper | [arxiv.org/abs/2510.15061](https://arxiv.org/abs/2510.15061) [accessed:2026-04-28] |
| Venue | **ICLR 2026** |
| Authors | Samuel Paech, Allen Roush, Judah Goldfeder, Ravid Shwartz-Ziv |
| Code | [github.com/sam-paech/auto-antislop](https://github.com/sam-paech/auto-antislop)（MIT license per paper §6） |

**Abstract verbatim 关键节选**：

> "Widespread LLM adoption has introduced characteristic repetitive phraseology, termed 'slop,' which degrades output quality and makes AI-generated text immediately recognizable. We present Antislop, a comprehensive framework providing tools to both detect and eliminate these overused patterns."

**三件套**：

#### (a) Antislop Sampler — 推理时抑制（重要）

- 实现：[github.com/sam-paech/antislop-sampler](https://github.com/sam-paech/antislop-sampler) [accessed:2026-04-28]
- Stars: 345，Apache-2.0
- 机制：**backtracking** — 当 LLM 准备输出 disallowed phrase 时，rewind + retry with 调整后的 token probabilities
- 集成方式：HuggingFace transformers 的 `chat_antislop()` / `generate_antislop()`
- 关键参数：`slop_phrase_prob_adjustments`（dict，形如 `["testament to", 0.5]`，value 是概率压缩系数）
- 性能（paper 报告）：**8,000+ patterns 同时抑制**而不降质，相对地纯 token banning 在 2,000 patterns 就 unusable

**对我们的可行性**：
- ⚠️ **DeepSeek API 无 logits 访问** → Antislop Sampler **不能直接用**（它需要在 forward pass 中介入 logits）
- ✅ 但是其 **slop word list 可以直接抄**（已 release 在 repo）作为我们 detector v1.1 的扩展词库
- ✅ 自托管阶段（若 Phase 4+ 上 vLLM）则可全力使用

#### (b) Automated profiling pipeline

- 对每个 model 跑出 "model-specific slop"（vs human baseline）
- 我们的应用：跑 DeepSeek V4-Pro 的 slop profile（中文版），找出 DeepSeek 特有的中文套话

#### (c) FTPO — Final Token Preference Optimization（微调）

- 关键 claim：**"FTPO achieves 90% slop reduction while maintaining or improving performance in cross-domain evals including GSM8K, MMLU, and creative writing tasks. In contrast, DPO suffers significant degradation in writing quality and lexical diversity despite achieving weaker suppression."**
- 机制：LoRA 微调，只对 "banned pattern 在 inference trace 里出现的那个 final token" 调整 logits；多个 preferred tokens 同时更新（对比 DPO 的单 token）
- **优于 DPO**：DPO 牺牲写作质量换抑制；FTPO 不牺牲

**对我们的可行性**：
- 🟡 **Phase 1 不上**：我们用 DeepSeek API，没有自家 model 可微调
- ✅ **Phase 3+ 考虑**：如果未来切换到自托管 Qwen3/GLM-4.6/DeepSeek-OSS，FTPO 是最值得跑的实验

### F2 · Slop Forensics — 数据 / Profile 工具

| Field | Value |
|---|---|
| Repo | [github.com/sam-paech/slop-forensics](https://github.com/sam-paech/slop-forensics) [accessed:2026-04-28] |
| Stars | 332 |
| License | MIT |
| 用途 | 给定 model 跑出 single-word / bigram / trigram / 多词 slop list；建模型 phylogenetic tree（看哪些 model "亲戚"近） |

**对我们的可行性**：
- ✅ **Phase 1 立即用**：跑一遍 DeepSeek V4-Pro 在中文小说上的 slop profile，把高频结果加到我们 detector v1.1 的词库
- ⚠️ **不支持中文**：NLTK English-only tokenizer/stopwords；移植到中文需要替换分词为 jieba + 中文停用词；约 1 天工作量
- 可行性 = high

### F3 · autonovel evaluate.py — 我们已经在用

| Field | Value |
|---|---|
| Repo | [github.com/NousResearch/autonovel](https://github.com/NousResearch/autonovel) [accessed:2026-04-28] |
| Stars | ~1,000 |
| License | **NO LICENSE FILE**（per R4 agent finding）→ 只能借鉴思路，不能 copy code |
| 我们的现状 | Phase 0 `backend/quality/slop_detector.py` 是 evaluate.py 的中文化 port |

**autonovel 的更新值得抄的点**：
- `ANTI-SLOP.md`：词级 AI pattern 词库（更新更频，我们可以定期拉新）
- `ANTI-PATTERNS.md`：结构 AI pattern（我们已有 `不仅仅是…更是…` 等）
- `adversarial_edit.py`：分类哪些字可以删——值得我们 Phase 2 实现作为"修剪" agent
- `compare_chapters.py`：**Elo tournament** between chapter versions——可以替代我们当前的 fixed-threshold consistency 判断

**对我们的可行性**：
- ✅ 已使用；继续跟进新 patterns
- ⚠️ license 风险：必须自己写代码，不能 copy；这一点 Phase 0 已经做对（我们自己 port 的）

### F4 · Two-Layer Validator（Ozigi 产品博客）

| Field | Value |
|---|---|
| Source | [blog.ozigi.app/blog/stopping-ai-slop-in-production-banned-lexicon-validator](https://blog.ozigi.app/blog/stopping-ai-slop-in-production-banned-lexicon-validator) [accessed:2026-04-28] |
| Type | 产品博客（非 paper） |

**架构**：
- Layer 1（prompt）：在 prompt 里嵌入"不要用 X / 不要 Y"的负向指令
- Layer 2（code）：四类检测 pass — **vocabulary / phrases / openers / regex structures**；触发即"one bounded repaired retry"

**banned 例子（verbatim）**：
- Vocabulary tells: `delve, tapestry, robust, seamlessly, paradigm`
- Corporate fluff: `cutting-edge, game-changer, thought leadership`
- AI tells: `"at its core," "plays a significant role," "in today's fast-paced"`
- Structural: `**Term:**` bold-colon prefix；`It's not X. It's Y.` contrast structure；同词 3+ 连续 sentence openers

**对我们的可行性**：
- ✅ **Layer 1 立即抄**：anti-slop 指令进 prompt（Phase 1 改 prompt 时一并）
- ✅ **Layer 2 我们已有**（detector v1）；扩到 4 类 detection pass
- 缺：未给 GitHub 代码，要自己写

### F5 · 中文 anti-cliché 现状（gap finding）

**搜索 `Chinese 网文 anti-cliché LLM 文笔 套话 检测 2026` 的结果**：
- [blog.lyc8503.net/post/llm-classifier](https://blog.lyc8503.net/post/llm-classifier/) — 网文 AIGC **检测** 经典 ML 方法（FP < 0.01% at 70% threshold）；但**目标是分类人写 vs LLM 写**，**不是抑制 slop**
- [EnsemJudge (arXiv:2603.27949)](https://arxiv.org/pdf/2603.27949) — NLPCC2025 Shared Task 1 第一名；中文 LLM-generated text **detection** ensemble；**同样不是抑制方向**

**结论（labeled `[no-source-found:topic-likely-undeveloped]`）**：
- 搜不到专门做中文小说 **anti-slop 抑制 / 词库** 的学术或开源 paper
- 这是一个**真空地带**：中文 LLM 套话词库（`心底深处 / 命运的齿轮 / 仿佛 / 千丝万缕`）需要自己整理
- 我们 Phase 0 的 `TIER1_BANNED_ZH` 是目前已知的（小规模）首批工程化样本
- 战略意义：如果 Phase 1+ 我们整理出 1000+ 中文 slop 词条 + 工程化抑制管道，**可发表**或至少在中文 LLM 社区获得显著影响力

### F6 · LLM-as-judge 多评委合议（Critic Room）

#### EQ-Bench Creative Writing v3

- Source（via search snippet）：[llm-stats.com/benchmarks/creative-writing-v3](https://llm-stats.com/benchmarks/creative-writing-v3) [accessed:2026-04-28]
- 机制：**32 prompts × 3 iterations**；rubric + **Elo pairwise comparison**；与人类 preference rank 相关性 **98.6%**

**对我们的可行性**：
- ✅ **Phase 6 Critic Room 设计直接参考**：多 judge LLM + pairwise + Elo aggregation
- ⚠️ 成本：每章生成多版本 + 多评委成本会乘起来；Phase 0 单章 ¥0.055 → 加 critic room 可能 ¥0.5+/章；监督要重新评估 AC4 cost 上限

#### Awesome-LLM-as-a-Judge

- Source: [github.com/llm-as-a-judge/Awesome-LLM-as-a-judge](https://github.com/llm-as-a-judge/Awesome-LLM-as-a-judge) [accessed:2026-04-28]
- 类型：综述 repo，列出 50+ paper / tool
- 用途：找 specific niche judges（如 dialogue judge / coherence judge / 中文 judge）

## Comparison: 抑制方法 vs 我们 stack

| 方法 | 接入位置 | 不需要 logits | DeepSeek API ✓ | 中文支持 | Phase 1 可用 | 长期价值 |
|---|---|---|---|---|---|---|
| **prompt 负指令**（Two-Layer 的 Layer 1） | prompt 顶部 | ✅ | ✅ | ✅（要翻译指令） | ✅ 立即 | 低（model 易忽略） |
| **detector v1**（autonovel port，已有） | 生成后扫描 | ✅ | ✅ | ✅（我们的中文词库） | ✅ 已有 | 中 |
| **detector v1.1 frequency-aware tier1**（Phase 0 backlog） | 同上 | ✅ | ✅ | ✅ | ✅ | 中-高（修我们已知 FP） |
| **Antislop Sampler**（backtracking 推理时） | LLM forward pass | ❌ | ❌ | 要中文 slop list | ❌ | 极高（必须自托管才能用） |
| **FTPO 微调** | weights | ❌ | ❌ | 需中文 prefer pairs | ❌ | 极高（自家 model 后） |
| **Critic Room** (EQ-Bench style) | post-generation | ✅ | ✅ | ✅ | 🟡 cost 待评估 | 高 |
| **slop-forensics profile**（DeepSeek 中文 slop list 抽取） | 离线分析 | ✅ | ✅ | 需移植中文分词 | ✅ 1 天工作量 | 高（输入给 detector + prompt） |
| **adversarial_edit 修剪 agent** | post-generation | ✅ | ✅ | ✅ | 🟡 Phase 2 | 中-高 |

## Recommendation

### Phase 1（立即）

1. **slop_detector v1.1 frequency-aware tier1**（Phase 0 backlog 兑现）
   - `仿佛 / 犹如 / 宛如 / 如同 / 在心底深处` 等单次合法的 metaphor word：单次不扣，2+ in same paragraph 才扣（修我们已知 FP 案例如鲁迅《社戏》"仿佛是踊跃的铁的兽脊"）
   - 验收：runs against AC3 v5 PD corpus, precision_pd_excerpt **由 0.97 → 1.00**

2. **prompt 层 anti-slop 指令**（参考 Two-Layer Layer 1）
   - 在 Writer agent 的 prompt 顶部加 negative instruction list
   - 中文化（"不要用：仿佛 / 犹如 / 宛如 / 如同 / 千丝万缕 / 命运的齿轮 / ..."）
   - 在 prompt 里给反例 + 正例

3. **slop-forensics 中文化 + DeepSeek profile**
   - fork repo，把 NLTK English tokenizer 换成 jieba；停用词换成中文
   - 让它跑 DeepSeek V4-Pro 在中文小说生成上的 specific slop list
   - 把高频结果加进我们的 `TIER1_BANNED_ZH`
   - 工作量：1 天

4. **autonovel ANTI-SLOP.md / ANTI-PATTERNS.md 跟进**
   - 定期（每月）抓取最新版本，diff 出新 patterns，移植到中文

### Phase 2（中期）

5. **Critic Room（EQ-Bench inspired）**
   - 3 个 judge LLM 对每章给评分 + 一对一 Elo
   - 与 AC4 cost 上限重新协调（监督决定）
   - 单章 cost 估算：3 × ¥0.05 + Elo overhead ≈ ¥0.2-0.3

6. **adversarial_edit "修剪"  agent**
   - 接受 Writer 的稿，分类哪些字 / 短语可删而不损意；让 Writer 重写后保留删字理由

### Phase 3+（条件触发）

7. **Antislop Sampler**：仅当我们切到自托管 LLM（vLLM/llama.cpp）才能用；否则跳过

8. **FTPO 微调**：当我们有 (instruction, prefer, reject) 对 + 自家 model 后，跑 LoRA FTPO 实验；目标 SEQR rhetoric_quality 提升 +1 分

## 时效性 / 鲁棒性 / 可行性 评分

| 方案 | 时效性（when published） | 鲁棒性 | 可行性（Phase 1） |
|---|---|---|---|
| slop_detector v1.1 | 我们自家 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| prompt anti-slop 指令 | 2026 业界共识 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| slop-forensics 中文化 | 2025 repo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐（1 天） |
| Antislop Sampler | ICLR 2026 SOTA | ⭐⭐⭐⭐⭐ | ⭐（API 不行） |
| FTPO 微调 | ICLR 2026 SOTA | ⭐⭐⭐⭐⭐ | ⭐（无自家 model） |
| Critic Room | EQ-Bench v3 | ⭐⭐⭐⭐ | ⭐⭐⭐（cost） |

## Open questions

- DeepSeek V4-Pro / Qwen3 / GLM-4.6 哪个在 prompt 层 anti-slop 服从最好？需 A/B 测。
- 中文 slop 词库的 ground-truth：我们 21 章 + 22 wikisource PD 段落是否足够训练 slop-forensics？应该不够，可能要扩到 100+ 章。
- Critic Room 的"评委多样性"：用 3 个 DeepSeek 评委 vs DeepSeek+Qwen+GLM 评委，哪个 ICR（inter-rater correlation）更接近 hum?
- FTPO + 中文：原 paper 是英文。中文 token 化方式不同（BPE 中文 token 短），FTPO 在中文 logits 上的效果未验证。

## Sources

- [arxiv.org/abs/2510.15061 (Antislop paper)](https://arxiv.org/abs/2510.15061) [accessed:2026-04-28]
- [openreview.net (ICLR 2026 ANTISLOP)](https://openreview.net/pdf/6916f45661bf884811be66da937b7467b97a9114.pdf) [accessed:2026-04-28; PDF binary not parseable via WebFetch, abstract via WebSearch]
- [emergentmind.com/topics/final-token-preference-optimization-ftpo](https://www.emergentmind.com/topics/final-token-preference-optimization-ftpo) [via search snippet, accessed:2026-04-28]
- [github.com/sam-paech/antislop-sampler](https://github.com/sam-paech/antislop-sampler) [accessed:2026-04-28]
- [github.com/sam-paech/slop-forensics](https://github.com/sam-paech/slop-forensics) [accessed:2026-04-28]
- [github.com/sam-paech/auto-antislop](https://github.com/sam-paech/auto-antislop) [via paper §6, accessed:2026-04-28]
- [github.com/NousResearch/autonovel](https://github.com/NousResearch/autonovel) [accessed:2026-04-28]
- [blog.ozigi.app/.../stopping-ai-slop-in-production](https://blog.ozigi.app/blog/stopping-ai-slop-in-production-banned-lexicon-validator) [accessed:2026-04-28]
- [llm-stats.com/benchmarks/creative-writing-v3 (EQ-Bench Creative Writing v3)](https://llm-stats.com/benchmarks/creative-writing-v3) [via search snippet, accessed:2026-04-28]
- [github.com/llm-as-a-judge/Awesome-LLM-as-a-judge](https://github.com/llm-as-a-judge/Awesome-LLM-as-a-judge) [via search snippet, accessed:2026-04-28]
- [blog.lyc8503.net/post/llm-classifier (Chinese 网文 AIGC detection)](https://blog.lyc8503.net/post/llm-classifier/) [via search snippet, accessed:2026-04-28]
- [arxiv.org/pdf/2603.27949 (EnsemJudge)](https://arxiv.org/pdf/2603.27949) [via search snippet, accessed:2026-04-28]
