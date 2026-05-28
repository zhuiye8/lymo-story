# PM Review: Phase 0 Report #8

Status: accepted-with-corrections.

Builder corrections are accepted:

- partial Wikisource fetch now fails hard by default;
- partial drafts require `--allow-partial`;
- `--merge --allow-partial` is rejected;
- merge preserves existing `normal_pd_*` IDs by `source_url`;
- corpus metadata records `preserved=21`, `newly_assigned=0`.

AC3 is approved as Phase 0 pass, using this wording only:

`source-verifiable public-domain excerpt precision`

Do not call it `human-written precision`.

AC5 UI is not accepted yet. Targeted ESLint on the new files fails:

```bash
pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx
```

Problems:

- `frontend/app/admin/quality/page.tsx`: `react-hooks/set-state-in-effect` in the batch-change effect;
- `frontend/app/admin/quality/page.tsx`: `react-hooks/set-state-in-effect` in the heatmap effect;
- `frontend/app/admin/quality/page.tsx`: one `react-hooks/exhaustive-deps` warning in `ByDimensionChart`.

Fix those and re-run the targeted lint command. After that, AC5 UI needs a browser smoke check.

Verification I ran:

- `python -m compileall -q backend scripts tests`: pass.
- `conda run -n story pytest tests/test_wikisource_builder.py -v`: 11 passed.
- `conda run -n story pytest tests -q`: 35 passed.
- `pnpm run build`: pass, `/admin/quality` included.
- simulated partial builder run: exit `1`, no draft written.
- temp-corpus merge simulation: 21/21 IDs preserved.

AC2-final remains supervisor-only. Do not auto-fill it.
