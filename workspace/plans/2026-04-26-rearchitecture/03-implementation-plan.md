# 03 · 实施计划（6 阶段路线）

## 总体策略：基线驱动渐进改造

**不是 big bang 重写**，而是：
1. **Phase 0 必须最先做**——建立客观评测基线（WebNovelBench 8 维度 + autonovel slop 检测）
2. 后续每个 Phase 都要在基线上证明 ≥ X% 改进，否则**回滚或改方案**
3. 现有 LangGraph / 版本化 / DeepSeek 适配器 / 前端组件库**全部保留**，逐步替换 agent 实现

## 目标终态架构（基于调研整合）

```
┌──── 创意层 (Phase 5) ────┐  DailyHotApi → 博查 → Jina → InspirationCard
└──────────┬───────────────┘
┌──── 契约层 (Phase 4) ────┐  StoryContract（读者承诺/爽点密度/钩子）
└──────────┬───────────────┘
┌──── 设定层 (Phase 1+) ───┐  Bible Lab + VoiceBible + ForeshadowLedger + AntiPatternBook
└──────────┬───────────────┘
┌──── 模拟层 (Phase 4) ────┐┌──── 导演层 (Phase 3) ────┐
│ World Sim Kernel          ││ NarrativeDirector         │
│ Actor/Goal/WorldClock     ││ ChapterFocusPlan          │
│ → EventCandidate Pool     ││                           │
└──────────┬───────────────┘└──────────┬───────────────┘
┌──── 戏剧层 (Phase 3) ────┐  SceneCard（欲望/障碍/转折/代价/钩子）
└──────────┬───────────────┘
┌──── 记忆层 (Phase 2) ────┐  Graphiti+Kuzu / WorldBook(SillyTavern字段) / ContextCompiler
└──────────┬───────────────┘
┌──── 写作层 (Phase 3) ────┐  Per-Role Agent (CreAgentive) + 多候选 best-of-N
└──────────┬───────────────┘
┌──── 编辑部 (Phase 1+6) ──┐  Continuity / Drama / Style / Pacing / Reader / Market
│                           │  + slop_score（机械） + DOME conflict detection
└──────────┬───────────────┘
┌──── 修订层 (Phase 1+6) ──┐  RevisionBrief → 局部重写 / Pairwise Elo
└──────────┬───────────────┘
┌──── 评测基线 (Phase 0) ──┐  WebNovelBench 8 维度 + HNES 综合分（每章自动评分）
└───────────────────────────┘
```

---

## Phase 0：评测基线 · 1.5 周 · 第一优先级

> **元原则**：没有基线 = 没有进步证据。本 Phase 先于任何"重构"动作。

### 任务

| # | 任务 | 输出物 | 工作量 |
|---|------|--------|--------|
| 0.1 | 中文小说评测器（WebNovelBench 8 维度） | `backend/quality/webnovel_judge.py` | 2 天 |
| 0.2 | 反 AI 味检测器（autonovel slop_score 中文化） | `backend/quality/slop_detector.py` | 1 天 |
| 0.3 | HNES 综合分计算器 | `backend/quality/hnes.py` | 0.5 天 |
| 0.4 | 跑现有 3 本小说基线 | `data/baselines/{story_id}.json` | 0.5 天 |
| 0.5 | 前端 `/insights/quality` Tab | 4 个图表（趋势/对比/分布/heatmap） | 2 天 |
| 0.6 | 自建中文 AI 味坏样本库（100 条） | `data/baselines/slop_samples.json` | 1 天 |

### 出口标准

- 现有 3 本小说每章每维度都有评分入库
- 前端能展示「质量趋势曲线」和「跨小说对比」
- slop_score 在 100 条人工标注的中文坏样本上召回率 ≥ 80%
- **基线分数文档化**（写入 `data/baselines/baseline_report.md`）

### 关键技术决策

- **评委 LLM**：建议 DeepSeek-V4-Pro（关思考），论文用 V3 可对照
- **评分方式**：每章一次评测 = 1 次 LLM 调用，约 ¥0.05/章
- **存储**：新增 `chapter_quality_scores` 表（chapter_id, dimension, score, evidence, judged_at, judge_model）

### 为什么先做这个

> 用户原话："长篇越来越散" / "AI 味重" / "效果太差"。这些都是**主观感受**，没有数字就无法证伪。
> 先做基线 = 给后续每个 Phase 一把"质量标尺"。否则三个月后我们还在凭感觉说"好像变好了一点"。

