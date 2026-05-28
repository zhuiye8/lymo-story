# Decision: Phase 0 Report #6 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-6.md` |

## Decision

Report #6 substantially improves the Phase 0 baseline:

- AC3 v5 now uses source-verifiable `public_domain_excerpt` samples instead of model-memory excerpts.
- `calibrate_slop_detector.py --threshold 0.5` reproduces recall `0.9700`, precision overall `0.9700`, and public-domain excerpt precision `0.9700`.
- Trend delta is now locked to Algorithm A: symmetric exclude-middle.
- `tests/test_quality_admin_delta.py` passed 17/17, including the live-DB consistency check for `61513478`.

However, AC5 backend is not final. The report says all 4 chart endpoints are covered by strict readiness gates, but the implementation still has two gaps in score-table completeness. AC5 frontend UI should not start until these are fixed, because otherwise the UI can render partial quality data as ready.

AC3 can be treated as data-ready for supervisor review, but final gate wording must not call the v5 negative samples "human-written precision". The correct label is `source-verifiable public-domain excerpt precision` plus `project-accepted synthetic fiction precision`.

## Findings

### AC5 heatmap readiness misses whole missing chapters

`get_heatmap()` only checks dimensions for chapters that appear in `chapter_quality_scores`. If all 8 score rows for a selected chapter are missing, that chapter is absent from `chapters`, `incomplete` stays empty, and the endpoint can return `data_ready=true` with a shortened matrix.

Required fix:

- derive expected chapters for the story from `chapter_quality_evaluations` for the same `evaluation_batch_id` and `story_id`;
- require each expected chapter to have all `len(DIMENSIONS)` score rows;
- return `data_ready=false` with missing chapter numbers and/or missing dimensions.

### AC5 distribution readiness ignores score-table completeness

`get_distribution()` gates only `chapter_quality_evaluations`, but its `per_dimension_histograms` are built from `chapter_quality_scores`. If evaluations are complete and score rows are partial, composite/slop histograms are complete while dimension histograms are incomplete, yet the endpoint still returns `data_ready=true`.

Required fix:

- require both `evaluations_complete` and `scores_complete` for distribution;
- include the expected and actual score counts in the failure reason.

### Phase gate should reflect AC3 v5 evidence standard

`phase-gate.md` still describes AC3 as `100 + 50 + 50` and does not mention the v5 `public_domain_excerpt` subset. This is now stale against Report #6 and can make future reviews use the wrong acceptance standard.

Required fix:

- update AC3 scope to `100 slop + 50 generic-normal + 50 project-accepted fiction-normal + 21 public_domain_excerpt`;
- define final approval wording as `precision_fiction_mixed >= 0.7` and `precision_pd_excerpt >= 0.7`;
- keep `human-written` out unless independent human samples are actually added.

## Supervisor Decisions

- AC5 frontend UI: wait. Fix heatmap and distribution readiness first.
- AC3: data-ready, not yet final-labelled until phase-gate wording is updated and the supervisor either spot-checks several Wikisource URLs or accepts the stored `source_url`/`_raw_traditional` provenance as sufficient for Phase 0.
- AC2-final: still the remaining hard gate. Do not auto-fill it.
- `opencc`: do not add a dependency by itself. Either commit a reproducible Wikisource sample builder script and add `opencc-python-reimplemented` to dev deps, or document that `slop_samples_zh.json` is a static audited corpus.

## Verification

- `conda run -n story pytest tests/test_quality_admin_delta.py -v` passed: 17 tests.
- `python scripts/calibrate_slop_detector.py --threshold 0.5` passed: recall `0.9700`, precision overall `0.9700`, precision public-domain excerpt `0.9700`.
- `python -m compileall -q backend scripts` passed.
- Local JSON audit confirmed `normal_fiction` contains 50 `engineer_synthetic` and 21 `public_domain_excerpt`; all public-domain entries have `source_url`, `verification_status`, `_raw_traditional`, `accepted_by`, `accepted_at`, and `author_death_year`.
