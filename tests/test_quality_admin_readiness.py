"""Regression tests for AC5 endpoint readiness gates.

Per Report #6 review:
  - heatmap must reject when an entire chapter's 8 score rows are absent
    (the previous bug only checked dimensions for chapters that appeared
    in chapter_quality_scores; if a chapter had 0 score rows it silently
    fell out of the chapter list and incompleteness went undetected).
  - distribution must require BOTH evaluations_complete AND scores_complete
    (per_dimension_histograms come from the scores table).

These tests build a tiny synthetic SQLite DB so we can exercise the gates
without touching the real `data/story.db`.

Run: pytest tests/test_quality_admin_readiness.py -v
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set test env vars BEFORE importing main (Settings reads at import time)
os.environ.setdefault("STORY_LITELLM_MODEL", "test-model")
os.environ.setdefault("STORY_LITELLM_API_KEY", "test-key")


# --- DB fixture ---

DIMENSIONS = [
    "fluency", "dialogue_distinct", "character_consistency", "scene_drama",
    "sensory_detail", "rhetoric_quality", "continuity", "overall_readability",
]


def _build_synthetic_db(tmp_path: Path, *,
                        scope_chapter_count: int,
                        story_id: str,
                        eval_chapters: list[int],
                        score_chapters_dims: list[tuple[int, str]]) -> Path:
    """Create a minimal sqlite DB with the schema bits the endpoints need.

    score_chapters_dims: list of (chapter_num, dimension) pairs to insert
    into chapter_quality_scores. Omitted pairs simulate partial coverage.
    """
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE stories (
            id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE evaluation_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_label TEXT NOT NULL UNIQUE,
            rubric_version TEXT NOT NULL,
            judge_model TEXT NOT NULL,
            judge_options_json TEXT,
            detector_version TEXT NOT NULL,
            description TEXT,
            scope_story_ids TEXT NOT NULL,
            scope_chapter_count INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT
        );
        CREATE TABLE chapter_quality_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_batch_id INTEGER NOT NULL,
            story_id TEXT NOT NULL,
            chapter_num INTEGER NOT NULL,
            source_version_id INTEGER,
            rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0',
            judge_run_id INTEGER NOT NULL,
            composite_score REAL NOT NULL,
            mean_quality REAL NOT NULL,
            slop_penalty REAL NOT NULL,
            word_count INTEGER NOT NULL,
            judged_at TEXT NOT NULL
        );
        CREATE TABLE chapter_quality_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_batch_id INTEGER NOT NULL,
            story_id TEXT NOT NULL,
            chapter_num INTEGER NOT NULL,
            source_version_id INTEGER,
            dimension TEXT NOT NULL,
            score REAL NOT NULL,
            evidence TEXT,
            judge_run_id INTEGER NOT NULL,
            judged_at TEXT NOT NULL,
            rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0'
        );
        """
    )
    cur.execute("INSERT INTO stories (id, title) VALUES (?, ?)",
                (story_id, "Test Story"))
    cur.execute(
        """INSERT INTO evaluation_batches
           (batch_label, rubric_version, judge_model, detector_version,
            scope_story_ids, scope_chapter_count, started_at, status)
           VALUES (?, 'SEQR-v0', 'test-judge', 'slop-v1',
                   ?, ?, '2026-04-27T00:00:00Z', 'completed')""",
        ("test-batch", f'["{story_id}"]', scope_chapter_count),
    )
    batch_id = cur.lastrowid
    for ch in eval_chapters:
        cur.execute(
            """INSERT INTO chapter_quality_evaluations
               (evaluation_batch_id, story_id, chapter_num, judge_run_id,
                composite_score, mean_quality, slop_penalty, word_count, judged_at)
               VALUES (?, ?, ?, 1, 5.0, 6.0, 1.0, 1000, '2026-04-27T00:00:00Z')""",
            (batch_id, story_id, ch),
        )
    for ch, dim in score_chapters_dims:
        cur.execute(
            """INSERT INTO chapter_quality_scores
               (evaluation_batch_id, story_id, chapter_num, dimension, score,
                evidence, judge_run_id, judged_at)
               VALUES (?, ?, ?, ?, 7.0, 'test', 1, '2026-04-27T00:00:00Z')""",
            (batch_id, story_id, ch, dim),
        )
    con.commit()
    con.close()
    return db_path


