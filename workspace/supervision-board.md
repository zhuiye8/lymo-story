# Supervision Board

## Latest Review: 2026-04-27 Report #6

Status: accepted-with-corrections.

- AC3 v5 calibration is data-ready: recall `0.9700`, precision overall `0.9700`, public-domain excerpt precision `0.9700`.
- Trend delta contract is now unified as symmetric exclude-middle; regression tests pass 17/17.
- AC5 backend is still not final: `heatmap` can miss a whole absent chapter, and `distribution` does not require score-table completeness.
- AC5 frontend UI should wait until those two readiness gaps are fixed.
- AC2-final remains the hard gate and must not be auto-filled.

Current PM instruction is in `workspace/inbox/from-pm/2026-04-27-phase-0-report-6-review.md`.

## Latest Review: 2026-04-27 Report #7

Status: accepted-with-corrections.

- Report #6 findings are closed: heatmap, distribution, and phase-gate AC3 v5 wording are fixed.
- AC5 backend is approved for frontend UI implementation.
- AC3 remains data-ready, but final label waits for Wikisource builder hard-fail and stable-ID fixes.
- AC2-final remains supervisor-only and must not be auto-filled.

Current PM instruction is in `workspace/inbox/from-pm/2026-04-27-phase-0-report-7-review.md`.

## Latest Review: 2026-04-27 Report #8

Status: accepted-with-corrections.

- Wikisource builder corrections are accepted: partial fetch fails hard, partial merge is forbidden, and IDs are stable by `source_url`.
- AC3 is approved as Phase 0 pass under the wording `source-verifiable public-domain excerpt precision`.
- AC5 UI is implemented but not accepted: targeted ESLint fails in `frontend/app/admin/quality/page.tsx`.
- AC2-final remains supervisor-only and must not be auto-filled.

Current PM instruction is in `workspace/inbox/from-pm/2026-04-27-phase-0-report-8-review.md`.

## Latest Review: 2026-04-28 Report #9

Status: accepted.

- Report #8 AC5 UI lint finding is closed; targeted ESLint is clean.
- AC5 backend + UI are accepted at Phase 0 smoke level.
- AC3 remains final pass under `source-verifiable public-domain excerpt precision`.
- AC2-final is now the only remaining hard Phase 0 gate and must not be auto-filled.

Current PM instruction is in `workspace/inbox/from-pm/2026-04-28-phase-0-report-9-review.md`.

更新时间：2026-04-28  
监督角色：架构监督 / 技术 PM / 质量审稿人  
当前状态：Phase 0 Report #9 已审；AC1/AC1b/AC3/AC4/AC5/AC6 已过 Phase 0 标准；AC2-final 是唯一剩余硬门槛

## 当前活跃事项

| 项目 | 路径 | 状态 | 下一步 |
|---|---|---|---|
| Phase 0 评测基线 | `plans/2026-04-26-rearchitecture/phase-0/` | in-progress / report-9-accepted | AC2-final 仍等监督独立评分；其他 Phase 0 gate 已按当前标准通过 |
| 沟通协议 | `skill-draft/pm-engineer-collaboration/` | active-draft | 作为通用 PM/工程师协作 skill 草案使用 |
| 架构蓝图 | `../docs/rearchitecture_blueprint.md` | standing-reference | 作为审查基准 |
| 项目背景 | `project-brief.md` | active-reference | 存放 Story Engine 特定审查原则 |
| 长期决议 | `decisions/standing/` | active | 新提案必须遵守或显式挑战 |
| 旧 skill 草案 | `skill-draft/archive/novel-rearchitecture-supervisor/` | archived | 不作为当前沟通规范使用 |
| 范围纠偏 | `inbox/from-pm/2026-04-26-communication-protocol-correction.md` | must-read | 工程师提交 Phase 0 前必须阅读 |

## 当前监督判断

已有方案的优点：

- 建立了独立工作区，方向正确。
- 把 Phase 0 评测基线放在第一步，这是必要的。
- 已经意识到 Writer 不能继续吞全量上下文。
- 已经开始把外部项目拆成记忆、评审、检索、热点等模块评估。

需要收紧的地方：

- 方案文本太长，PM review 成本高。后续阶段汇报必须用模板压缩。
- 部分外部项目结论写得过于确定，未复核前不能直接进入决策。
- “渐进改造 vs 完全重构”与用户最新意图存在张力。用户已明确不拘泥当前框架，因此工程师不能默认保留旧架构为最高优先级。
- 质量指标不能只写“提升 X%”，必须说明评测样本、评委模型、人工校准方式和失败阈值。
- Graphiti、WebNovelBench、CreAgentive、DOME、Qwen3-235B 等当前性结论需要单独证据文件或复核记录。

## 已生效决策

以下 3 件事已经拍板：

1. 接受“AI 小说编辑部”作为目标架构。
2. Phase 0 先做评测基线，允许不绑定旧代码。
3. 工程师下一步先提交一个 1-2 周的 Phase 0 详细执行计划。

其余技术选型暂不拍板，等 PoC 或复核后再决定。

## 监督红线

- 不允许把重构重新做成“更多 Agent 的流水线”。
- 不允许 Writer 直接读取全量历史和全量设定。
- 不允许世界模拟直接决定正文，只能输出候选事件和约束。
- 不允许没有评测基线就声称质量提升。
- 不允许未经复核的外部仓库结论进入 `decisions/`。
- 不允许阶段计划没有退出条件和回滚方案。

## 推荐下一条给工程师的指令

请工程师继续 Phase 0，但不要宣称 Phase 0 完成。下一次汇报聚焦：

- AC5 endpoints 的 `data_ready` 已按完整 batch coverage 判断，不再只看是否有行。
- API/report/contract 的 first-half/second-half delta 算法已统一，并覆盖奇数章节测试。
- AC3 public-domain excerpts 已替换/补充为 source-verifiable 样本，并重跑 calibration。
- `bc910038/ch1` 的 AC2-final artifact 已准备。
- AC5 frontend UI 仍等 AC2-final，不提前启动。
