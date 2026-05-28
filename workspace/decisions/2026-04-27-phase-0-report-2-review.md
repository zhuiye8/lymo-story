# Decision: Phase 0 Report #2 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-2.md` |

## Decision

Report #2 is accepted as real progress, but it is not a Phase 0 exit.

The previous AC1/AC1b pass-logic finding is resolved. The previous AC6 report finding is mostly addressed, but the report still says "variance" while supplying `stdev`; this must be made exact before AC6 remains Pass.

AC3 is not rejected, but the current calibration is only a provisional/smoke pass because the negative set is out-of-domain for a Chinese fiction slop detector.

## Findings

### AC6 Variance vs Stdev

`data/baselines/baseline_report_2026-04-27.md` says AC6 contains `mean/variance/trend`, but the table uses `stdev`. Standard deviation is useful, but it is not variance.

Required fix:

- add actual variance columns, or
- explicitly change the accepted AC6 metric from `variance` to `stdev/dispersion` in the phase gate and report.

Do not keep saying variance while reporting stdev.

### AC3 Negative Set Is Out-of-Domain

`data/baselines/slop_samples_zh.json` has 100 slop + 50 normal samples, and the script result is reproducible. However, the normal samples are described as daily-life/office/family/travel prose. The detector will be used on Chinese novel prose, where metaphors, emotion, dramatic beats, and dialogue are naturally more common.

This makes `precision=1.00` too easy and likely inflated.

Required fix before AC3 final Pass:

- add an in-domain normal negative set: at least 50 human-written or manually accepted Chinese fiction paragraphs/chapters;
- rerun calibration and report recall/precision separately for generic-normal and fiction-normal negatives;
- keep the current AC3 as provisional until then.

## Supervisor Decisions

- AC2-final chapter remains `bc910038 / chapter 1`.
- Detector regex decision: choose v1 fix inside Phase 0, not just threshold lowering. Fix the known regex misses, bump detector version, and rerun calibration. Do not silently change threshold to 0.3 as the only response.
- `rhetoric_quality` anti-cliche sensitivity should be a Phase 1 requirement.
- AC5 may start with data-contract design, but final UI should wait until AC2-final and AC3-final data contracts are stable.

## Verification

- `python -m compileall -q backend scripts` passed.
- `python scripts/calibrate_slop_detector.py --threshold 0.5` reproduced `recall=0.94`, `precision=1.00` on the current sample set.
- `python scripts/compute_ac2_bootstrap.py --template data/baselines/ac2-bootstrap-template-batch-2.json` reproduced mean Spearman `0.4506`.
- `pnpm run build` passed in `frontend`.
