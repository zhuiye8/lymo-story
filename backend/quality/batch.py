"""Evaluation batch management.

Per supervisor condition C1 (decisions/2026-04-26-phase-0-v2-review.md):
every baseline run must create a new evaluation_batch_id; AC1/AC1b/AC4
must filter by it.
"""
import json
from datetime import datetime, timezone

import aiosqlite

from backend.quality import RUBRIC_VERSION, DETECTOR_VERSION


async def create_batch(
    db_path: str,
    batch_label: str,
    judge_model: str,
    judge_options: dict | None,
    description: str,
    scope_story_ids: list[str],
    scope_chapter_count: int,
    rubric_version: str = RUBRIC_VERSION,
    detector_version: str = DETECTOR_VERSION,
) -> int:
    """Insert a new evaluation_batches row, return its id."""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            """INSERT INTO evaluation_batches
               (batch_label, rubric_version, judge_model, judge_options_json,
                detector_version, description, scope_story_ids,
                scope_chapter_count, started_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running')""",
            (
                batch_label, rubric_version, judge_model,
                json.dumps(judge_options or {}, ensure_ascii=False),
                detector_version, description,
                json.dumps(scope_story_ids, ensure_ascii=False),
                scope_chapter_count, now,
            ),
        )
        await db.commit()
        return cur.lastrowid or 0


async def finish_batch(db_path: str, batch_id: int, status: str = "completed") -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE evaluation_batches SET status = ?, finished_at = ? WHERE id = ?",
            (status, now, batch_id),
        )
        await db.commit()


async def get_batch(db_path: str, batch_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM evaluation_batches WHERE id = ?", (batch_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_batches(db_path: str, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM evaluation_batches ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def batch_summary(db_path: str, batch_id: int) -> dict:
    """Roll up AC1/AC1b/AC4 stats for a batch."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM chapter_quality_scores WHERE evaluation_batch_id = ?",
            (batch_id,),
        )
        scores_count = (await cur.fetchone())["n"]
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM chapter_quality_evaluations WHERE evaluation_batch_id = ?",
            (batch_id,),
        )
        evals_count = (await cur.fetchone())["n"]
        cur = await db.execute(
            """SELECT COUNT(*) AS n, AVG(total_cost_cny) AS mean_cost,
                      SUM(total_cost_cny) AS total_cost,
                      AVG(latency_ms) AS mean_latency
               FROM judge_runs WHERE evaluation_batch_id = ?""",
            (batch_id,),
        )
        runs = await cur.fetchone()
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM slop_findings WHERE evaluation_batch_id = ?",
            (batch_id,),
        )
        slop_count = (await cur.fetchone())["n"]

    batch = await get_batch(db_path, batch_id)
    scope = batch["scope_chapter_count"] if batch else 0
    expected_scores = scope * 8

    # Per supervisor 2026-04-27 review
    # (workspace/decisions/2026-04-27-phase-0-report-1-review.md):
    # Pass condition is FULL coverage; 90% is only a warning/triage indicator.
    ac1_pass = scope > 0 and scores_count == expected_scores
    ac1b_pass = scope > 0 and evals_count == scope
    ac1_partial_warning = (
        scope > 0 and scores_count < expected_scores and scores_count >= int(expected_scores * 0.9)
    )
    ac1b_partial_warning = (
        scope > 0 and evals_count < scope and evals_count >= int(scope * 0.9)
    )

    return {
        "batch_id": batch_id,
        "batch_label": batch["batch_label"] if batch else None,
        "status": batch["status"] if batch else None,
        "scope_chapter_count": scope,
        "expected_scores_count": expected_scores,
        "scores_count": scores_count,
        "evaluations_count": evals_count,
        "judge_runs_count": runs["n"] or 0,
        "mean_cost_cny": runs["mean_cost"] or 0.0,
        "total_cost_cny": runs["total_cost"] or 0.0,
        "mean_latency_ms": runs["mean_latency"] or 0,
        "slop_findings_count": slop_count,
        # AC gate booleans — strict full coverage required
        "ac1_pass": ac1_pass,
        "ac1b_pass": ac1b_pass,
        "ac4_pass": (runs["mean_cost"] or 0) <= 0.10,
        # Triage indicators (informational; never replace pass logic)
        "ac1_partial_warning": ac1_partial_warning,
        "ac1b_partial_warning": ac1b_partial_warning,
    }
