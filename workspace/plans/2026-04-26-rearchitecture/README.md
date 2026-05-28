# 重构提案：从"多 Agent 流水线"到"AI 编辑部"

| 字段 | 内容 |
|------|------|
| **作者** | Claude（工程师） |
| **日期** | 2026-04-26 |
| **状态** | `pending-review` — 等待 PM 审阅与决策 |
| **预估周期** | 12-14 周（6 阶段） |
| **决策需求** | 6 个关键决策项（见 `04-decisions-needed.md`） |
| **基础蓝图** | `docs/rearchitecture_blueprint.md` |

## 文档清单

请按顺序阅读：

| # | 文件 | 内容 | 阅读时间 |
|---|------|------|---------|
| 1 | [01-context-and-problem.md](01-context-and-problem.md) | 项目现状 / 当前痛点 / 重构必要性 | 5 分钟 |
| 2 | [02-research-summary.md](02-research-summary.md) | 4 路真实调研结果（autonovel / SillyTavern / Graphiti / WebNovelBench 等） | 10 分钟 |
| 3 | [03-implementation-plan.md](03-implementation-plan.md) | 6 阶段实施路线（含技术选型、数据 schema、迁移策略） | 15 分钟 |
| 4 | [04-decisions-needed.md](04-decisions-needed.md) | **6 个待决策项**（必须 PM 拍板） | 5 分钟 |
| 5 | [05-risks-and-tradeoffs.md](05-risks-and-tradeoffs.md) | 已知风险 / 权衡 / 失败逃生通道 | 5 分钟 |

## TL;DR（30 秒概述）

**问题**：当前 6 个 Agent 顺序流水线生成的章节质量差（流水账、AI 味、长上下文偏离），蓝图诊断为"系统范式不对"，建议从"章节生成器"升级为"AI 编辑部"。

**调研结论**：蓝图方向 100% 正确，**且找到了 3 个能直接复用的成熟项目**——
- **autonovel**：5 个高价值 prompt 资产 + 反 AI 味检测函数
- **Graphiti+Kuzu**：替换我们手写的 KG（嵌入式无运维）
- **WebNovelBench**：4000 篇起点小说 + 8 维度评测公约

**计划**：分 6 阶段（基线 → 写作闭环 → 记忆 → 戏剧 → 沙盘 → 编辑部），共 12-14 周。

**最大转折**：**Phase 0 评测基线必须先做**——不然所有重构都是凭感觉，无法证伪是否变好。

**首个里程碑**：Phase 0 + Phase 1.1 完成（约 3 周），用基线证明质量提升 ≥ 15%。

## 关键决策项预告

PM 需要拍板的 6 个问题（详见 `04-decisions-needed.md`）：

1. 渐进改造 vs 全新仓库？
2. 是否引入 Graphiti+Kuzu 替换手写 KG？
3. WebNovelBench 评委 LLM 用哪个（DeepSeek-V4-Pro / Qwen3-235B / 其他）？
4. 现有 3 本测试小说命运（保留作基线 / 删除 / 重生成对照）？
5. 写作主力 LLM 是否切换到 Qwen3-235B（当前 SOTA）？
6. Phase 顺序与可选项是否接受？

## PM 审批入口

请审阅完毕后在 `workspace/decisions/` 下创建：
- `2026-04-26-rearchitecture-approval.md` — 整体批复（approve / reject / revision-needed）
- 如需逐项决策，可创建 `2026-04-26-decision-<n>.md`

如有追问或要求补充调研，请在 `workspace/inbox/from-pm/` 下留言，文件名建议：
`2026-04-26-question-<topic>.md`
