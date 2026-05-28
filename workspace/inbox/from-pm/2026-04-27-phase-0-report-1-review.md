# Direction: Phase 0 Report #1 Review

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-27 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-27-phase-0-report-1-review.md` |
| Default if no answer | Continue AC2-final, AC3, AC5; fix AC6 report and AC1/AC1b pass logic first. |

## Result

Report #1 is accepted with required corrections.

You may continue Phase 0. Do not claim Phase 0 complete yet.

## Required Corrections

### 1. AC6 Report

Fix AC6 in `data/baselines/baseline_report_2026-04-27.md`.

Current issue: AC6 is marked Pass because the file exists, but the approved gate requires the baseline report to show per-story mean, variance, and trend. The current table has per-story means but not variance/trend.

Either add those fields and keep AC6 Pass, or mark AC6 partial/pending until they are added.

### 2. AC1/AC1b Pass Logic

Fix `backend/quality/batch.py`.

Current issue: `ac1_pass` and `ac1b_pass` use 90% coverage as the pass condition. The approved gate requires complete baseline coverage. Use:

- `scores_count == scope_chapter_count * 8`
- `evaluations_count == scope_chapter_count`

The 90% threshold can remain as a warning/triage indicator, but it must not be the pass boolean used by reports or future UI.

## AC2-Final

Use this chapter:

- story_id: `bc910038`
- chapter_num: `1`

Prepare the AC2-final artifact for supervisor rating. The supervisor will independently score this chapter and write the final calibration conclusion.

## Next Work

- Expand slop samples to 100 bad + 50 normal and run AC3 calibration.
- Run AC2-bootstrap in parallel.
- Implement AC5 only after the chart data contracts are stable.
- Keep Phase 0 scoped to evaluation baseline; do not begin generation architecture implementation in this phase.

## Notes

- Batch isolation and aggregate score storage are verified.
- The current batch has 100% coverage, so this pass-logic bug does not invalidate the existing batch 2 data.
- Full-reset-only deletion is aligned between backend and frontend.
- The previous `deleteFromChapter` cleanup is verified.
- Existing frontend lint debt in `frontend/app/stories/[id]/page.tsx` remains outside this review, but no new touched-file lint debt should be added.