---

## Phase 1：核心写作闭环 · 2-3 周 · 第二优先级

> 蓝图原计划"6 个新模块一起做"，调研后修正为：**先做最小可见效的部分**——抄 autonovel 5 资产 + 加 2 个 critic agent。

### 任务

#### 1.1 植入 autonovel 5 大资产（中文版）· 0.5 周

| 资产 | 路径 | 用途 |
|------|------|------|
| `anti_slop.md` | `backend/prompts/assets/anti_slop_zh.md` | Writer / Consistency / Revision 引用 |
| `anti_patterns.md` | `backend/prompts/assets/anti_patterns_zh.md` | 12 个 AI 失败模式清单 |
| `craft.md` | `backend/prompts/assets/craft_zh.md` | Save the Cat / MICE 等结构理论 |
| `voice_template.md` | `backend/prompts/assets/voice_template_zh.md` | 文风指纹模板（每本小说初始化时填充） |
| `canon_schema.md` | `backend/prompts/assets/canon_schema_zh.md` | 硬事实 7 大类 schema |

具体动作：英文 → 中文翻译（人工 review 后入库），写一个 prompt loader 让所有 agent 都能引用。

#### 1.2 新增 `AdversarialEditor` agent · 0.5 周

```
输入：刚生成的章节
输出：分类切割表 [{quote, type: FAT/REDUNDANT/OVER-EXPLAIN/GENERIC/TELL/STRUCTURAL,
                   reason, action: CUT/REWRITE, rewrite}]
集成：chapter graph 在 scene_consistency 之后跑一次
```

#### 1.3 新增 `RevisionBriefGenerator` agent · 0.5 周

```
输入：critique + adversarial cuts + slop score + reader panel（如有）
输出：可执行的修订 brief（markdown 格式）
集成：替代当前"盲生" retry，直接喂给 scene_writer 做定向重写
```

#### 1.4 改造 chapter graph · 0.5 周

```
旧：write_scenes → consistency_check → save_chapter
新：write_scenes → scene_consistency → adversarial_edit
   → assemble_chapter → consistency_check + slop_check
   → revision_brief（如失败）→ rewrite_targeted（局部，不重写整章）
   → save_chapter
```

#### 1.5 评分校准 prompt 库 · 0.5 周

照抄 autonovel 的 "9-10 分必须 surprise / 必须先说 gap 再打分" 规则到所有 critic agent 的 prompt。

### 出口标准

- **Phase 0 基线评分提升 ≥ 15%**（用 WebNovelBench 8 维度平均分对比）
- slop_score 平均下降 ≥ 30%
- 每章生成的 LLM 调用数 ≤ 25（控制成本）
- 前端能展示新增的 adversarial cuts / revision brief

### 风险

- AdversarialEditor 输出可能不稳定 → 用 DeepSeek-V4-Pro 思考模式生成
- 中文翻译资产可能丢失部分英文场景的精髓 → 翻译后让母语作者 review

---

## Phase 2：记忆内核重构 · 2 周

### 任务

#### 2.1 引入 Graphiti + Kuzu · 0.5 周

```bash
pip install "graphiti-core[kuzu]"
```

- 新增 `backend/memory/graphiti_kg.py`（替换手写 KG）
- 数据迁移脚本：把 SQLite `knowledge_triples` 表迁到 Graphiti episodes
- 与 LangGraph 的集成层

#### 2.2 重构 `KnowledgeGraph` API · 0.5 周

- 旧 API：`add_triple / query_relationships / format_for_prompt`
- 新 API（基于 Graphiti）：`add_episode / search_nodes / search_facts / get_evidence`
- 自动 provenance + 自动 fact invalidation（替代手写 valid_from/valid_to）

#### 2.3 WorldBook 升级（SillyTavern 30+ 字段）· 1 周

| 新增字段 | 作用 |
|---------|------|
| `key + keysecondary + selectiveLogic` | 4 元逻辑触发 |
| `constant / keyed / vectorized` 三态 | 主角永远在 / 配角按需 / 远古传说语义召回 |
| `position + depth + order` | 精确插入控制 |
| `group + groupWeight` | 同组互斥防堆叠 |
| `sticky / cooldown / delay` | 时序控制 |
| `excludeRecursion` 等 | 防 lore 雪崩 |

