# Standing Decisions

Use standing decisions for principles that future proposals must respect or explicitly challenge.

## When To Create One

Create a standing decision only when:

- The same question is likely to recur.
- Re-opening it would waste review time.
- The rule meaningfully constrains future design.
- There is a clear revisit trigger.

Do not create standing decisions for small implementation details.

## Format

```markdown
# Standing Decision <ID>: <topic>

| Field | Value |
|---|---|
| ID | <area>-001 |
| Approved | <YYYY-MM-DD> by <name> |
| Source proposal | <path> |
| Status | active / superseded by <id> |
| Revisit trigger | <condition> |

## Decision

<One-sentence decision.>

## Rationale

<3-5 lines.>

## Constraints On Future Proposals

- <constraint>
- <constraint>
```

## Review Rule

If a proposal conflicts with a standing decision and does not declare the conflict, return `revision-needed`.

If the conflict is intentional, require:

```markdown
| Challenges Standing | <decision-id>: <reason> |
```
