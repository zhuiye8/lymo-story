# Decision: Phase 0 Report #3 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-3.md` |

## Decision

Report #3 is accepted as real progress, but Phase 0 is still not an exit.

The AC6 variance/stdev issue is resolved in the baseline report. Detector v1 regex fixes are technically plausible and the AC3 v2 calibration script reproduces the reported numbers. The AC5 data contract is directionally approved.

However, the implementation still has provenance and versioning problems that must be fixed before declaring AC3/Phase 0 final.

## Findings

### Detector Version Is Split-Brain

`backend/quality/slop_detector.py` declares `DETECTOR_VERSION = "v1"`, but `backend/quality/__init__.py` still exports `DETECTOR_VERSION = "slop-v0"`.

`backend/quality/batch.py` and `scripts/run_phase0_baseline.py` import the stale package-level constant, so future batches and `slop_findings` rows can be written as `slop-v0` while actually using v1 detector logic.

Required fix:

- make detector version a single source of truth;
- ensure `create_batch`, `run_phase0_baseline.py`, and any future rescore scripts write the actual detector version used;
- keep old v0 batch metadata intact.

### Do Not Mutate Batch 2 In Place

Report #3 proposes rescoring batch 2 and possibly archiving v0 data into an ad-hoc `chapter_quality_scores_v0` table by default.

That violates the batch-isolation principle. A completed batch is an immutable audit record.

Required fix:

- do not overwrite batch 2 rows;
- if v1 detector data is needed, create a new `evaluation_batch_id`, or create an explicitly linked derived batch/snapshot with `source_batch_id = 2`;
- do not create ad-hoc archive tables unless a migration and query contract are approved.

### Phase Gate Is Still Stale

`workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` still hard-codes 24 chapters / 192 scores and the old AC3 sample shape.

Required fix:

- AC1/AC1b should use `scope_chapter_count` in the acceptance table;
- AC3 should specify 100 slop + 50 generic normal + 50 fiction-normal, or whatever final accepted split is;
- cost/sample-size text should stop saying 24 chapters if the current accepted baseline scope is 21.

### AC3 Fiction-Normal Provenance Is Not Auditable

The v2 corpus claims normal fiction samples are human-written, but the schema says `engineer hand-authored` and per-sample `source` is empty. Since the engineer is an AI-assisted worker in this process, this is not enough to claim human-written negative precision.

Required fix:

- add per-sample provenance fields, e.g. `source_type`, `source_note`, `accepted_by`, `accepted_at`;
- if the fiction-normal set is synthetic/project-accepted rather than independently human-written, say that explicitly and avoid claiming human-written precision;
- keep AC3 as provisional until the provenance claim is accurate.

## Supervisor Decisions

- AC2-final chapter remains `bc910038/ch1`.
- AC5 data contract is approved in principle.
- AC5 backend endpoints may start only after the detector version and batch immutability issues are corrected.
- AC5 frontend UI still waits for AC2-final and stable final data contracts.
- Detector v1 regex direction is approved, but metadata/provenance must be fixed before final AC3 pass.

## Verification

- `python -m compileall -q backend scripts` passed.
- `pnpm run build` passed in `frontend`.
- `pnpm exec eslint components/DeepSeekSetupPanel.tsx` passed.
- Targeted lint on `frontend/app/stories/[id]/page.tsx` still fails due existing debt.
- `python scripts/calibrate_slop_detector.py --threshold 0.5` reproduced recall `0.97`, precision overall `1.00`, precision fiction `1.00` on the current corpus.
- Current DB batches still record detector version `slop-v0`.
