# R4 · 开源小说生成项目调研(v2 终稿)

- 方向:R4 — 开源长篇小说生成项目(架构 / prompt 库 / 失败案例 / star / last-commit / LICENSE)
- 综合者:research-agent (Claude)
- 日期:2026-05-30(本稿 v2)· 上一版 v1:2026-04-28
- 焦点:GitHub 上 2025–2026 活跃的长篇小说生成项目,按"对你重构最可借鉴"排序(非按 star)
- 方法学:所有 star/fork/pushed_at/license/archived 字段均来自 `api.github.com/repos/{repo}` 实时查询;架构与失败案例来自实际 WebFetch 的 README / PIPELINE.md;arxiv/aclanthology 论文经独立 agent 逐条验真。accessed 时间统一 **2026-05-30**。
- 用户优先级锚定:**记忆(R2)= 角色(R5)= 大纲(R1)> 图谱(R3)**。本方向为 S 档,下文 S 档项目展开最深,B/C 档点到为止。

> **验真说明(v2 关键):** 本方向 30 个被引仓库经独立验真**全部存在(exists=true, high confidence)**;唯一 exists=false 的是 **Ex3 论文的 aclanthology URL**(原 URL 指向的是另一篇论文 M4LE,Ex3 论文本身存在但正确地址不同)——已在下文 §3 纠正并记入幻觉清单。此外应用了三项基础事实核查:**"PerRoleCognition" 系杜撰**(全网无此文献,真实近义为 RPNA / RoleRAG / Character-LLM)、**WebNovelBench 八维度逐字核实**、**2026 中文大模型文笔实测对比**(详见 §3 与 §4)。

---

## 0. 一句话总览(候选全景表)

| 项目 | Star | last push | License | 成熟度 | 中文 | 一句话定位 | 验真 |
|---|---|---|---|---|---|---|---|
| **tyxben/AI_novel** | 225 | 2026-05-25 | **MIT** | prototype→prod | ✅原生 | LangGraph 5-agent + Ledger + Brief + StyleBible,**和你架构几乎同构**,MIT 可抄码 | ✅exists |
| **xiamuceer-j/MuMuAINovel** | 2520 | 2026-05-29 | GPL-3.0 | production | ✅原生 | 最活跃的中文产品级:伏笔管理+章节关系图谱+世界观,FastAPI+PG+React | ✅exists |
| **YILING0013/AI_NovelGenerator** | 5152 | 2026-05-19 | AGPL-3.0 | production | ✅原生 | star 王,设定-目录-章节-定稿四段式+向量检索+一致性校对,正在 2.0 重构 | ✅exists |
| **RhythmicWave/NovelForge** | 880 | 2026-04-26 | AGPL-3.0 | production | ✅原生 | **结构化生成标杆**:JSON-Schema 卡片+@DSL 上下文引用+Neo4j/SQLite 图谱 | ✅exists |
| **NousResearch/autonovel** | 1025 | 2026-03-20 | ⚠️**无 license** | prototype | ❌英文 | **prompt 工艺金矿**:modify-eval-keep/discard 循环 + ANTI-SLOP/CRAFT,代码不可抄 | ✅exists |
| **mrigankad/Novel-OS** | 11 | 2026-05-23 | **MIT** | prototype | ❌英文 | 5-agent + **确定性(免 LLM)连续性引擎**,思路干净可抄码 | ✅exists |
| **guerra2fernando/libriscribe** | 81 | 2025-10-24 | **MIT** | prototype | ❌英文 | 11-agent 教科书式流水线,含查重/事实核查 agent | ✅exists |
| **datacrystals/AIStoryWriter** | 249 | 2025-11-24 | AGPL-3.0 | prototype | ❌英文 | 老牌大纲-章节-critique 循环,本地 Ollama 友好 | ✅exists |
| **Doriandarko/gemini-writer** | 279 | 2025-12-24 | MIT(署名) | prototype | ❌英文 | **单 agent loop** 路线(非多 agent),1M 上下文+自动压缩,对照组 | ✅exists |
| **wfcz10086/AI-自动生成** | 869 | 2025-07-01 | Apache-2.0 | production | ✅原生 | **prompt 模板工作流**(非 agent),声称数百工作室在用,prompt 库可借鉴 | ✅exists |
| **MaoXiaoYuZ/Long-Novel-GPT** | 1138 | 2025-11-05 | 无 license | prototype | ✅原生 | 大纲-章节-正文三层 + RAG 改写 + 成本实时显示,但无 license | ✅exists |
| **cjyyx/AI_Gen_Novel** | 419 | 2024-09-04 ⚠️stale | MIT | prototype | ✅原生 | RecurrentGPT 思路开山之一,作者结论:"现阶段 LLM 还写不了长篇网文" | ✅exists |
| **xindoo/ai-novel-lab** | ~41 | 2026-03 | MIT | case study | ✅原生 | 100 章 42.8 万字爽文实战,**AGENTS.md 约束文件**范式 | ✅exists |
| **KazKozDev/NovelGenerator** | ~130 | 2025-11 | other/未明 | prototype | ❌英文 | 多线叙事 + **角色"此刻知道什么"状态**,适合悬疑/多 POV | ✅exists |
| **adamwlarson/ai-book-writer** | ~384 | 2025-03 | ⚠️无 license | prototype | ❌英文 | AutoGen 六 agent,含专职 **Memory Keeper** | ✅exists |
| **BlinkDL/AI-Writer** | 3724 | 2025-05-15 | Apache-2.0 | —(模型) | ✅原生 | RWKV 中文网文**预训练模型**,非 agent 框架,另一品类参考 | ✅exists |
| **forsonny/Claude-Code-Novel-Writer** | 58 | 2025 | ⚠️无 license | prototype | ❌英文 | 用 Claude Code CLI 写整本书,Shell 驱动,思路参考 | ✅exists |