#### 2.4 PromptManager 模块 · 0.5 周

- 把现有硬编码 prompt 拆成可配置 PromptSlot
- 引入 marker 系统（`{{outlet::name}}` 宏）
- admin UI 加 **Prompt Inspector** 页面（每次生成后展示完整拼装树）

#### 2.5 DOME conflict detection · 0.5 周

- 每章生成后从内容抽 (s, a, o, c) 四元组
- 跟现有事实做冲突检查
- 冲突写入 `chapter_quality_scores` 维度

### 出口标准

- 30+ 章后角色事实问答准确率 ≥ 90%（自建 100 题测试集）
- conflict rate 较 Phase 1 下降 ≥ 50%（DOME 论文证据：可达 8 倍）
- **Phase 0 基线评分继续提升 ≥ 10%**

---

## Phase 3：Per-Role Cognition + 戏剧场景 · 2 周

### 任务

#### 3.1 RoleCognitionAgent（CreAgentive PlotWeave）· 1 周

- 每个角色一个轻量 agent
- 只能访问 `character_memories` 中自己的部分（已有过滤逻辑）
- 在写场景前，每个 agent 输出"我此刻会怎么做"的预案
- 解决"角色都说同一种话"的根本问题

#### 3.2 强化 `SceneCard` 字段 · 0.5 周

新增字段（蓝图 §4.6 已设计完整）：
```
desire / obstacle / opposition / information_gap
turning_point / cost / emotional_shift
required_payoff / ending_hook / forbidden
```

#### 3.3 改造 `scene_writer` · 0.5 周

- 输入新增"在场角色的 RoleCognition 预案"
- Writer 不再凭空想象角色行动，而是按预案叙事化

#### 3.4 新增 `ChapterFocusPlan`（蓝图 §4.5 NarrativeDirector）· 0.5 周

- 输入：StoryContract + ForeshadowLedger + EventPool
- 输出：本章问题 / 读者情绪目标 / 信息隐藏 / 钩子
- **重命名 `Camera Agent` 为 `NarrativeDirector`**（蓝图 §4.4 强烈建议）

### 出口标准

- D5 对话区分度评分提升 ≥ 30%（角色不再千篇一律）
- D4 角色塑造评分提升 ≥ 20%
- **Phase 0 基线评分继续提升 ≥ 10%**

---

## Phase 4：世界沙盘 + 故事契约 · 1.5 周

### 任务

#### 4.1 StoryContract 模块 · 0.5 周

- 蓝图 §4.2 schema 已设计完整
- 与现有 `story_bible.json` 平行存储
- 锁定读者承诺、爽点密度、不能漂移的方向
- 每个 critic agent 都引用它

#### 4.2 轻量 World Simulation Kernel · 0.5 周

```
Actor / Goal / Resource / Constraint 数据结构
WorldClock：全局倒计时
OffscreenAction：视野外行动池
EventCandidatePool：候选事件池
```

章节生成前 World 先 tick 一次，产出 EventCandidates，由 NarrativeDirector 二次选择。

#### 4.3 ForeshadowLedger 伏笔账本 · 0.5 周

- schema 见蓝图 §4.3
- 每条伏笔有 planted_at / planned_payoff_window / status
- 每章生成时强制注入到 prompt：本章哪些伏笔可推进

### 出口标准

- 长篇结构稳定性 +20%（D3 情节连贯度）
- 至少 1 条伏笔被成功埋下并在 5-10 章内回收
- **Phase 0 基线评分继续提升 ≥ 5%**

---

## Phase 5：外部素材层（可选） · 1.5 周

> 标记为可选 — 如果 Phase 0-4 已经把质量做上去，可以延后

### 任务

| # | 任务 | 工具栈 |
|---|------|--------|
| 5.1 | 部署 DailyHotApi（Docker） | DailyHotApi |
| 5.2 | 接入博查 BoChaAI 搜索 | bochaai SDK |
| 5.3 | Jina Reader 提取 | jina API |
| 5.4 | InspirationCard 数据结构 + 生成器 | 蓝图 §4.1 schema |
| 5.5 | 前端"创意雷达"页面 | 每日 20 张候选卡 |
| 5.6 | 版权安全转译机制 | LLM 只接收"话题+情绪+结构"输入 |

