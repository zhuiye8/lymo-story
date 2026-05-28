# Decision: Phase 0 Report #8 Review

| Field | Value |
|---|---|
| Decider | supervisor |
| Date | 2026-04-27 |
| Status | accepted-with-corrections |
| Related report | `workspace/inbox/from-engineer/2026-04-27-phase-report-phase-0-8.md` |

## Decision

The two Report #7 builder findings are closed:

- partial Wikisource fetch now fails hard by default and does not write the canonical draft;
- `--allow-partial` exists only for debug drafts and cannot be combined with `--merge`;
- merge now preserves existing `normal_pd_*` IDs by `source_url`;
- current corpus reports `id_stability.preserved = 21` and `newly_assigned = 0`.

AC3 can now be labelled Phase 0 pass, with the precise wording: `source-verifiable public-domain excerpt precision`, not `human-written precision`.

AC5 UI has been implemented, but is not accepted yet because the new page has targeted ESLint errors. The UI can proceed after those errors are fixed and a targeted lint check passes.

AC2-final remains supervisor-only and must not be auto-filled.

## Finding

### AC5 UI has new lint errors

`frontend/app/admin/quality/page.tsx` fails targeted ESLint:

- `react-hooks/set-state-in-effect` at the batch-change effect (`setTrend`, `setByDim`, `setDistrib`, `setHeatmap`, `setStoryId`);
- `react-hooks/set-state-in-effect` at the heatmap effect (`setHeatmap(null)`);
- one `react-hooks/exhaustive-deps` warning for `ByDimensionChart`.

Required fix:

- refactor the loading/reset state so the effect does not synchronously call these setters in the effect body, or use a reducer/state shape that derives loading state from `batchId` / request lifecycle;
- remove the unnecessary `data` dependency in `ByDimensionChart` or make dependencies stable;
- re-run targeted lint: `pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx`.

## Supervisor Decisions

- AC3: final pass for Phase 0 evidence standard.
- AC5 backend: still approved.
- AC5 frontend: implemented but pending lint correction and UI smoke.
- AC2-final: still pending supervisor independent scoring.

## Verification

- `python -m compileall -q backend scripts tests` passed.
- `conda run -n story pytest tests/test_wikisource_builder.py -v` passed: 11 tests.
- `conda run -n story pytest tests -q` passed: 35 tests.
- `pnpm run build` passed and includes `/admin/quality`.
- `pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx` failed on the new quality page as described above.
- Simulated partial builder run exited `1` and wrote no draft.
- Temp-corpus merge simulation preserved all 21 public-domain IDs.
- `slop_samples_zh.json` schema has `id_stability: preserved=21, newly_assigned=0`.
