# Phase Gate: <phase name>

Every phase needs this gate approved before implementation starts. Missing required sections mean `revision-needed`.

| Field | Value |
|---|---|
| Phase | <phase> |
| Author | <name> |
| Date | <YYYY-MM-DD> |
| Estimated duration | <weeks/days> |
| Cost ceiling | <CNY or USD> |
| Status | draft / pending-review / approved / blocked |

## One-Sentence Goal

<One sentence.>

## Non-Goals

- <Explicitly out of scope>
- <Explicitly out of scope>

## Artifact Schema

<Core data model, API shape, file shape, or UI artifact. Use SQL/Pydantic/TypeScript when useful.>

## Acceptance Criteria

Each criterion must include sample source, sample size, metric, pass threshold, and fail threshold.

| # | Criterion | Method | Pass | Fail / rollback trigger |
|---|---|---|---|---|
| AC1 | <criterion> | <method> | <threshold> | <threshold> |
| AC2 | <criterion> | <method> | <threshold> | <threshold> |

## Evaluation Method

| Item | Value |
|---|---|
| Judge model | <model or none> |
| Evaluation sample | <source + count> |
| Human calibration | <yes/no + method> |
| Automated metrics | <list> |
| Evaluation frequency | <when> |
| Estimated evaluation cost | <cost> |

## Cost Bound

| Category | Estimate | Ceiling | Warning threshold |
|---|---|---|---|
| LLM calls | <cost> | <ceiling> | <threshold> |
| External APIs | <cost> | <ceiling> | <threshold> |
| Engineering time | <time> | <ceiling> | <threshold> |

## Rollback / Exit Conditions

| Trigger | Action |
|---|---|
| Acceptance fail threshold reached | <action> |
| Cost ceiling exceeded | <action> |
| User experience worsens | <action> |
| Supervisor stops phase | <action> |

## Dependencies

| Dependency | Type | Evidence |
|---|---|---|
| <dependency> | phase/library/API/model | <evidence tag or link> |

## Standing Decisions Touched

- <decision id or none>

## Ask

<Approve / reject / choose option / provide missing input.>

## Default If No Review

```text
Default action:
Trigger time:
Rollback cost:
Post-action notice:
```

