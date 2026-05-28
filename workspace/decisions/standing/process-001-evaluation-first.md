# Standing Decision process-001: evaluation first

| Field | Value |
|---|---|
| ID | process-001 |
| Approved | 2026-04-26 by supervisor |
| Source proposal | `docs/rearchitecture_blueprint.md`; `workspace/decisions/2026-04-26-skill-additions.md` |
| Status | active |
| Revisit trigger | PM accepts a phase that is explicitly exploratory and not intended to claim quality improvement. |

## Decision

No module may claim writing-quality improvement without a baseline, sample size, evaluation method, cost bound, and rollback trigger.

## Rationale

Novel generation quality is easy to describe subjectively and hard to improve reliably. Without evaluation first, the team can spend weeks adding memory, agents, prompts, or external services while losing focus on whether chapters are actually more novel-like, coherent, and interesting.

## Constraints On Future Proposals

- Every phase gate must define acceptance criteria before implementation starts.
- External project claims must be tagged as `[verified:YYYY-MM-DD:URL]`, `[needs-review]`, `[assumption]`, or `[stale:YYYY-MM-DD]`.
- PoCs must specify sample size, evaluation rubric, cost or latency budget, and rollback plan.
- "Feels better" is useful user feedback, but cannot be the only acceptance criterion for a phase.
