# R7 + R8 终稿 v2 · Agent 编排框架对比(decision)+ 商业写作工具 UX(light scan)

| Field | Value |
|---|---|
| Topic | R7: confirm「维持 LangGraph」是否正确(决策类);R8: 抄 Sudowrite / Novelcrafter / NovelAI 的 UX 模式(借鉴类) |
| Author | engineer (Claude) |
| Researched | 2026-05-30(clean-room 重做,叠加 v1 2026-04-28) |
| 优先级档 | **C 档(light)** — 记忆(R2)=角色(R5)=大纲(R1)>图谱(R3) 是 S/A 档;本方向点到为止 |
| Verdict | **R7: 维持 LangGraph + 维持固定 DAG,不切换、不引入动态 supervisor/swarm**;**R8: 工程层借 NovelAI Lorebook 预算机制 + Novelcrafter Codex 别名链接/Progressions;UI 层借 Sudowrite Canvas 模板/细粒度写作动作** |

> 时效/鲁棒/可行三维约定:发布或最近 commit 日期(>18 月没动标 stale)、star/maturity(theoretical / prototype / production)、adoption cost(low / medium / high / rewrite)+ 中文就绪度。
> **来源可信度提示:** 本方向引用的 2026 框架排名/benchmark 多来自营销或聚合类博客(Alice Labs / gurusup / CallSphere / Augment Code),非同行评审或独立审计。文中「90M downloads」「18% token overhead」「性能提升近 50%」等具体数字一律打折看,若写进正式重构决策文档须复核一手数据(LangChain 官方 release notes、PyPI 统计)。

---

## Part A — R7:编排框架对比(决策类,需扎实)

### A0. 一句话结论(先给判断)

**维持 LangGraph 是正确的,且这是一个比 v1 更有把握的结论。** 2026 年的格局里,LangGraph 已从「一个选项」变成「有状态、可控、生产级 agent 的事实标准」,其核心卖点(durable execution / checkpointing / human-in-the-loop / 循环图)正好命中我们小说流水线最痛的两点:**章节重试循环** 与 **长程状态(world state + memory)持久化**。其余候选要么定位错配(MetaGPT 偏写代码、AutoGen 偏多方对话),要么会被 outgrow(CrewAI 易上手但多 agent 调试时抽象变不透明),要么绑死单一模型厂商(OpenAI / Claude SDK)与我们的 LiteLLM 多 provider 策略冲突。详见 A6 综合判断。

### A1. LangGraph — 当前事实标准(production)

- **版本/时效:** LangChain 与 LangGraph 于 **2025-10-22** 同时发布 1.0,官方标题「LangChain and LangGraph Agent Frameworks Reach v1.0 Milestones」,明确承诺稳定性「no breaking changes until 2.0」(LangGraph 1.0 强调 durable state persistence + human-in-the-loop)。仓库内可见 `langgraph-sdk==0.4.0`,说明 2026 年仍高频迭代。<https://www.langchain.com/blog/langchain-langgraph-1dot0> [accessed:2026-05-30]
- **鲁棒性:** GitHub **33.4k stars**,MIT,Python 为主;官方定位「a low-level orchestration framework for constructing stateful, long-running agent systems」/「Build resilient agents」。四大能力 = durable execution(失败后从断点自动恢复)/ human-in-the-loop(运行中可检查与修改 state)/ comprehensive memory(short-term + long-term)/ production-ready deployment。<https://github.com/langchain-ai/langgraph> [accessed:2026-05-30]
- **采用度(第三方,营销类,打折看):** 多篇 2026 测评称其有「90M monthly downloads」、生产部署方含 Uber / JP Morgan / BlackRock / Cisco / LinkedIn / Klarna,被称为「the definitive standard for controllable, stateful AI agents」。这些数字来自 LangChain 官方博客转引,非独立审计。<https://gurusup.com/blog/best-multi-agent-frameworks-2026> [accessed:2026-05-30]
- **maturity:** production。**adoption cost:** 我们已经在用 = **none/已沉没**;从零学 = medium(需理解 graph + state schema)。
- **中文就绪度:** 框架与语言无关,prompt 全中文无障碍;现有六 agent 流水线已是明证。
- **时效 ⭐⭐⭐⭐⭐ / 鲁棒 ⭐⭐⭐⭐⭐ / 可行(维持)✅ 已用**

