"""AC5 quality dashboard endpoints (Phase 0).

Per data contract `workspace/plans/2026-04-26-rearchitecture/phase-0/ac5-data-contract.md`,
approved-in-principle by supervisor (Report #4 review).

4 endpoints under `/api/admin/quality/batch/{batch_id}/`:
  - trend          : story × chapter time series + per-story aggregates
  - by-dimension   : story × dimension means
  - heatmap        : chapter × dimension grid for one story
  - distribution   : composite + slop + per-dim histograms

All responses share QualityResponse envelope so the frontend can
render a consistent "data-ready / loading / empty" state.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean, pstdev, pvariance
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_settings
from backend.config import Settings
from backend.quality import RUBRIC_VERSION, DETECTOR_VERSION, DIMENSIONS

router = APIRouter()


# --- Response envelope ---

class QualityResponse(BaseModel):
    """Common envelope for all quality dashboard endpoints."""
    batch_id: int
    rubric_version: str
    detector_version: str
    judge_model: str
    generated_at: str
    data_ready: bool
    reason: str | None = None
    data: dict | None = None


# --- Aggregation helpers ---

def _slope(xs: list[float], ys: list[float]) -> float:
    """Linear regression slope of ys over xs (least-squares)."""
    if len(xs) < 2:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def _half_half_delta(values: list[float]) -> tuple[float, float, float]:
    """Return (first_half_mean, second_half_mean, delta)."""
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0
    half = n // 2
    first = values[:half]
    second = values[-half:] if n % 2 == 0 else values[half + 1:]
    if not first or not second:
        return 0.0, 0.0, 0.0
    fm = mean(first)
    sm = mean(second)
    return fm, sm, sm - fm


def _stat_block(values: list[float], precision: int = 4) -> dict[str, float]:
    """Mean / variance / stdev / min / max — used in every aggregate."""
    if not values:
        return {"mean": 0.0, "variance": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(mean(values), precision),
        "variance": round(pvariance(values), precision),
        "stdev": round(pstdev(values), precision),
        "min": round(min(values), precision),
        "max": round(max(values), precision),
    }


# --- Batch-level helpers ---

async def _get_batch_meta(db_path: str, batch_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM evaluation_batches WHERE id = ?", (batch_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def _coverage_check(db_path: str, batch_id: int,
                          scope_chapter_count: int) -> dict:
    """Compute coverage stats vs scope_chapter_count for readiness gating.

    Per Report #5 review §"AC5 Readiness Must Validate Completeness":
    a batch is data_ready only when its child rows match scope.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM chapter_quality_evaluations WHERE evaluation_batch_id = ?",
            (batch_id,),
        )
        n_evals = (await cur.fetchone())["n"]
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM chapter_quality_scores WHERE evaluation_batch_id = ?",
            (batch_id,),
        )
        n_scores = (await cur.fetchone())["n"]
    expected_scores = scope_chapter_count * len(DIMENSIONS)
    return {
        "scope_chapter_count": scope_chapter_count,
        "n_evaluations": n_evals,
        "n_scores": n_scores,
        "expected_scores": expected_scores,
        "evaluations_complete": n_evals == scope_chapter_count and scope_chapter_count > 0,
        "scores_complete": n_scores == expected_scores and expected_scores > 0,
    }


