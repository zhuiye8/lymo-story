# Batch Immutability Policy + Derived-Batch Design

| Field | Value |
|---|---|
| Author | engineer |
| Date | 2026-04-27 |
| Status | proposal — schema change pending supervisor approval |
| Related | Report #3 review §"Do Not Mutate Batch 2 In Place"；conditions C1 (`decisions/2026-04-26-phase-0-v2-review.md`) |

## Policy

A completed evaluation batch is an **immutable audit record**.

Once `evaluation_batches.status = 'completed'`, none of the following are allowed for that batch's id:
- `UPDATE` on any row in `chapter_quality_scores`, `chapter_quality_evaluations`, `slop_findings`, or `judge_runs`
- `DELETE` of any row above
- `INSERT` of new child rows that retroactively expand the scope
- Re-running evaluation with a different `detector_version` / `rubric_version` / `judge_model` and writing back to the same `evaluation_batch_id`

Allowed:
- `UPDATE` on `evaluation_batches.description` (operator notes only)
- `INSERT` of audit-only rows (e.g. retrospective comments) into a future, non-yet-existing `batch_audit_notes` table

## What Report #3 Asked For (Wrong)

Report #3 asked: "Detector v1 是否回算 batch 2…如果同意我会写 `scripts/rescore_slop_for_batch.py`，将 v0 数据归档为 `chapter_quality_scores_v0`."

This was wrong. It would:
1. Mutate batch 2's child rows (overwriting v0 results with v1)
2. Create an undeclared archive table without migration/query contract
3. Break the audit trail — anyone querying batch 2 later cannot reproduce the original AC pass evidence

**Engineer self-correction**: do not run that script. Batch 2 stays as-is.

## Proposed Schema Change: `source_batch_id`

To re-evaluate a story scope with a new detector / judge / rubric **without** mutating the original batch, introduce a derived-batch concept.

### Migration (proposed, not yet executed)

```sql
ALTER TABLE evaluation_batches
  ADD COLUMN source_batch_id INTEGER NULL
  REFERENCES evaluation_batches(id);

ALTER TABLE evaluation_batches
  ADD COLUMN derived_kind TEXT NULL;
  -- one of:
  --   NULL                  : original batch (no source)
  --   'detector_rescore'    : same scope, new detector_version
  --   'judge_rescore'       : same scope, new judge_model
  --   'rubric_rescore'      : same scope, new rubric_version
  --   'scope_subset'        : same setup but narrower scope (debug)
```

Constraints:
- A derived batch MUST inherit `scope_story_ids` and `scope_chapter_count` from its source for `detector_rescore` / `judge_rescore` / `rubric_rescore`.
- `derived_kind = 'scope_subset'` may have a smaller scope but never larger.
- Multiple derived batches can chain: B3.source = B2; B4.source = B3 (linked list, not DAG).
- The `slop_findings` table writes the **derived batch's** `evaluation_batch_id` (not the source's), so each batch's child rows remain self-consistent.

### Query Contract

| Use case | SQL |
|---|---|
| List all evaluations of one scope | `SELECT * FROM evaluation_batches WHERE id = :b OR source_batch_id = :b OR id IN (recursive walk)` |
| Compare detector v0 vs v1 on the same scope | join `chapter_quality_scores` on `(story_id, chapter_num)` between source and `derived_kind='detector_rescore'` |
| Audit: which batch is "the" baseline | `SELECT id FROM evaluation_batches WHERE batch_label = 'phase0-baseline-2026-04-27' AND source_batch_id IS NULL` |

### Front-end implication

`/api/admin/quality/batch/{id}/*` endpoints (per AC5 data contract) must:
- For an original batch: return data as-is
- For a derived batch: include `source_batch_id` + `derived_kind` in the response envelope so the UI can label the chart "(detector v1 rescore of batch 2)"

## What This Means For Detector v1

Two paths, both legitimate:

### Path A: Wait for Phase 1

Phase 1 work generates new chapters. When Phase 1 evaluation runs, it naturally uses detector v1 (single source). Batch 2 stays as the v0 historical record. No detector-rescore needed.

**Pros**: zero schema migration; batch 2 remains the canonical Phase 0 baseline.
**Cons**: cannot directly compare same-chapter v0 vs v1 detector scores.

### Path B: Implement source_batch_id, then re-evaluate

1. Supervisor approves the migration above.
2. Implement migration + `create_derived_batch(source_batch_id, derived_kind)` helper.
3. Run `scripts/rescore_slop_for_batch.py --source 2 --derived-kind detector_rescore` → creates batch N with batch N's `slop_findings` written using detector v1, scoring the same 21 chapters.
4. UI can now overlay v0 vs v1 slop trend on the same x-axis.

**Pros**: clean comparison; future-proof.
**Cons**: requires migration + ~1 day implementation; needs supervisor sign-off.

**Engineer recommendation**: Path A for Phase 0 closure (zero migration risk). Path B becomes a Phase 1 prerequisite if/when comparison data is needed.

## Default if Supervisor Doesn't Decide

- Engineer goes Path A: batch 2 stays untouched; future batches use detector v1 automatically (single source already wired).
- Engineer does NOT write `rescore_slop_for_batch.py` until Path B is approved.

## Implementation Status of Policy

| Item | Status |
|---|---|
| Single-source `DETECTOR_VERSION = 'slop-v1'` (`backend/quality/__init__.py` re-exports from `slop_detector`) | ✅ Done (verified `from backend.quality import DETECTOR_VERSION` → `'slop-v1'`) |
| `create_batch` writes the actual detector version | ✅ Already does (`detector_version: str = DETECTOR_VERSION` default) |
| `slop_findings` write the actual detector version | ✅ Already does (uses imported constant) |
| Existing batches 1-2 keep their `slop-v0` tag | ✅ Verified — DB shows `slop-v0` for both, untouched |
| `source_batch_id` migration | 🟡 Proposed only; awaiting supervisor approval |
| `rescore_slop_for_batch.py` | 🚫 NOT implemented; would require Path B approval first |