> **stale 判定(>18 月没动):** 仅 **cjyyx/AI_Gen_Novel**(2024-09)算 stale。其余全部在近 12 个月内有提交——说明这是一个**正在快速演化**的赛道,直接照抄 18 个月前的设计会落后。
>
> **评估基准 / 模型(非生成框架,但与质量系统强相关):**
> - **OedonLestrange42/webnovelbench**(MIT,EACL 2026 Findings,4000+ 中文网文语料 + 8 维 LLM-Judge)——见 §3。
> - **yingpengma/Awesome-Story-Generation**(meta 论文清单)——见 §5 学术血脉。

---

## 1. 可借鉴清单(按对你系统的价值排序)

### 1.1 ⭐ 最高价值:tyxben/AI_novel —— 几乎是你系统的"平行宇宙开源版"

- URL: https://github.com/tyxben/AI_novel [accessed:2026-05-30] · 225★ · MIT · pushed 2026-05-25 · v1.3.0(2026-04)
- **时效性**:近一周有提交,活跃。**鲁棒性**:225 star 中等,社区验证有限但非孤儿。**可行性**:**同栈 + MIT,移植成本最低**。
- **为什么对你最重要**:后端栈与你**高度重合**——LangGraph + LangChain + FastAPI + SQLite + Chroma(向量)+ NetworkX(图谱),Python 3.10+,且**原生中文网文场景**(修真/都市/武侠/轻小说等风格预设)。MIT = 可以直接读代码、抄实现。
  - ⚠️ **定位澄清(验真补充)**:验真证据显示该仓库官方描述偏向"AI 小说推文自动化——小说一键转短视频(有声书+AI 配图),适用于抖音/小红书"。也就是说**该仓库对外卖点是"小说→短视频"管线**,本调研关注的是它**内部的多 agent 文本生成层(LedgerStore/Brief/StyleBible 等)**。这层确实存在且与你同构,但移植前请 clone 实际代码确认这些组件是当前版本而非历史/营销 README 描述。
- **5-agent 架构**(与你六 agent 对应):
  - `ProjectArchitect`(骨架提案/接受/重生)≈ 你的 Director
  - `VolumeDirector`(单卷大纲与结算)—— **你目前缺的"卷级"层**
  - `ChapterPlanner`(实时 brief,消费 LedgerStore)≈ Planner
  - `Writer`(2000–3000 字 + ReAct 推理)≈ Writer
  - `Reviewer`(三维统一质量评估)≈ Consistency
- **直接可偷的组件设计**(正中你 R1/R2/R5 优先级):
  - **`LedgerStore`**:统一台账,跟踪**伏笔(foreshadowing)/叙事债(narrative debt)/角色状态**。把"伏笔+欠账"显式化,比你现在分散的 `knowledge_triples` + `character_memories` 更聚合。【R2 记忆 + R1 大纲】
  - **`BriefAssembler`**:每章生成前实时聚合上下文成 brief(≈ 你的 Camera + load_memories 合并)。【R2】
  - **`PrevTailSummarizer`**:把上一章结尾压成 ≤200 字,**专门防逐字重复**(§2 头号失败模式)。【R2,防重复刚需】
  - **`MilestoneTracker`**:卷级进度预算 + **强制推进**(防剧情原地打转)。【R1 大纲】
  - **`StyleBible`**:项目级文风锚定,带量化指标 + 范例段落。【R5 角色/Writer 风格】
  - **`Prompt Registry`**:**版本化 prompt** + 分阶段选模型(大模型做大纲、便宜模型做正文)。
  - **"budget mode"**:用规则替代部分 LLM 调用,声称降本约 40%。
- adoption cost: **low–medium**(同栈、同语言、MIT,可逐组件移植 LedgerStore / PrevTailSummarizer / StyleBible)。

### 1.2 ⭐ 结构化生成范式:RhythmicWave/NovelForge

- URL: https://github.com/RhythmicWave/NovelForge [accessed:2026-05-30] · 880★ · AGPL-3.0(+商业授权)· pushed 2026-04-26 · v0.9.5
- **时效性**:一个月内有提交。**鲁棒性**:880 star,中上。**可行性**:思路移植成本低,但 Neo4j 是新依赖;AGPL 闭源商用需走商业授权或只借思路。
- **核心可借鉴 = "schema-first / 卡片式"**:每种卡片(角色/场景/概念/世界观)有 **JSON Schema 定义**,AI 生成时按结构校验。验真确认其官方定位为"卡片式创作 + 基于 JSON Schema 的结构化 AI 生成与上下文引用 + 知识图谱集成"。**这命中你 SQLite+JSON 混存的痛点**——把生成强约束到 schema。【R1/R5】
- **`@DSL` 上下文引用语法**:`@title`/`@type`/`@self`/`@parent`,带过滤器 `[previous]`/`[filter:...]` 和字段级选择。一套**比纯向量检索更可控的"显式上下文注入"** DSL,值得抄进你的 load_context/load_memories。【R2】
- **知识图谱双存储**:Neo4j 或 SQLite,实体关系跟踪 + 自动注入参与实体到章节(对应你的 R3,优先级低,作为加分项)。
- 栈:FastAPI + SQLModel + Electron/Vue3(**Electron 桌面应用**,后端思路可借,前端形态与你 Next.js admin 不同)。
- adoption cost: **medium**。

### 1.3 ⭐ Prompt 工艺金矿:NousResearch/autonovel —— 读思想,别抄码

