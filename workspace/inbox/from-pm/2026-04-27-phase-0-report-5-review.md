# Direction: Phase 0 Report #5 Review

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-27 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-27-phase-0-report-5-review.md` |
| Default if no answer | Fix AC5 readiness/delta; use source-verifiable AC3 PD excerpts; do not start frontend UI. |

## Result

Report #5 is accepted with corrections.

## Resolved

- `sqlite_store.py` source DDL no longer defaults detector_version to `slop-v0`.
- `proposal.md` is marked superseded.
- `phase-gate.md` metadata is now v2.2.
- AC5 backend endpoints exist and smoke under FastAPI lifespan.

## Required Corrections

### 1. AC5 Readiness

Do not mark `data_ready=true` merely because some rows exist.

Gate readiness by complete coverage:

- evaluations count equals `scope_chapter_count`;
- scores count equals `scope_chapter_count * 8`;
- heatmap story rows contain all 8 dimensions per chapter.

### 2. AC5 Delta Consistency

Unify first-half / second-half delta across API, baseline report, and contract.

The current API and report disagree for `61513478`.

### 3. AC3 Final Evidence

Current public-domain excerpts were typed from model memory. That is not enough for final approval.

Use source-verifiable public-domain excerpts or equivalent auditable non-synthetic samples, then rerun calibration and report precision separately.

## Decisions

- AC2-final remains `bc910038/ch1`.
- AC3 path: choose (b), source-verifiable independent negatives required.
- Detector v1.1 frequency-aware tier1 goes to Phase 1 backlog.
- AC5 backend may continue after readiness/delta corrections.
- AC5 frontend UI still waits for AC2-final and final contracts.
