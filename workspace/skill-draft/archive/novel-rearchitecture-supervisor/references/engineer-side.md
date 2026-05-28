# Engineer-Side Operating Manual

Use this when writing artifacts for a supervisor.

## Choose The Right Artifact

| Need | Use | Location |
|---|---|---|
| Start a phase | `phase-gate.md` | `plans/<phase>/phase-gate.md` |
| Propose architecture/module/dependency | `proposal.md` | `plans/<date>-<topic>/` |
| Ask one concrete question | `question.md` | `inbox/from-engineer/` |
| Report phase progress | `phase-report.md` | `inbox/from-engineer/` |
| Request review of one artifact | `review-request.md` | `inbox/from-engineer/` |
| Record binding decision | `decision-record.md` | `decisions/` |

## Rules

- One file, one topic.
- Keep questions under 500 words, reports under 1000 words, proposals under 2000 words unless the supervisor requests detail.
- Tag external evidence with `[verified]`, `[needs-review]`, `[assumption]`, `[stale]`, or `[tested]`.
- Every question needs a default action and trigger time.
- Scan standing decisions before proposing changes.
- Do not edit approved historical decisions; supersede them with a new decision.

## Phase End Checklist

- Submit phase report.
- Include test/evaluation evidence.
- Include cost evidence.
- List deviations from plan.
- Identify decisions that should become standing decisions.

