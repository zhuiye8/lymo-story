# Direction: Phase 0 Report #4 Review

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-27 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-27-phase-0-report-4-review.md` |
| Default if no answer | Path A; no batch 2 rescore; add independent AC3 negatives before final pass. |

## Result

Report #4 is accepted with minor corrections.

## Resolved

- Do not mutate batch 2: resolved.
- Phase-gate AC1/AC1b and AC3 main rows: resolved.
- Fiction-normal provenance: resolved as `engineer_synthetic`, no longer overclaimed as human-written.
- Detector version split-brain: resolved at import level.

## Required Corrections

1. Update `backend/storage/sqlite_store.py` detector defaults, or remove the defaults and require explicit detector_version.
2. Mark `proposal.md` superseded or update its stale 24-chapter / 100+50 human-normal wording.
3. Bump phase-gate header/version metadata from v2.1 to v2.2.

## Decisions

- AC2-final remains `bc910038/ch1`.
- Detector comparison: Path A for Phase 0. Do not rescore batch 2 and do not add `source_batch_id` migration now.
- AC3 final: choose option B. Current synthetic corpus stays provisional. Add at least 20 auditable non-synthetic fiction-normal samples (`public_domain_excerpt` or equivalent), then rerun and report precision separately.
- AC5 backend may start after the required corrections above. Frontend UI still waits for AC2-final and final data contracts.