> **对我们的直接意义:** 我们的 `chapter graph`(load_context → … → consistency_check →(pass: save / fail: retry up to 3x))本质就是 LangGraph 最擅长的**带条件边的循环图 + checkpoint**。这正是 CrewAI/AutoGen 的弱项(见下)。换框架 = 纯负收益。

### A2. CrewAI — 最快出原型,但会被 outgrow(production,定位偏「角色团队」)

- **版本/时效:** v1.14.x 量级,2026 仍活跃。<https://github.com/crewAIInc/crewAI> [accessed:2026-05-30]
- **鲁棒性:** **52.5k stars**,MIT;官方描述「Framework for orchestrating role-playing, autonomous AI agents … a lean, lightning-fast Python framework built entirely from scratch—completely independent of LangChain or other agent frameworks」(2024 年它还依赖 LangChain,现已完全独立)。架构双轨:**Crews**(自治角色协作)+ **Flows**(事件驱动、精确控制的工作流)。<https://github.com/crewAIInc/crewAI> [accessed:2026-05-30]
- **公认短板(第三方,打折看):** 「lowest barrier to entry / fastest path from idea to prototype」但「many teams eventually outgrow its simpler role-based orchestration」;尤其「when you need to debug a failure in a five-agent pipeline, the abstraction becomes opaque」。某 2026 benchmark 称其 3-agent crew 比同等 LangGraph 实现多用约 18% token(营销类,未独立审计)。<https://alicelabs.ai/en/insights/best-ai-agent-frameworks-2026> [accessed:2026-05-30]
- **maturity:** production。**adoption cost(迁到它):** high(等于重写编排层,换来一个我们已知会撞墙的抽象)。**中文就绪:** prompt 中文 OK。
- **时效 ⭐⭐⭐⭐ / 鲁棒 ⭐⭐⭐⭐ / 可行(切换)⭐ 不值**

> **判断:** 我们的 6 agent 是**固定角色 + 固定流水线 + 重条件分支与重试**,不是「自治团队自由协作」。CrewAI 的 Crews 范式优势用不上,Flows 范式则不如 LangGraph 图模型直接。**不值得换。**

### A3. AutoGen — 已进入维护模式,官方劝退新项目(⚠️ 排除)

- **时效/状态:** 仓库**明确写着「AutoGen is now in maintenance mode … community managed going forward」**,官方引导「New users should start with **Microsoft Agent Framework**」,后者被定位为 enterprise-ready 继任者。<https://github.com/microsoft/autogen> [accessed:2026-05-30]
- **鲁棒性:** 58.5k stars(历史积累),官方标题「AutoGen - A Programming Framework for Agentic AI」,定位「a framework for creating multi-agent AI applications that can act autonomously or work alongside humans」。但 stars 高 ≠ 该选 —— **核心团队已转向新框架**。
- **定位:** conversation-driven(agent 多方对话/辩论/分工),擅长 brainstorm 与 review-heavy 流程,但「less predictable」、memory 较简单。<https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen> [accessed:2026-05-30]
- **maturity:** maintenance(新功能停摆且官方劝退)。**adoption cost:** rewrite,且方向错。
- **时效 ⭐⭐(维护模式)/ 鲁棒 ⭐⭐⭐(历史积累)/ 可行 ⭐ 排除**

> **判断:** 直接排除。官方都劝你别用的框架不应进入候选。若未来真需要「多 agent 辩论式 brainstorm」,应评估其继任者 Microsoft Agent Framework(MAF)而非 AutoGen —— 但那是另一个调研(见 Open Questions;**注意:MAF 真实仓库在 `github.com/microsoft/agent-framework`,不是 autogen 仓库,本轮未验证其成熟度**)。

### A4. MetaGPT — 定位「AI 软件公司」,与小说生成赛道错配(production 但跑偏)

