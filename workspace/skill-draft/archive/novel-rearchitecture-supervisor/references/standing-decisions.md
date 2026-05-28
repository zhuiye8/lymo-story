# Standing Decisions

Use standing decisions to prevent re-litigating settled architecture and process rules.

## Directory

```text
decisions/
└── standing/
    ├── arch-001-editorial-office.md
    ├── process-001-evaluation-first.md
    └── ...
```

## Format

```markdown
# Standing Decision <ID>: <topic>

| Field | Value |
|---|---|
| ID | arch-001 |
| Approved | <YYYY-MM-DD> by <name> |
| Source proposal | <path> |
| Status | active / superseded by <id> |
| Revisit trigger | <condition> |

## Decision

<One-sentence decision.>

## Rationale

<3-5 lines.>

## Constraints On Future Proposals

<What future plans must respect or explicitly challenge.>
```

## Engineer Rule

Before submitting a proposal, scan standing decisions. If the proposal challenges one, add:

```markdown
| Challenges Standing | <decision-id>: <reason> |
```

## Supervisor Rule

If a proposal silently conflicts with a standing decision, return `revision-needed`.

