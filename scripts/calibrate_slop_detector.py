"""AC3 calibration: run slop_detector on labelled samples; report recall/precision.

Per phase-gate AC3:
    pass: recall >= 0.8 AND precision >= 0.7
    fail: recall < 0.5 OR precision < 0.5 → slop downgraded to optional

Decision rule: a sample is "detected as slop" if total_penalty >= THRESHOLD.
(v1 changed comparator from > to >= for clean threshold-edge semantics —
 a sample with penalty exactly equal to the threshold counts as detected.)

v2 schema (Report #2 supervisor correction): negative set is split into
  - normal_generic  : 50 daily-life prose (out-of-domain easy negatives)
  - normal_fiction  : 50 Chinese fiction prose (in-domain hard negatives)
Metrics are reported overall AND per-subdomain so we can see if precision
is inflated by the easy generic set.

Usage:
    python scripts/calibrate_slop_detector.py
    python scripts/calibrate_slop_detector.py --threshold 0.5
    python scripts/calibrate_slop_detector.py --json data/baselines/slop_samples_zh.json
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.quality.slop_detector import SlopDetector, DETECTOR_VERSION


def _score_set(detector: SlopDetector, samples: list[dict],
               threshold: float, label: str) -> dict:
    """Run detector over a list of samples, return per-set stats."""
    detected = []
    misses = []
    score_dist = []
    per_cat = defaultdict(int)
    for s in samples:
        findings = detector.detect(s["text"])
        penalty = SlopDetector.total_penalty(findings)
        score_dist.append(penalty)
        cats = [f.category for f in findings]
        is_detected = penalty >= threshold
        if is_detected:
            detected.append({"id": s.get("id"), "penalty": penalty, "categories": cats})
            for c in cats:
                per_cat[c] += 1
        else:
            misses.append({
                "id": s.get("id"),
                "text": s["text"][:80],
                "penalty": penalty,
                "categories": cats,
            })
    n = len(samples)
    return {
        "label": label,
        "n": n,
        "n_detected": len(detected),
        "n_not_detected": len(misses),
        "per_category": dict(per_cat),
        "score_distribution": {
            "mean": round(sum(score_dist) / max(1, n), 3),
            "min": min(score_dist) if score_dist else 0.0,
            "max": max(score_dist) if score_dist else 0.0,
        },
        "misses": misses[:20],
    }


def evaluate(samples_path: str, threshold: float = 0.5) -> dict:
    data = json.loads(Path(samples_path).read_text(encoding="utf-8"))

    slop_samples = data.get("slop", [])
    # v2 split; fall back to legacy "normal" key if subdomain split absent
    normal_generic = data.get("normal_generic", data.get("normal", []))
    normal_fiction = data.get("normal_fiction", [])

    # v4 provenance split inside normal_fiction (Report #4 review §AC3 final standard).
    # Split fiction into engineer_synthetic (project-internal) vs public_domain_excerpt
    # (independent non-synthetic) so we can report precision separately.
    fic_synthetic = [s for s in normal_fiction
                     if s.get("source_type") == "engineer_synthetic"]
    fic_pd = [s for s in normal_fiction
              if s.get("source_type") == "public_domain_excerpt"]
    fic_other = [s for s in normal_fiction
                 if s.get("source_type") not in ("engineer_synthetic", "public_domain_excerpt")]

    detector = SlopDetector()

    slop_stats = _score_set(detector, slop_samples, threshold, "slop")
    gen_stats = _score_set(detector, normal_generic, threshold, "normal_generic")
    fic_stats = _score_set(detector, normal_fiction, threshold, "normal_fiction")
    fic_synth_stats = _score_set(detector, fic_synthetic, threshold, "normal_fiction_synthetic")
    fic_pd_stats = _score_set(detector, fic_pd, threshold, "normal_fiction_pd_excerpt")

    tp = slop_stats["n_detected"]
    fn = slop_stats["n_not_detected"]
    fp_gen = gen_stats["n_detected"]
    tn_gen = gen_stats["n_not_detected"]
    fp_fic = fic_stats["n_detected"]
    tn_fic = fic_stats["n_not_detected"]
    fp_fic_synth = fic_synth_stats["n_detected"]
    fp_fic_pd = fic_pd_stats["n_detected"]
    fp_total = fp_gen + fp_fic
    tn_total = tn_gen + tn_fic

    recall = tp / max(1, slop_stats["n"])
    precision_overall = tp / (tp + fp_total) if (tp + fp_total) else 0.0
    precision_generic = tp / (tp + fp_gen) if (tp + fp_gen) else 0.0
    precision_fiction = tp / (tp + fp_fic) if (tp + fp_fic) else 0.0
    # provenance-split (Report #4 §AC3 final standard)
    precision_fiction_synthetic = (
        tp / (tp + fp_fic_synth) if (tp + fp_fic_synth) else 0.0
    )
    precision_fiction_pd = (
        tp / (tp + fp_fic_pd) if (tp + fp_fic_pd) else 0.0
    ) if fic_pd_stats["n"] > 0 else None
    n_total = slop_stats["n"] + gen_stats["n"] + fic_stats["n"]
    accuracy = (tp + tn_total) / max(1, n_total)
    f1 = (2 * recall * precision_overall / (recall + precision_overall)
          if (recall + precision_overall) else 0.0)

    # v0 misclassified-slop list — surface FN samples for debugging
    misclassified_slop = slop_stats["misses"]
    # FP samples merged across subdomains
    misclassified_normal = (
        [{"subdomain": "generic", **m} for m in gen_stats["misses"] if m["penalty"] >= threshold]
        + [{"subdomain": "fiction", **m} for m in fic_stats["misses"] if m["penalty"] >= threshold]
    )
    # actually misses from each set means below-threshold; FPs are ones we DID detect.
    # Re-derive: misclassified_normal should be detected ones in the normal sets.
    # Since _score_set stores detected-list with no text excerpt, build separately.
    fp_records = []
    for s in normal_generic:
        f = detector.detect(s["text"])
        p = SlopDetector.total_penalty(f)
        if p >= threshold:
            fp_records.append({
                "subdomain": "generic", "id": s.get("id"),
                "text": s["text"][:80], "penalty": p,
                "categories": [x.category for x in f],
            })
    for s in normal_fiction:
        f = detector.detect(s["text"])
        p = SlopDetector.total_penalty(f)
        if p >= threshold:
            fp_records.append({
                "subdomain": "fiction", "id": s.get("id"),
                "text": s["text"][:80], "penalty": p,
                "categories": [x.category for x in f],
            })

    return {
        "samples_path": samples_path,
        "detector_version": DETECTOR_VERSION,
        "threshold": threshold,
        "n_slop": slop_stats["n"],
        "n_normal_generic": gen_stats["n"],
        "n_normal_fiction": fic_stats["n"],
        "n_normal_fiction_synthetic": fic_synth_stats["n"],
        "n_normal_fiction_pd_excerpt": fic_pd_stats["n"],
        "n_normal_fiction_other": len(fic_other),
        "tp": tp, "fn": fn,
        "fp_generic": fp_gen, "tn_generic": tn_gen,
        "fp_fiction": fp_fic, "tn_fiction": tn_fic,
        "fp_fiction_synthetic": fp_fic_synth,
        "fp_fiction_pd_excerpt": fp_fic_pd,
        "fp_total": fp_total, "tn_total": tn_total,
        "recall": round(recall, 4),
        "precision_overall": round(precision_overall, 4),
        "precision_generic": round(precision_generic, 4),
        "precision_fiction": round(precision_fiction, 4),
        "precision_fiction_synthetic": round(precision_fiction_synthetic, 4),
        "precision_fiction_pd_excerpt": (round(precision_fiction_pd, 4)
                                          if precision_fiction_pd is not None else None),
        "accuracy": round(accuracy, 4),
        "f1": round(f1, 4),
        "per_set_stats": {
            "slop": slop_stats,
            "normal_generic": gen_stats,
            "normal_fiction": fic_stats,
            "normal_fiction_synthetic": fic_synth_stats,
            "normal_fiction_pd_excerpt": fic_pd_stats,
        },
        "misclassified_slop": misclassified_slop,
        "false_positives": fp_records,
        # AC3 gate (uses overall precision; both subdomains contribute)
        "ac3_pass": recall >= 0.8 and precision_overall >= 0.7,
        "ac3_fail_threshold": recall < 0.5 or precision_overall < 0.5,
        # In-domain stress: a stricter view
        "ac3_pass_fiction_only": (recall >= 0.8 and precision_fiction >= 0.7
                                  if fic_stats["n"] > 0 else None),
        # Independence stress (Report #4 §AC3 final standard):
        # PD excerpt precision must independently meet the 0.7 bar.
        "ac3_pass_pd_excerpt": (
            recall >= 0.8 and precision_fiction_pd >= 0.7
            if precision_fiction_pd is not None else None
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="data/baselines/slop_samples_zh.json")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="penalty >= threshold counts as detected as slop")
    parser.add_argument("--out", default=None,
                        help="optional JSON output file")
    args = parser.parse_args()

    result = evaluate(args.json, threshold=args.threshold)

    print(f"=== Slop calibration ({args.json}, detector={result['detector_version']}, threshold={args.threshold}) ===")
    print(f"slop samples:                      {result['n_slop']}")
    print(f"normal_generic samples:            {result['n_normal_generic']}")
    print(f"normal_fiction (total):            {result['n_normal_fiction']}")
    print(f"  └─ engineer_synthetic:           {result['n_normal_fiction_synthetic']}")
    print(f"  └─ public_domain_excerpt:        {result['n_normal_fiction_pd_excerpt']}")
    print()
    print(f"  TP={result['tp']}  FN={result['fn']}")
    print(f"  generic       FP/TN = {result['fp_generic']}/{result['tn_generic']}")
    print(f"  fic_synthetic FP/TN = {result['fp_fiction_synthetic']}/{result['n_normal_fiction_synthetic'] - result['fp_fiction_synthetic']}")
    print(f"  fic_pd        FP/TN = {result['fp_fiction_pd_excerpt']}/{result['n_normal_fiction_pd_excerpt'] - result['fp_fiction_pd_excerpt']}")
    print(f"  total         FP/TN = {result['fp_total']}/{result['tn_total']}")
    print()
    print(f"  recall                       = {result['recall']:.4f}  (AC3 pass >= 0.8)")
    print(f"  precision overall            = {result['precision_overall']:.4f}  (AC3 pass >= 0.7)")
    print(f"  precision generic            = {result['precision_generic']:.4f}  (out-of-domain ref)")
    print(f"  precision fiction            = {result['precision_fiction']:.4f}  (in-domain mixed)")
    print(f"  precision fic_synthetic      = {result['precision_fiction_synthetic']:.4f}  (project-internal)")
    pd_p = result['precision_fiction_pd_excerpt']
    pd_p_str = f"{pd_p:.4f}" if pd_p is not None else "N/A"
    print(f"  precision fic_pd_excerpt     = {pd_p_str}  (independent non-synthetic)")
    print(f"  f1 (overall)                 = {result['f1']:.4f}")
    print(f"  accuracy                     = {result['accuracy']:.4f}")
    print()
    print(f"  AC3 PASS (overall):                       {result['ac3_pass']}")
    print(f"  AC3 PASS (fiction-mixed):                 {result['ac3_pass_fiction_only']}")
    print(f"  AC3 PASS (pd_excerpt only, independent):  {result['ac3_pass_pd_excerpt']}")
    print(f"  AC3 FAIL THRESHOLD:                       {result['ac3_fail_threshold']}")
    print()
    print("Score distribution:")
    for label in ("slop", "normal_generic", "normal_fiction"):
        s = result["per_set_stats"][label]["score_distribution"]
        print(f"  {label:18s} mean={s['mean']:.3f}  range={s['min']}-{s['max']}")
    print()
    if result["misclassified_slop"]:
        print("Slop missed (first 5):")
        for m in result["misclassified_slop"][:5]:
            print(f"  {m['id']}: penalty={m['penalty']:.3f} cats={m['categories']}")
    if result["false_positives"]:
        print(f"\nNormal false-positives (n={len(result['false_positives'])}, first 5):")
        for m in result["false_positives"][:5]:
            print(f"  [{m['subdomain']}] {m['id']}: penalty={m['penalty']:.3f} cats={m['categories']}")
    else:
        print("\nNo false positives in either subdomain.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\nWrote: {args.out}")


if __name__ == "__main__":
    main()