- **时效/版本:** **68.4k stars**,MIT。⚠️ **数据矛盾点须标注**:官方带 tag 的「最新 release」停在 v0.8.1(2024-04 量级);但 README 时间线又列出 2025-01(AFlow 入选 ICLR 2025)、2025-02(MGX 产品)等更近活动;第三方聚合站(star-history)显示仓库 2026 年仍有更新。综合看:**主仓库带版本号 release 节奏偏慢,但底层仍有 commit 与衍生研究**。引用「last commit 2026」时务必注明它来自第三方聚合而非官方 release tag。<https://github.com/FoundationAgents/MetaGPT> [accessed:2026-05-30] / <https://www.star-history.com/foundationagents/metagpt/> [accessed:2026-05-30]
- **定位:** 官方描述「The Multi-Agent Framework: First AI Software Company, Towards Natural Language Programming」—— SOP 驱动、模拟软件公司(产品经理/架构师/工程师),一行需求 → 用户故事 + 竞品分析 + 数据结构 + API + 文档。本质是**代码/软件工程生成器**。<https://github.com/FoundationAgents/MetaGPT> [accessed:2026-05-30]
- **中文就绪:** **候选中最好的一项** —— README 原生「[En | 中 | Fr | 日]」,中文文档齐全,团队为中国团队(DeepWisdom / FoundationAgents)。
- **maturity:** production(在其本职赛道)。**adoption cost(迁到它做小说):** rewrite + 范式错配。
- **时效 ⭐⭐⭐(release 慢、commit 有)/ 鲁棒 ⭐⭐⭐⭐(本职赛道)/ 可行 ⭐ 范式错配**

> **判断:** 唯一吸引力是中文母语团队 + 中文文档,但其 SOP / 软件公司范式与「世界一致性 + 角色记忆 + 叙事连贯」的小说生产几乎不重叠。**不换;但其 AFlow(自动化 agentic workflow 生成,ICLR 2025 oral paper)值得日后单独瞄一眼**(自动编排,而非手写图)。**注意:AFlow 不在 MetaGPT 仓库内,独立仓库在 `github.com/FoundationAgents/AFlow`(本轮未读源码/paper 原文)。**

### A5. 轻量替代:OpenAI Agents SDK / Claude Agent SDK(值得知道,当前不切换)

- **OpenAI Agents SDK:** 官方仓库 `openai-agents-python`,描述「A lightweight, powerful framework for multi-agent workflows」,MIT,Python 99.7%,约 26.8k stars。2025-03 发布,取代实验性的 Swarm,最小原语 = agents / handoffs / guardrails,内置 tracing,**handoffs over orchestration**(去中心化、agent 间直接交棒)。强项是「coordinator routes to specialists」的干净 handoff;**短板:与 OpenAI 模型强耦合,对复杂分支 / 有状态长流程支持有限**。<https://github.com/openai/openai-agents-python> [accessed:2026-05-30] / 对比背景见 <https://callsphere.ai/blog/ai-agent-frameworks-comparison-2026-openai-agents-sdk-langgraph-crewai> [accessed:2026-05-30]
- **Claude Agent SDK:** 第三方 2026 排名把它列为「#2 for Anthropic-native production agents(powers Claude Code)」。<https://alicelabs.ai/en/insights/best-ai-agent-frameworks-2026> [accessed:2026-05-30]
- **时效 ⭐⭐⭐⭐ / 鲁棒 ⭐⭐⭐⭐ / 可行(切换)⭐ 绑单厂商**

> **判断:** 两者都**与单一模型厂商强绑**;我们靠 LiteLLM 做 100+ provider 抽象,绑死一家是退步。**当前不切换**;但若未来要做「supervisor 路由到专家 agent」的某个子模块,OpenAI SDK 的 handoff 原语可作局部参考。

### A6. 架构模式借鉴(在 LangGraph 内部就能用,无需换框架)

这一节是**「不换框架、但可借鉴的内部模式」**,对重构最有可操作性:

