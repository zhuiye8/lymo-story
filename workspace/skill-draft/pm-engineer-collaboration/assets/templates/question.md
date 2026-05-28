# Question: <topic>

| Field | Value |
|---|---|
| From | <PM/engineer> |
| To | <PM/engineer> |
| Date | <YYYY-MM-DD> |
| Status | open / answered / closed |
| Needed by | <date> |
| Default if no answer | <required: action + trigger time + rollback cost> |

`Default if no answer` is mandatory. If it is blank, the question is invalid and should be rewritten. The default must be specific enough that the requester can continue without blocking.

## Question

<一句话问题。>

## Context

<必要上下文，不超过 10 行。>

## Options

| Option | Tradeoff |
|---|---|
| A | <tradeoff> |
| B | <tradeoff> |

## Recommendation

<提问方建议。>

## Default Behavior

If no answer arrives by `Needed by`, execute this default:

```text
Default action:
Trigger time:
Rollback cost: low / medium / high
Post-action notice:
```

Good default:

```text
Default action: proceed with Option A for Phase 0 judge model only.
Trigger time: 2026-04-30 23:59
Rollback cost: low
Post-action notice: send a short report to inbox/from-engineer.
```
