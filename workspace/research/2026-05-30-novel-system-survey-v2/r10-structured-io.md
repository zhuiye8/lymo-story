# R10 · Structured LLM I/O —— Phase 1 选型终稿(v2)

> 优先级档位 **A** · 调研日期全程 `[accessed:2026-05-30]` · 本稿为 v2 终稿,基于 clean-room 调研稿 + 全量引用验真 + 基础事实核查综合而成。
>
> 锚定上下文:现有栈 = DeepSeek API + LiteLLM gateway + LangGraph 六 agent;所有 prompt/产出为中文;大量结构化产物(Story Bible JSON、角色记忆、世界事件、章节 beats、一致性检查报告)。
>
> 优先级提醒(用户给定):记忆(R2)= 角色(R5)= 大纲(R1)> 图谱(R3)。R10 本身是 A 档基础设施,**其价值在于为这些高优先级子系统提供可靠的结构化输入/输出**(Bible→大纲、记忆抽取、角色卡、一致性报告全都吃 R10 的成果),所以落地排序按"谁喂养 S 档子系统"来定。

---

## 为什么这对我们重要(背景,沿用 v1)

Phase 0 整条 pipeline 全是手写 `json.loads(response.content)` + 兜底 try/except。**6 个 agent × 多 prompt** 意味着 30+ 处脆弱点,一处 LLM 返回 malformed JSON 就掉链子。在长篇小说生成里,这条 fail mode 会随章节数线性累积。R10 的目标:找一个 **2026 年仍活跃 + 与 LiteLLM/DeepSeek 兼容 + Pydantic-friendly** 的结构化输出框架,把"prompt 写 → 调 LLM → parse JSON"这条手工链替换为单一抽象,并把它落到 `BaseAgent._call_json()` 内部而不动 agent 层。

---

## 0. 决定整个选型逻辑的硬约束(v2 新增的核心分析)

**DeepSeek 没有 final-message 的 json_schema 约束解码能力。** DeepSeek 官方 API 文档把 `response_format.type` 只列为 `text` 或 `json_object`(后者只保证语法是合法 JSON,不保证符合你的 schema),不支持把普通 `response_format` 设为 `json_schema` 做最终消息的结构化输出 —— https://api-docs.deepseek.com/guides/json_mode `[accessed:2026-05-30]`。

唯一的 schema 强约束在 **beta 端点的 strict 工具调用**(base_url 设为 `https://api.deepseek.com/beta`、每个 function 加 `strict:true`)—— https://api-docs.deepseek.com/guides/function_calling `[accessed:2026-05-30]`。但这条路有一个**已知 bug 且官方 closed as not planned**:strict 模式下 `function.arguments` 返回的 JSON 第一个 key 缺右引号(返回 `{"selected: [...]}` 而非 `{"selected": [...]}`)、无法解析 —— https://github.com/deepseek-ai/DeepSeek-V3/issues/1069 `[accessed:2026-05-30]`(状态:**Closed as not planned**,即官方近期不会修)。

LiteLLM 侧印证同一约束:有用户报 DeepSeek 走 `response_format` 报错 `response_format.type 'json_schema' is unavailable now`,该 issue 被 **closed as not planned** —— https://github.com/BerriAI/litellm/issues/7580 `[accessed:2026-05-30]`。LiteLLM 的 `json_schema` 原生支持名单是 OpenAI/Azure/Gemini/Vertex/Bedrock 等,DeepSeek 不在其中;它给的兜底是 `enable_json_schema_validation=True` 做**客户端**校验 —— https://docs.litellm.ai/docs/completion/json_mode `[accessed:2026-05-30]`。

**这条约束的直接推论:**
- "靠约束解码保证 100% 合规"这一整条路线(Outlines / Guidance 的核心卖点)对你们**当前栈无效** —— 它们的 FSM/CFG token-mask 只能作用于本地权重(transformers/vLLM/llama.cpp),对远端 DeepSeek API 只能退化成普通 JSON mode。
- 你们的真问题不是"如何在解码时约束",而是 **"如何在 DeepSeek 返回脏 JSON / markdown 包裹 / reasoning 前缀时仍稳健拿到合法对象,并在 schema 不符时自动重问"**。这把价值锚定到 **robust parsing + reask(Instructor)** 或 **schema-aligned parsing(BAML)**。

