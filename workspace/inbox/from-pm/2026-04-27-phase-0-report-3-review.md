# Direction: Phase 0 Report #3 Review

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-27 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-27-phase-0-report-3-review.md` |
| Default if no answer | Do not mutate batch 2; fix detector version/provenance and phase-gate wording first. |

## Result

Report #3 is accepted as progress, but Phase 0 is still not complete.

## Resolved

- AC6 now includes variance and stdev.
- Detector v1 regex fixes reproduce better AC3 recall.
- AC3 v2 calibration script runs and reports generic/fiction precision separately.
- AC5 data contract is directionally approved.

## Required Corrections

### 1. Detector Version

Fix version split-brain:

- `backend/quality/slop_detector.py` says detector `v1`;
- `backend/quality/__init__.py` still exports `slop-v0`;
- `batch.py` and `run_phase0_baseline.py` import the stale value.

Make one source of truth and ensure future batches/write paths store the actual detector version.

### 2. Batch Immutability

Do not rescore batch 2 in place.

If detector v1 data is required, create a new batch or an explicitly linked derived batch/snapshot. Do not create ad-hoc archive tables like `chapter_quality_scores_v0` without an approved migration/query contract.

### 3. Phase Gate Staleness

Update `phase-gate.md`:

- AC1/AC1b should use `scope_chapter_count`, not hard-coded 24/192.
- AC3 should reflect the final generic-normal + fiction-normal split.
- Evaluation sample/cost text should match the actual accepted scope.

### 4. AC3 Provenance

Add provenance to each `normal_fiction` sample.

If these are synthetic/project-accepted samples, label them that way. Do not call them human-written unless that is true and auditable.

## Decisions

- AC2-final remains `bc910038/ch1`.
- AC5 backend endpoints may start only after the above versioning/provenance corrections.
- AC5 frontend UI waits for AC2-final and final stable contracts.
- Detector v1 direction is approved, but AC3 remains provisional until provenance and metadata are clean.
