# PM Review: Phase 0 Report #7

Status: accepted-with-corrections.

The previous three review findings are closed:

- heatmap now uses evaluations as the authoritative expected chapter list;
- distribution now requires both aggregate and score coverage;
- phase-gate is v2.3 and AC3 wording reflects v5.

AC5 backend is approved. You may start the AC5 frontend UI. The UI must treat `data_ready=false` as non-renderable chart data and show the returned `reason`.

Two new corrections are required for the Wikisource builder before AC3 gets a final label:

1. `scripts/build_wikisource_pd_corpus.py` must fail hard on partial fetch. During review, one run fetched 20/21 after a transient SSL EOF, still exited `0`, and wrote a 20-entry draft. `--merge` must never be able to merge a partial corpus.
2. `--merge` must preserve stable `normal_pd_*` IDs. The current draft text matches the corpus by `source_url`, but the builder order differs from existing IDs for entries 12-21. Re-running `--merge` would churn IDs and invalidate calibration references such as false-positive sample IDs.

Required implementation:

- require `len(drafts) == len(TARGETS)` before writing canonical draft or merging;
- report failed target names/URLs and exit non-zero on mismatch;
- optionally add `--allow-partial` for debugging only, never with `--merge`;
- preserve existing IDs by `source_url`, or put explicit IDs in `TARGETS`.

Verification I ran:

- `python -m compileall -q backend scripts tests`: pass.
- `conda run -n story pytest tests -v`: 24 passed.
- `conda run -n story python scripts/calibrate_slop_detector.py --threshold 0.5`: recall/precision/pd precision all `0.9700`.
- Direct Python `scripts/build_wikisource_pd_corpus.py`: retry fetched 21/21.
- Draft-vs-corpus by `source_url`: 0 text mismatches.
- Live API smoke: batch 2 trend/by-dimension/distribution and all story heatmaps returned `data_ready=true`.

AC2-final remains supervisor-only. Do not auto-fill it.
