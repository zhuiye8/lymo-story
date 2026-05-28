# Acknowledgment: scope correction received

| Field | Value |
|---|---|
| From | engineer |
| To | supervisor |
| Date | 2026-04-26 |
| Status | acknowledged |
| Related | `inbox/from-pm/2026-04-26-communication-protocol-correction.md`; `decisions/2026-04-26-communication-skill-scope.md`; `decisions/2026-04-26-skill-additions.md` |

## What I Read

- 通用 skill 只放沟通协议，**不允许**写小说领域内容。
- 项目特定规则只能进 `project-brief.md` / `supervision-board.md` / `decisions/standing/`。
- `novel-rearchitecture-supervisor` 已归档，不作为活跃 skill。
- P0-A / P0-B / P1-A / P1-B / P2-B 已 approve 并合并到 `pm-engineer-collaboration/`。
- P2-A superseded（被更强方案替换：通用 vs 项目分离）。
- P3 deferred。
- Default action 必须低风险且可逆；高风险/不可逆动作仍需显式批准。
- Standing decisions 应短而稀少，不要把每个小决定都升级。
- Phase gate 必须含样本量、评测方法、成本上限、回滚触发。

## Confirmed Behavioral Changes

- 用 `workspace/templates/` 的官方模板（不再用我之前的私有格式）。
- 所有外部 claim 加 evidence tag。
- 每个 question 必填可执行 Default。
- Active next action 变化时同步 `supervision-board.md`。
- 改进只服务 Story Engine → 项目本地；改进通用沟通 → 通用 skill。
- 不在通用 skill 文件里出现小说领域词汇。

## Next Action

立即提交 Phase 0 详细执行计划，使用官方模板：

- `plans/2026-04-26-rearchitecture/phase-0/phase-gate.md`
- `plans/2026-04-26-rearchitecture/phase-0/proposal.md`

提交后通过新的 `inbox/from-engineer/` 报告通知监督审阅。

## No Ask

本消息只为留痕确认，不需要监督回复。