- URL: https://github.com/NousResearch/autonovel [accessed:2026-05-30] · 1025★ · **无 LICENSE 文件** · pushed 2026-03-20 · created 2026-03-14(很新)
- **时效性**:约 10 周未 push,活跃度中。**鲁棒性**:1025 star,但**仅实跑过 1 本书**(n=1)。**可行性(思想)**:high;**可行性(抄码)**:🚫**禁止**。
- ⚠️ **法律红线**:无 license = **保留全部版权,默认不可复制、不可改、不可分发**。你**不能抄它的代码**,但 README 里的 prompt 工艺文档是公开可读方法论,学思路合法。
- **方法论(灵感来自 karpathy/autoresearch 的 modify-evaluate-keep/discard,验真确认 autoresearch 仓库存在)**——四阶段流水线,细节见 `PIPELINE.md`(验真确认该文件存在,记录了 75k 字 / 23 章 / 5 轮 revision 的生产元数据):
  - 每个产物都走:**生成 → 评估(机械打分 + LLM judge)→ 分数变好就 commit,变差就 `git reset --hard HEAD~1`**。**用 git 当"接受/回滚"机制**是个很妙的工程 trick,你的 retry-loop 可以借鉴"只保留更优版本"的硬门控。
  - 阈值示例:foundation 退出 `foundation_score>7.5 AND lore_score>7.0`;章节接受 `score>6.0`(最多重试 5 次);修订循环连续 2 轮 Δ<0.5 就停。
  - **五个共演层**(voice / world / characters / outline / theme)**双向传播,debt 记在 state.json** —— 与你"graph state 是唯一真相源"哲学一致。
- **`ANTI-SLOP.md` / `ANTI-PATTERNS.md` / `CRAFT.md`**(仓库根目录可读,v1 已逐条摘录,见下方"v1 已验证细节"):**对抗"AI 腔"的负面规则库**——禁用词、套话、被动语态、句式雷同检测。**强烈建议读完后用自己的话重写成中文版"反 AI 腔"规则**喂给 Writer/Consistency agent。
- **它自己承认的失败案例**(§2.1 详述,对你最值钱)。
- adoption cost(借思想):**low**;抄码:**禁止(no license)**。

**v1 已验证细节(autonovel,可直接复用):**
- ANTI-SLOP 三检测:① 词级(`delve`/`utilize`/`leverage` 等过度词);② 结构(僵化段落模板、过度列表);③ 统计(perplexity、句长方差、burstiness)。禁用句式如 "This isn't just X—it's Y" / "It's worth noting that..."。
- ANTI-PATTERNS 12 类:Over-Explain、Triadic Listing、Negative-Assertion Repetition、Cataloging-by-Thinking、Simile Crutch、Section Break Overuse、Paragraph Uniformity、Predictable Emotional Arcs、Repetitive Chapter Endings、Balanced Antithesis("Not X, but Y")、Polished Dialogue、Scene-Summary Imbalance。
- CRAFT 8 正面启发:Specificity、Surprise、Rhythm Variation、Subtext、Earned Metaphor、Sensory Grounding、Restraint、Quiet Moments。对话测试:"删掉所有对话标签,还能分辨谁在说话吗?"

### 1.4 确定性连续性引擎:mrigankad/Novel-OS

- URL: https://github.com/mrigankad/Novel-OS [accessed:2026-05-30] · 仅 11★ · **MIT** · pushed 2026-05-23 · 验真确认其定位为"production-grade 多 agent 框架,持久记忆 + 自动连续性检查 + 5-agent 编辑流水线,v1.1"
- **时效性**:近一周有提交。**鲁棒性**:仅 11 star,**别当生产依赖**。**可行性**:MIT + Python,确定性引擎可作为独立模块直接移植。
- **一个设计点值得偷**:**确定性(免 LLM)连续性引擎**——纯规则预校验,捕捉"休眠伏笔(idle>3 章)/逾期未解决/未回收伏笔/角色缺席>5 章/不一致",**完全不花 LLM token**。这正好补强你的 Consistency agent——很多连续性检查根本不需要 LLM,用规则跑 ledger 即可,**省钱又稳定**。【R2/R5,降本】
- 5-agent:Architect / Scribe / Editor(5 种修订模式:line/developmental/pacing/dialogue/tension)/ Guardian(取证式连续性核查)/ Curator(文风)。结构化输出 merge 进**中央 JSON state**——和你 ChapterGraphState 同理。
- adoption cost: **low**。

### 1.5 教科书式多 agent 拆分:guerra2fernando/libriscribe

- URL: https://github.com/guerra2fernando/libriscribe [accessed:2026-05-30] · 81★ · **MIT** · pushed 2025-10-24 · 验真确认作者 Fernando Guerra & Lenxys,"多 agent 引导写作从构思到定稿"
- **时效性**:约 7 个月未 push,活跃度低但非 stale。**鲁棒性**:81 star。**可行性**:MIT,但 agent 太碎,按需挑。
- 价值:**11 个职责极细的 agent**(Concept/Outline/Character/Worldbuilding/Writing/ContentReview/Style/FactChecking/Plagiarism/Research/Formatting),给你**"agent 该怎么切"的菜单**。其中**查重 agent(Plagiarism)**和**事实核查 agent(FactChecking)**是你六 agent 里没有的,可按需补。支持 OpenAI/Claude/DeepSeek/Gemini/Mistral,ChromaDB。
- 局限(自承):产出只是起点非定稿,需人工复审。adoption cost: **low**。

### 1.6 中文产品级对照:MuMuAINovel / AI_NovelGenerator

- **xiamuceer-j/MuMuAINovel** https://github.com/xiamuceer-j/MuMuAINovel [accessed:2026-05-30] · 2520★ · GPL-3.0 · pushed **2026-05-29(昨天)** —— 当前**最活跃的中文小说产品**(验真确认定位"基于 AI 的智能小说创作助手")。
  - **时效性**:昨天有提交,最活跃。**鲁棒性**:2520 star,产品级。**可行性**:GPL-3.0,借思路可,抄码会传染 copyleft。
  - 可借鉴产品化特性:**伏笔管理(可视化时间线)**【R1/R2】、**章节关系图谱("思维链与章节关系图谱")**、**世界观自定义职业/力量体系**、**Prompt Workshop 社区模板共享**、**拆书功能**。栈:FastAPI+PostgreSQL+SQLAlchemy / React18+AntDesign+Zustand,Docker 部署带约 400MB embedding 模型。adoption cost: **medium**。