> ⚠️ **v2 新增的模型层提醒(来自基础事实核查,直接影响本约束的适用范围):** 上述约束是"绑定 DeepSeek"前提下成立的。但 2026 年的中文创意写作实测显示,**Kimi K2.6 在创意写作 + 角色扮演双榜第一(超 GPT-5),DeepSeek V4 系列强在知识/推理与极致性价比、文笔评测无专项突出**(来源见 §6)。这意味着:若 Writer 之外的某些结构化 agent 将来切到别的模型,**本约束(无 final-message json_schema)是否成立要按模型重新核**。例如若引入支持 native json_schema 的模型,Instructor 可走 `Mode.JSON_SCHEMA`/tool 路而非 MD_JSON。因此本方案的设计目标之一是 **provider-中立**:Instructor-over-LiteLLM 天然让"换模型 = 换 binding",不锁死在 DeepSeek 的能力边界上。

---

## 1. 六候选逐一评估(时效性 / 鲁棒性 / 可行性)

### 1) Instructor(567-labs/instructor)—— ✅ 推荐主选
- 来源:https://github.com/567-labs/instructor `[accessed:2026-05-30]`(验真:exists=true,"Structured Outputs for LLMs",Pydantic 校验)
- **时效性**:最新 v1.15.1(2026-04-03),108 个 release,活跃,production。PyPI 在线 —— https://pypi.org/project/instructor/ `[accessed:2026-05-30]`(验真:exists=true,作者 Jason Liu / Ivan Leo)。
- **鲁棒性**:13.1k star,MIT,3M+/月下载 —— 官网 https://python.useinstructor.com/ `[accessed:2026-05-30]`(验真:exists=true,"the most popular Python library for extracting structured data from LLMs")。核心机制 = **Pydantic 校验 + reask 自愈循环**:`max_retries=N`,校验失败把 Pydantic 的 `ValidationError` 反馈回模型让它改,全部失败抛 `InstructorRetryException` —— https://python.useinstructor.com/concepts/retrying/ `[accessed:2026-05-30]`(验真:exists=true,实际标题 "Retry Logic with Tenacity",基于 Tenacity 实现重试)。
- **DeepSeek 兼容**:官方有专页 —— https://python.useinstructor.com/integrations/deepseek/ `[accessed:2026-05-30]`(验真:exists=true,覆盖同步/异步、嵌套对象、流式、推理模型,并给出 `https://api.deepseek.com` base_url 配置)。默认 `Mode.Tools`(走 DeepSeek 的 tool calling);`deepseek-reasoner`(R1)推荐用 `Mode.MD_JSON`,并能从 `raw_completion` 的 `message.reasoning_content` 取推理链。
- **LiteLLM 共存(关键,v2 纠正 v1)**:`instructor.from_litellm(completion)` 直接 patch 现有的 `litellm.completion`;也能 patch LiteLLM Router;async 用 `acompletion` —— https://python.useinstructor.com/integrations/litellm/ `[accessed:2026-05-30]`(验真:exists=true)+ LiteLLM 官方 instructor 教程 https://docs.litellm.ai/docs/tutorials/instructor `[accessed:2026-05-30]`(验真:exists=true,"combine LiteLLM with jxnl's instructor library")。**意味着零新增网关、不动 model binding 体系。**(v1 误以为 Instructor 不内置 LiteLLM 支持、要绕 OpenAI-compat 端点;实则有官方 `from_litellm` 一等公民集成。)
- **LangGraph 共存**:Instructor 不是 agent 框架,只在 node 内部把"裸 LLM 调用 → 结构化对象"这一步替换掉,与 LangGraph 正交,无冲突。
- **中文就绪度**:与语言无关,prompt 仍是你自己写的中文;reask 反馈也用模型自己的语言,对中文产出无额外负担。
- **adoption cost = low**。已知坑:Instructor 的严格 JSON parser 对 markdown 包裹 / CoT 前缀的容错弱于 BAML SAP(见下对比),但 DeepSeek 走 Tools 模式时这点风险被工具调用的结构化协议大幅缓解。

