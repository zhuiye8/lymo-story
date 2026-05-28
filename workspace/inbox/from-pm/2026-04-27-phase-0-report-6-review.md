# PM Review: Phase 0 Report #6

Status: accepted-with-corrections.

You made real progress:

- AC3 v5 replaces memory-recall excerpts with Wikisource-sourced `public_domain_excerpt` entries.
- Slop calibration reproduces recall and precision at `0.9700`.
- Trend delta is now unified around symmetric exclude-middle.
- The new delta tests pass 17/17.

Do not call AC5 backend final yet. Two readiness bugs remain:

1. `backend/api/quality_admin.py::get_heatmap()` does not detect a whole missing chapter if all 8 score rows for that chapter are absent. Derive expected chapters from `chapter_quality_evaluations` for the same batch/story, then require every expected chapter to have all 8 dimensions.
2. `backend/api/quality_admin.py::get_distribution()` checks only aggregate evaluation completeness, but returns per-dimension histograms from `chapter_quality_scores`. It must also require `scores_complete`.

Also update `workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` so AC3 reflects v5:

- `100 slop + 50 generic-normal + 50 project-accepted fiction-normal + 21 public_domain_excerpt`;
- final approval should mention `precision_pd_excerpt >= 0.7`;
- do not call this human-written precision.

Supervisor decisions:

- AC5 frontend UI waits until the two readiness gaps are fixed.
- AC3 is data-ready, but final labelling waits for the phase-gate wording update and optional source URL spot-check.
- AC2-final remains the hard gate and should not be auto-filled.
- Only add `opencc-python-reimplemented` to dev deps if you also commit a reproducible Wikisource sample builder script. Otherwise treat the JSON corpus as static audited data.

Verification I ran:

- `conda run -n story pytest tests/test_quality_admin_delta.py -v`: 17 passed.
- `python scripts/calibrate_slop_detector.py --threshold 0.5`: recall `0.9700`, precision overall `0.9700`, precision public-domain excerpt `0.9700`.
- `python -m compileall -q backend scripts`: pass.
- JSON provenance audit: 21 public-domain entries have the required source/provenance fields.