- **YILING0013/AI_NovelGenerator** https://github.com/YILING0013/AI_NovelGenerator [accessed:2026-05-30] · **5152★(star 王)** · AGPL-3.0 · pushed 2026-05-19 · V1.4.x。验真确认定位"用 AI 生成多章节长篇小说,自动衔接上下文、伏笔"。
  - **时效性**:约 11 天前 push,活跃。**鲁棒性**:5152 star,最高,但注意"star 高 ≠ 架构先进"(它是顺序流水线非真多 agent)。**可行性**:AGPL,copyleft 限制商用抄码。
  - 四段式流水线:**设定生成 → 目录创建 → 章节起草(向量检索上下文)→ 定稿(更新 character_state.txt / plot_arcs.txt + 一致性校对)**。`prompt_definitions.py` + `prompt_definitions_en.py` 模板化 prompt。**正在做 2.0 重构**。**它的 issue 区是你的同栈避雷指南**(见 §2.3)。adoption cost: **medium**。

### 1.7 其余对照组(C 档,点到为止)

- **Doriandarko/gemini-writer**(279★/MIT 署名/pushed 2025-12-24,验真确认"gemini 3 flash 驱动的写作 agent,自主创作小说"):**单 agent loop 路线**(非多 agent),1M 上下文 + 自动压缩。**作为你多 agent 架构的对照组**——证明单 agent + 超长上下文也是一条路,但缺显式状态管理。
- **wfcz10086/AI-自动生成**(869★/Apache-2.0,验真确认"基于 AI+提示词,数百家工作室/作者在用,v5.2"):**prompt 模板工作流**(非 agent)。Apache-2.0,**prompt 库可放心借鉴**。
- **xindoo/ai-novel-lab**(MIT,验真确认已产出"100 章 42.8 万字都市重生科幻《大厂重生:我用代码征服世界》",核心文档含 AGENTS.md):**AGENTS.md 单文件约束范式**——LLM 每章读取的 Markdown,含体裁惯例/角色规则/禁用词,dirt simple 且有效。n=1 案例,数字别照搬。
- **KazKozDev/NovelGenerator**(验真确认"LLM agent 生成完整小说,连贯剧情+人物+多文风"):**角色"此刻知道什么"知识状态**【R5,悬疑/多 POV 价值高】、多线同步时间线。TypeScript 栈,license 未明。
- **adamwlarson/ai-book-writer**(⚠️无 license,验真确认"AutoGen 多 agent 生成整本书"):六 agent 含 **Story Planner / World Builder / Memory Keeper / Writer / Editor / Outline Creator**,**专职 Memory Keeper agent** 是你没有的【R2】。无 license 只可读。
- **forsonny/Claude-Code-Novel-Writer**(⚠️无 license,验真确认"用 Claude Code CLI 写整本书",Shell 85.6%):一种"把 coding agent 当写作 agent"的另类思路,只可读。
- **BlinkDL/AI-Writer**(3724★/Apache-2.0,验真确认"RWKV 中文网文预训练生成模型,玄幻/言情"):**另一品类**——预训练模型而非 agent 框架。若将来想 fine-tune 中文网文写手,这是参考。
- **MaoXiaoYuZ/Long-Novel-GPT**(1138★/无 license,验真确认"基于 GPT 等大模型的长篇生成器 + 各种 prompt 与教程",自上而下大纲-章节-正文):成本实时显示 + 拆书能力,但无 license 只可读。

---

## 2. 失败案例 / 局限(本研究最值钱的部分,直接喂给你的设计约束)

### 2.1 ⭐ autonovel PIPELINE.md 自承的失败模式(来自实跑一本约 75k 字小说)

来源: https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md [accessed:2026-05-30](验真:文件存在,记录"The Second Son of the House of Bells"项目 75k 字 / 23 章 / 5 轮 revision)
- **节奏(pacing)是结构性顽疾**:评估器反复抓到"重复的节奏",作者结论"**把 7 分当节奏的天花板,除非重构剧情**"。→ 启示:节奏问题靠改 prompt/局部修订解决不了,得在**大纲/卷级**动刀(对应你 R1 大纲优先级)。
- **过度压缩反噬**:章节砍到 <1800 字会**制造出新的最弱章**;扩写 brief 实际产出比指定多约 30% 字数。→ 你的 2000–4000 字目标要留 buffer,别盲目压缩。
- **改一个分数掉另一个**:"修一个分常常掉另一个……转 2 轮后就停"。→ **多目标优化会互搏**,你的 retry-loop 设硬上限是对的(你现在 3 次),别无限重试。
- **AI 腔占修订量大头**:过度解释约 32%、冗余约 26%、跨章重复的"短语公式"。→ 直接印证你需要中文版 ANTI-SLOP 规则。
- **评估器有盲区**:自动打分**抓不到**"清单式全是 yes、无摩擦的盟友收集"和"把角色写成机制而非人"的单薄感——**只有 reader-panel(多角色读者模拟)能抓到**。→ 启示:纯 LLM-judge 不够,补一个"读者视角"评估维度。
- 成本现实:75k 字小说约 **15–30 小时** API 时间 + 多轮重构。

### 2.2 cjyyx/AI_Gen_Novel 作者的"投降宣言"(2024,虽 stale 但结论犀利)

来源: https://github.com/cjyyx/AI_Gen_Novel [accessed:2026-05-30](验真:项目标题"探究 AI 写网文能力的极限",419★/MIT)
- 作者直接写明:"**目前的大语言模型还没有足够的能力创作长篇网络小说**"。方案借 RecurrentGPT 的"循环计算"+ 记忆压缩(长文压成摘要)。→ 这是 2024 的判断;2025–2026 模型变强后,新项目(tyxben/MuMu)靠**更强的 ledger/brief 工程**部分绕过了,但"长篇靠纯生成不行、必须靠结构+记忆工程兜底"的结论依然成立。

### 2.3 YILING0013 issue 区暴露的工程坑(你的同栈避雷)

