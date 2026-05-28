# Direction: Phase 0 Greenlight

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-26 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-26-phase-0-greenlight.md` |
| Default if no answer | Start Phase 0 according to v2.1; keep AC2-final as a blocking exit gate. |

## Direction

Phase 0 is approved to start.

Use the v2.1 plan and keep scope limited to the evaluation baseline.

## Required During Implementation

- Every baseline run must create and use one `evaluation_batch_id`.
- Do not claim Phase 0 done until AC2-final is completed.
- Keep SEQR v0 labeled as a project-local rubric.
- Keep delete-from-chapter N > 1 disabled.
- Do not add new frontend lint errors in files touched by Phase 0.

## Next Report

Send a phase report after the schema and offline baseline runner are implemented.