### 2) BAML(BoundaryML/baml)—— 强力备选 / 鲁棒性天花板(Phase 1.5 escape hatch)
- 来源:https://github.com/BoundaryML/baml `[accessed:2026-05-30]`(验真:exists=true,"adds the engineering to prompt engineering",Apache-2.0,8.3k star,347 releases)
- **时效性**:最新 v0.222.0(2026-04-27),347 个 release,周更,production。
- **鲁棒性**:8.3k star,Apache-2.0,Rust 内核。杀手锏 = **SAP(Schema-Aligned Parsing)**:即使模型不支持 native tool calling,也能从"JSON 里夹 markdown、回答前带 CoT、多余空白、部分残缺"中恢复结构化对象 —— 技术原理见 https://boundaryml.com/blog/schema-aligned-parsing `[accessed:2026-05-30]`(验真:exists=true,"assumes LLM outputs will contain errors",用 edit-distance 纠正 malformed JSON / 类型不符 / 未转义字符)。官网 https://boundaryml.com/ `[accessed:2026-05-30]`(验真:exists=true,"Basically A Made-Up Language")。明确支持 DeepSeek-R1 及 OpenAI 兼容端点(Ollama/OpenRouter/vLLM/LMStudio/TogetherAI)。
- **LangGraph 共存**:成熟模式 —— `.baml` 定义编译成 `baml_client`(里面是 Pydantic 模型),node 里 `from baml_client import b`;安装/codegen 见 https://docs.boundaryml.com/guide/installation-language/python `[accessed:2026-05-30]`(验真:exists=true,`pip install baml-py` + `baml-cli init/generate`);公开范例仓库 Hekmatica(BAML+LangGraph deep research)https://github.com/kargarisaac/Hekmatica `[accessed:2026-05-30]`(验真:exists=true,"agent implemented using BAML and LangGraph")。
- **代价**:引入一门 DSL(`.baml` 文件)+ 构建步(codegen);社区比 Instructor 小(8.3k vs 13.1k)。**adoption cost = medium**。
- **选它的唯一充分理由**:当实测发现 DeepSeek 输出脏到 Instructor reask 都频繁失败、成本/延迟不可接受;或将来要多语言客户端共享 schema(reader 是 TS,BAML 可同时产 Python+TS client)。中文无特殊问题。
- **v2 对 v1 "2-4× 提速"claim 的纠正**:v1 引用 Medium 文称 BAML 比 OpenAI FC-strict "2-4× faster",该数字来自第三方博客且未独立验真,**不应作为选型硬依据**;选 BAML 的真实理由是 SAP 的脏输出鲁棒性与多语言 codegen,而非速度数字。速度是否成立须按 §4 open question 自行 A/B。

### 3) PydanticAI(pydantic/pydantic-ai)—— 仅当你顺带要换 agent 编排才考虑
- 来源:https://github.com/pydantic/pydantic-ai `[accessed:2026-05-30]`(验真:exists=true,"AI Agent Framework, the Pydantic way",MIT,17.4k star)
- **时效性**:v1.104.0(2026-05-29,就在调研当天),production,势头极猛。(v1 记的是 v1.103.0 / 2026-05-27,v2 据当日实查更新到 v1.104.0。)
- **鲁棒性**:17.4k star(六者最高),MIT。支持 LiteLLM 与 DeepSeek 作为 provider,支持流式结构化输出 + 即时校验 + 校验失败 reflection 重试 —— 官方文档 https://ai.pydantic.dev/ `[accessed:2026-05-30]`(验真:exists=true,301 跳转到 pydantic.dev/docs/ai/overview/,"GenAI Agent Framework")。
- **LiteLLM 通道**:除官方 provider 外,社区包 `pydantic-ai-litellm` 完整支持 tool/stream/structured over LiteLLM 100+ provider —— https://pypi.org/project/pydantic-ai-litellm/ `[accessed:2026-05-30]`(验真:exists=true,作者 Mottakin Chowdhury,MIT,v0.2.6)。
- **LangGraph 共存**:可"增量"共存(PydanticAI agent 作为 LangGraph node 落入),但**二者功能重叠**(都管 agent loop/tool/编排)—— 对比见 https://www.zenml.io/blog/pydantic-ai-vs-langgraph `[accessed:2026-05-30]`(验真:exists=true)。
- **判断**:对 Phase 1 是"杀鸡用牛刀"。你们已有 LangGraph 做编排,仅为结构化 I/O 引入 PydanticAI 会带来两套 agent 抽象的概念冲突。**adoption cost = medium~high**(只取其结构化输出部分不如直接用 Instructor;整体迁移编排到 PydanticAI 是 rewrite 级)。除非你们本就对 LangGraph 不满意想换,否则 Phase 1 不建议上。中文无特殊问题。(此结论与 v1 一致,v2 补齐了 LiteLLM 双通道证据。)

