# Collaboration Protocol

Use this protocol for async PM/engineer work where one side supervises direction and the other executes implementation.

## Artifacts

| Artifact | Purpose | Location |
|---|---|---|
| Board | Current state, active blocker, next action | `workspace/supervision-board.md` |
| Proposal | Non-trivial design or implementation plan | `workspace/plans/` |
| Phase gate | Approval contract before a phase starts | `workspace/plans/` or `workspace/phase-gates/` |
| Decision | Binding PM/supervisor outcome | `workspace/decisions/` |
| Standing decision | Long-lived rule future proposals must respect | `workspace/decisions/standing/` |
| Inbox message | Short question, report, or escalation | `workspace/inbox/` |

## Operating Loop

1. Engineer submits a proposal, phase gate, report, or question.
2. Supervisor reviews the artifact, not the whole history.
3. Supervisor returns one of: `approve`, `approve-with-conditions`, `revision-needed`, `reject`, `blocked-pending-evidence`.
4. Binding outcomes are written to `decisions/`.
5. The board is updated with current status and next action.

## Efficiency Rules

- One artifact should ask for one decision.
- A question must include `Default if no answer`.
- A report summary should fit in 5 lines.
- A proposal should keep the main body short and link to deep evidence.
- A decision must say what was rejected or deferred, not only what was accepted.
- A phase must not start without acceptance criteria and rollback conditions.

## State Labels

Use these labels unless the project already has better ones:

```text
draft -> pending-review -> approved / revision-needed / rejected -> in-progress -> done
open -> answered -> accepted / follow-up-needed -> closed
```

## Failure Modes To Catch

- Long chat replaces durable decisions.
- Proposal asks for many unrelated approvals.
- Engineer blocks while waiting for a minor answer that could have a safe default.
- Supervisor reviews the same settled principle repeatedly.
- External claims are treated as fact without date and source.
- Work starts before success, failure, and rollback are defined.