- **Supervisor vs Swarm(LangChain 官方 benchmark,2025-06-10,作者 Will Fu-Hinthorn):** 测了 single agent / supervisor / swarm 三种,用 gpt-4o + 改造版 τ-bench(含 distractor domain)。结论:single agent 在出现 ≥2 个干扰域时准确率急剧下滑;swarm 略胜 supervisor;supervisor 因 agent 间「翻译」开销持续多用 token;但通过「去掉 handoff 消息 + message forwarding + 优化 tool 命名」可让 supervisor 性能显著提升。<https://www.langchain.com/blog/benchmarking-multi-agent-architectures> [accessed:2026-05-30]
- **选型经验法则(第三方,Augment Code 指南,2026-04):** 「先用 supervisor(更易构建/调试,早期路由准确性比延迟更重要),当数据证明延迟是瓶颈、且 agent 很少错路由时再升级到 swarm」。<https://www.augmentcode.com/guides/swarm-vs-supervisor> [accessed:2026-05-30]

> **对我们的意义(反向 confirm):** 我们当前是**固定 DAG(无中心 supervisor 动态路由)**,这其实是最稳的形态(确定性最高、token 最省、最易 debug)。小说流水线的阶段顺序本就确定,**动态路由只会增加不确定性与 token 开销**。结论:**不必引入 supervisor/swarm 的动态路由**;这一节的价值是反向 confirm「固定图编排是对的」。

---

## Part B — R8:商业写作工具 UX 借鉴(light scan,借鉴类)

> 三家定位:**Sudowrite**(辅助创作 + 自有小说模型 Muse)、**Novelcrafter**(规划 + 知识库 Codex + BYOK)、**NovelAI**(co-writing + Lorebook 关键词记忆)。我们抄的是**交互模式与数据结构**,不是模型。

### B1. ✅ 可借鉴清单(按对我们价值排序)

