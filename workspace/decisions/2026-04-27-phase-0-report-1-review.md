# Decision: Phase 0 Report #1 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | approved-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-1.md` |
| Related baseline | `data/baselines/baseline_report_2026-04-27.md` |

## Decision

Phase 0 Report #1 is accepted as sufficient to continue work.

The implementation has cleared the previous blocking issues around batch isolation, aggregate chapter scores, full-reset-only deletion, and the new DeepSeek setup lint error. Phase 0 is still not complete because AC2-final, AC3, AC5, and the corrections below remain open.

## Required Corrections

### AC6 Report Completeness

`data/baselines/baseline_report_2026-04-27.md` currently marks AC6 as Pass only because the report file exists. That is too loose.

AC6 must either:

- include per-story mean, variance, and trend fields in the report, then remain Pass; or
- be downgraded to partial/pending until those fields are added.

The database already contains enough data to calculate per-story variance, so this should be a report correction, not a schema blocker.

### AC1/AC1b Pass Logic

`backend/quality/batch.py` currently marks AC1/AC1b as passed at 90% coverage. That should not be the green condition.

The Phase Gate success condition is complete batch coverage: `scores_count == scope_chapter_count * 8` and `evaluations_count == scope_chapter_count`. The 90% threshold can be kept as a warning/triage threshold, but it must not be the pass boolean used by reports or future UI.

## AC2-Final Selection

Use `bc910038 / chapter 1` for AC2-final.

Rationale:

- It is the long high-slop candidate, so it stress-tests whether SEQR v0 can distinguish generic fluent prose from novel-quality prose.
- It represents the current weakest story cluster by slop penalty.
- It is more useful than a normal/easy chapter for validating the rubric before Phase 1 rewrite work.

The engineer should prepare the AC2-final artifact for this chapter. The supervisor will complete the independent rating and conclusion.

## Next Directions

- Correct AC6 report status/content before calling Phase 0 green.
- Correct AC1/AC1b pass booleans to require full coverage.
- Expand slop samples toward 100 bad + 50 normal and run AC3 calibration.
- Run AC2-bootstrap in parallel with AC3.
- Start AC5 frontend only after the data contracts for the 4 charts are stable.
- Do not expand Phase 0 into generation architecture work yet.

## Verification

- `python -m compileall -q backend scripts` passed.
- `pnpm run build` passed in `frontend`.
- Targeted eslint still fails only on existing `frontend/app/stories/[id]/page.tsx` debt; the previous `DeepSeekSetupPanel.tsx` and `deleteFromChapter` issues are no longer present.
- Database check for batch 2: 21 chapters, 168 dimension scores, 21 chapter aggregate evaluations, 0 duplicate score groups.