### 出口标准

- 每日自动产出 ≥ 20 张 InspirationCard
- 人工 approve 率 ≥ 50%
- 月成本 ≤ 60 元

---

## Phase 6：完整编辑部 · 2 周

### 任务

#### 6.1 Reader Panel（autonovel 4 personas）· 0.5 周

- 4 个 persona：编辑 / 类型读者 / 作家 / 普通读者
- 关键设计：**找分歧而非共识**
- 用 `find_disagreements()` 提取部分 reader 提到的章节问题

#### 6.2 Pairwise Elo 章节对比 · 0.5 周

- 每章生成 2-3 个候选
- critic 做 pairwise 比较
- 累积 Elo 分数，选最佳

#### 6.3 Opus-style 全书 Review · 0.5 周

- 双重人格（critic + professor）
- 跨章节连贯性、长线伏笔回收检查

#### 6.4 修订循环升级 · 0.5 周

- Diff-aware rewriting：只改有问题的段落
- 保留有效段落

### 出口标准

- 100% 章节有 ≥ 2 个候选版本
- 全书 review 能检出 ≥ 80% 的连贯性问题
- **总评分较 Phase 0 基线提升 ≥ 60%**（最终目标）

---

## 总览与时间表

| Phase | 名称 | 工作量 | 累计时间 | 关键技术来源 | 出口标准（vs Phase 0 基线） |
|-------|------|--------|---------|--------------|--------------------------|
| **0** | 评测基线 | 1.5 周 | 1.5 周 | WebNovelBench + autonovel slop | 基线建立 |
| **1** | 核心写作闭环 | 2-3 周 | 4 周 | autonovel 5 资产 | +15% |
| **2** | 记忆内核 | 2 周 | 6 周 | Graphiti+Kuzu + SillyTavern | +25% |
| **3** | Per-Role + 戏剧 | 2 周 | 8 周 | CreAgentive PlotWeave | +35% |
| **4** | 世界沙盘 + 契约 | 1.5 周 | 9.5 周 | 蓝图 §4.2/§4.4 + ForeshadowLedger | +40% |
| **5** | 外部素材（可选） | 1.5 周 | 11 周 | DailyHotApi + 博查 + Jina | 不影响质量评分 |
| **6** | 完整编辑部 | 2 周 | 13 周 | autonovel Reader Panel + Pairwise Elo | +60% |
| | **合计** | **12-14 周** | | | |

## 数据迁移与兼容

**承诺**：所有 Phase 都**保留现有 3 本测试小说数据**，作为基线对照。

| Phase | 数据迁移动作 |
|-------|-----------|
| Phase 0 | 新增 `chapter_quality_scores` 表，回填现有 24 章评分 |
| Phase 1 | 无需迁移（仅 prompt 资产 + 新 agent） |
| Phase 2 | `knowledge_triples` → Graphiti episodes（一次性脚本） |
| Phase 3 | 角色卡新增 RoleCognition 字段（向后兼容） |
| Phase 4 | 新增 `story_contracts` / `foreshadow_ledgers` / `world_actors` 表 |
| Phase 5 | 新增 `inspiration_cards` 表 |
| Phase 6 | 新增 `chapter_candidates` / `pairwise_elo` 表 |

每个 Phase 开始前**自动备份 `data/story.db`**。

## 与现有架构的对应关系

| 现有模块 | Phase | 命运 |
|---------|-------|------|
| `LangGraph` 编排 | - | **保留**，仅扩展节点 |
| `LiteLLM` + DeepSeek 适配器 | - | **保留** |
| `chapter_versions` + `is_live` | - | **保留** |
| 前端组件库 + 8 页深度可视化 | - | **保留**，每 Phase 加新 Tab |
| `KnowledgeGraph`（手写） | Phase 2 | 替换为 Graphiti |
| `WorldBook`（5 字段） | Phase 2 | 升级为 SillyTavern 30+ 字段 |
| `LayeredMemory` | Phase 2 | 整合进 Graphiti + WorldBook |
| `Camera Agent` | Phase 3 | 重命名 `NarrativeDirector`，职责改为"叙事选择" |
| `scene_writer` | Phase 3 | 接收 RoleCognition 预案 |
| `consistency` agent | Phase 1 | 加 slop_check + adversarial_edit |
| `outline_planner` | Phase 4 | 加 StoryContract 引用 |
