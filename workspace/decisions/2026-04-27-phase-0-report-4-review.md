# Decision: Phase 0 Report #4 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-minor-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-4.md` |

## Decision

Report #4 resolves the main findings from Report #3 review:

- batch 2 is not being mutated;
- detector version split-brain is fixed at the Python import level;
- phase-gate AC1/AC1b and AC3 acceptance rows now use the dynamic scope and domain-split sample set;
- AC3 sample provenance is now explicit and no longer overclaims "human-written".

Phase 0 is still not complete because AC2-final remains open and AC3 final status still needs an independent negative set decision.

## Remaining Corrections

### Storage Schema Defaults

`backend/storage/sqlite_store.py` still declares `detector_version TEXT NOT NULL DEFAULT 'slop-v0'` in `evaluation_batches` and `slop_findings`.

Current code paths pass `DETECTOR_VERSION` explicitly, so existing behavior is not broken. But the schema default is now stale and can reintroduce audit pollution if a future write path omits the field.

Required fix:

- update the schema default to `slop-v1`, or
- remove the misleading default and require explicit detector_version in all inserts.

### Stale Proposal Document

`workspace/plans/2026-04-26-rearchitecture/phase-0/proposal.md` is still an old v2 proposal that says 24 chapters and 100+50 human-normal samples.

Required fix:

- mark the proposal as superseded by phase-gate v2.2; or
- update the stale lines to the current scope/sample wording.

The phase-gate header should also be bumped from v2.1 to v2.2 to match the body and Report #4.

## Supervisor Decisions

- AC2-final remains `bc910038/ch1`.
- Detector comparison path: choose Path A for Phase 0. Do not rescore batch 2. Do not add `source_batch_id` migration in Phase 0.
- AC3 final standard: choose stricter option B. Add independent negative samples before final AC3 pass.
- Minimum AC3 next step: add at least 20 `public_domain_excerpt` or other auditable non-synthetic fiction-normal samples, report precision separately for `engineer_synthetic` and independent negatives, then ask for final AC3 approval.
- AC5 backend endpoints may start after the two minor corrections above. AC5 frontend UI still waits for AC2-final and final data-contract stability.

## Verification

- `python -m compileall -q backend scripts` passed.
- `pnpm run build` passed in `frontend`.
- `pnpm exec eslint components/DeepSeekSetupPanel.tsx` passed.
- Secret scan over `scripts`, `backend`, and `frontend` found no hard-coded API key.
- `python scripts/calibrate_slop_detector.py --threshold 0.5` reproduced detector `slop-v1`, recall `0.97`, precision overall `1.00`, precision fiction `1.00`.
- Current DB batch 2 remains `slop-v0` with 168 scores, 21 evaluations, 21 judge runs, and 27 slop findings.
