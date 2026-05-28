"""Build AC2-final calibration artifact for supervisor.

Per condition C2 (decisions/2026-04-26-phase-0-v2-review.md):
- AC2-final supervisor must independently rate one chapter
- Save artifact to `data/baselines/ac2-final-calibration-<batch>.json`
- Schema: chapter_id / rubric / human_scores / llm_scores / supervisor_conclusion

This script extracts LLM data from DB and writes a template the supervisor
fills in (`human_scores`, `human_evidence`, `supervisor_conclusion`,
`supervisor_notes`).

Usage:
    python scripts/build_ac2_final_artifact.py --batch 2 --story bc910038 --chapter 1
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiosqlite

from backend.quality import DIMENSIONS, RUBRIC_VERSION


async def build(batch_id: int, story_id: str, chapter_num: int, db_path: str = "data/story.db") -> dict:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # batch info
        cur = await db.execute(
            "SELECT * FROM evaluation_batches WHERE id = ?", (batch_id,)
        )
        batch = dict(await cur.fetchone() or {})

        # chapter info
        cur = await db.execute(
            "SELECT chapter_num, title, content FROM chapters WHERE story_id = ? AND chapter_num = ?",
            (story_id, chapter_num),
        )
        ch = dict(await cur.fetchone() or {})

        # LLM per-dim scores + evidence
        cur = await db.execute(
            """SELECT dimension, score, evidence
               FROM chapter_quality_scores
               WHERE evaluation_batch_id = ? AND story_id = ? AND chapter_num = ?""",
            (batch_id, story_id, chapter_num),
        )
        score_rows = [dict(r) for r in await cur.fetchall()]
        llm_scores = {r["dimension"]: r["score"] for r in score_rows}
        llm_evidence = {r["dimension"]: r["evidence"] for r in score_rows}

        # aggregate
        cur = await db.execute(
            """SELECT composite_score, mean_quality, slop_penalty, word_count, judge_run_id
               FROM chapter_quality_evaluations
               WHERE evaluation_batch_id = ? AND story_id = ? AND chapter_num = ?""",
            (batch_id, story_id, chapter_num),
        )
        agg = dict(await cur.fetchone() or {})

        # judge run
        cur = await db.execute(
            "SELECT judge_model, judge_options_json FROM judge_runs WHERE id = ?",
            (agg.get("judge_run_id") or 0,),
        )
        run = dict(await cur.fetchone() or {})

        # slop findings
        cur = await db.execute(
            """SELECT category, hits_json, weighted_penalty
               FROM slop_findings
               WHERE evaluation_batch_id = ? AND story_id = ? AND chapter_num = ?""",
            (batch_id, story_id, chapter_num),
        )
        slop_rows = []
        for r in await cur.fetchall():
            d = dict(r)
            try:
                d["hits"] = json.loads(d.pop("hits_json", "[]"))
            except Exception:
                d["hits"] = []
            slop_rows.append(d)

    return {
        "schema_version": "ac2-final-v1",
        "purpose": "Supervisor independent calibration — gate for Phase 0 SEQR-v0 rubric.",
        "batch": {
            "id": batch_id,
            "label": batch.get("batch_label"),
            "rubric_version": batch.get("rubric_version", RUBRIC_VERSION),
        },
        "chapter": {
            "story_id": story_id,
            "chapter_num": chapter_num,
            "title": ch.get("title", ""),
            "word_count": agg.get("word_count", len(ch.get("content", ""))),
            "content": ch.get("content", ""),
        },
        "judge": {
            "model": run.get("judge_model"),
            "options": json.loads(run.get("judge_options_json") or "{}"),
        },
        "rubric": {
            "version": RUBRIC_VERSION,
            "dimensions": DIMENSIONS,
            "scale": "0-10 each; 9-10 reserved for surprising work; err toward lower",
        },
        "llm_scores": llm_scores,
        "llm_evidence": llm_evidence,
        "llm_aggregate": {
            "mean_quality": agg.get("mean_quality"),
            "slop_penalty": agg.get("slop_penalty"),
            "composite_score": agg.get("composite_score"),
        },
        "slop_findings": slop_rows,
        "human_scores": {d: None for d in DIMENSIONS},
        "human_evidence": {d: "" for d in DIMENSIONS},
        "human_aggregate": {
            "mean_quality": None,
            "slop_penalty_estimate": None,
            "composite_score": None,
        },
        "supervisor_conclusion": None,
        "supervisor_notes": "",
        "calibration_outcome": {
            "is_relative_ranking_reasonable": None,
            "max_dimension_disagreement": None,
            "decision": None,
        },
        "calibrated_at": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="evaluation_batch_id")
    parser.add_argument("--story", required=True, help="story_id")
    parser.add_argument("--chapter", type=int, required=True, help="chapter_num")
    parser.add_argument("--db", default="data/story.db")
    parser.add_argument(
        "--out",
        default=None,
        help="Output path; default data/baselines/ac2-final-calibration-batch-<id>.json",
    )
    args = parser.parse_args()

    artifact = await build(args.batch, args.story, args.chapter, args.db)
    out = args.out or f"data/baselines/ac2-final-calibration-batch-{args.batch}.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote AC2-final artifact: {out}")
    print(f"  Story:     {args.story} / chapter {args.chapter}")
    print(f"  Title:     {artifact['chapter']['title']}")
    print(f"  Word count: {artifact['chapter']['word_count']}")
    print(f"  Judge:     {artifact['judge']['model']} (options={artifact['judge']['options']})")
    print(f"  LLM composite: {artifact['llm_aggregate']['composite_score']}")
    print()
    print("Supervisor: please fill the human_scores / human_evidence / supervisor_conclusion fields.")
    print("Schema reference: see workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md AC2-final row.")


if __name__ == "__main__":
    asyncio.run(main())