| # | 借鉴点 | 来源 | 对应我们模块 | 优先级 |
|---|--------|------|-------------|--------|
| 1 | **关键词触发式记忆注入(Lorebook 机制)** | NovelAI | memory 系统 / LayeredMemory 的 L2 场景注入 | 高 |
| 2 | **Codex 自动识别 + 别名链接 + RAG 注入** | Novelcrafter | 角色/世界 知识库自动注入 prompt | 高 |
| 3 | **Progressions:时序化覆盖旧设定** | Novelcrafter | KnowledgeGraph 的 valid_from/valid_to 时序三元组 | 高(几乎是我们设计的产品化镜像) |
| 4 | **Story Bible 作为「写一次,全程引用」的单一事实源** | Sudowrite / Novelcrafter | StoryBible 2.0 | 中 |
| 5 | **Canvas 2D 空间白板(卡片 + 大纲模板)** | Sudowrite | 大纲/事件图 的可视化编辑 UI | 中(B 档 UI) |
| 6 | **细粒度写作动作(Write/Rewrite/Describe/Expand/Brainstorm)** | Sudowrite | Writer agent 的「局部操作」工具集 | 中 |
| 7 | **预置剧作结构模板(Hero's Journey / Story Circle / Hollywood Beats / Romance)** | Sudowrite Canvas | Planner agent 的 beat 模板库 | 中 |
| 8 | **BYOK + 可接本地模型** | Novelcrafter | 我们已有(LiteLLM + 模型 web 配置)= 验证方向正确 | 低(已具备) |

### B2. 机制细节(load-bearing,值得照抄的具体设计)

**① NovelAI Lorebook —— 关键词触发 + 预算管理(最值得抄的工程设计):**
- **Search Range:** 检查最近故事文本(上限约 10,000 字符)中是否出现 activation key;命中则把该条目文本插入 context。key 默认大小写不敏感,regex key 大小写敏感。
- **Insertion Order:** 条目按此值排序,**高 order 先预留 token、先插入**。
- **Insertion Position:** 数值精确定位(0 = 顶部,负数 = 从底部倒数)。
- **Token Budget / Reserved Tokens:** 每条目有最大 token 配额,**所有预留在任何条目放入前先完成**。
- **Always On:** 绕过关键词检测(= 我们的 L0 身份核心)。
- **Cascading activation:** 条目可在其他非故事 context 条目里继续搜 key(级联触发)。
- **Key-Relative Insertion:** 把条目插到其 key 出现的位置附近,而非固定位置。
- 官方文档另含 Entries / Generator / Placement Settings / Phrase Bias / Categories / Advanced Conditions 等模块。
<https://docs.novelai.net/en/text/lorebook/> [accessed:2026-05-30]

> **对我们的直接意义:** 这套「**关键词命中 → 按 order/position/budget 注入**」几乎是一份**可执行的 L2 场景记忆注入规格**。我们的 LayeredMemory「L2 scene-relevant(context filtered)」可直接借用:Always On = L0、按情感权重排序 ≈ Insertion Order、token budget 预留 = 避免 context 超长。建议把这套预算/位置机制写进 memory 检索层。

**② Novelcrafter Codex —— 自动链接 + RAG + 时序覆盖:**
- 官方定位「The Codex: A Story Bible That Writes With You」「seamlessly organize every story element in one searchable, intelligent system」。
- **自动识别与链接:** 「Names, aliases, and nicknames are instantly recognized and linked as you type」—— 边写边把人名/别名/昵称映射并链接到实体,跨手稿/聊天/片段统计每次出现。
- **RAG 式注入:** 以 Codex 为 source of truth,生成/编辑场景时**自动把相关 Codex 信息注入 prompt**,防止模型偏离设定。
- **五类实体:** Characters / Locations / Lore / Objects(Items) / Subplots。
- **Progressions(时序):** 「Overwrite outdated lore with new progressions to keep your series bible accurate to the current moment」—— 不是静态笔记,而是**记录随章节推进的状态变化**。
- **Custom Metadata:** 用户自定义题材字段(奇幻的魔法体系、科幻的外星种族)= 灵活 schema。
- **Series Sharing:** 一次定义跨系列多本书共享。
<https://www.novelcrafter.com/features/codex> [accessed:2026-05-30]

> **对我们的直接意义:** **Progressions ≈ 我们 KnowledgeGraph 的 valid_from/valid_to 时序三元组的产品化形态** —— 强力 confirm「时序化知识(而非静态设定)」是行业共识方向。Codex 的「边写边自动识别别名并链接」则是一个我们可补的**前端体验**:在编辑器里自动高亮已知实体、点击跳到设定。

**③ Sudowrite Story Bible / Canvas / 写作动作:**
- **Story Bible:** 官方文档定义其两大功能 ——(1)引导作者走过 brainstorming→scene 的叙事开发阶段;(2)「works as a source of truth that both you and the AI can refer back to later」。经典例子「写一次『侦探有战伤跛脚』,生成新场景时自动自然引用」。<https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC> [accessed:2026-05-30]
- **Canvas(2D 白板):** 官方描述「a flexible digital whiteboard where you can drop notes, draft outlines, and freely rearrange everything in a 2D space」。三类元素 —— **Cards**(自定义内容:角色细节/场景笔记/点子)、**Text**(给卡片簇贴标签)、**Outlines**(预置结构:Hero's Journey / Hollywood Beats / Story Circle / Romance Outline,以「相连卡片」呈现)。交互:点拖选择、底部菜单加元素、空格+点+拖平移、撤销/重做/缩放/居中;三点菜单可把大纲导出到文档或 Story Bible。**强调用户主导规划,而非全自动生成**。<https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/canvas/pQGLNzeYo1kLhGo14rdBy6> [accessed:2026-05-30]
- **细粒度动作:** Write / Rewrite / Describe / Brainstorm / First Draft / Expand / Visualize / Quick Edit / Selection Menu / Find and Replace。Describe 调五感生成感官细节;Rewrite 是「手术刀」(选中段落给具体指令)。
- **Muse 模型(仅作背景,我们不抄模型):** 自有小说微调模型,官方文档定位「the first AI made for fiction, designed for authors」,含 Creativity 设置与 Style Examples。2025 年中公开。<https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/sudowrite-muse/4k9bFDMSyic6mFPkYFHrkZ> [accessed:2026-05-30]

> **对我们的直接意义:** (a) **Canvas 的剧作结构模板**(Hero's Journey 等)→ 直接做成 Planner agent 的 beat 模板库,低成本高感知价值。(b) **细粒度写作动作**(尤其 Rewrite/Describe/Expand)→ 把 Writer agent 从「整章生成」扩成「可对选区做局部操作」,是面向编辑工作流的明显升级。(c) Canvas「用户主导而非全自动」的克制设计,提醒我们**保留人工干预入口**(与 LangGraph 的 human-in-the-loop 天然契合)。

---

## C. 综合判断 + Top 候选 + Open Questions

### C1. R7 综合判断(决策)

> **维持 LangGraph = 正确,无需改动编排框架。** 三条理由:
> 1. **定位最匹配:** 我们的核心是「带条件分支 + 重试循环 + 长程状态持久化」的确定性流水线,这正是 LangGraph 1.0 的本职(durable execution + checkpoint + HITL)。
> 2. **替代项各有硬伤:** CrewAI 会被 outgrow 且换框架成本 = high;AutoGen 已进维护模式(官方劝退);MetaGPT 跑代码赛道、范式错配;OpenAI/Claude SDK 绑单一模型厂商,与我们的 LiteLLM 多 provider 策略冲突。
> 3. **生态成熟度第一:** 2026 多个第三方测评一致把 LangGraph 列为有状态生产 agent 的默认/第一(来源多为营销博客,需打折,但方向一致)。

**唯一要内化的反向结论:** 不要为了「显得先进」而引入 supervisor/swarm 动态路由 —— 官方 benchmark 表明动态路由带来 token 与不确定性开销,而我们的阶段顺序本就确定,**固定 DAG 是最优解**。

### C2. R8 综合判断(借鉴)

三家工具高度趋同地验证了**我们既有架构方向是对的**:Story Bible(= 我们的 StoryBible)、Codex/Lorebook(= 记忆 + 知识库)、Progressions(= 时序三元组)、BYOK(= LiteLLM + web 配置)。**最高 ROI 的两个具体借鉴是工程层而非 UI 层:**
1. **把 NovelAI Lorebook 的「关键词命中 + Insertion Order + Token Budget/Reserved」机制吸收进 LayeredMemory 的 L2 注入层**(adoption: low,纯检索逻辑)。
2. **把 Novelcrafter Codex 的「自动别名识别 + RAG 注入 + Progressions 时序覆盖」对齐到我们的 KnowledgeGraph/角色记忆**(adoption: low~medium,大部分我们已有,缺的是「自动别名链接」这一前端体验)。

UI 层(Canvas 空间白板、剧作模板、细粒度写作动作)归 B 档 UI,light 即可,排在记忆/角色之后。

### C3. Top 候选(给重构的最终推荐)

| 项 | 推荐 | 理由 | adoption |
|----|------|------|----------|
| 编排框架 | **维持 LangGraph(不动)** | 定位最匹配,替代项全有硬伤 | none |
| 编排模式 | **维持固定 DAG,不引入动态 supervisor/swarm** | benchmark + 我们流程确定性 → 固定图最优 | none |
| 记忆注入 | **借 NovelAI Lorebook 预算/位置机制** | 可执行规格,直接落到 L2 | low |
| 知识库 | **借 Novelcrafter Codex 别名链接 + Progressions** | 验证时序方向 + 补自动链接体验 | low~medium |
| 写作工具 | **借 Sudowrite 细粒度动作 + 剧作模板** | Writer 从整章 → 局部可编辑 | medium(B档) |
| 自家 prose 模型 | **保留为远期 differentiator**(对标 Sudowrite Muse) | 闭源工具靠自有微调模型立差异;我们 Phase 3+ FTPO 可走此路 | high(远期,非本轮) |

### C4. 与基础事实核查的对齐(模型选型背景,非本方向主线)

本方向不主导模型选型(归 R9 中文 / 评测线),但「自家 prose 模型 / 写作动作背后用哪个底模」与基础事实核查相关,顺带锚定一笔:**2026 中文文笔维度,Kimi K2.6 在创意写作与角色扮演评测双榜领先(第三方称超 GPT-5);DeepSeek V4-Pro 中文综合强但缺专项文笔数据;GLM-5.x / Qwen 3.x 通用强但创意非强项。** 我们靠 LiteLLM 多 provider,这一结论的价值是:**无论 Writer 的细粒度动作落在哪个底模,都应保持可切换,优先在「文笔强」的中文模型上跑 Writer/Describe/Rewrite。** [模型对比来源见 R9 / 基础事实核查,本方向不展开]

### C5. Open Questions(留给后续/更高档调研)

1. **Microsoft Agent Framework(MAF)** 作为 AutoGen 正统继任者,2026 现状/成熟度如何?本轮未深挖(AutoGen 已排除,故未追)。⚠️ **更正 v1/初稿隐患:MAF 的真实仓库是 `https://github.com/microsoft/agent-framework`(官方描述「A framework for building, orchestrating and deploying AI agents and multi-agent workflows with support for Python and .NET」),不是 autogen 仓库** —— 若未来要做「多 agent 辩论式 brainstorm」,需单独评估 MAF。[本轮未对 MAF 仓库单独验证成熟度]
2. **MetaGPT 的 AFlow(自动化 agentic workflow 生成,ICLR 2025 oral paper)** —— 「让 LLM 自动生成编排图」与我们「手写固定图」是两条路。⚠️ **更正:AFlow 不在 MetaGPT 仓库内,独立仓库为 `https://github.com/FoundationAgents/AFlow`;paper 真实存在(openreview.net / iclr.cc 可查)。** AFlow 是否能用于自动生成/优化小说流水线?值得日后单独看 paper 原文。[本轮未读 AFlow 源码/paper]
3. **第三方 stars/下载量/性能差数字可信度:** 「90M downloads」「18% token overhead」「性能提升近 50%」等均来自营销/聚合类博客(Alice Labs / gurusup / CallSphere / Augment Code),非同行评审或独立审计。写进正式重构决策文档前建议复核一手数据(LangChain 官方 release notes、PyPI 下载统计)。
4. **MetaGPT release 数据矛盾:** 官方带 tag 的最新 release 偏旧,但第三方称仍有近期 commit。需到 GitHub commits 页核实主分支真实活跃度,避免误判 stale。
5. **三家商业工具均闭源:** Lorebook/Codex 的内部实现细节只能从公开文档推断,真实检索/排序算法不可见。我们的借鉴是基于**公开行为规格**的重建,非源码移植。

---

## v1 ↔ v2 diff

> v1 = `workspace/research/2026-04-28-novel-system-survey/r7-r8-light.md`(2026-04-28)。本节列出 v2 相对 v1 的新增 / 纠正 / 删除。

### 新增(v2 有、v1 无)

- **R7 候选扩到 5 类:** v1 只对比了 LangGraph / CrewAI / AutoGen / MetaGPT 四家;v2 新增 **OpenAI Agents SDK 与 Claude Agent SDK**(轻量替代),并给出「绑单一模型厂商 vs 我们 LiteLLM 多 provider」这一明确否决理由。
- **新增 A6「架构模式借鉴」整节:** v1 完全没有 supervisor / swarm 维度。v2 引入 LangChain 官方 benchmark(2025-06-10)与 Augment Code 指南,得出**反向 confirm「固定 DAG 最优、不引入动态路由」**这一对重构有直接约束力的结论。这是 v2 最重要的增量。
- **R8 从「两类 UX 印象」升级为「可执行工程规格」:** v1 只给了 Sudowrite「muse 按钮」+ Novelcrafter「Codex 侧栏」两个泛泛 UX 点。v2 补齐 **NovelAI Lorebook 的完整注入机制**(Search Range / Insertion Order / Position / Token Budget / Always On / Cascading / Key-Relative),并明确「这几乎是一份可执行的 L2 记忆注入规格」,把借鉴点从 UI 层下沉到记忆引擎层(对优先级最高的 R2 记忆线直接有用)。
- **新增 Progressions ↔ 我们 KnowledgeGraph 时序三元组的镜像对应**,强力 confirm「时序化知识」是行业共识(v1 未触及)。
- **新增「来源可信度」分级提示**:v2 通篇标注哪些数字来自营销/聚合博客需打折,v1 直接把数字当结论用。
- **新增 C3 Top 候选表 + C4 模型选型锚定 + 完整 Open Questions**,v1 只有零散 Recommendation。

### 纠正(v1 有但 v2 修订/弱化)

- **AutoGen 状态纠正:** v1 把 AutoGen 列为「⭐⭐⭐⭐ Production 推荐,可在 LangGraph 节点内嵌一个 AutoGen instance」。v2 据官方 README **纠正为「已进入维护模式、官方劝退新项目」**,从「可内嵌使用」降级为「排除」。v1 的「内嵌 AutoGen」建议在 2026-05 已不成立。
- **量化 benchmark 数字降可信度:** v1 引用的「LangGraph 复杂任务 62% / CrewAI 54% / AutoGen 58% 完成率」「60% faster debugging」等具体百分比,其来源(pooya.blog / openagents.org / meta-intelligence.tech)未在本轮验真清单中,v2 不再沿用这些精确数字作论据,改用官方仓库 README 的能力描述 + 打折标注的第三方排名,**结论方向一致(LangGraph 第一)但证据更稳健**。
- **NovelAI 定位纠正:** v1 称 NovelAI「偏 ACG / 二次元 / 同人,与我们网文 segment 不重叠」,几乎弃用。v2 **纠正为 NovelAI 的 Lorebook 是本方向最高价值的工程借鉴来源** —— 模型定位与机制设计是两回事,Lorebook 的注入预算机制与题材无关。
- **Sudowrite Muse 表述纠正:** v1 称 Muse「crafted with permission from authors」并引用一条用户反馈,但其引用的对比博客 URL 未经验证。v2 改以**官方文档**(docs.sudowrite.com 的 Muse 页)为准描述 Muse,并把「自家 prose 模型」明确归为远期 differentiator 而非可抄项。

### 删除(幻觉 / 失效 URL,据验真结果剔除)

本轮验真把若干 URL 标为 **exists=false**(实体多为真,但**所指 URL 错误或失效**),已从正文剔除或更正:

1. **Sudowrite Muse 博客 `https://sudowrite.com/blog/sudowrite-muse-the-first-ai-writer-built-specifically-for-fiction/`** —— exists=false(HTTP 404)。Muse 产品真实,但该 slug 不存在(真实深度介绍在 `.../what-is-sudowrite-muse-a-deep-dive...`)。v2 **删除该 URL**,改引官方 docs Muse 页。
2. **「MAF 仓库 = `https://github.com/microsoft/autogen`」** —— exists=false(该 URL 指向 AutoGen,非 MAF)。v2 **纠正**:MAF 真实仓库为 `https://github.com/microsoft/agent-framework`,并在 Open Questions 明确标注「本轮未验证 MAF 成熟度」,避免把 autogen 仓库误当 MAF 引用。
3. **「AFlow 仓库 = `https://github.com/FoundationAgents/MetaGPT`」** —— exists=false(该 URL 是 MetaGPT,仅在其示例中提及 AFlow)。v2 **纠正**:AFlow 独立仓库为 `https://github.com/FoundationAgents/AFlow`,paper 本身真实(ICLR 2025 oral);引用时区分仓库与提及。
4. **v1 的 SidekickWriter(F5)与未直接 fetch 的零散对比博客**(pooya.blog / openagents.org / meta-intelligence.tech / nerdynav / novarrium / sidekickwriter)—— 均**不在本轮验真白名单**,且对 C 档 light 结论无 load-bearing 作用。v2 **不再引用这些未验证来源**,改以验真通过的官方仓库/官方文档/已验证第三方(Alice Labs / gurusup / CallSphere / DataCamp / Augment Code / LangChain 官方 blog)为证据基底。

> **基础事实核查应用说明:** 本方向不涉及「PerRoleCognition」(经核查为杜撰,未在本稿出现)与「WebNovelBench 8 维度」(归 R6/评测线);二者已在对应方向处理。模型对比结论仅在 C4 以「保持可切换、Writer 优先跑文笔强的中文模型」形式轻量锚定,不展开,符合 C 档 light 定位。