来源: https://github.com/YILING0013/AI_NovelGenerator/issues [accessed:2026-05-30]。以下 issue 经独立验真**逐条存在**:
- **#129(验真 ✅,Bug/Closed)**:`ValueError: Unknown embedding interface_format: DeepSeek`——非 OpenAI embedding 在定稿阶段崩。→ 你用 Chroma + 多 provider 时,**embedding 适配层要单独硬化**。【直接命中你的 R2 记忆栈】
- **#135(验真 ✅,作者 bolihai,2025-03-13,Open/bug)**:"在进行第一章的定稿时,报出未配置环境变量以及未在代码中传递 api 密钥"——**配置测试通过但实跑报"未配置 API key"**,测试态与运行态环境变量不一致(Windows 11)。→ 你的 ModelRegistry/deps 注入要保证**测试路径 = 运行路径**。
- **#112(验真 ✅)**:"生成第二章草稿出现问题"——多章衔接的早期 bug。→ 第 2 章是连续性问题的高发点(无"上一章"上下文时尤甚),重点测试章 2。
- ⚠️ **v1 中提到的 #120/#149/#150 未纳入本轮独立验真**(只验了 #112/#129/#135),引用前请二次确认这三个编号。

### 2.4 行业普遍失败模式(Reddit 写作者共识,二手聚合)

来源: https://resizemyimg.com/blog/writing-a-novel-with-ai-in-2025-what-works-what-fails-and-real-reddit-writers-feedback-on-using-chatgpt-or-similar-models/ [accessed:2026-05-30](验真 ✅,标题与"What Works / What Fails"分节、"60/40 split"均核实;**二手聚合 Reddit,非一手,可信度中**)
- 共识:"**AI 能当助手,不能当救世主**";擅长头脑风暴/大纲/世界观,**缺情感细腻度与人物塑造**,放养就出套话/平淡。自出版 Reddit 用户对 AI 辅助呈约 60/40 分歧。
- 关键长文失败机制:"在一段说了个点,过会儿换种说法又说一遍"——因为**文本越长,统计上最安全的预测往往是已引入过的概念**。→ 这从原理上解释了为什么 PrevTailSummarizer / 防重复 是刚需,不是锦上添花。

---

## 3. 基础事实核查应用(v2 关键纠偏)

> 本节是 v2 相对 v1 的硬增量:把三项独立事实核查的结论直接落到你的设计决策上。

### 3.1 🚩 "PerRoleCognition" = 杜撰,务必剔除

- **结论**:`PerRoleCognition` **不存在于 arXiv / Google Scholar / 全网任何学术文献**。若任何调研稿/方案引用了它,应视为杜撰或误记并删除。(本 R4 findings 原稿未直接引用此名,但作为跨方向纠偏在此明确记录,防止从 R5 角色方向串入。)
- **真实近义(可替代引用)**:
  - **RPNA(RP-Neuron-Activated Eval Framework)** — 《Dissecting Role Cognition in Medical LLMs via Neuronal Ablation》https://arxiv.org/abs/2510.24677(2025-10):用神经元消融研究 LLM 角色认知,探讨"角色提示是否诱发不同认知过程"。【与 R5 角色一致性相关】
  - **RoleRAG** — 《RoleRAG: Enhancing LLM Role-Playing via Graph Guided Retrieval》https://arxiv.org/abs/2505.18541:知识图谱引导检索增强角色扮演。【R5 + R3】
  - **Character-LLM** — https://arxiv.org/abs/2310.10158(EMNLP 2023):可训练的角色扮演 agent。【R5】

### 3.2 ✅ WebNovelBench 八维度(逐字核实,直接用作你的 LLM-Judge rubric)

- 来源:WebNovelBench 论文 Table 1,https://arxiv.org/html/2505.14818v1(repo: OedonLestrange42/webnovelbench,MIT,EACL 2026 Findings,>4000 中文网文语料,验真 ✅)。
- **八个评估维度(英文逐字 + 建议中译)**——**这是你质量系统应直接采用的 rubric**(取代任何凭记忆杜撰的维度名):
  1. Use of Literary Devices — 文学手法运用
  2. Richness of Sensory Detail — 感官细节丰富度
  3. Balance of Character Presence — 角色登场平衡
  4. Distinctiveness of Character Dialogue — 角色对话辨识度
  5. Consistency of Characterisation — 人物塑造一致性
  6. Atmospheric and Thematic Alignment — 氛围与主题契合
  7. Contextual Appropriateness — 语境恰当性
  8. Scene-to-Scene Coherence — 场景间连贯性
- 用法:LLM-as-Judge 对每章/每场景打分 → PCA 聚合 → 映射到相对人类语料的**百分位**(比裸分更可解释)。HuggingFace 上 4000+ 中文网文语料可同时用作**微调数据 + 百分位基线**。
- ⚠️ **历史教训**:早期会话曾凭记忆杜撰过这些维度名——**永远引用论文,不用训练记忆**。本稿八维度为逐字核实版。

### 3.3 ✅ 2026 中文大模型文笔实测对比(指导你的 ModelRegistry 选型)

来源:2026-03~05 多方实测聚合(知乎/CSDN/苏米客/TokenMix/DEV 等,见 citations)。accessed 2026-05-30。
- **中文文笔/创意写作排名**:
  1. **Kimi K2.6** — **首位**(创意写作 + 挑战性角色扮演双榜第一,创意写作评测超 GPT-5;K2 Thinking 能驾驭微妙文风、长篇保持风格连贯、情感共鸣强、意象生动)。
  2. **Claude 4.6 Opus**(参考对标,业界天花板,最自然"人味",非主要对比对象)。
  3. **DeepSeek V4-Pro** — 其次(中文综合强、SimpleQA 84.4%,但**文笔专项数据有限**,强项在知识/推理)。
  4. **GLM-5.1 / Qwen 3.6-Plus** — 相当(通用强,创意写作非重点)。