def _client_for_db(db_path: Path) -> TestClient:
    """Build a FastAPI TestClient pointed at the synthetic DB."""
    os.environ["STORY_SQLITE_PATH"] = str(db_path)
    # re-import to pick up the new sqlite_path
    from importlib import reload
    import backend.config as cfg
    reload(cfg)
    import backend.main as main
    reload(main)
    return TestClient(main.app)


# --- heatmap regression ---

class TestHeatmapReadiness:
    def test_complete_chapter_returns_ready(self, tmp_path):
        """Sanity: 1 chapter × 8 dims fully populated → ready=true."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=1,
            story_id="story_a",
            eval_chapters=[1],
            score_chapters_dims=[(1, d) for d in DIMENSIONS],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/heatmap",
                      params={"story_id": "story_a"})
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is True, j.get("reason")
            assert j["data"]["chapters"] == [1]
            assert len(j["data"]["matrix"]) == 1
            assert len(j["data"]["matrix"][0]) == 8

    def test_chapter_entirely_missing_from_scores(self, tmp_path):
        """The Report #6 bug: ch2 has 0 score rows → endpoint must return
        ready=false (previous version silently dropped ch2 from the chapter
        list and reported the truncated 1×8 matrix as ready)."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=2,
            story_id="story_a",
            eval_chapters=[1, 2],
            # ch1 fully scored, ch2 has zero score rows
            score_chapters_dims=[(1, d) for d in DIMENSIONS],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/heatmap",
                      params={"story_id": "story_a"})
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is False
            reason = j.get("reason", "")
            assert "entirely absent" in reason or "missing" in reason
            assert "2" in reason  # the missing chapter number should be mentioned

    def test_chapter_missing_some_dims(self, tmp_path):
        """ch1 has only 7 dims (missing 'continuity') → ready=false."""
        partial = [(1, d) for d in DIMENSIONS if d != "continuity"]
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=1,
            story_id="story_a",
            eval_chapters=[1],
            score_chapters_dims=partial,
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/heatmap",
                      params={"story_id": "story_a"})
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is False
            assert "continuity" in j["reason"]

    def test_no_evaluations_for_story(self, tmp_path):
        """Story has no evaluation rows at all → ready=false with explanation."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=1,
            story_id="story_a",
            eval_chapters=[],
            score_chapters_dims=[],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/heatmap",
                      params={"story_id": "story_a"})
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is False
            assert "evaluations" in j["reason"]


# --- distribution regression ---

class TestDistributionReadiness:
    def test_evaluations_and_scores_both_complete(self, tmp_path):
        """1 chapter, 8 dims fully scored → ready=true."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=1,
            story_id="story_a",
            eval_chapters=[1],
            score_chapters_dims=[(1, d) for d in DIMENSIONS],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/distribution")
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is True, j.get("reason")
            assert j["data"]["totals"]["n_chapters"] == 1

    def test_evaluations_complete_but_scores_partial(self, tmp_path):
        """The Report #6 bug: 2 chapters in evals but only 1 chapter's worth
        of scores → distribution previously returned ready=true and would
        render a misleading per_dimension_histograms. Must now reject."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=2,
            story_id="story_a",
            eval_chapters=[1, 2],
            # only ch1 scored; ch2 missing all 8 dims
            score_chapters_dims=[(1, d) for d in DIMENSIONS],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/distribution")
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is False
            reason = j.get("reason", "")
            # both expected and actual counts should be in the reason
            assert "scores" in reason and "expected" in reason
            # expected is 2 × 8 = 16; actual is 8
            assert "16" in reason
            assert "8" in reason

    def test_evaluations_missing(self, tmp_path):
        """0 evaluations → ready=false (existing behaviour but covered here too)."""
        db_path = _build_synthetic_db(
            tmp_path,
            scope_chapter_count=1,
            story_id="story_a",
            eval_chapters=[],
            score_chapters_dims=[],
        )
        with _client_for_db(db_path) as c:
            r = c.get("/api/admin/quality/batch/1/distribution")
            assert r.status_code == 200
            j = r.json()
            assert j["data_ready"] is False
            assert "evaluations" in j["reason"]
