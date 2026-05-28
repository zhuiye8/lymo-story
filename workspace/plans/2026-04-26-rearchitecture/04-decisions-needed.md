# 04 · 待 PM 决策项

> 工程师可以决定技术细节，但下面 6 个属于**架构与产品方向**，必须 PM 拍板才能开工。
> 每项给出选项 + 工程师推荐 + 论据，PM 在 `workspace/decisions/` 下回复即可。

---

## 决策 1：渐进改造 vs 全新仓库

**问题**：是在现有 14000 行代码上演化，还是另开新坑？

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 渐进改造**（推荐） | 在 `backend/frontend/reader` 上逐 Phase 演化 | 复用 LangGraph / 版本化 / 适配器 / 前端组件；每 Phase 可独立验证 | 偶尔受老代码约束 |
| B. 全新仓库 | 另开 `story-v2/`，老仓库归档 | 设计纯净 | 损失 2 个月工程积累；并行维护成本高 |
| C. Big bang 一次性重写 | 推倒重来 | 设计最纯净 | 失败风险极高；至少 4 个月零产出 |

**工程师推荐**：**A · 渐进改造**

**论据**：
- 现有代码里有大量正确部分（LangGraph 编排、版本化机制、TaskRegistry、DeepSeek 适配器、shadcn 组件库、3D 宇宙等）
- 真正缺的是评测基线、编辑闭环、Per-Role、强 KG —— 都可以**叠加**到现有 LangGraph 上
- 渐进改造允许每个 Phase 独立验证，失败可回滚
- 全新仓库会让前端可视化、3 本测试小说、用户已熟悉的 UI 全部作废

**风险 if A**：偶尔会有「这个旧 agent 实在不能改造，必须新建」的情况——可以接受，按需新建。

---

## 决策 2：是否引入 Graphiti + Kuzu 替换手写 KG

**问题**：用 Graphiti（嵌入式图库 Kuzu）替换我们手写的 `KnowledgeGraph`？

| 选项 | 描述 |
|------|------|
| **A. 引入 Graphiti+Kuzu**（推荐） | Phase 2 时迁移，自动 provenance + fact invalidation + hybrid retrieval |
| B. 强化手写 KG | 给现有 `KnowledgeGraph` 加 conflict detection + provenance |
| C. 暂不动，等 Phase 2 末再决定 | Phase 2 先做 WorldBook 升级，KG 留到 Phase 2.5 |

**工程师推荐**：**A · 引入 Graphiti+Kuzu**

**论据**：
- Kuzu 是嵌入式（类似 SQLite），**不需要 Neo4j 服务**，运维负担为零
- 已被 Zep 团队用于生产，2026-04 仍在更新
- 提供我们做不到的能力：自动 provenance（每个事实链回章节原文）、自动 fact invalidation
- 论文级证据：DOME 加 conflict detection 后冲突率降 8 倍；我们的手写 KG 没有这些
- 安装一行命令：`pip install graphiti-core[kuzu]`

**风险 if A**：每章多 1-3 次 LLM 调用做实体抽取（增加 ~¥0.1-0.3/章成本）。

**风险 if B**：自研 conflict detection / hybrid retrieval 至少多花 2-3 周，且不如成熟项目。

---

## 决策 3：WebNovelBench 评委 LLM 选哪个

**问题**：Phase 0 评测用哪个模型当"评委"？

| 选项 | 单价 | 质量 |
|------|------|------|
| **A. DeepSeek-V4-Pro 关思考**（推荐） | ¥0.05/章 | 与论文 V3 同源，稳定 |
| B. DeepSeek-V4-Pro 开思考 | ¥0.08/章 | 更细致，但慢 |
| C. Qwen3-235B（论文 SOTA 模型） | ~¥0.3/章 | 最强，但贵 |
| D. GPT-4o | ~$0.2/章 | 国外模型，需要海外 IP |

**工程师推荐**：**A · DeepSeek-V4-Pro 关思考**

**论据**：
- 与 WebNovelBench 论文用的 V3 同源，可对照论文结果
- 关思考使评分稳定（思考会引入随机性）
- 成本最低，可频繁评测（24 章 ≈ ¥1.2，整本 100 章 ≈ ¥5）
- 写作主力可单独配 Qwen3-235B 或 V4-Pro 思考（PM 决策 5）

---

## 决策 4：现有 3 本测试小说的命运

**问题**：3 本测试小说（24 章）怎么处理？

| 选项 | 描述 |
|------|------|
| **A. 保留作为基线对照**（推荐） | 不动，跑 Phase 0 评测，作为「重构前」基线；新章用新架构生成 |
| B. 删除，重新开始 | 全部清空，所有数据从头生成 |
| C. 用新架构重生成对照 | 保留原章节快照，每个 Phase 后用新架构重生同样的章节，做 A/B 对比 |

