# Decision: Phase 0 Report #7 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-7.md` |

## Decision

Report #7 closes the three direct findings from Report #6:

- `get_heatmap()` now derives expected chapters from `chapter_quality_evaluations` and catches whole missing chapters.
- `get_distribution()` now requires both evaluation and score-table completeness.
- `phase-gate.md` is now v2.3 and AC3 wording reflects v5, including `precision_pd_excerpt >= 0.7` and no `human-written` claim.

AC5 backend is approved for frontend UI implementation. The UI can start now, provided it treats `data_ready=false` as a hard placeholder state and surfaces `reason`.

AC3 is still data-ready, but final labelling should wait for two reproducible-builder fixes below because the engineer chose the "committed builder + opencc dev dep" path as the audit mechanism.

AC2-final remains the only hard Phase 0 gate not handled by the engineer.

## Findings

### Wikisource builder must fail hard on partial fetch

Observed during review: one run fetched only 20/21 excerpts after a transient Wikisource SSL EOF, still exited `0`, and wrote `data/baselines/_pd_excerpts_draft.json` with 20 entries. A later retry fetched 21/21.

This means the builder can silently produce partial evidence. Worse, `--merge` would merge that partial list into `slop_samples_zh.json` and update schema counts instead of failing.

Required fix:

- track failures and no-paragraph targets;
- require `len(drafts) == len(TARGETS)` before writing the canonical draft or merging;
- exit non-zero with target names/URLs on mismatch;
- if partial drafts are useful for debugging, put them behind an explicit `--allow-partial` flag and never allow partial `--merge`.

### Wikisource merge must preserve stable sample IDs

The builder's current `--merge` path assigns `normal_pd_001...` by current `TARGETS` order. The existing corpus has the same 21 source URLs and matching text, but a different order for entries 12-21. Running `--merge` would therefore churn `normal_pd_012` onward and invalidate stable references such as the calibration false-positive IDs.

Required fix:

- preserve existing `id` by `source_url` when replacing an existing public-domain sample; or
- make `TARGETS` carry explicit stable IDs and update the current corpus to that order once.

Do not let a reproducibility script rewrite audit IDs as a side effect of refreshing source text.

## Supervisor Decisions

- AC5 UI: approved to start.
- AC3: data-ready, final label waits for the two builder fixes or an explicit decision to treat `slop_samples_zh.json` as the static audited corpus instead of relying on `--merge`.
- AC2-final: still waits for supervisor independent scoring. Do not auto-fill.

## Verification

- `python -m compileall -q backend scripts tests` passed.
- `conda run -n story pytest tests -v` passed: 24 tests.
- `conda run -n story python scripts/calibrate_slop_detector.py --threshold 0.5` passed: recall `0.9700`, precision overall `0.9700`, public-domain excerpt precision `0.9700`.
- Direct environment Python ran `scripts/build_wikisource_pd_corpus.py`; retry fetched 21/21 excerpts.
- Draft-vs-corpus comparison by `source_url` found 0 text mismatches across the 21 public-domain excerpts.
- Live FastAPI TestClient: batch 2 trend/by-dimension/distribution and all three story heatmaps returned `data_ready=true`.
