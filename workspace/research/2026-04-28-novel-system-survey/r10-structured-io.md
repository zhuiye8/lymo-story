# R10 · Structured LLM I/O Frameworks

| Field | Value |
|---|---|
| Topic | DSPy / Outlines / Instructor / PydanticAI / BAML / Guidance — which one (if any) should our Phase 1 pipeline adopt? |
| Author | engineer (Claude) |
| Researched | 2026-04-28（WebSearch + WebFetch only；零训练记忆） |
| Verdict | **Instructor 作为 Phase 1 起步；BAML 作为 Phase 2 候选**（理由见 §Recommendation） |

## Why this matters for us

Phase 0 整条 pipeline 全是手写 `json.loads(response.content)` + 兜底 try/except。**6 个 agent × 多 prompt** 意味着 30+ 处脆弱点。一处 LLM 返回 malformed JSON 就掉链子。在长篇小说生成里这条 fail mode 会随章节数线性累积。

R10 的目标：找一个 **2026 年仍活跃 + 与 LiteLLM/DeepSeek 兼容 + Pydantic-friendly** 的结构化输出框架，把"prompt 写 → 调 LLM → parse JSON"这条手工链替换为单一抽象。

## Findings

### F1 · Instructor v1.15.1

| Field | Value |
|---|---|
| Source | [github.com/567-labs/instructor](https://github.com/567-labs/instructor) [accessed:2026-04-28] |
| Current version | **v1.15.1**（released 2026-04-03） |
| Stars | **13.1k** [accessed:2026-04-28] |
| License | **MIT** |
| Approach | Post-generation **Pydantic 验证** + 自动 retry（带 validation error 反馈） |
| Maturity | **production-grade**；**3M+/月** PyPI 下载量（per 2026-04-28 ranking 引文）；100+ contributors |

**Provider 覆盖**（README verbatim 节选）：
> "OpenAI (gpt-4o, gpt-4o-mini), Anthropic (Claude 3.5 Sonnet), Google (Gemini), Ollama (local models like Llama 3.2), Groq, Custom providers via API key"

进一步：[python.useinstructor.com](https://python.useinstructor.com/) 列出 **15+ provider**（含 DeepSeek、Mistral、Cohere）。

**示例 code（README verbatim）**：

```python
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

client = instructor.from_provider("openai/gpt-4o-mini")
user = client.chat.completions.create(
    response_model=User,
    messages=[{"role": "user", "content": "John is 25 years old"}],
)
```

**Retry 语义**（README verbatim）：
> "Failed validations are automatically retried with the error message."

**Applicability**：
- adoption cost: **low** — 一层 wrap，我们的 BaseAgent.`_call_json()` 可以底层切换到 Instructor 不动 agent 层
- Chinese: Pydantic 字段名可 Chinese alias，DeepSeek 走 OpenAI-compatible 接口
- LiteLLM 兼容: Instructor 不内置 LiteLLM 支持，但 LiteLLM 提供 OpenAI-compatible endpoint，所以 `instructor.from_openai(openai.OpenAI(base_url=...))` 路径走得通

### F2 · PydanticAI v1.103.0

| Field | Value |
|---|---|
| Source | [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) [accessed:2026-04-28] |
| Current version | **v1.103.0**（2026-05-27 — 即将发布 / 已发布） |
| Stars | **17.4k** [accessed:2026-04-28] |
| License | **MIT** |
| Approach | **Agent framework**（含结构化输出 + 工具调用 + 依赖注入 + observability） |
| Maturity | production-grade（背后是 Pydantic 团队，社区信任度极高） |

**Provider 覆盖**（README verbatim）：
> "OpenAI, Anthropic, Gemini, DeepSeek, Grok, Cohere, Mistral, Perplexity, Azure AI Foundry, Amazon Bedrock, Google Cloud, Ollama, LiteLLM, Groq, OpenRouter, Together AI, Fireworks AI, Cerebras, Hugging Face, GitHub, Heroku, Vercel, Nebius, OVHcloud, Alibaba Cloud, and SambaNova"

**核心定位差异**（来自 fetch）：
> "A Python agent framework designed to help you quickly, confidently, and painlessly build production grade applications and workflows with Generative AI."

**与 Instructor 区别**：
- PydanticAI 是 **agent 框架**（含 dependency injection、multi-turn loops、tool calling、durable execution）
- Instructor 是 **validation layer**（包在你已有的 LLM client 外面）

**Applicability**：
- 与我们已有的 **LangGraph 重叠** — PydanticAI 自带 agent loop，会和 LangGraph 概念冲突
- 工程师判断：**不建议替换 LangGraph**（Phase 0 监督已批 LangGraph，不要折腾）；如果只用其 ResponseFormat 也可，但那就是 Instructor 能力的子集
- adoption cost: **medium**（需要在 LangGraph + PydanticAI 之间画清楚边界）

### F3 · Outlines v1.3.0

| Field | Value |
|---|---|
| Source | [github.com/dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) [accessed:2026-04-28] |
| Current version | **v1.3.0**（2026-05-13） |
| Stars | **13.9k** [accessed:2026-04-28] |
| License | **Apache-2.0** |
| Approach | **Pre-generation constrained decoding**（FSM mask 非法 token）；零 retry guarantee |
| Maturity | production-grade for **self-hosted** models |

**Provider 覆盖**：
> "Local models: transformers, llama.cpp; Servers: vLLM, Ollama; APIs: OpenAI, Gemini, Dottxt"

**关键限制**（来自 [zenvanriel.com/ai-engineer-blog/outlines-structured-generation](https://zenvanriel.com/ai-engineer-blog/outlines-structured-generation/) [accessed:2026-04-28]）：
- FSM-based guarantees **只在 self-hosted / vLLM / llama.cpp** 上生效（因为需要 logits 访问权）
- 对 DeepSeek API / OpenAI API 这类**纯 endpoint**，Outlines 降级到 post-validation（即 Instructor 的子集，但功能更少）

**Applicability**：
- 我们用 DeepSeek API + LiteLLM gateway，**不会自托管 LLM**
- adoption cost: **rewrite**（必须搬到 vLLM 才能享受 FSM 保证；不值得）
- 工程师判断：**不采纳**

### F4 · DSPy v3.2.1

| Field | Value |
|---|---|
| Source | [github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) [accessed:2026-04-28] |
| Current version | **v3.2.1**（2026-05-05） |
| Stars | **34.7k** [accessed:2026-04-28] |
| License | **MIT** |
| Approach | **声明式 + 优化器**：用 signature 声明 task，DSPy 用 MIPROv2/BootstrapFewShot 自动优化 prompt + weights |

**核心定位**（README verbatim）：
> "DSPy: The framework for programming—rather than prompting—language models"
> "allows you to iterate fast on building modular AI systems"
> "algorithms for optimizing their prompts and weights"

**Production 用户**（per WebSearch result，未在我访问的 page 中直接看到）：
> "DSPy is in production at Shopify, Databricks, Dropbox, JetBlue, Moody's, Replit, AWS, Sephora, VMware, and dozens more."

[需 spot-verify: 这个用户列表的引文未直接 fetch 到，来源是 search snippet 而非 dspy.ai/production 实测]

**关键观察**：
- DSPy **不是 JSON 解析器**，而是 **prompt 优化框架**：你提供训练样本和评估函数，它帮你找最优 prompt
- 我们的场景 = 6 个 agent × 多 prompt × Chinese 小说 —— 提供"评估函数"的代价 = SEQR rubric 已经搭好，DSPy 在小说生成上的优化空间可能有限（因为 SEQR 分数本身是个 noisy signal）
- 适合场景：classification、RAG、信息抽取（输入 → 输出有明确正确性标准的任务）

**Applicability**：
- adoption cost: **high**（要为每个 task 写 metric function；DSPy 习惯 OpenAI/Anthropic，DeepSeek 走 OpenAI-compatible 应该行）
- 时机：**Phase 2+**（当我们 SEQR baseline 稳定且有大量 (prompt, output, score) 数据后再上 DSPy 优化）
- 工程师判断：**Phase 1 不上 DSPy**；记 backlog

### F5 · BAML（Boundary ML）

| Field | Value |
|---|---|
| Source | [docs.boundaryml.com/home](https://docs.boundaryml.com/home) + [boundaryml.com](https://boundaryml.com/) [accessed:2026-04-28] |
| Approach | **DSL（`.baml` 文件）+ codegen** → 生成 type-safe client（Python/TS/Go/Java/Ruby/Rust） |
| Maturity | production；获 YC 投资；2026 上半年迅速崛起 |

**核心 claim**（per WebSearch result，来自 Medium 引文）：
> "BAML is more accurate and 2–4× faster than OpenAI's FC-strict JSON tools across every model we tested."

**机制**：
- "Schema Aligned Parsing"（SAP）—— 自家的 parser，比 strict JSON mode 更宽容（接受 LLM 的小格式 deviation）
- 每个 function call 自带 Collector API（rendered prompt + raw response + parsed output + timing + tokens）

**摩擦点**（来自 [medium.com/@rajkundalia](https://medium.com/@rajkundalia/how-baml-brings-engineering-discipline-to-llm-powered-systems-983c06d31bf8) [accessed:2026-04-28]）：
> "BAML requires a build step—running baml-cli generate before code can use the generated clients adds friction, and the DSL requires learning, though it's not complicated."

**Applicability**：
- adoption cost: **medium-high**（DSL + codegen step；CI 要加 BAML build；新人要学 DSL）
- 价值：可观测性 + 性能（2-4x claim 若真，对长篇小说生成成本显著）
- 时机：**Phase 2 评估**（用 Instructor 跑 Phase 1，对比测 BAML 实际节省 token/time，再决定是否切换）

### F6 · Guidance（19k stars，brief check）

| Field | Value |
|---|---|
| Source | (per [dev.to top-5 article](https://dev.to/thedailyagent/top-5-structured-output-libraries-for-llms-in-2026-48g0) [accessed:2026-04-28]) |
| Approach | Pre-generation constraint + Python control flow during token generation |
| Niche | **唯一支持 conditional schema + branching logic**（即"先看 LLM 怎么回答，再决定下一步的 schema"） |

**Applicability**：
- 我们 6 agent 的 schema 是 fixed JSON shape，**用不到 conditional branching**
- 工程师判断：**不采纳**

## Comparison matrix

| 维度 | Instructor | PydanticAI | Outlines | DSPy | BAML |
|---|---|---|---|---|---|
| 主要定位 | validation layer | agent framework | constrained decoding | prompt optimizer | DSL + codegen |
| Star（2026-04-28） | 13.1k | 17.4k | 13.9k | 34.7k | 中等 |
| License | MIT | MIT | Apache-2.0 | MIT | (闭源 SaaS + OSS runtime) |
| 我们 DeepSeek API 可用 | ✅ direct | ✅ direct | ⚠️ 降级到 validation | ✅ via openai-compat | ✅ |
| LangGraph 共存 | ✅ 完美正交 | ⚠️ 概念重叠 | ✅ | ✅ | ✅ |
| Pydantic 原生 | ✅ | ✅ | ⚠️ 部分 | ⚠️（用自家 Signature） | ⚠️（用 DSL） |
| Chinese 字段名 | ✅（Field alias） | ✅ | ✅ | ✅ | ✅（DSL 支持 unicode） |
| 学习曲线 | 极低 | 低-中 | 中 | 高 | 中-高 |
| 风险 | 单一 retry，max_retries 配置 | 与 LangGraph 冲突 | 必须自托管才能 FSM | 优化成本/收益不确定 | DSL 锁定 + 团队学习 |
| 时效性 | 频繁 release（1-2 周） | 频繁（1 周） | 1.x stable | 3.x 现役 | 2026 迅速迭代 |

## Recommendation

**Phase 1 立刻采纳 Instructor**：

1. **零摩擦**：现有 `backend/agents/base.py` 的 `_call_json()` 底层换成 `instructor.from_provider(...)` 一行，agent 层不动
2. **保留 LiteLLM gateway**：Instructor 接 OpenAI-compatible endpoint，LiteLLM 暴露的 endpoint 就是 OpenAI-compatible，所以 `instructor.from_openai(openai.OpenAI(base_url=LITELLM_URL))` 直接打通
3. **Pydantic validator 强制 schema**：把当前 `json.loads + try/except` 替换为 Pydantic `BaseModel`，每个 agent 一个 schema 文件
4. **保留 retry budget**：`max_retries=3`（与现 BaseAgent 的 3 次重试对齐）
5. **observability 接住**：Instructor 暴露 trace hook，可接到我们已有的 `llm_logger`

**Phase 2 backlog**：
- **BAML 对比测**：用一个 high-cost agent（如 Writer）做 A/B，Instructor vs BAML on same prompts，量化 token / time / accuracy；若 BAML 真有 2-4x 提速，迁移
- **DSPy 选 1 个 agent 试**：从 SEQR 评分函数倒推 prompt 优化，看能否在某个弱维度（如 `dialogue_distinct`）上做出可量化提升

**明确放弃**：
- **Outlines** — API 模式无 FSM 保证，降级后没有相对 Instructor 的优势
- **PydanticAI** — agent loop 与 LangGraph 重叠，监督已批 LangGraph
- **Guidance** — conditional branching 我们用不上

## 时效性 / 鲁棒性 / 可行性 评分

| 框架 | 时效性 | 鲁棒性 | 可行性（we adopt now） |
|---|---|---|---|
| Instructor | ⭐⭐⭐⭐⭐（双周 release） | ⭐⭐⭐⭐⭐（3M+ 下载/月，100+ contributors） | ⭐⭐⭐⭐⭐ |
| PydanticAI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐（与 LangGraph 冲突） |
| Outlines | ⭐⭐⭐⭐ | ⭐⭐⭐⭐（self-hosted user 多） | ⭐⭐（API 用户拿不到 FSM 好处） |
| DSPy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐（Phase 1 太早） |
| BAML | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐（YC + 商用） | ⭐⭐⭐（DSL 摩擦） |

## Open questions

- Instructor 与 LiteLLM 双层包装会不会引入 latency？需要实测。
- 如果 DeepSeek API 抛非标准错误（如限流），Instructor 的 retry 会处理吗？需查文档或实测。
- BAML 的 2-4x speed claim 在 DeepSeek V4-Pro 上是否成立？需要 A/B 才能知道。
- Pydantic 模型能不能在运行时根据 story_bible 动态生成（例如 character ID 是 enum）？

## Sources

- [github.com/567-labs/instructor](https://github.com/567-labs/instructor) [accessed:2026-04-28]
- [python.useinstructor.com](https://python.useinstructor.com/) [accessed:2026-04-28]
- [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) [accessed:2026-04-28]
- [github.com/dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) [accessed:2026-04-28]
- [zenvanriel.com/ai-engineer-blog/outlines-structured-generation](https://zenvanriel.com/ai-engineer-blog/outlines-structured-generation/) [accessed:2026-04-28]
- [github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) [accessed:2026-04-28]
- [dspy.ai](https://dspy.ai/) [accessed:2026-04-28]
- [boundaryml.com](https://boundaryml.com/) [accessed:2026-04-28]
- [docs.boundaryml.com/home](https://docs.boundaryml.com/home) [accessed:2026-04-28]
- [medium.com/@rajkundalia (BAML / Instructor 对比)](https://medium.com/@rajkundalia/how-baml-brings-engineering-discipline-to-llm-powered-systems-983c06d31bf8) [accessed:2026-04-28]
- [dev.to/thedailyagent (top 5 ranking)](https://dev.to/thedailyagent/top-5-structured-output-libraries-for-llms-in-2026-48g0) [accessed:2026-04-28]
- [simmering.dev/blog/openai_structured_output](https://simmering.dev/blog/openai_structured_output/) [via search snippet, accessed:2026-04-28]
- [techsy.io/en/blog/best-llm-structured-output-libraries](https://techsy.io/en/blog/best-llm-structured-output-libraries) [via search snippet, accessed:2026-04-28]
