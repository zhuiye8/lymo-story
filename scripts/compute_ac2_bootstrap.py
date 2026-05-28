"""AC2-bootstrap step 2: compute per-dimension Spearman ρ between engineer
self-ratings and LLM judge scores.

Input:
    --template <filled engineer-scored JSON> (from build_ac2_bootstrap_template.py)
    --db <story.db>

Output:
    Per-dimension ρ (engineer rank vs LLM rank across the n chapters)
    Per-chapter side-by-side score table
    Optional --out JSON with full result

Spearman ρ is computed manually (stdlib only): rank both vectors with
average ranks for ties, then Pearson on ranks. With n=5 chapters
the metric is noisy; this is an internal sanity check, not a phase gate.
"""
import argparse
import json
import math
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


def average_ranks(values: list[float]) -> list[float]:
    """Return average ranks (1-based) with ties broken by mean."""
    indexed = sorted(enumerate(values), key=lambda kv: kv[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return float("nan")
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))


def fetch_llm_scores(con: sqlite3.Connection, batch_id: int,
                     story_id: str, chapter_num: int) -> dict[str, float]:
    cur = con.cursor()
    cur.execute(
        """
        SELECT dimension, score
        FROM chapter_quality_scores
        WHERE evaluation_batch_id = ?
          AND story_id = ?
          AND chapter_num = ?
        """,
        (batch_id, story_id, chapter_num),
    )
    return {r[0]: float(r[1]) for r in cur.fetchall()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True,
                        help="filled JSON from build_ac2_bootstrap_template.py")
    parser.add_argument("--db", default="data/story.db")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    template = json.loads(Path(args.template).read_text(encoding="utf-8"))
    batch_id = template["batch_id"]
    chapters = template["chapters"]

    # validate fill
    missing = []
    for ch in chapters:
        for dim in DIMENSIONS:
            v = ch["engineer_scores"].get(dim)
            if v is None or not isinstance(v, (int, float)):
                missing.append(f"{ch['story_id']}/ch{ch['chapter_num']}:{dim}")
    if missing:
        print(f"ERROR: {len(missing)} unfilled scores:", file=sys.stderr)
        for m in missing[:20]:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    # collect LLM scores per chapter
    enriched: list[dict] = []
    for ch in chapters:
        llm = fetch_llm_scores(con, batch_id, ch["story_id"], ch["chapter_num"])
        enriched.append({
            "story_id": ch["story_id"],
            "chapter_num": ch["chapter_num"],
            "engineer_scores": ch["engineer_scores"],
            "llm_scores": llm,
        })
    con.close()

    # per-dim Spearman across the n chapters
    per_dim = {}
    for dim in DIMENSIONS:
        eng = [c["engineer_scores"][dim] for c in enriched]
        llm = [c["llm_scores"].get(dim) for c in enriched]
        if any(v is None for v in llm):
            per_dim[dim] = {"rho": None, "note": "missing LLM score for some chapters"}
            continue
        rho = spearman(eng, llm)
        per_dim[dim] = {
            "rho": round(rho, 4) if not math.isnan(rho) else None,
            "engineer_mean": round(sum(eng) / len(eng), 3),
            "llm_mean": round(sum(llm) / len(llm), 3),
            "engineer_values": eng,
            "llm_values": llm,
        }

    # aggregate scalar: mean of rhos that aren't None/nan
    valid_rhos = [d["rho"] for d in per_dim.values()
                  if d.get("rho") is not None]
    mean_rho = round(sum(valid_rhos) / len(valid_rhos), 4) if valid_rhos else None

    result = {
        "schema_version": "ac2-bootstrap-result-v1",
        "batch_id": batch_id,
        "n_chapters": len(enriched),
        "n_dimensions": len(DIMENSIONS),
        "chapters": [{"story_id": e["story_id"], "chapter_num": e["chapter_num"]} for e in enriched],
        "per_dimension_spearman": per_dim,
        "mean_spearman_rho": mean_rho,
        "interpretation": (
            "ρ > 0.7: strong agreement; "
            "0.4-0.7: moderate; "
            "0.0-0.4: weak; "
            "< 0: inverse — judge rubric likely misaligned with engineer intuition. "
            "n=5 makes ρ noisy (one swap drastically changes rank correlation); "
            "treat as direction-of-agreement signal, not a precise metric."
        ),
        "raw_chapters": enriched,
    }

    # console table
    print("=" * 80)
    print(f"AC2-bootstrap Spearman ρ (batch {batch_id}, n={len(enriched)} chapters)")
    print("=" * 80)
    print(f"{'dim':<24} {'eng_mean':>9} {'llm_mean':>9} {'ρ':>8}  values (eng | llm)")
    print("-" * 80)
    for dim in DIMENSIONS:
        d = per_dim[dim]
        if d.get("rho") is None:
            print(f"{dim:<24} {'-':>9} {'-':>9} {'N/A':>8}  {d.get('note','')}")
        else:
            eng_str = ",".join(f"{v:g}" for v in d["engineer_values"])
            llm_str = ",".join(f"{v:g}" for v in d["llm_values"])
            print(f"{dim:<24} {d['engineer_mean']:>9.3f} {d['llm_mean']:>9.3f} "
                  f"{d['rho']:>8.4f}  {eng_str} | {llm_str}")
    print("-" * 80)
    if mean_rho is not None:
        print(f"mean Spearman ρ across {len(valid_rhos)} dims = {mean_rho:.4f}")
    print()
    print(result["interpretation"])

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\nWrote: {args.out}")


if __name__ == "__main__":
    main()
