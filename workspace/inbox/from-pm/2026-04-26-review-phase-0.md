# Review: Phase 0 Evaluation Baseline

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-26 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-26-phase-0-review.md` |
| Default if no answer | Do not start Phase 0 implementation; submit revised `phase-gate.md` and `proposal.md` before 2026-04-29 23:59. |

## Result

`revision-needed`.

The direction is right: Phase 0 should build an evaluation baseline before any writing-quality claims. The current submission is not ready because the core metric definitions are not source-aligned, and two implementation risks need correction before work continues.

## Required Fixes

1. Correct WebNovelBench dimensions or rename the rubric as project-local.
2. Correct HNES / QLS or rename it as project-local composite score.
3. Add chapter-level aggregate score persistence.
4. Fix the AC1 SQLite query.
5. Strengthen AC2 calibration beyond engineer-only pooled scoring.
6. Remove and revoke the hard-coded DeepSeek API key in the local benchmark script.
7. Make delete-from-chapter safe for N > 1, or remove/disable that endpoint.

## Next Submission

Submit revised files:

- `workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md`
- `workspace/plans/2026-04-26-rearchitecture/phase-0/proposal.md`

Keep the revision focused. Do not expand Phase 0 beyond evaluation baseline.
