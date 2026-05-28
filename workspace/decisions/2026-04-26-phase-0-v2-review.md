# Decision: Phase 0 Evaluation Baseline v2 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-26 |
| Status | approve-with-conditions |
| Related proposal | `workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md`; `workspace/plans/2026-04-26-rearchitecture/phase-0/proposal.md` |
| Related review request | `workspace/inbox/from-engineer/2026-04-26-review-request-phase-0-v2.md` |
| Supersedes | `workspace/decisions/2026-04-26-phase-0-review.md` |

## Decision

Approve Phase 0 v2 in principle. Implementation may start only after the conditions below are applied.

## What Is Accepted

- Accept the local `SEQR v0` name and scope. Do not implement WebNovelBench-strict or CreAgentive/HNES in Phase 0.
- Accept `SEQR_composite = mean(8 dimensions) - slop_penalty` as a project-local v0 metric for internal longitudinal comparison.
- Accept DeepSeek-V4-Pro non-thinking as the first PoC judge model. Do not treat it as permanently selected until calibration passes.
- Accept disabling delete-from-chapter for `N > 1` until safe rewind snapshots exist.
- Accept engineer bootstrap calibration as informative data.

## Conditions

1. Add evaluation batch isolation before implementing the DB schema.
   - Add `evaluation_batch_id` or equivalent to `judge_runs`, `chapter_quality_scores`, `chapter_quality_evaluations`, and `slop_findings`.
   - AC1 and AC1b must filter by one batch, otherwise reruns will break `=192` and `=24`.

2. AC2-final is required.
   - Supervisor will review one selected chapter as the independent gate.
   - The chapter, rubric, human scores, LLM scores, and conclusion must be saved as an artifact under `data/baselines/` or `workspace/plans/.../phase-0/`.
   - Do not fall back to engineer-only bootstrap after this approval.

3. Align the frontend delete UI with backend safety.
   - Since backend rejects `chapter_num > 1`, the UI must not present "delete from any chapter" as an available operation.
   - Either expose only "full reset all chapters" or hide the feature until safe rewind is designed.

4. Fix the new lint error in `DeepSeekSetupPanel.tsx`.
   - Existing repo lint debt does not block this review.
   - Newly introduced lint errors do block accepting the touched UI file.

5. Confirm key hygiene.
   - The hard-coded benchmark key was removed from source. The user/developer must confirm it is revoked on DeepSeek.
   - `.env` remains local and gitignored; do not commit it.

## Ask Decisions

| Ask | Decision |
|---|---|
| Overall v2 | `approve-with-conditions` |
| SEQR v0 local rubric | accepted |
| Implement paper-true WebNovelBench/HNES | rejected for Phase 0 |
| AC2-final by supervisor | accepted, one chapter |
| Judge LLM | DeepSeek-V4-Pro non-thinking PoC only |
| Safe rewind for N > 1 | defer to separate proposal |

## Verification Performed

- External source spot-check passed for WebNovelBench dimensions and PCA/ECDF.
- External source spot-check passed that HNES belongs to CreAgentive/HNES context, not this local score.
- `python -m compileall -q backend scripts` passed.
- Secret scan did not find the old `sk-a0ac...` key in tracked workspace files; `.env` still contains a local API key and is gitignored.
- `pnpm run lint` still fails due to existing frontend debt, plus one new error in `DeepSeekSetupPanel.tsx`.

## Sources Checked

- WebNovelBench: `https://arxiv.org/html/2505.14818`
- CreAgentive / HNES: `https://arxiv.org/html/2509.26461`
