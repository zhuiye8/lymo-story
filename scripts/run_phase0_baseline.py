"""Phase 0 baseline offline runner.

Per supervisor greenlight (workspace/decisions/2026-04-26-phase-0-greenlight.md):
- Every run creates a new evaluation_batch_id
- Writes per-dim scores, aggregate evaluations, slop findings, judge runs
- Only target: build SEQR v0 baseline; do not touch chapter generation pipeline.

Usage:
    DEEPSEEK_API_KEY=sk-... \
    python scripts/run_phase0_baseline.py [--story-id <id>] [--limit N] [--label <batch_label>] [--judge <model>]

Examples:
    python scripts/run_phase0_baseline.py --all-stories --label phase0-baseline-2026-04-27
    python scripts/run_phase0_baseline.py --story-id 61513478 --limit 1   # smoke test 1 chapter
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiosqlite

from backend.quality import RUBRIC_VERSION, DETECTOR_VERSION
from backend.quality.batch import create_batch, finish_batch, batch_summary
from backend.quality.composite import composite_score
from backend.quality.seqr_judge import SEQRJudge
from backend.quality.slop_detector import SlopDetector


# ----- pricing for cost tracking (CNY/M tokens; matches deepseek provider PRESETS) -----
PRICING = {
    "deepseek/deepseek-v4-flash": {"input": 1.0, "output": 2.0},
    "deepseek/deepseek-v4-pro":   {"input": 12.0, "output": 24.0},
    "deepseek/deepseek-chat":     {"input": 2.0, "output": 8.0},
}


def _get_pricing(model: str) -> tuple[float, float]:
    p = PRICING.get(model) or {}
    return p.get("input", 0.0), p.get("output", 0.0)


async def list_chapters(db_path: str, story_id: str | None = None) -> list[dict]:
    """List (story_id, chapter_num, content) for evaluation."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        if story_id:
            cur = await db.execute(
                "SELECT story_id, chapter_num, title, content, length(content) AS word_count "
                "FROM chapters WHERE story_id = ? ORDER BY chapter_num",
                (story_id,),
            )
        else:
            cur = await db.execute(
                "SELECT story_id, chapter_num, title, content, length(content) AS word_count "
                "FROM chapters ORDER BY story_id, chapter_num"
            )
        return [dict(r) for r in await cur.fetchall()]


async def get_live_version_id(db_path: str, story_id: str, chapter_num: int) -> int | None:
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT id FROM chapter_versions WHERE story_id = ? AND chapter_num = ? AND is_live = 1",
            (story_id, chapter_num),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def load_bible(json_store_dir: str, story_id: str) -> dict | None:
    p = Path(json_store_dir) / story_id / "story_bible.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