- **价格(2026-04)**:DeepSeek V4 Flash $0.25/M(最便宜)< Qwen 3.6-Plus(约 ¥0.035/1K 输入)< GLM-5.1($1.26/M 输入,中高)< Kimi K2.6(¥3–3.5/M,最贵,创意溢价)。
- **上下文长度**:Kimi K2.6 **2M**(最长)> Qwen 3.6-Plus / DeepSeek V4-Pro **1M** > GLM-5.1 **128K**(最短)。
- **对你 ModelRegistry 的直接建议(per-agent 绑定 + 分阶段选模型)**:
  - **Writer / 正文文笔最重的 agent** → 首选 **Kimi K2.6**(文笔第一 + 2M 上下文利于长篇连贯);成本敏感时降级 **DeepSeek V4**(文笔可接受、极致性价比)。
  - **大纲 / 设定 / 一致性等结构性 agent** → **DeepSeek V4-Pro**(知识/推理强、1M 上下文、便宜),或便宜档跑机械校验。
  - **完全开源/本地部署需求** → **Qwen 3.6-Plus**(Apache-2.0,C-Eval 93%,¥0.035/K)。
  - 这与 autonovel/tyxben 的 **"大模型做大纲、便宜模型做正文 / budget mode"** 思路可结合——但注意:网文场景下"正文"恰恰最吃文笔,**别把正文一刀切降到最便宜模型**,建议 Writer 用文笔档、其余降级。

---

## 4. 综合判断 & Top 候选

**赛道判断**:2025–2026 是开源长篇小说生成的爆发期,十几个项目近 12 个月都在更新。**共识收敛**——长篇连贯性**不靠"更强生成",靠四件套工程**:
1. **分层大纲 + 卷级强制推进**(tyxben MilestoneTracker、autonovel pacing 结论、MuMu 伏笔时间线);【R1】
2. **显式 ledger 跟踪伏笔/叙事债/角色状态**(tyxben LedgerStore、Novel-OS 确定性引擎);【R2/R5】
3. **上一章结尾压缩防重复**(tyxben PrevTailSummarizer,Reddit 原理 + autonovel 跨章重复数据共同印证);【R2】
4. **机械规则 + LLM-judge + 读者模拟三层评估**(autonovel dual immune + reader-panel、WebNovelBench 8 维)。

你现有六 agent 架构**方向正确**,但**缺两层**:(a)**卷级层**(Volume/Milestone);(b)**显式 ledger 聚合层**(把分散的 knowledge_triples + character_memories 聚成一张伏笔/债/角色台账)。

### Top 3 候选(给你的行动建议)

1. **🥇 tyxben/AI_novel(MIT,同栈,原生中文)—— 首选移植源**
   - 行动:clone 读码,**逐组件移植** `LedgerStore`(伏笔+叙事债+角色状态聚合)、`PrevTailSummarizer`(防重复)、`StyleBible`(文风锚定)、`MilestoneTracker`(卷级强推)、`Prompt Registry`(版本化 prompt)。MIT 零法律负担。**移植前 clone 确认这些组件是当前版本**(因其对外 README 偏"小说转短视频"营销)。adoption: **low–medium**。

2. **🥈 NousResearch/autonovel(无 license,读思想)—— 首选方法论源**
   - 行动:**只读不抄**。把 `ANTI-SLOP.md`/`ANTI-PATTERNS.md`/`CRAFT.md`/`PIPELINE.md` 读透,产出**你自己的中文版"反 AI 腔规则 + 接受/回滚硬门控 + 多目标互搏止损规则 + reader-panel 评估维度"**。adoption(思想): **low**。

3. **🥉 WebNovelBench 八维度 + 语料(MIT)+ RhythmicWave/NovelForge 结构化范式**
   - 行动 A(质量系统):把 §3.2 的**八维度逐字**接入 LLM-Judge,PCA → 百分位;用 HuggingFace 4000+ 中文网文做基线。adoption: **low**。
   - 行动 B(结构化生成,AGPL 只借思路):借鉴 NovelForge 的 **JSON-Schema 卡片**(强约束生成,治"看着能用实则一团乱")和 **@DSL 上下文引用语法**(可控注入,补充纯向量检索),改进 load_context/load_memories。adoption: **medium**。

**辅助**:
- Novel-OS 的**确定性免-LLM 连续性引擎**单独偷过来强化 Consistency agent(省 token);
- libriscribe 的 **agent 切分菜单**(查重 Plagiarism / 事实核查 FactChecking)按需补;
- adamwlarson 的**专职 Memory Keeper agent** 概念可考虑【R2】;
- **模型选型**(§3.3):Writer 用 Kimi K2.6,结构 agent 用 DeepSeek V4-Pro,开源需求用 Qwen 3.6-Plus。

### License 速查(能不能抄码)

- ✅ **可放心抄码(宽松)**:tyxben/AI_novel(MIT)、Novel-OS(MIT)、libriscribe(MIT)、gemini-writer(MIT+署名)、wfcz10086(Apache-2.0)、BlinkDL/AI-Writer(Apache-2.0)、cjyyx/AI_Gen_Novel(MIT)、xindoo/ai-novel-lab(MIT)、webnovelbench(MIT)。
- ⚠️ **copyleft,抄码会传染/商用受限**:MuMuAINovel(GPL-3.0)、AI_NovelGenerator(AGPL-3.0)、NovelForge(AGPL-3.0,有商业授权)、AIStoryWriter(AGPL-3.0)。**借思路 OK,直接 copy 进闭源商用要谨慎**。
- 🚫 **无 license = 默认不可复制**:NousResearch/autonovel、MaoXiaoYuZ/Long-Novel-GPT、adamwlarson/ai-book-writer、forsonny/Claude-Code-Novel-Writer。KazKozDev/NovelGenerator 标"other/未明",同样按不可抄处理。**只能读不能抄**。

---

## 5. 学术血脉(给架构决策提供"为什么",B 档点到为止)

