# R7 + R8 · Agent 编排 confirm + 商业工具脚注（Light Scan）

| Field | Value |
|---|---|
| Topic | R7: confirm LangGraph 仍是 right choice，无颠覆性新框架；R8: NovelCrafter / Sudowrite / NovelAI 学 UX 模式 |
| Author | engineer (Claude) |
| Researched | 2026-04-28 |
| Verdict | **R7: 维持 LangGraph，不切换**；**R8: 学 Sudowrite 的"创作 muse"+ Novelcrafter 的"Codex world-building DB"两类 UX** |

> 用户优先级声明：两者都是 Tier C；仅 confirm，不深扒。

## R7 · Agent 编排（confirm）

### Findings

#### F1 · 2026 多 Agent 框架对比

| 框架 | 复杂任务（8+ 步）完成率 | 中等任务完成率 | Production 推荐度 |
|---|---|---|---|
| **LangGraph** | **62%** | **76%** | ⭐⭐⭐⭐⭐ |
| CrewAI | 54% | 71% | ⭐⭐⭐（线性任务佳） |
| AutoGen / AG2 | 58% | 68% | ⭐⭐⭐⭐ |
| MetaGPT | n/a（SOP-driven） | n/a | ⭐⭐⭐（code-artifact 强） |

**来源**：[pooya.blog/blog/crewai-vs-langgraph-autogen-comparison-2026](https://pooya.blog/blog/crewai-vs-langgraph-autogen-comparison-2026/) [accessed:2026-04-28] + [openagents.org/blog/.../open-source-ai-agent-frameworks-compared](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) [accessed:2026-04-28]

**关键 verbatim**：
> "Teams using LangGraph reported 60% faster debugging cycles compared to conversation-based frameworks for workflows with 3+ conditional branches."
> "Regulated, exception-heavy, or customer-facing workflows usually need LangGraph because approval paths, retries, and auditability matter."

#### F2 · 我们当前 LangGraph 适用性

- ✅ **我们的 graph 有 3+ 条件分支**（consistency_check → pass/fail → retry / save → extract_memories）
- ✅ **要求 auditability**（监督 protocol 期间每 step 可追踪）
- ✅ **state 管理 = ChapterGraphState / InitGraphState 已定义**
- ✅ Phase 0 监督已批 LangGraph，无理由切换

### Recommendation

- **Phase 1: 维持 LangGraph 1.x**
- **Phase 1+: 升级 LangGraph 2.x 时随官方迁移指南做**（不主动切换框架）
- **Phase 4+ 单独评估**：如果某些 micro-agent（如 polish step）想用 conversation-style，可在 LangGraph 节点内嵌一个 AutoGen instance（不破坏整体架构）

### 时效性 / 鲁棒性 / 可行性

| 框架 | 时效性 | 鲁棒性 | 可行性（切换） |
|---|---|---|---|
| LangGraph（保持） | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 已用 |
| CrewAI（切） | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐（不切，无收益） |
| AutoGen（切） | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| MetaGPT（切） | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |

### Sources (R7)

- [pooya.blog (LangGraph vs CrewAI vs AutoGen 2026)](https://pooya.blog/blog/crewai-vs-langgraph-autogen-comparison-2026/) [accessed:2026-04-28]
- [openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) [accessed:2026-04-28]
- [meta-intelligence.tech (2026 comparison)](https://www.meta-intelligence.tech/en/insight-ai-agent-frameworks) [via search snippet, accessed:2026-04-28]

---

## R8 · 商业工具脚注

### F3 · Sudowrite ("Muse" school) — 创作 muse 范式

**定位**（per [sudowrite.com](https://sudowrite.com/blog/sudowrite-vs-novelcrafter-the-ultimate-ai-showdown-for-novelists/) [accessed:2026-04-28]）：
> "The wild-eyed muse whispering beautiful, chaotic prose."

**架构特色**：
- 自家 prose model 叫 **Muse**，"crafted with permission from authors for authors"
- 强调"prose style / sensory detail / genre conventions"
- 不强调结构 / outline / world-building

**用户反馈**：
> "Sudowrite's latest update, specifically its Muse model, is described as 'the first one that has actually felt useful for drafting fiction.'"

**对我们的可行性**：
- ⚠️ 闭源 SaaS，**架构不可抄**
- ✅ **UX 模式可借鉴**：把"灵感快速注入"做成 admin UI 的"创作 muse" 按钮（点一下生成 3 段候选写法，作者挑）
- ✅ 启示：自家 prose model（即 Phase 3+ FTPO 微调）可能成为 differentiator

### F4 · Novelcrafter ("Architect" school) — Codex 世界书

**定位**（per [ilampadmanabhan.medium.com (2026-04 review)](https://ilampadmanabhan.medium.com/novelcrafter-review-powerful-for-fiction-writers-frustrating-to-set-up-april-2026-64d391c629a2) [accessed:2026-04-28]）：
> "The master architect handing you the blueprints to your world."
> "A control-first option: deeper in some areas, more flexible, and much more demanding."

**架构特色**：
- **Codex** = "personal story wiki on steroids"（中央数据库：角色 / 设定 / lore / notes）
- BYOM（Bring Your Own Model）：允许接 OpenAI / Anthropic / Mistral / local
- **不强迫 UI 范式**，作者自己决定 workflow
- 学习曲线陡峭

**对我们的可行性**：
- ✅ **Codex 模式正是我们 story_bible + world_book + characters 的产品化形态**
- ✅ **BYOM 模式与我们 LiteLLM gateway 的设计一致**
- 启示：我们的 admin UI 可以围绕"Codex"组织（侧栏 = entity browser，主区 = chapter writer）
- ⚠️ 学习曲线警告：Novelcrafter 的差评主要是"setup cost is real"，我们要避免

### F5 · SidekickWriter — 2026 新晋竞争者

- Source: [sidekickwriter.com/blog/...-2026](https://www.sidekickwriter.com/blog/sudowrite-vs-novelcrafter-vs-sidekickwriter-2026) [accessed:2026-04-28]
- 定位：定位偏 mid-segment（介于 Sudowrite 简单和 Novelcrafter 复杂之间）
- 较新，未广泛 review

### F6 · NovelAI

- Source: 多个 search 提及，未直接 fetch
- 定位：偏 ACG / 二次元 / 同人 fiction，与我们主流网文 segment 不重叠

### Recommendation

#### UX 设计借鉴

1. **从 Sudowrite 抄"创作 muse"按钮**
   - 每个 chapter / scene editor 加一个"灵感按钮"
   - 点击 → 给当前段落 3 个备选续写，作者挑或合成
   - **Phase 4 admin UI 设计要点**

2. **从 Novelcrafter 抄"Codex"组织方式**
   - 我们的 story_bible / world_book / characters 在 UI 上呈现为"侧栏 entity browser + 关联浏览"
   - **Phase 1 UI 设计要点**：现在 admin 散乱在多个 tab，应该重构为 Codex

3. **避开 Novelcrafter 的 setup 陡坡**
   - 给一键 onboarding（"创建你的第一本书"向导）
   - 默认 reasonable template，进阶用户再自定义

#### 商业模式数据点（参考）

- 来源：reviews 散见
- 三家典型定价：$10-30/月
- 我们 Phase 4 上线后若收费：可考虑 freemium + 按 token / 章节定价

### Sources (R8)

- [sudowrite.com (Sudowrite vs Novelcrafter)](https://sudowrite.com/blog/sudowrite-vs-novelcrafter-the-ultimate-ai-showdown-for-novelists/) [accessed:2026-04-28]
- [sidekickwriter.com (2026 三家对比)](https://www.sidekickwriter.com/blog/sudowrite-vs-novelcrafter-vs-sidekickwriter-2026) [accessed:2026-04-28]
- [ilampadmanabhan.medium.com (2026-04 Novelcrafter review)](https://ilampadmanabhan.medium.com/novelcrafter-review-powerful-for-fiction-writers-frustrating-to-set-up-april-2026-64d391c629a2) [accessed:2026-04-28]
- [nerdynav.com/sudowrite-review (2026 Sudowrite test)](https://nerdynav.com/sudowrite-review/) [via search snippet, accessed:2026-04-28]
- [novarrium.com/blog/best-ai-writing-tool-novels-2026 (5 工具 ranking)](https://novarrium.com/blog/best-ai-writing-tool-novels-2026) [via search snippet, accessed:2026-04-28]
