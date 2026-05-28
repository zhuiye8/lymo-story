# Decision: Phase 0 Greenlight

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-26 |
| Status | approved |
| Related decision | `workspace/decisions/2026-04-26-phase-0-v2-review.md` |
| Related report | `workspace/inbox/from-engineer/2026-04-26-report-conditions-applied.md` |

## Decision

Phase 0 Evaluation Baseline is greenlit for implementation under the v2.1 plan.

## Rationale

The five pre-start conditions from the v2 review have been applied:

- Evaluation batches isolate reruns and keep AC1/AC1b stable.
- AC2-final remains a real supervisor gate and must save a calibration artifact.
- The frontend no longer exposes deleting from chapter N > 1.
- The new DeepSeek setup component no longer has the previous lint error.
- The hard-coded benchmark key was removed from source; `.env` is gitignored and untracked.

## Conditions During Implementation

- Do not expand Phase 0 beyond the evaluation baseline.
- Do not claim Phase 0 exit until AC2-final is completed.
- Keep SEQR v0 clearly labeled as a project-local rubric.
- Any rerun must create a new `evaluation_batch_id`.
- Keep delete-from-chapter N > 1 disabled until a separate safe-rewind design is approved.

## Non-Blocking Cleanup

- Remove the now-unused `deleteFromChapter` state in `frontend/app/stories/[id]/page.tsx`.
- Existing frontend lint debt remains outside this greenlight, but touched new files should not add new errors.
- User should confirm the old DeepSeek test key is revoked in the DeepSeek console.

## Verification

- `python -m compileall -q backend scripts` passed.
- `pnpm run build` passed.
- Targeted eslint confirms `DeepSeekSetupPanel.tsx` no longer has the previous error.
- Secret scan found no old `sk-a0ac...` key outside local `.env`.

## Follow-Up

- [ ] Engineer starts Phase 0 implementation.
- [ ] Engineer sends first phase report after schema + offline baseline runner are implemented.
- [ ] Supervisor performs AC2-final calibration when engineer provides the selected chapter and artifact.