def _envelope(batch_meta: dict, data_ready: bool,
              data: Any | None = None, reason: str | None = None) -> dict:
    return {
        "batch_id": batch_meta["id"],
        "rubric_version": batch_meta.get("rubric_version", RUBRIC_VERSION),
        "detector_version": batch_meta.get("detector_version", DETECTOR_VERSION),
        "judge_model": batch_meta.get("judge_model", "unknown"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_ready": data_ready,
        "reason": reason,
        "data": data,
    }


# --- Endpoint 1: trend (story × chapter) ---

@router.get("/batch/{batch_id}/trend")
async def get_trend(batch_id: int, settings: Settings = Depends(get_settings)) -> dict:
    """Story × chapter trend with per-story aggregates."""
    meta = await _get_batch_meta(settings.sqlite_path, batch_id)
    if not meta:
        raise HTTPException(404, f"batch {batch_id} not found")

    cov = await _coverage_check(settings.sqlite_path, batch_id, meta["scope_chapter_count"])
    if not cov["evaluations_complete"]:
        return _envelope(meta, data_ready=False,
                         reason=(f"trend requires complete coverage: "
                                 f"chapter_quality_evaluations={cov['n_evaluations']} "
                                 f"!= scope_chapter_count={cov['scope_chapter_count']}"))

    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT story_id, chapter_num, composite_score, mean_quality,
                   slop_penalty, word_count
            FROM chapter_quality_evaluations
            WHERE evaluation_batch_id = ?
            ORDER BY story_id, chapter_num
            """,
            (batch_id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        # story titles
        cur2 = await db.execute("SELECT id, title FROM stories")
        titles = {r["id"]: r["title"] for r in await cur2.fetchall()}

    by_story: dict[str, list[dict]] = {}
    for r in rows:
        by_story.setdefault(r["story_id"], []).append(r)

    stories_payload = []
    for sid in sorted(by_story.keys()):
        recs = sorted(by_story[sid], key=lambda r: r["chapter_num"])
        comps = [r["composite_score"] for r in recs]
        chs = [r["chapter_num"] for r in recs]
        first_m, second_m, delta = _half_half_delta(comps)
        comp_block = _stat_block(comps)
        comp_block["slope_per_chapter"] = round(_slope(chs, comps), 4)
        comp_block["first_half_mean"] = round(first_m, 4)
        comp_block["second_half_mean"] = round(second_m, 4)
        comp_block["delta"] = round(delta, 4)
        stories_payload.append({
            "story_id": sid,
            "story_title": titles.get(sid, ""),
            "n_chapters": len(recs),
            "chapters": [
                {
                    "chapter_num": r["chapter_num"],
                    "word_count": r["word_count"],
                    "composite_score": round(r["composite_score"], 4),
                    "mean_quality": round(r["mean_quality"], 4),
                    "slop_penalty": round(r["slop_penalty"], 4),
                }
                for r in recs
            ],
            "aggregates": {
                "composite": comp_block,
                "mean_quality": _stat_block([r["mean_quality"] for r in recs]),
                "slop_penalty": _stat_block([r["slop_penalty"] for r in recs]),
                "word_count": _stat_block([float(r["word_count"]) for r in recs]),
            },
        })

    return _envelope(meta, data_ready=True, data={"stories": stories_payload})


# --- Endpoint 2: by-dimension (story × dim mean) ---

@router.get("/batch/{batch_id}/by-dimension")
async def get_by_dimension(batch_id: int,
                           settings: Settings = Depends(get_settings)) -> dict:
    """Per-story × per-dimension means + global aggregate."""
    meta = await _get_batch_meta(settings.sqlite_path, batch_id)
    if not meta:
        raise HTTPException(404, f"batch {batch_id} not found")

    cov = await _coverage_check(settings.sqlite_path, batch_id, meta["scope_chapter_count"])
    if not cov["scores_complete"]:
        return _envelope(meta, data_ready=False,
                         reason=(f"by-dimension requires complete coverage: "
                                 f"chapter_quality_scores={cov['n_scores']} "
                                 f"!= expected={cov['expected_scores']} "
                                 f"(scope_chapter_count={cov['scope_chapter_count']} × {len(DIMENSIONS)} dims)"))

    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT story_id, dimension, score
            FROM chapter_quality_scores
            WHERE evaluation_batch_id = ?
            """,
            (batch_id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        cur2 = await db.execute("SELECT id, title FROM stories")
        titles = {r["id"]: r["title"] for r in await cur2.fetchall()}

    # group: story → dim → [scores]
    grouped: dict[str, dict[str, list[float]]] = {}
    global_grouped: dict[str, list[float]] = {}
    for r in rows:
        grouped.setdefault(r["story_id"], {}).setdefault(r["dimension"], []).append(r["score"])
        global_grouped.setdefault(r["dimension"], []).append(r["score"])

    def _build(story_id: str, story_title: str, dim_to_scores: dict[str, list[float]]) -> dict:
        n_chapters = max((len(v) for v in dim_to_scores.values()), default=0)
        return {
            "story_id": story_id,
            "story_title": story_title,
            "n_chapters": n_chapters,
            "scores": {dim: _stat_block(dim_to_scores.get(dim, [])) for dim in DIMENSIONS},
        }

    per_story = [
        _build(sid, titles.get(sid, ""), grouped[sid])
        for sid in sorted(grouped.keys())
    ]
    global_block = _build("ALL", "全部小说", global_grouped)

    return _envelope(meta, data_ready=True, data={
        "dimensions": DIMENSIONS,
        "per_story": per_story,
        "global": global_block,
    })


# --- Endpoint 3: heatmap (chapter × dim for one story) ---

@router.get("/batch/{batch_id}/heatmap")
async def get_heatmap(batch_id: int, story_id: str,
                      settings: Settings = Depends(get_settings)) -> dict:
    """Chapter × dimension matrix for a single story."""
    meta = await _get_batch_meta(settings.sqlite_path, batch_id)
    if not meta:
        raise HTTPException(404, f"batch {batch_id} not found")

    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        # Fetch SCORES (granular) and EXPECTED CHAPTERS (from evaluations).
        # Per Report #6 review §"AC5 heatmap readiness misses whole missing
        # chapters": readiness must be derived from the evaluations table,
        # NOT from the score-table-observed chapter list, otherwise a chapter
        # whose 8 score rows are entirely missing simply disappears from
        # `chapters` and incompleteness goes undetected.
        cur = await db.execute(
            """
            SELECT chapter_num
            FROM chapter_quality_evaluations
            WHERE evaluation_batch_id = ? AND story_id = ?
            ORDER BY chapter_num
            """,
            (batch_id, story_id),
        )
        expected_chapters = [r["chapter_num"] for r in await cur.fetchall()]
        cur = await db.execute(
            """
            SELECT chapter_num, dimension, score, evidence
            FROM chapter_quality_scores
            WHERE evaluation_batch_id = ? AND story_id = ?
            ORDER BY chapter_num
            """,
            (batch_id, story_id),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        cur2 = await db.execute(
            "SELECT title FROM stories WHERE id = ?", (story_id,)
        )
        title_row = await cur2.fetchone()
        story_title = title_row["title"] if title_row else ""

    if not expected_chapters:
        return _envelope(meta, data_ready=False,
                         reason=(f"heatmap requires evaluations for story {story_id} in batch {batch_id}; "
                                 f"chapter_quality_evaluations has 0 rows for that pair"))

    # Build chapter × dim grouping (only for chapters that have at least one score row)
    by_chapter: dict[int, dict[str, dict]] = {}
    for r in rows:
        by_chapter.setdefault(r["chapter_num"], {})[r["dimension"]] = {
            "score": r["score"], "evidence": r.get("evidence") or "",
        }

    # Completeness: every EXPECTED chapter must have all DIMENSIONS scores.
    missing_chapters: list[int] = []  # chapter present in evaluations but absent from scores entirely
    incomplete_chapters: dict[int, list[str]] = {}  # chapter present but missing some dims
    for c in expected_chapters:
        dims_for_c = by_chapter.get(c, {})
        if not dims_for_c:
            missing_chapters.append(c)
            continue
        missing_dims = [d for d in DIMENSIONS if d not in dims_for_c]
        if missing_dims:
            incomplete_chapters[c] = missing_dims
    if missing_chapters or incomplete_chapters:
        parts = []
        if missing_chapters:
            preview = missing_chapters[:5]
            parts.append(
                f"{len(missing_chapters)} chapter(s) entirely absent from scores: "
                f"{preview}{'+' if len(missing_chapters) > 5 else ''}"
            )
        if incomplete_chapters:
            preview = list(incomplete_chapters.items())[:3]
            parts.append(
                f"{len(incomplete_chapters)} chapter(s) missing dims: "
                f"{[(c, dims) for c, dims in preview]}"
                f"{'+' if len(incomplete_chapters) > 3 else ''}"
            )
        return _envelope(meta, data_ready=False,
                         reason=(f"heatmap requires every expected chapter "
                                 f"(from chapter_quality_evaluations) to have all "
                                 f"{len(DIMENSIONS)} dimensions in chapter_quality_scores; "
                                 + "; ".join(parts)))

    chapters = expected_chapters  # use the authoritative chapter list
    matrix = [
        [round(by_chapter[c][d]["score"], 4) for d in DIMENSIONS]
        for c in chapters
    ]
    evidence = {
        str(c): {d: by_chapter[c][d]["evidence"] for d in DIMENSIONS}
        for c in chapters
    }

    return _envelope(meta, data_ready=True, data={
        "story_id": story_id,
        "story_title": story_title,
        "dimensions": DIMENSIONS,
        "chapters": chapters,
        "matrix": matrix,
        "meta": {"score_range": [0, 10], "color_scheme_hint": "RdYlGn"},
        "evidence": evidence,
    })


# --- Endpoint 4: distribution (histograms) ---

def _histogram(values: list[float], bin_low: float, bin_high: float,
               n_bins: int) -> list[dict]:
    """Build n_bins-bucket histogram over [bin_low, bin_high]."""
    if not values:
        return []
    width = (bin_high - bin_low) / n_bins
    counts = [0] * n_bins
    for v in values:
        if v < bin_low:
            counts[0] += 1
        elif v >= bin_high:
            counts[-1] += 1
        else:
            idx = min(n_bins - 1, int((v - bin_low) / width))
            counts[idx] += 1
    return [
        {
            "bin_low": round(bin_low + i * width, 4),
            "bin_high": round(bin_low + (i + 1) * width, 4),
            "count": counts[i],
        }
        for i in range(n_bins)
    ]


@router.get("/batch/{batch_id}/distribution")
async def get_distribution(batch_id: int,
                           settings: Settings = Depends(get_settings)) -> dict:
    """Composite + slop + per-dimension histograms."""
    meta = await _get_batch_meta(settings.sqlite_path, batch_id)
    if not meta:
        raise HTTPException(404, f"batch {batch_id} not found")

    cov = await _coverage_check(settings.sqlite_path, batch_id, meta["scope_chapter_count"])
    # Per Report #6 review §"AC5 distribution readiness ignores score-table
    # completeness": per_dimension_histograms come from chapter_quality_scores,
    # so we MUST gate both evaluations_complete and scores_complete.
    if not (cov["evaluations_complete"] and cov["scores_complete"]):
        gaps = []
        if not cov["evaluations_complete"]:
            gaps.append(f"chapter_quality_evaluations={cov['n_evaluations']} "
                        f"!= scope_chapter_count={cov['scope_chapter_count']}")
        if not cov["scores_complete"]:
            gaps.append(f"chapter_quality_scores={cov['n_scores']} "
                        f"!= expected={cov['expected_scores']} "
                        f"({cov['scope_chapter_count']} × {len(DIMENSIONS)} dims)")
        return _envelope(meta, data_ready=False,
                         reason="distribution requires complete coverage of BOTH "
                                "evaluations and scores tables: " + "; ".join(gaps))

    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT composite_score, slop_penalty, story_id
            FROM chapter_quality_evaluations
            WHERE evaluation_batch_id = ?
            """,
            (batch_id,),
        )
        eval_rows = [dict(r) for r in await cur.fetchall()]
        cur2 = await db.execute(
            """
            SELECT dimension, score
            FROM chapter_quality_scores
            WHERE evaluation_batch_id = ?
            """,
            (batch_id,),
        )
        score_rows = [dict(r) for r in await cur2.fetchall()]

    composites = [r["composite_score"] for r in eval_rows]
    slops = [r["slop_penalty"] for r in eval_rows]
    by_dim: dict[str, list[float]] = {}
    for r in score_rows:
        by_dim.setdefault(r["dimension"], []).append(r["score"])

    return _envelope(meta, data_ready=True, data={
        "composite_histogram": _histogram(composites, 0.0, 10.0, 20),
        "slop_histogram": _histogram(slops, 0.0, 3.0, 12),
        "per_dimension_histograms": {
            dim: _histogram(by_dim.get(dim, []), 0.0, 10.0, 20)
            for dim in DIMENSIONS
        },
        "totals": {
            "n_chapters": len(eval_rows),
            "n_stories": len({r["story_id"] for r in eval_rows}),
        },
    })


# --- Listing helpers (utility) ---

@router.get("/batches")
async def list_batches(settings: Settings = Depends(get_settings)) -> dict:
    """List all evaluation batches (most recent first)."""
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT id, batch_label, rubric_version, detector_version,
                   judge_model, scope_chapter_count, status,
                   started_at, finished_at
            FROM evaluation_batches
            ORDER BY started_at DESC
            """
        )
        return {"batches": [dict(r) for r in await cur.fetchall()]}
