# Decision: Skill Collaboration Additions

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-26 |
| Status | approved-with-conditions; superseded-in-scope by `2026-04-26-communication-skill-scope.md` |
| Related request | `workspace/inbox/from-engineer/2026-04-26-question-skill-improvements.md` |

## Decision

Approve and merge P0-A, P0-B, P1-A, P1-B, and P2-B. Defer P3.

Scope correction: these mechanisms now belong to the generic `pm-engineer-collaboration` skill, not a novel-specific supervisor skill.

## Rationale

The approved items directly reduce review latency without changing project architecture: evidence labels, required defaults, standing decisions, phase gates, and engineer-side instructions. They make the collaboration protocol stricter and easier to reuse.

P2-A was superseded by a stronger scope correction: the reusable skill should be generic PM/engineer collaboration only. Project-specific rules stay in this workspace's project brief and standing decisions.

P3, automatic inbox state aging, is useful only if the inbox starts accumulating stale messages. It adds process machinery before we have enough volume.

## Options Considered

| Option | Result | Reason |
|---|---|---|
| P0-A evidence tagging | accepted | High ROI and directly addresses unverified external claims. |
| P0-B required default action | accepted with condition | Defaults must be specific and low-risk; high-risk defaults still need explicit approval. |
| P1-A standing decisions | accepted | Prevents repeated review of settled architecture principles. |
| P1-B phase gate | accepted | Turns phase starts into measurable contracts. |
| P2-A split skill | superseded | Replaced by a generic communication skill plus project-local rules. |
| P2-B engineer-side manual | accepted | Reduces formatting mistakes and review churn. |
| P3 message state automation | deferred | Wait until inbox volume justifies it. |

## Conditions

- External claims must use evidence tags before they can support a binding decision.
- A default action cannot authorize high-risk irreversible work; those still require explicit approval.
- Standing decisions should be short and rare. Do not turn every minor choice into a standing decision.
- Phase gates must include sample size, evaluation method, cost bound, and rollback trigger.

## Revisit Trigger

Revisit whether to add domain-specific extension skills after Phase 0 completes or after this protocol is reused in another project.

## Follow-Up

- [x] Merge approved references and templates into the generic skill draft.
- [x] Update current workspace question template.
- [x] Add phase-gate template.
- [x] Create actual standing decisions for the target architecture and evaluation-first process.
