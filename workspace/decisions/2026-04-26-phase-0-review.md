# Decision: Phase 0 Evaluation Baseline Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-26 |
| Status | revision-needed |
| Related proposal | `workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md`; `workspace/plans/2026-04-26-rearchitecture/phase-0/proposal.md` |
| Related review request | `workspace/inbox/from-engineer/2026-04-26-review-request-phase-0.md` |

## Decision

Phase 0 direction is approved in principle, but the submitted gate/proposal is not approved for implementation yet.

Required status: `revision-needed`.

## Blocking Findings

1. WebNovelBench dimensions are materially wrong.
   - The proposal uses `fluency / vocab / plot / character / dialogue / theme / innovation / overall`.
   - The source paper's eight dimensions are literary devices, sensory detail, balance of character presence, distinctiveness of character dialogue, consistency of characterisation, atmospheric/thematic alignment, contextual appropriateness, and scene-to-scene coherence.
   - Fix: either implement the paper dimensions and weights, or explicitly rename this to an internal rubric and stop calling it WebNovelBench.

2. HNES / QLS formula is not verified and does not match the source.
   - The proposal defines `HNES = (Sq + Sl) / 2 - slop_penalty`, with `Sq = mean(8 dims)` and a custom log length factor.
   - The source defines HNES as Hierarchical Narrative Evaluation with State-Tracking and uses QLS from quality score and length score; quality uses seven dimensions and AHP weights.
   - Fix: either implement the paper formula correctly, or rename this to a project-local composite score.

3. Aggregate score persistence is missing.
   - The proposed DB schema stores per-dimension scores, slop findings, and judge runs, but not one row per chapter containing `hnes_score`, `final_score`, mean quality, word count, and evaluation version.
   - The Pydantic schema and UI both expect aggregate chapter-level scores.
   - Fix: add a `chapter_quality_evaluations` or equivalent aggregate table.

4. AC1 query is not SQLite-valid as written.
   - `COUNT(DISTINCT story_id, chapter_num, dimension)` is not valid SQLite syntax.
   - Fix: use a grouped subquery or a uniqueness constraint plus `COUNT(*)`.

5. AC2 calibration is too weak to be the main pass/fail gate.
   - Pooling 5 chapters × 8 dimensions into 40 pairs can hide per-dimension failure.
   - Engineer self-scoring is useful for bootstrap, but should not be the only calibration source.
   - Fix: report per-dimension agreement where possible, and require at least one supervisor/PM calibration sample or a clearly marked bootstrap-only threshold.

6. A local benchmark script contains a hard-coded API key.
   - Fix immediately: revoke the key, remove the literal from the file, and read from environment variables only.

7. The new delete-from-chapter endpoint can leave future world state and event graph contamination.
   - It deletes chapter rows, memories, and related tables, but only resets world state and event graph when deleting from chapter 1.
   - For deleting from chapter N > 1, future world state/events from deleted chapters remain and can poison regeneration.
   - Fix: either disable this endpoint for N > 1, or implement a safe rewind using persisted world/event snapshots.

## Decisions On Ask Items

| Ask | Decision |
|---|---|
| Overall Phase 0 | `revision-needed` before implementation |
| Judge LLM | Use DeepSeek-V4-Pro non-thinking for first PoC only; do not bind as final until AC2 is revised |
| WebNovelBench review | Must be corrected before coding the rubric; not parallel |
| AC2 human scoring | Engineer may bootstrap, but final gate needs independent calibration or explicitly downgraded confidence |

## Conditions For Resubmission

- Replace or rename the WebNovelBench dimensions.
- Replace or rename the HNES formula.
- Add aggregate evaluation persistence.
- Fix AC1 SQL.
- Strengthen AC2 calibration.
- Remove/revoke the hard-coded API key.
- Make delete-from-chapter safe or remove it from scope.

## Verification Performed

- `python -m compileall -q backend scripts` passed.
- `pnpm run lint` failed, mostly due to existing frontend lint debt, but the new `DeepSeekSetupPanel.tsx` also adds at least one lint error.

## Sources Checked

- WebNovelBench paper: `https://aclanthology.org/2026.findings-eacl.94.pdf`
- CreAgentive / HNES paper: `https://openreview.net/pdf?id=8R4r7MXOpo`
- DeepSeek V4 official release/pricing docs: `https://api-docs.deepseek.com/news/news260424`, `https://api-docs.deepseek.com/quick_start/pricing`
