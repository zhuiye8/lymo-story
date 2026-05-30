"""质量仪表盘 API（Phase 1 重写，按 story 存，无 batch 概念）。

依据 phase1/00-architecture.md §7。
端点（4 图表 + 列表）：
  GET /stories                          有质量数据的故事列表
  GET /story/{story_id}/trend           per-chapter composite/quality/slop 趋势 + 聚合
  GET /story/{story_id}/by-dimension    per-chapter × 8 维（雷达/对比）
  GET /story/{story_id}/heatmap         chapter × dimension 网格
  GET /story/{story_id}/distribution    composite + slop 直方图

数据来自新 schema：chapter_quality_evaluations / chapter_quality_scores / slop_findings
（均按 story_id + chapter_num 存，save_quality 写入）。
"""
from __future__ import annotations

from statistics import mean, pstdev, pvariance

import aiosqlite
from fastapi import APIRouter, Depends

from backend.deps import get_settings
from backend.config import Settings
from backend.quality import DIMENSIONS, DIMENSION_LABELS_ZH, RUBRIC_VERSION

router = APIRouter()


def _slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def _half_half_delta(values: list[float]) -> tuple[float, float, float]:
    """算法 A：对称排除中位（与 baseline_report 一致；偶数对半，奇数排中间）。"""
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0
    half = n // 2
    first = values[:half]
    second = values[-half:] if n % 2 == 0 else values[half + 1:]
    return mean(first), mean(second), mean(second) - mean(first)


def _stat(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "variance": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(mean(values), 4), "variance": round(pvariance(values), 4),
        "stdev": round(pstdev(values), 4), "min": round(min(values), 4), "max": round(max(values), 4),
    }


def _histogram(values: list[float], lo: float, hi: float, n_bins: int) -> list[dict]:
    if not values:
        return []
    width = (hi - lo) / n_bins
    counts = [0] * n_bins
    for v in values:
        idx = min(n_bins - 1, max(0, int((v - lo) / width)))
        counts[idx] += 1
    return [{"bin_low": round(lo + i * width, 3), "bin_high": round(lo + (i + 1) * width, 3), "count": c}
            for i, c in enumerate(counts)]


@router.get("/stories")
async def list_quality_stories(settings: Settings = Depends(get_settings)) -> dict:
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT e.story_id, s.title, COUNT(*) AS n_chapters,
                      ROUND(AVG(e.composite_score),3) AS avg_composite
               FROM chapter_quality_evaluations e
               LEFT JOIN stories s ON s.id = e.story_id
               GROUP BY e.story_id ORDER BY n_chapters DESC""")
        return {"stories": [dict(r) for r in await cur.fetchall()]}


async def _evals(db_path: str, story_id: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chapter_num, composite_score, mean_quality, slop_penalty, word_count "
            "FROM chapter_quality_evaluations WHERE story_id = ? ORDER BY chapter_num", (story_id,))
        return [dict(r) for r in await cur.fetchall()]


@router.get("/story/{story_id}/trend")
async def get_trend(story_id: str, settings: Settings = Depends(get_settings)) -> dict:
    rows = await _evals(settings.sqlite_path, story_id)
    if not rows:
        return {"story_id": story_id, "rubric_version": RUBRIC_VERSION, "data_ready": False,
                "reason": "无质量数据", "data": None}
    comps = [r["composite_score"] for r in rows]
    chs = [r["chapter_num"] for r in rows]
    fm, sm, delta = _half_half_delta(comps)
    comp_stat = _stat(comps)
    comp_stat.update({"slope_per_chapter": round(_slope(chs, comps), 4),
                      "first_half_mean": round(fm, 4), "second_half_mean": round(sm, 4),
                      "delta": round(delta, 4)})
    return {
        "story_id": story_id, "rubric_version": RUBRIC_VERSION, "data_ready": True, "reason": None,
        "data": {
            "chapters": [{"chapter_num": r["chapter_num"], "composite_score": round(r["composite_score"], 4),
                          "mean_quality": round(r["mean_quality"], 4), "slop_penalty": round(r["slop_penalty"], 4),
                          "word_count": r["word_count"]} for r in rows],
            "aggregates": {"composite": comp_stat,
                           "mean_quality": _stat([r["mean_quality"] for r in rows]),
                           "slop_penalty": _stat([r["slop_penalty"] for r in rows]),
                           "word_count": _stat([float(r["word_count"]) for r in rows])},
        },
    }


@router.get("/story/{story_id}/by-dimension")
async def get_by_dimension(story_id: str, settings: Settings = Depends(get_settings)) -> dict:
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chapter_num, dimension, score FROM chapter_quality_scores "
            "WHERE story_id = ? ORDER BY chapter_num", (story_id,))
        rows = [dict(r) for r in await cur.fetchall()]
    if not rows:
        return {"story_id": story_id, "data_ready": False, "reason": "无评分数据", "data": None}
    by_dim: dict[str, list[float]] = {}
    for r in rows:
        by_dim.setdefault(r["dimension"], []).append(r["score"])
    return {
        "story_id": story_id, "data_ready": True, "reason": None,
        "data": {
            "dimensions": DIMENSIONS,
            "labels": DIMENSION_LABELS_ZH,
            "per_dimension": {d: _stat(by_dim.get(d, [])) for d in DIMENSIONS},
        },
    }


@router.get("/story/{story_id}/heatmap")
async def get_heatmap(story_id: str, settings: Settings = Depends(get_settings)) -> dict:
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chapter_num, dimension, score FROM chapter_quality_scores "
            "WHERE story_id = ? ORDER BY chapter_num", (story_id,))
        rows = [dict(r) for r in await cur.fetchall()]
    if not rows:
        return {"story_id": story_id, "data_ready": False, "reason": "无评分数据", "data": None}
    by_ch: dict[int, dict[str, float]] = {}
    for r in rows:
        by_ch.setdefault(r["chapter_num"], {})[r["dimension"]] = r["score"]
    chapters = sorted(by_ch.keys())
    matrix = [[round(by_ch[c].get(d, 0.0), 3) for d in DIMENSIONS] for c in chapters]
    return {
        "story_id": story_id, "data_ready": True, "reason": None,
        "data": {"chapters": chapters, "dimensions": DIMENSIONS, "labels": DIMENSION_LABELS_ZH,
                 "matrix": matrix, "meta": {"score_range": [0, 10], "color_scheme_hint": "RdYlGn"}},
    }


@router.get("/story/{story_id}/distribution")
async def get_distribution(story_id: str, settings: Settings = Depends(get_settings)) -> dict:
    rows = await _evals(settings.sqlite_path, story_id)
    if not rows:
        return {"story_id": story_id, "data_ready": False, "reason": "无质量数据", "data": None}
    comps = [r["composite_score"] for r in rows]
    slops = [r["slop_penalty"] for r in rows]
    return {
        "story_id": story_id, "data_ready": True, "reason": None,
        "data": {
            "composite_histogram": _histogram(comps, 0.0, 10.0, 20),
            "slop_histogram": _histogram(slops, 0.0, 3.0, 12),
            "totals": {"n_chapters": len(rows)},
        },
    }