async def evaluate_one_chapter(
    db_path: str,
    batch_id: int,
    judge: SEQRJudge,
    detector: SlopDetector,
    chapter: dict,
    bible: dict | None,
) -> dict:
    """Evaluate one chapter and persist all rows. Returns summary."""
    story_id = chapter["story_id"]
    chapter_num = chapter["chapter_num"]
    content = chapter["content"]
    version_id = await get_live_version_id(db_path, story_id, chapter_num)
    started_at = datetime.now(timezone.utc).isoformat()

    # 1. LLM judge
    print(f"  [judge] story={story_id} ch={chapter_num} ({len(content)} chars)... ", end="", flush=True)
    t0 = time.time()
    result = await judge.evaluate(content, bible=bible)
    judge_ms = int((time.time() - t0) * 1000)
    if result["error"]:
        print(f"ERR: {result['error'][:80]}")
        return {"ok": False, "error": result["error"], "story_id": story_id, "chapter_num": chapter_num}
    print(f"{judge_ms}ms CNY{result['cost_cny']:.4f} mean_score={sum(result['scores'].values())/8:.2f}")

    # 2. Slop detector
    findings = detector.detect(content)
    slop_penalty = SlopDetector.total_penalty(findings)

    # 3. Composite
    comp = composite_score(result["scores"], slop_penalty)

    # 4. Persist
    finished_at = datetime.now(timezone.utc).isoformat()
    judged_at = finished_at
    options_json = json.dumps(
        {"thinking": judge.thinking} if judge.thinking else {}, ensure_ascii=False
    )

    async with aiosqlite.connect(db_path) as db:
        # judge_runs
        cur = await db.execute(
            """INSERT INTO judge_runs
               (evaluation_batch_id, story_id, chapter_num, judge_model, judge_options_json,
                rubric_version, total_input_tokens, total_output_tokens,
                total_cost_cny, latency_ms, status, started_at, finished_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', ?, ?)""",
            (
                batch_id, story_id, chapter_num, judge.judge_model, options_json,
                RUBRIC_VERSION, result["input_tokens"], result["output_tokens"],
                result["cost_cny"], result["latency_ms"], started_at, finished_at,
            ),
        )
        judge_run_id = cur.lastrowid
        # chapter_quality_scores (8 dims)
        for dim, score in result["scores"].items():
            evidence = result["evidence"].get(dim, "")
            await db.execute(
                """INSERT INTO chapter_quality_scores
                   (evaluation_batch_id, story_id, chapter_num, source_version_id,
                    dimension, score, evidence, judge_run_id, judged_at, rubric_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (batch_id, story_id, chapter_num, version_id,
                 dim, score, evidence, judge_run_id, judged_at, RUBRIC_VERSION),
            )
        # chapter_quality_evaluations (1 row aggregate)
        await db.execute(
            """INSERT INTO chapter_quality_evaluations
               (evaluation_batch_id, story_id, chapter_num, source_version_id,
                rubric_version, judge_run_id, composite_score, mean_quality,
                slop_penalty, word_count, judged_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (batch_id, story_id, chapter_num, version_id,
             RUBRIC_VERSION, judge_run_id, comp["composite_score"], comp["mean_quality"],
             comp["slop_penalty"], chapter["word_count"], judged_at),
        )
        # slop_findings (variable rows)
        for f in findings:
            await db.execute(
                """INSERT INTO slop_findings
                   (evaluation_batch_id, story_id, chapter_num, source_version_id,
                    category, hits_json, raw_score, weighted_penalty, detected_at, detector_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (batch_id, story_id, chapter_num, version_id,
                 f.category, json.dumps(f.hits, ensure_ascii=False),
                 f.raw_score, f.weighted_penalty, judged_at, DETECTOR_VERSION),
            )
        await db.commit()

    return {
        "ok": True,
        "story_id": story_id,
        "chapter_num": chapter_num,
        "mean_quality": comp["mean_quality"],
        "slop_penalty": comp["slop_penalty"],
        "composite": comp["composite_score"],
        "cost_cny": result["cost_cny"],
        "tokens": (result["input_tokens"], result["output_tokens"]),
        "latency_ms": result["latency_ms"],
        "slop_findings": len(findings),
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/story.db")
    parser.add_argument("--json-store-dir", default="data/stories")
    parser.add_argument("--story-id", default=None, help="Single story (default: all)")
    parser.add_argument("--all-stories", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limit chapters (0=no limit)")
    parser.add_argument("--label", default=None, help="batch_label (default: phase0-baseline-<ts>)")
    parser.add_argument("--description", default="Phase 0 baseline run")
    parser.add_argument("--judge", default="deepseek/deepseek-v4-pro",
                        help="Judge model (litellm format)")
    parser.add_argument("--thinking", default="disabled",
                        choices=["enabled", "disabled", "none"],
                        help="DeepSeek thinking mode (default: disabled per supervisor)")
    parser.add_argument("--api-key", default=None, help="Override env DEEPSEEK_API_KEY")
    parser.add_argument("--api-base", default=None)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--cost-warn", type=float, default=15.0,
                        help="Total CNY cost warning threshold (per phase-gate Cost Bound)")
    parser.add_argument("--cost-stop", type=float, default=30.0,
                        help="Total CNY cost stop threshold")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("ERROR: DEEPSEEK_API_KEY env var or --api-key required")

    # gather chapters
    chapters = await list_chapters(args.db, story_id=args.story_id)
    if args.limit > 0:
        chapters = chapters[: args.limit]
    if not chapters:
        sys.exit("ERROR: no chapters found")
    story_ids = sorted(set(c["story_id"] for c in chapters))

    # batch label
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_label = args.label or f"phase0-baseline-{ts}"

    # set up judge + detector
    cost_in, cost_out = _get_pricing(args.judge)
    thinking = None if args.thinking == "none" else args.thinking
    judge = SEQRJudge(
        judge_model=args.judge,
        api_key=api_key,
        api_base=args.api_base,
        thinking=thinking,
        cost_per_million_input=cost_in,
        cost_per_million_output=cost_out,
        max_tokens=args.max_tokens,
    )
    detector = SlopDetector()

    print(f"=== Phase 0 baseline runner ===")
    print(f"DB:           {args.db}")
    print(f"Batch label:  {batch_label}")
    print(f"Judge model:  {judge.judge_model} (thinking={thinking})")
    print(f"Pricing:      input CNY{cost_in}/M, output CNY{cost_out}/M")
    print(f"Stories:      {story_ids}")
    print(f"Chapters:     {len(chapters)}")
    print(f"Cost stop:    CNY{args.cost_stop}")
    print()

    batch_id = await create_batch(
        db_path=args.db,
        batch_label=batch_label,
        judge_model=judge.judge_model,
        judge_options={"thinking": thinking} if thinking else {},
        description=args.description,
        scope_story_ids=story_ids,
        scope_chapter_count=len(chapters),
    )
    print(f"Created batch_id={batch_id}")
    print()

    # iterate
    results: list[dict] = []
    total_cost = 0.0
    failures = 0
    for i, ch in enumerate(chapters, start=1):
        # bible per story
        bible = await load_bible(args.json_store_dir, ch["story_id"])
        print(f"[{i}/{len(chapters)}]", end=" ")
        r = await evaluate_one_chapter(args.db, batch_id, judge, detector, ch, bible)
        results.append(r)
        if r.get("ok"):
            total_cost += r["cost_cny"]
        else:
            failures += 1

        # cost guard
        if total_cost >= args.cost_stop:
            print(f"\n!! cost stop triggered: CNY{total_cost:.4f} >= CNY{args.cost_stop}; aborting")
            await finish_batch(args.db, batch_id, status="aborted")
            break
        if total_cost >= args.cost_warn and i % 5 == 0:
            print(f"   (cost so far: CNY{total_cost:.4f}, warn @ CNY{args.cost_warn})")

    else:
        await finish_batch(args.db, batch_id, status="completed")

    # summary
    print()
    summary = await batch_summary(args.db, batch_id)
    print("=== Batch summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print()
    print(f"Total cost: CNY{total_cost:.4f}, failures: {failures}/{len(chapters)}")
    print(f"AC1 pass:  {summary['ac1_pass']}  ({summary['scores_count']} / {summary['scope_chapter_count']*8})")
    print(f"AC1b pass: {summary['ac1b_pass']} ({summary['evaluations_count']} / {summary['scope_chapter_count']})")
    print(f"AC4 pass:  {summary['ac4_pass']}  (mean_cost CNY{summary['mean_cost_cny']:.4f} / ceiling CNY0.10)")


if __name__ == "__main__":
    asyncio.run(main())