**工程师推荐**：**A · 保留作为基线对照**（C 太贵，B 损失对照价值）

**论据**：
- A：零成本，跑一遍评测就有基线，每个 Phase 完成后只需要**新生成的章节**对比即可
- B：损失对照基线，无法证明"重构前 vs 重构后"
- C：每章 LLM 重生成成本 ~¥0.5-1，3 本 24 章 × 6 Phase = 144 次重生成 ≈ ¥100-150，**但能给出最强证据**

**备选建议**：A 为主 + C 选 1 章做完整 6 Phase 对照（成本 ¥6）。

---

## 决策 5：写作主力 LLM 是否切换到 Qwen3-235B

**问题**：当前写作主力是 DeepSeek-V4 系列。WebNovelBench SOTA 是 Qwen3-235B（5.21 分）。要不要切？

| 选项 | 描述 | 单章成本 |
|------|------|---------|
| **A. 保持 DeepSeek，按现有分层**（推荐） | scene_writer = V4-Flash 思考 / 创作 init = V4-Pro | ~¥0.09/章 |
| B. 切到 Qwen3-235B | 写作全部走 Qwen | ~¥0.5-1/章 |
| C. 混合策略 | scene_writer 用 Qwen，其他保持 DeepSeek | ~¥0.3-0.5/章 |
| D. Phase 0 后做 A/B 对比再决定 | 用基线评分判断 | 需多花 ¥10-20 |

**工程师推荐**：**A 当前不动，Phase 0 完成后做 D（轻量 A/B）**

**论据**：
- Phase 0 完成前，无法客观判断"切了真的好"
- DeepSeek V4 还是新模型，没人在 WebNovelBench 测过（论文用的是 V3）
- 切模型会增加 5-10x 成本，必须有数据支撑
- Phase 0 完成后跑 D，1 章 5 个模型对比，¥10 内能定 SOTA

---

## 决策 6：Phase 顺序与可选项

**问题**：Phase 0-6 的顺序和必做项，是否接受？

**工程师推荐顺序**：

```
Phase 0（必做）  评测基线 [1.5 周]
   ↓
Phase 1（必做）  核心写作闭环 [2-3 周]   ← 第一个里程碑：质量 +15%
   ↓
Phase 2（必做）  记忆内核 [2 周]
   ↓
Phase 3（必做）  Per-Role + 戏剧 [2 周]
   ↓
Phase 4（必做）  世界沙盘 + 契约 [1.5 周]
   ↓
Phase 5（可选）  外部素材 [1.5 周]   ← 锦上添花，可延后
   ↓
Phase 6（必做）  完整编辑部 [2 周]   ← 最终目标：质量 +60%
```

**关键论点**：
- Phase 0 最先 — 没有基线 = 没有进步证据
- Phase 1 = 第一个可见效里程碑（3 周内看到肉眼提升）
- Phase 5 标记为可选 — 如果 Phase 0-4 已经把质量做上去，可以延后到 Phase 6 之后
- 顺序之间有依赖：Phase 3 RoleCognition 需要 Phase 2 的强 KG / Phase 4 ForeshadowLedger 需要 Phase 2 的 episode provenance

**待 PM 选项**：
- ✅ 接受工程师推荐顺序
- ⚠️ 调整某个 Phase 的位置（请说明理由）
- ❌ 推迟某个 Phase（请说明）

---

## 决策回复模板

PM 请在 `workspace/decisions/2026-04-26-rearchitecture-approval.md` 创建文件，按下面模板回复：

```markdown
# 重构提案审批决议

| 字段 | 内容 |
|------|------|
| 审批人 | <PM 姓名> |
| 决议日期 | 2026-04-XX |
| 提案路径 | `workspace/plans/2026-04-26-rearchitecture/` |
| 总体决议 | approve / approve-with-changes / reject / revision-needed |

## 6 项决策回复

| # | 决策项 | 选择 | 备注 |
|---|--------|------|------|
| 1 | 渐进 vs 重写 | A / B / C | |
| 2 | Graphiti+Kuzu | A / B / C | |
| 3 | 评委 LLM | A / B / C / D | |
| 4 | 测试小说命运 | A / B / C / 自定义 | |
| 5 | 写作主力 LLM | A / B / C / D | |
| 6 | Phase 顺序 | 接受 / 调整（说明） | |

## 补充指示（可选）

<PM 的额外要求或修改建议>

## 后续

- [ ] 工程师：按决议开始 Phase 0
- [ ] 每个 Phase 末提交进度报告到 `workspace/inbox/from-engineer/`
- [ ] 任何重大风险 24 小时内书面汇报
```
