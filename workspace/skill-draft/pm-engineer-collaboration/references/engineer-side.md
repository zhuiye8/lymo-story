# Engineer-Side Handoff Rules

Use this reference when writing instructions for engineers or checking whether an engineer's artifact is reviewable.

## Choose The Right Artifact

| Situation | Artifact |
|---|---|
| Need approval before building | `proposal.md` |
| Need to start a phase | `phase-gate.md` |
| Need to report progress or results | `phase-report.md` |
| Need PM/supervisor to choose | `question.md` |
| Need to record a binding answer | `decision-record.md` |
| Need review on a concrete diff or design | `review-request.md` |

## Defaults

Every question must include:

```text
Default action:
Trigger time:
Rollback cost:
Post-action notice:
```

Good defaults are narrow, reversible, and visible. Do not use a default to authorize high-risk irreversible work.

## Evidence

Tag claims with:

- `[verified:YYYY-MM-DD:URL-or-path]`
- `[needs-review]`
- `[assumption]`
- `[stale:YYYY-MM-DD]`

If the claim affects architecture, budget, legal exposure, data safety, production reliability, or user experience, untagged evidence is not enough.

## Report Style

- Start with the decision or status.
- Keep the main body under 80 lines.
- Link details instead of pasting long logs.
- State the next one action.
- Update the board when status changes.
