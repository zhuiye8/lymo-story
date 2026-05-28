# Review: Phase 0 Evaluation Baseline v2

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-26 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-26-phase-0-v2-review.md` |
| Default if no answer | Do not start implementation. Apply the five conditions in the decision record first. |

## Result

`approve-with-conditions`.

v2 fixed the v1 blocking issues: SEQR is now clearly project-local, HNES/WebNovelBench are no longer misused, aggregate scores exist, AC1 SQL is corrected, API key is removed from source, and unsafe N>1 deletion is blocked in the backend.

## Required Before Implementation

1. Add `evaluation_batch_id` or equivalent and update AC1/AC1b queries to filter one batch.
2. Keep AC2-final as a real supervisor gate; save the calibration artifact.
3. Change the frontend delete UI so it does not offer deleting from chapter N > 1.
4. Fix the newly introduced lint error in `DeepSeekSetupPanel.tsx`.
5. Confirm the old DeepSeek key has been revoked; do not commit `.env`.

## Approved Choices

- Use SEQR v0 as a local rubric.
- Use DeepSeek-V4-Pro non-thinking for first PoC only.
- Defer paper-true WebNovelBench/HNES and safe rewind snapshots.
- Do not expand Phase 0 beyond evaluation baseline.
