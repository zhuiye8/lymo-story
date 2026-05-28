# Decision: Phase 0 Report #5 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-5.md` |

## Decision

Report #5 closes the three direct findings from Report #4 review:

- source DDL no longer defaults detector versions to `slop-v0`;
- `proposal.md` is clearly marked superseded;
- `phase-gate.md` header/version metadata is now v2.2.

The AC5 backend implementation is accepted as a useful start, but it is not final. Two implementation issues must be corrected before AC5 can be called pass.

AC3 remains not-final. The added public-domain excerpts are not auditable enough because they were typed from model memory rather than checked against source text.

## Findings

### AC5 Readiness Must Validate Completeness

The quality endpoints currently set `data_ready=true` when any rows exist. They do not verify that the batch has complete coverage relative to `scope_chapter_count`.

Required fix:

- trend/distribution should require `chapter_quality_evaluations == scope_chapter_count`;
- by-dimension should require `chapter_quality_scores == scope_chapter_count * 8`;
- heatmap should require the selected story's chapters each have all 8 dimensions;
- if incomplete, return `data_ready=false` with a concrete reason.

### AC5 Trend Delta Must Use One Contracted Algorithm

The trend endpoint excludes the middle chapter for odd chapter counts, while `baseline_report_2026-04-27.md` reports a different delta for `61513478`.

Required fix:

- choose one first-half/second-half algorithm;
- update `baseline_report`, `ac5-data-contract.md`, and `quality_admin.py` to the same definition;
- add at least one regression test for an odd chapter count.

## Supervisor Decisions

- AC2-final remains `bc910038/ch1`.
- AC3 final approval: choose path (b). Replace or supplement the model-memory excerpts with source-verifiable public-domain excerpts. Each excerpt should have a source reference/path and a verification note. The current v4 numbers are useful smoke evidence, not final gate evidence.
- Detector v1.1 frequency-aware tier1 can move to Phase 1 backlog; do not change detector scoring again inside Phase 0 unless AC3 recheck fails.
- AC5 backend may continue after the two endpoint corrections above.
- AC5 frontend UI still waits for AC2-final and final data contracts.

## Verification

- `python -m compileall -q backend scripts` passed.
- `pnpm run build` passed in `frontend`.
- `python scripts/calibrate_slop_detector.py --threshold 0.5` reproduced detector `slop-v1`, recall `0.97`, precision overall `0.9798`.
- FastAPI TestClient with lifespan returns 200 for the implemented quality endpoints and 404 for missing batch.
- Existing local DB still reports old `slop-v0` defaults in `PRAGMA table_info`, but current write paths pass detector versions explicitly. Treat this as an operational caveat for the local runtime DB, not a source DDL blocker.
