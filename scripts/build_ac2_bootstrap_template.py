"""AC2-bootstrap step 1: build a blind template for engineer self-rating.

Picks 5 chapters spanning the composite-score range from a batch (excluding
the AC2-final candidate which must remain independent). Outputs a JSON
template containing chapter text + 8 empty score slots per chapter.
LLM scores are NOT included in the template — engineer rates blind.

After filling, run:
    python scripts/compute_ac2_bootstrap.py --template <filled.json>

Usage:
    python scripts/build_ac2_bootstrap_template.py --batch 2 \\
        --exclude bc910038:1 \\
        --out data/baselines/ac2-bootstrap-template-batch-2.json
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DIMENSIONS = [
    "fluency",
    "dialogue_distinct",
    "character_consistency",
    "scene_drama",
    "sensory_detail",
    "rhetoric_quality",
    "continuity",
    "overall_readability",
]

DIM_DESCRIPTIONS = {
    "fluency": "语言流畅度（句法自然 / 不生硬 / 中文语感）",
    "dialogue_distinct": "对白独特性（不同角色说话有区分度）",
    "character_consistency": "角色一致性（行为符合人设）",
    "scene_drama": "场景戏剧性（冲突 / 张力 / 转折）",
    "sensory_detail": "感官描写（视觉 / 听觉 / 触觉具体）",
    "rhetoric_quality": "修辞质量（不烂用比喻 / 不堆套话）",
    "continuity": "跨场景衔接（前后逻辑通顺）",
    "overall_readability": "整体可读性（综合判断）",
}


def pick_chapters(con: sqlite3.Connection, batch_id: int,
                  exclude: set[tuple[str, int]], n: int = 5) -> list[dict]:
    """Pick n chapters spanning composite-score quartiles, excluding given pairs."""
    cur = con.cursor()
    cur.execute(
        """
        SELECT story_id, chapter_num, composite_score, mean_quality, slop_penalty, word_count
        FROM chapter_quality_evaluations
        WHERE evaluation_batch_id = ?
        ORDER BY composite_score ASC
        """,
        (batch_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    rows = [r for r in rows if (r["story_id"], r["chapter_num"]) not in exclude]
    if not rows:
        raise RuntimeError(f"no eligible chapters for batch {batch_id}")

    n_total = len(rows)
    if n_total <= n:
        return rows

    # pick at quartile boundaries: 0%, 25%, 50%, 75%, 100%
    indices = [round(i * (n_total - 1) / (n - 1)) for i in range(n)]
    return [rows[i] for i in indices]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--db", default="data/story.db")
    parser.add_argument("--exclude", action="append", default=[],
                        help="story_id:chapter_num to exclude (repeatable)")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    exclude: set[tuple[str, int]] = set()
    for token in args.exclude:
        sid, ch = token.split(":")
        exclude.add((sid, int(ch)))

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    chapters_meta = pick_chapters(con, args.batch, exclude, args.n)

    template = {
        "schema_version": "ac2-bootstrap-v1",
        "purpose": "engineer self-rates 5 chapters blind to LLM scores; supplied scores joined later via compute_ac2_bootstrap.py",
        "batch_id": args.batch,
        "n_chapters": len(chapters_meta),
        "rubric": {
            "dimensions": DIMENSIONS,
            "scale": "1-10 integer",
            "descriptions": DIM_DESCRIPTIONS,
        },
        "instructions": (
            "Read each chapter.text and fill engineer_scores for all 8 dimensions (1-10). "
            "Optionally include engineer_evidence (per-dim brief reason). "
            "DO NOT look at chapter_quality_dim_evals in the DB before filling. "
            "Once all 5 chapters are filled, run compute_ac2_bootstrap.py."
        ),
        "chapters": [],
    }

    cur = con.cursor()
    for meta in chapters_meta:
        story_id = meta["story_id"]
        ch_num = meta["chapter_num"]
        cur.execute(
            "SELECT title, content FROM chapters WHERE story_id=? AND chapter_num=?",
            (story_id, ch_num),
        )
        row = cur.fetchone()
        title = row["title"] if row else ""
        text = row["content"] if row else ""
        template["chapters"].append({
            "story_id": story_id,
            "chapter_num": ch_num,
            "title": title,
            "word_count": meta["word_count"],
            "text": text,
            "engineer_scores": {dim: None for dim in DIMENSIONS},
            "engineer_evidence": {dim: "" for dim in DIMENSIONS},
            "engineer_overall_note": "",
        })
    con.close()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote template: {out_path}")
    print(f"Chapters selected (spanning composite quartiles, excluded {sorted(exclude)}):")
    for ch in template["chapters"]:
        print(f"  {ch['story_id']}/ch{ch['chapter_num']}  ({ch['word_count']} words)")
    print()
    print("Next step:")
    print("  1. fill engineer_scores for each chapter (read chapter.text first)")
    print("  2. run: python scripts/compute_ac2_bootstrap.py --template", out_path)


if __name__ == "__main__":
    main()