来源: https://github.com/yingpengma/Awesome-Story-Generation [accessed:2026-05-30](验真 ✅)。以下论文经独立验真,**标注真实地址**:
- **RecurrentGPT**(2023,任意长文本交互生成)— https://arxiv.org/abs/2305.13304 ✅(代码 aiwaves-cn/RecurrentGPT)。长文记忆"自然语言 LSTM"范式的源头,你 LayeredMemory 的祖先。
- **Ex3: Automatic Novel Writing by Extracting, Excelsior and Expanding**(ACL 2024)— ⚠️**正确地址 https://aclanthology.org/2024.acl-long.494/**(ACL 2024, pp.9125–9146)。**v1/旧稿曾用的 `.../2024.acl-long.832/` 是错的**(那个 URL 指向另一篇 M4LE 论文)——见 §"v1 ↔ v2 diff"。
- **Weaver: Foundation Models for Creative Writing**(2024)— https://arxiv.org/abs/2401.17268 ✅(创意写作基座模型)。
- **2025–2026 多 agent / 记忆方向(与你 R1/R2 直接相关):**
  - **Agents' Room: Narrative Generation through Multi-step Collaboration**(ICLR 2025)— https://arxiv.org/abs/2410.02603 ✅(DeepMind,叙事理论驱动的多 agent 分工)——**多 agent 写作的学术背书**。
  - **Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement(DOME)**(arXiv 2412.13575,NAACL 2025 线)— https://arxiv.org/abs/2412.13575 ✅。**动态分层大纲(DHO)+ 基于时序知识图谱的记忆增强模块**——**同时正中你 R1(大纲)+ R2(记忆)+ R3(图谱)**,与你架构目标最贴近的单篇论文。
- ⚠️ v1 中提到的 **SCORE / LongEval / HAMLET / SWAG / "Improving Pacing in Long-Form Story Planning"** 本轮**未逐篇独立验真**,引用前请打开 arxiv 二次确认。

---

## 6. Open Questions(留给下一轮 / 你拍板)

1. **卷级(Volume)层要不要进你的 LangGraph?** tyxben(VolumeDirector)、autonovel(MilestoneTracker)、DOME(动态分层大纲)都有显式卷级/分层强推。你目前是章级 graph,**长篇(>30 章)很可能需要补一层卷级 graph**——值得单开设计 spike。【R1 最高优先级之一】
2. **Ledger vs 现有 knowledge_triples+character_memories,合并还是并存?** tyxben 的 `LedgerStore` 把伏笔/债/角色状态聚合成一张台账,可能比你分散的两套存储更易做"未回收伏笔/角色缺席"查询;Novel-OS 的免-LLM 规则引擎正好跑在这张台账上。需评估迁移成本。【R2/R5】
3. **autonovel 的 prompt 工艺文件能否合法借用文字?** 无 license 严格说连 prompt 文本都不可复制。**建议:读完用自己的话重写中文版**,不要逐字拷贝其 ANTI-SLOP/CRAFT。
4. **质量评估三层怎么落地?** WebNovelBench 八维(LLM-judge)+ Novel-OS 确定性规则(免 LLM)+ autonovel reader-panel(读者模拟)——三者如何编排进你现有 consistency_check 的 retry-loop(且保持 3 次硬上限不互搏死循环)?
5. **模型分层选型验证**:§3.3 建议 Writer=Kimi K2.6 / 结构 agent=DeepSeek V4-Pro / 开源=Qwen 3.6-Plus,但中文文笔评测多为二手聚合,**落地前建议用你自己的 WebNovelBench 八维 rubric 跑一轮 A/B**(用你的题材语料),别全信榜单。
6. **中文"反 AI 腔"规则缺乏现成开源库**:英文有 autonovel 的 ANTI-SLOP,**中文网文"AI 腔"特征(滥用"仿佛/此刻/不由得"、四字成语堆砌、"修长如玉手/星眸/嘴角勾起一抹弧度"、"不是 X 而是 Y")目前没看到现成开源规则集**——这是你需要自建、也是潜在差异化点(甚至可研究化发表)。[no-source-found:本轮未单独检索"中文 AI 写作 反 AI 腔 规则 开源",标注待补]

---

## 7. 方法学备注 & 未能验证项