### 4) Outlines(dottxt-ai/outlines)—— Phase 1 用不上其核心价值
- 来源:https://github.com/dottxt-ai/outlines `[accessed:2026-05-30]`(验真:exists=true,"Structured outputs for LLMs","guarantees structured outputs during generation");Rust 内核 https://github.com/dottxt-ai/outlines-core `[accessed:2026-05-30]`(验真:exists=true,"Faster structured generation")
- **时效性**:v1.3.0(2026-05-13),活跃,production。
- **鲁棒性**:13.9k star,Apache-2.0。核心是 FSM/CFG **约束解码,需作用于本地权重**(transformers/llama.cpp/vLLM/Ollama/SGLang)。对 API 模型只能走它们各自的 JSON 能力,**拿不到 token-level 约束**。
- **反向证据(v2 新增)**:JSONSchemaBench(arxiv 2501.10868,https://arxiv.org/abs/2501.10868 `[accessed:2026-05-30]`,验真:exists=true,"10K real-world JSON schemas")指出 Outlines 在复杂 schema 上编译慢且因超时导致合规率在被测引擎中偏低。
- **判断**:与你们当前(远端 DeepSeek API)不匹配。仅当将来自托管开源模型(vLLM/SGLang 自部署 —— 例如基础事实核查里提到的 Qwen 3.6-Plus Apache-2.0 本地部署路线)才值得回看。**adoption cost(API 场景)= 不适用**。(结论与 v1 一致:不采纳;v2 补了 JSONSchemaBench 量化反向证据。)

### 5) Guidance(guidance-ai/guidance)—— 同 Outlines,本地导向
- 来源:https://github.com/guidance-ai/guidance `[accessed:2026-05-30]`(验真:exists=true,"A guidance language for controlling LLMs",21.5k star,MIT,v0.3.2 / 2026-03-18)
- **时效性**:v0.3.2(2026-03-18),仍有 2026 活跃 issue,production 但更偏研究/本地。
- **鲁棒性**:21.5k star,MIT。支持 regex/CFG 约束 + 控制流交织,但精髓(token-level 约束、交织生成)同样要本地权重才发挥;对 DeepSeek API 退化为普通调用。姊妹项目 llguidance(给 serving 框架用的约束引擎)https://github.com/guidance-ai/llguidance `[accessed:2026-05-30]`(验真:exists=true,"Super-fast Structured Outputs")也是自部署场景的东西。
- **判断**:Phase 1 不选,理由同 Outlines(v1 也判不采纳,理由是"用不到 conditional branching";v2 给出更根本的理由 —— 其 token-level 约束对远端 API 无效)。**adoption cost(API 场景)= 不适用/high**。

### 6) DSPy(stanfordnlp/dspy)—— 解决的是另一个问题(prompt 优化),正交
- 来源:https://github.com/stanfordnlp/dspy `[accessed:2026-05-30]`(验真:exists=true,"framework for programming—rather than prompting—language models",Stanford NLP,34.7k star,MIT)
- **时效性**:v3.2.1(2026-05-05),production,34.7k star。
- **定位**:`programming not prompting` 的 prompt/权重优化框架(signatures + optimizer),**不是结构化输出库**。DSPy 使用 LiteLLM 做模型路由(经其官方 API 文档 `dspy.ai/api/models/LM/` 与 GitHub README 确认 —— 见下方 diff 中的 URL 纠正说明),与你栈天然兼容。
- **判断**:**正交,不是 R10 的答案**。DSPy 的 Signature 确实能定义输入输出结构,但它的价值在**自动优化 prompt**(few-shot / instruction tuning),属于另一个方向。Phase 1 不应为"结构化 I/O"引入 DSPy;但**值得标记为后续 R 方向候选** —— 当你有了评测集(你们 SEQR rubric 已搭)想自动调各 agent 的中文 prompt 时(这与 S 档的大纲/记忆/角色质量直接相关),DSPy 是该方向的一线选手。**adoption cost(作为结构化 I/O 用)= 不划算**。(与 v1 结论一致:Phase 1 不上、记 backlog。)

---

## 2. 横向对比表

| 方案 | 版本/日期 | star | license | maturity | 解决什么 | DeepSeek 兼容 | LiteLLM 共存 | LangGraph 共存 | 中文 | adoption cost |
|---|---|---|---|---|---|---|---|---|---|---|
| **Instructor** | v1.15.1 / 2026-04-03 | 13.1k | MIT | production | Pydantic 校验 + reask 自愈 | 官方专页 Tools/MD_JSON | **官方 from_litellm**(patch completion/Router) | 正交,node 内嵌 | 无关 | **low** |
| BAML | v0.222.0 / 2026-04-27 | 8.3k | Apache-2.0 | production | SAP 脏输出恢复 | 列 DeepSeek-R1 | OpenAI 兼容端点 | 成熟(baml_client) | 无关 | medium |
| PydanticAI | v1.104.0 / 2026-05-29 | 17.4k | MIT | production | agent 框架 + 结构化输出 | 官方 provider | 官方 + 社区包双通道 | 增量但功能重叠 | 无关 | medium~high |
| Outlines | v1.3.0 / 2026-05-13 | 13.9k | Apache-2.0 | production | 约束解码(本地) | API 退化为 JSON mode | 不经 LiteLLM | 正交 | 无关 | N/A(API) |
| Guidance | v0.3.2 / 2026-03-18 | 21.5k | MIT | production | 约束解码(本地) | API 退化 | 不经 LiteLLM | 正交 | 无关 | N/A(API) |
| DSPy | v3.2.1 / 2026-05-05 | 34.7k | MIT | production | prompt/权重优化 | 经 LiteLLM | 默认走 LiteLLM | 正交(另一层) | 无关 | 不划算 |

> 注:**没有任何一个候选 stale**(全部在 2.5 个月内有 release)。

---

## 3. 综合判断 & Top 候选

### Phase 1 选 **Instructor**,理由三条且都被验真来源锚定:

1. **零栈改造、最低成本落地**:`instructor.from_litellm(completion)` 或 patch Router 直接套现有 LiteLLM gateway 与 per-agent model binding —— 不引入新网关、不引入 DSL/构建步(对比 BAML)、不引入第二套 agent 抽象(对比 PydanticAI)。adoption cost = low。
2. **正好命中 DeepSeek 的真实约束**:DeepSeek 无 final-message json_schema、约束解码路线(Outlines/Guidance)对 API 无效;Instructor 的 Tools 模式 + reask 自愈是对"DeepSeek 偶发脏 JSON、schema 不符"最实用的解法,对 R1 reasoner 有官方 `Mode.MD_JSON` 路径。
3. **与 LangGraph 完全正交**:只替换 node 内部"裸调用 → 结构化对象"那一步,六 agent 编排不动。

### Phase 1.5 escape hatch = **BAML**(v2 把 v1 的"Phase 2 候选"细化为有触发条件的 escape hatch)
若接入后实测发现 DeepSeek(尤其 R1/V3 在长中文 prompt 下)脏输出导致 Instructor reask 频繁失败、成本/延迟不可接受,切到 BAML 的 SAP 是鲁棒性上限更高的方案,且 LangGraph 集成(`baml_client` + Hekmatica 范例)已成熟。代价是 DSL + codegen。**附加红利**:你们 reader 是 TS,BAML 能从同一份 `.baml` 同时产 Python + TS client,未来若要 reader 侧共享 schema,这是 Instructor 给不了的。

### 明确不选(Phase 1)
- **Outlines / Guidance**:约束解码对远端 API 无效;Outlines 在 JSONSchemaBench 上有合规率/编译速度的负面证据。(仅留作自部署开源模型时的备选。)
- **DSPy**:是 prompt 优化,属另一方向(质量/评测优化),不是结构化 I/O 的答案。
- **PydanticAI**:与已有 LangGraph 编排功能重叠,Phase 1 引入得不偿失 —— 除非你本就想换掉 LangGraph。

### 落地排序(锚定用户优先级:记忆 R2 = 角色 R5 = 大纲 R1 > 图谱 R3)

R10 是基础设施,落地顺序按"谁喂养 S 档子系统"排:

| 优先级 | agent | 结构化产物 | 喂养的高优先级方向 | 做法 |
|---|---|---|---|---|
| **最高** | Director | Story Bible JSON | **大纲(R1)** 的根输入 | 包 Instructor + Pydantic `response_model` + `max_retries=2` |
| **最高** | Planner | 章节 beats | **大纲(R1)** | 同上 |
| **最高** | ChapterExtractor(记忆抽取) | 角色记忆 / 关系 / 状态变更 | **记忆(R2)+ 角色(R5)** | 同上(这是 R2/R5 数据质量的咽喉,务必结构化 + 校验) |
| 高 | Camera | POV / 可见事件过滤 | 叙事一致性 | 同上 |
| 高 | Consistency | 校验报告 | 一致性 / 反哺记忆与角色 | 同上 |
| 中 | World | 世界事件 | 图谱(R3,优先级较低) | 按其输出形态决定 |
| **不动** | Writer | 2000-4000 字中文散文 | —— | **保持 `_call_text()` 不动**,散文不该被结构化 |

实现层:与现有 `BaseAgent` 的 `_call_json()` / `_call_text()` 二分法天然契合 —— **把 `_call_json()` 的内部实现换成 Instructor-over-LiteLLM 即可,agent 层接口零改动**(这正是 v1 已识别的零摩擦切入点,v2 据 from_litellm 把实现路径从"绕 OpenAI-compat 端点"纠正为"直接 patch litellm.completion / Router")。Writer 的 `_call_text()` 完全不碰。

---

## 4. Open questions(建议 Phase 1 实测 / 待验证)

1. **DeepSeek Tools 模式在长中文 prompt + 复杂嵌套 schema(如 Story Bible)下的真实失败率与重问次数?** 这决定 Instructor 够不够、要不要上 BAML。无现成中文小说场景的公开基准,需自测。`[no-source-found:DeepSeek tool-calling 中文小说结构化失败率]`
2. **DeepSeek beta strict 工具调用的右引号 bug(issue 1069)是否会修?** 调研时状态为 **Closed as not planned**(官方近期不修)—— https://github.com/deepseek-ai/DeepSeek-V3/issues/1069 `[accessed:2026-05-30]`。**结论:strict 路 Phase 1 不可作为保险,主路必须走 Tools/MD_JSON + reask。** 后续可定期复查是否重开。
3. **Instructor reask 的额外 token 成本**:每次校验失败多一轮往返,对章节级流水线的总成本/延迟影响多大?用 LLMLogger 量化(你们已有逐调用 token/cost/latency 日志,正好拿来度量)。这也回答 v1 的"Instructor + LiteLLM 双层包装会不会引入 latency"。
4. **DeepSeek R1(deepseek-reasoner)走 MD_JSON 时,reasoning_content 与结构化产物的解耦**:记忆/一致性 agent 若用 R1,要确认 Instructor 不把 CoT 误塞进结构化字段。官方 DeepSeek 集成页提到可单独取 `reasoning_content`,但需实测 —— https://python.useinstructor.com/integrations/deepseek/ `[accessed:2026-05-30]`。
5. **LiteLLM `enable_json_schema_validation=True` 客户端校验 与 Instructor reask 是否要二选一、会不会双重重试?** 需确认避免重复逻辑 —— https://docs.litellm.ai/docs/completion/json_mode `[accessed:2026-05-30]`。建议:**统一交给 Instructor 管 reask,关掉 LiteLLM 侧的 schema 校验**,避免两层重试叠加放大成本。
6. **模型选择对本方案的影响(v2 新增)**:基础事实核查显示 Kimi K2.6 在中文创意写作双榜第一、DeepSeek V4 强在性价比/知识而非文笔(见 §6)。若将来 Writer 切到 Kimi、或某些结构化 agent 切到支持 native json_schema 的模型,**本约束(无 final-message json_schema)需按模型重核**;Instructor-over-LiteLLM 的 provider-中立设计正是为应对这种切换。需在引入新模型时实测其 tool-calling / json_schema 能力。
7. **Pydantic 模型能否在运行时按 story_bible 动态生成?**(沿用 v1,例如把 character ID 收成 enum 以在校验期拦截"不存在的角色")—— 与 R5 角色一致性强相关,值得在 ChapterExtractor / Consistency 的 schema 上试 `create_model` 动态构造。
8. **BAML 的速度/成本 claim 实证**:v1 引的"2-4× faster"来自第三方博客,未验真;若进入 Phase 1.5,要用一个 high-cost agent 做 Instructor vs BAML 的 A/B,量化 token/time/合规率再决定切换。
9. **PromptPort 式 canonicalization + 轻量 verifier(arxiv 2601.06151,research prototype,2026-01-06)是否值得在 Instructor 之外加一层兜底?** —— https://arxiv.org/abs/2601.06151 `[accessed:2026-05-30]`(验真:exists=true,"A Reliability Layer for Cross-Model Structured Extraction",作者 Varun Kotte)。它是论文非生产库,**不建议直接依赖**,但其 ROS/CSS 双指标评估框架可借鉴来度量各 agent 的结构化可靠性。

---

## 5. 可借鉴清单(拿来即用的具体资产)

- **直接抄的集成模式**:装 instructor 的 litellm extra → `client = instructor.from_litellm(litellm.completion)`(或 patch 已有 Router)→ 调 `client.chat.completions.create`,传 `model` 为 deepseek 模型、`response_model` 为你的 Pydantic 模型、`max_retries=2`。来源:Instructor LiteLLM 集成页 + LiteLLM 官方 instructor 教程(均验真存在)。
- **R1/reasoner 特例**:用 `Mode.MD_JSON`,从 `raw_completion.choices[0].message.reasoning_content` 取推理链。来源:Instructor DeepSeek 页(验真存在)。
- **鲁棒性评估方法**:借 JSONSchemaBench(https://github.com/guidance-ai/jsonschemabench `[accessed:2026-05-30]`,验真:exists=true)的 schema 合规率指标 + PromptPort 的 ROS(严格解析可靠性)/ CSS(语义能力)双指标,搭一个针对你们中文 Story Bible / 记忆 schema 的内部小基准,用来对比 Instructor vs BAML。
- **BAML escape hatch 范例**:Hekmatica(BAML + LangGraph,验真存在)可作为将来切换时的 node 改造模板。
- **SAP 原理速读**:https://boundaryml.com/blog/schema-aligned-parsing `[accessed:2026-05-30]`(验真存在)—— 想理解"为什么 BAML 比纯 JSON parser 抗脏"先读这篇。

---

## 6. 模型层事实核查结论(v2 新增,影响 R10 的适用边界)

> R10 调研稿默认"DeepSeek 是锁定模型"。基础事实核查对 2026 年主流中文模型在小说/创意写作的实测做了横评,结论列此,供选型时与 R10 联动判断 `[accessed:2026-05-30]`。

**中文文笔维度排名(创意写作相关):**
1. **Kimi K2.6** —— 创意写作 + 挑战性角色扮演**双榜第一**(超 GPT-5),长篇风格连贯、情感共鸣强、意象生动;上下文 **2M tokens**(业界最长),但价格最贵(约 ¥3-3.5/百万 token)。
2. **DeepSeek V4-Pro** —— 中文知识/推理强(SimpleQA 84.4%),**文笔无专项突出数据**;1M 上下文;**极致性价比**(V4 Flash ~$0.25/百万 token,最便宜)。
3. **GLM-5.1 / Qwen 3.6-Plus** —— 通用强但创意写作非重点;Qwen 完全开源(Apache-2.0,可本地部署,对应 Outlines/Guidance 的潜在适用场景)。

**对 R10 选型的启示:**
- **当前(DeepSeek)**:R10 主路 = Instructor Tools/MD_JSON + reask,§0 约束成立。
- **若 Writer 切 Kimi 追文笔**:Writer 仍走 `_call_text()` 不受 R10 影响;但需复核 Kimi 的 tool-calling 能力以决定结构化 agent 是否也跟着切。
- **若结构化 agent 切到支持 native json_schema 的模型**:Instructor 可升级到走真 json_schema 约束,reask 频率下降。Instructor-over-LiteLLM 的设计让这种切换只是改 binding。
- **若走 Qwen 自部署**:此时 Outlines/Guidance 的约束解码才**首次变得可用**,可作为该路线的备选(但 R10 Phase 1 仍以 API 场景为准)。

> 说明:本节仅作"选型边界提醒",**不改变 Phase 1 选 Instructor 的结论** —— Instructor 的 provider-中立恰好是应对未来换模型的最稳妥姿势。

---

## v1 ↔ v2 diff

> v1 原稿(`2026-04-28-novel-system-survey/r10-structured-io.md`,239 行)本身已是**一份成型的调研**:含 F1–F6 六项 findings、comparison matrix、Recommendation(Instructor→Phase1 / BAML→Phase2)、时效性/鲁棒性/可行性评分、Open questions、Sources。**v2 的工作是在此之上做"验真纠错 + 深化 + 与其他 R 方向联动",而非从零重写。** v1 与 v2 的**主结论一致**(Phase 1 选 Instructor、放弃 Outlines/Guidance/PydanticAI、DSPy 记 backlog),分歧只在论据与精度。

### 删除(幻觉 / 失效引用)
- **删除 DSPy 文档 URL `https://dspy.ai/learn/programming/language_models/`**:验真 `exists=false` —— 该 URL 实为一个无实质内容的重定向页(跳到 `/getting-started/installation/`),不交付被引用的"DSPy 默认走 LiteLLM"材料。注意:此 URL **不在 v1 的 Sources 里**(v1 引的是 `dspy.ai/` 首页),它出现在 clean-room 调研稿中,v2 据验真**不予收录**,改由 DSPy 官方 API 文档 `dspy.ai/api/models/LM/` 与 GitHub README 佐证同一事实。这是本方向**唯一**一处幻觉/失效引用 —— 其余 30+ 条引用全部验真 `exists=true`。

### 纠正(事实精度)
- **Instructor 的 LiteLLM 集成方式(重要纠正)**:v1 写"Instructor 不内置 LiteLLM 支持,需走 `instructor.from_openai(openai.OpenAI(base_url=LITELLM_URL))` 这条 OpenAI-compatible 路径"。v2 据验真纠正:**Instructor 有官方一等公民集成 `instructor.from_litellm(litellm.completion)`,可直接 patch completion 或 Router**(Instructor LiteLLM 集成页 + LiteLLM 官方 instructor 教程双证)。落地更干净,不必绕 base_url。
- **新增 §0 DeepSeek 硬约束(v1 完全没有这层)**:v1 默认"DeepSeek 走 OpenAI-compatible 接口就行",未触及 DeepSeek **无 final-message json_schema** 这一关键事实。v2 用三条官方/社区来源(DeepSeek json_mode 文档、issue 1069、LiteLLM issue 7580)论证之,并据此**给出更根本的"为何放弃 Outlines/Guidance"的理由** —— v1 放弃 Outlines 的理由是"要自托管才有 FSM",放弃 Guidance 的理由是"用不到 conditional branching";v2 统一升级为"约束解码对远端 API 无效"。
- **issue 1069 / 7580 状态明确化**:v2 据验真明确二者均为 **Closed as not planned**,并据此把 strict 工具调用从"可选保险"降级为**"Phase 1 不可作保险,主路必须 Tools/MD_JSON + reask"**。
- **PydanticAI 版本**:v1 记 v1.103.0(2026-05-27),v2 据调研当日实查更新为 **v1.104.0(2026-05-29)**。
- **BAML "2-4× faster" claim**:v1 引第三方 Medium 博客作为 BAML 价值点之一;v2 标注该数字**未独立验真、不作选型硬依据**,把选 BAML 的理由收敛到 SAP 鲁棒性 + 多语言 codegen,速度留作 A/B open question。

### 新增(深化与联动)
- **§0 硬约束章节**(见上)。
- **PromptPort / JSONSchemaBench 等学术锚点**:v2 新增 JSONSchemaBench(arxiv 2501.10868)作为 Outlines 合规率/编译速度的**量化反向证据**,新增 PromptPort(arxiv 2601.06151)的 ROS/CSS 评估方法论作为可借鉴资产 —— v1 仅靠博客与 README。
- **落地排序锚定用户优先级**:v2 把落地顺序显式对齐到"记忆 R2 = 角色 R5 = 大纲 R1 > 图谱 R3",指出 Director/Planner/ChapterExtractor 应优先(因其分别喂养 R1 大纲与 R2/R5 记忆角色),World(喂 R3)其次,Writer 保持 `_call_text()` 不动 —— v1 的 Recommendation 是通用工程视角,没有与其他 R 方向的优先级联动。
- **§6 模型层事实核查**(全新):引入 2026 中文模型横评(Kimi K2.6 文笔双榜第一 / DeepSeek 强在性价比与知识),给出"换模型时 R10 约束需重核"的边界提醒,并论证 Instructor 的 provider-中立正是应对之策。v1 的 open question 里有一条"BAML 2-4x 在 DeepSeek V4-Pro 上是否成立",但没有把"是否该换模型"纳入视野。
- **每条引用补 `[accessed:2026-05-30]` + 验真标注**:v1 的引用是 2026-04-28 访问、未经本轮验真;v2 全部重新标注访问日期并标 exists 验真结果。

### 沿用 v1(未改的好结论)
- 主选 Instructor、`_call_json()` 内部切换的零摩擦切入点、`max_retries` 与现有 3 次重试对齐、observability 接现有 `llm_logger`、放弃 Outlines/Guidance/PydanticAI、DSPy 记 backlog、"Pydantic 模型能否按 story_bible 动态生成"这条 open question —— 这些 v1 已对,v2 原样保留并补强证据。

### 未应用的基础事实核查项(说明)
- **PerRoleCognition(经核查为杜撰,arXiv/Scholar/全网无此文)/ WebNovelBench 8 维度**:这两项基础事实核查与 R10(结构化 I/O)无关 —— R10 不涉及角色认知论文或小说质量评测维度,故不在本稿应用,留给 R5(角色)/ 评测方向使用。仅 **模型横评** 一项与 R10 选型边界相关,已落入 §6。