- 所有 star/fork/pushed_at/license/archived 字段均来自 `api.github.com/repos/{repo}` 实时查询(2026-05-30),非训练记忆。
- autonovel 无 license 经 `api.github.com/repos/NousResearch/autonovel/license` 返回 `Not Found` + 仓库根目录文件列表无 LICENSE 双重确认。
- 架构/失败案例来自实际 WebFetch 的 README 与 PIPELINE.md;Reddit 共识为二手聚合站,已标注可信度中。
- **未能验证项**:`mind-protocol/Lesterpaintstheworld/terminal-velocity` 经 GitHub API 返回 null,疑似改名/转移/私有,**未能验证,标 [no-source-found:GitHub API 对 Lesterpaintstheworld/terminal-velocity 返回空]**。
- **本轮新增验真覆盖**:tyxben/AI_novel、MuMuAINovel、AI_NovelGenerator(+issue #112/#129/#135)、NovelForge、autonovel(+PIPELINE.md)、Novel-OS、libriscribe、AIStoryWriter、gemini-writer、wfcz10086、Long-Novel-GPT、cjyyx/AI_Gen_Novel、BlinkDL/AI-Writer、KazKozDev、adamwlarson、forsonny、xindoo、Awesome-Story-Generation、RecurrentGPT、Agents' Room、DOME、Weaver、karpathy/autoresearch、Reddit 聚合页 —— **全部 exists=true**;唯一 exists=false 为 Ex3 的旧 aclanthology URL(论文真实,地址纠正)。

---

## v1 ↔ v2 diff

> v1 = `2026-04-28-novel-system-survey/r4-open-source.md`(20 个项目,英文为主,偏学术 repo 编目)。
> v2 = 本稿(2026-05-30,中文,按"对你重构价值"重排,叠加独立验真 + 三项基础事实核查)。

### 🆕 v2 新增(v1 没有的)

1. **整组 2026 新活跃项目**(v1 调研截止 04-28 前,这些要么没收要么没展开):
   - **tyxben/AI_novel**(v2 列为 🥇 首选移植源)—— v1 完全没有。这是 v2 最重要的新增:同栈 + MIT + 原生中文 + LedgerStore/PrevTailSummarizer/StyleBible/MilestoneTracker/Prompt Registry 五大可偷组件。
   - **xiamuceer-j/MuMuAINovel**(2520★,昨天还在更新的最活跃中文产品)—— v1 没有。
   - **RhythmicWave/NovelForge**(JSON-Schema 卡片 + @DSL 上下文引用)—— v1 没有,v2 列为 🥉 结构化范式。
   - **mrigankad/Novel-OS**(确定性免-LLM 连续性引擎)—— v1 没有。
   - **guerra2fernando/libriscribe**(11-agent + 查重/事实核查)—— v1 没有。
   - **Doriandarko/gemini-writer**(单 agent loop 对照组)、**wfcz10086/AI-自动生成**(prompt 工作流)—— v1 没有。
2. **"四件套工程"共识框架**(分层大纲+卷级强推 / 显式 ledger / 上一章压缩防重复 / 三层评估)—— v1 的 cross-project synthesis 较散,v2 收敛成可执行的四条。
3. **§3 基础事实核查整节**(v2 硬增量):
   - **"PerRoleCognition" 杜撰预警**(给出 RPNA/RoleRAG/Character-LLM 真实替代)。
   - **2026 中文大模型文笔实测对比**(Kimi K2.6 文笔第一 / DeepSeek V4 性价比 / Qwen 开源 / GLM 短上下文)+ **per-agent 模型绑定建议**。v1 完全没有模型选型维度。
4. **两层架构缺口诊断**:明确指出你缺"卷级层"+"显式 ledger 聚合层"——v1 没有这个聚焦结论。
5. **每条 finding 补"时效性/鲁棒性/可行性"三标签**,符合 v2 任务要求。
6. **失败案例 §2 整理成"可直接喂给设计约束"**(autonovel 五大失败模式 + 成本现实 + Reddit 长文重复原理)—— v1 的失败信息散在各项目"What to AVOID"里,v2 集中成最值钱的一节。

### ✏️ v2 纠正(v1 写错或需澄清的)

1. **Ex3 论文 URL 纠正(对应唯一 exists=false)**:正确地址是 **https://aclanthology.org/2024.acl-long.494/**;`.../2024.acl-long.832/` 是**错的**(指向另一篇 M4LE 论文)。v1 在 Awesome-Story-Generation 条目仅按名提及 Ex3 未给错 URL,但旧稿/串稿若用了 `.832` 必须改。
2. **WebNovelBench 八维度 = 逐字核实版**:v1 已列出且自标"verified verbatim",v2 **再次以独立核查确认**这 8 个英文维度名逐字正确,并定为质量系统应直接采用的 rubric(强调:永远引论文不引记忆)。
3. **tyxben/AI_novel 定位澄清**:验真显示其对外 README 偏"小说→短视频(有声书+AI 配图,抖音/小红书)"营销;v2 明确"本调研关注其**内部多 agent 文本生成层**,移植前须 clone 确认组件是当前版本",避免被营销描述误导。
4. **"star 高 ≠ 架构先进"延续并强化**:v1 已指出(YILING0013 5k star 实为顺序流水线),v2 在全景表与 1.6 节再次标注,并补"Novel-OS 仅 11 star 别当生产依赖"等鲁棒性提示。
5. **issue 编号收敛**:v1 §2.3 在旧稿语境引用过一串 issue;v2 只保留经**独立验真存在**的 **#112/#129/#135**,并显式标注 **#120/#149/#150 本轮未验真、引用前需二次确认**。
6. **autonovel 字数口径**:统一为约 **75k 字 / 23 章 / 5 轮 revision**(来自 PIPELINE.md 验真元数据);v1 文中"79k-word"为概数,v2 以验真记录的 75k 为准。

### 🗑️ v2 删除(剔除的幻觉 / 降权的内容)

1. **🚩 剔除幻觉:Ex3 的 aclanthology URL `https://aclanthology.org/2024.acl-long.832/`** —— 验真 exists=false(该 URL 实为 M4LE 论文)。已从所有引用中删除/替换为正确的 `.494`。**这是本方向唯一一条 exists=false 的引用。**
2. **🚩 跨方向预防性剔除:"PerRoleCognition"** —— 基础事实核查判定为全网无据的杜撰术语。本 R4 原 findings 未直接引用,但在 §3.1 明确登记"若出现即删",防止从 R5 角色方向串入终稿。
3. **降权(非删除)v1 的纯学术 repo 编目**:v1 用大量篇幅编目 Re3 / DOC / StoryWriter(THU-KEG)/ Ex3-NovelWriter / BookWorld / IBSEN / CreAgentive / SillyTavern 等(很多是 2022–2024 研究代码或非小说项目)。v2 按 S 档"对你重构最可借鉴"原则,将其**压缩进 §5 学术血脉点到为止**(DOME / Agents' Room / RecurrentGPT / Weaver 保留为架构依据),把正文篇幅让给 2025–2026 可落地的工程项目。**这不是说 v1 错,而是 v2 聚焦可行性。**
4. **未独立验真项显式降权**:v1 §3/末尾列的 SCORE / LongEval / HAMLET / SWAG / "Improving Pacing..." 等论文,v2 标注"本轮未逐篇验真,引用前二次确认",不再当作既定事实陈述。

### 备注:v1 中**未被验真否定**的内容予以保留

v1 对 autonovel 的 ANTI-SLOP/ANTI-PATTERNS/CRAFT 逐条摘录、WorldInfo 三层触发(SillyTavern)、各项目 memory/outline/character 对比表等,均未被本轮验真否定,作为已验证细节在 v2 §1.3 与正文中保留或引用(SillyTavern 因属"roleplay 运行时"非长篇生成主线,降权为参考)。
