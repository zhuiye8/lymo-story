"""Reproducible builder for source-verifiable public-domain Chinese fiction
samples used as in-domain stress negatives for the slop-detector AC3 calibration.

Per Report #6 review §"opencc decision":
    > Either commit a reproducible Wikisource sample builder script and add
    > opencc-python-reimplemented to dev deps, or document that
    > slop_samples_zh.json is a static audited corpus.

This script is the committed builder (path 1). Run it to regenerate the
`normal_fiction_pd_excerpt` portion of `data/baselines/slop_samples_zh.json`
from zh.wikisource.org. It is idempotent — a second run produces the same
text given Wikisource hasn't changed.

Strategy:
  1. Hard-coded list of (author, work, URL) targets — known PD authors
     (China copyright = author death + 50y; cutoff = current year - 50).
  2. urllib.request fetch + minimal regex HTML parsing (extract <p>...</p>).
  3. Skip nav/footer paragraphs heuristically (keyword filter).
  4. Pick first paragraph in [50, 280] chars.
  5. opencc t2s convert traditional→simplified.
  6. Each output entry carries source_url, fetch_at, _raw_traditional,
     and verification_status="wikisource_html_extracted_and_trad2simp_converted"
     so the supervisor can independently click every URL and re-derive the
     simplified text.

Usage:
    python scripts/build_wikisource_pd_corpus.py
        # writes data/baselines/_pd_excerpts_draft.json (draft, for inspection)

    python scripts/build_wikisource_pd_corpus.py --merge
        # also merges into data/baselines/slop_samples_zh.json normal_fiction
        # (replaces existing normal_pd_* entries; preserves engineer_synthetic)

Required dev dep: opencc-python-reimplemented (pyproject.toml [optional-dependencies] dev)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import opencc  # type: ignore
except ImportError:
    print("ERROR: opencc-python-reimplemented not installed.\n"
          "Install with: pip install -e \".[dev]\"  (or)  pip install opencc-python-reimplemented",
          file=sys.stderr)
    sys.exit(2)

CC_T2S = opencc.OpenCC("t2s")

DRAFT_PATH = Path("data/baselines/_pd_excerpts_draft.json")
CORPUS_PATH = Path("data/baselines/slop_samples_zh.json")

# (author, death_year, work, url)
# Death-year decides PD-in-China (author death + 50 years).
# As of 2026: anyone deceased <= 1975 is public domain.
TARGETS: list[tuple[str, int, str, str]] = [
    # 朱自清 (1898-1948, PD since 1998)
    ("朱自清", 1948, "《背影》",
     "https://zh.wikisource.org/wiki/%E8%83%8C%E5%BD%B1"),
    ("朱自清", 1948, "《荷塘月色》",
     "https://zh.wikisource.org/wiki/%E8%8D%B7%E5%A1%98%E6%9C%88%E8%89%B2"),
    ("朱自清", 1948, "《匆匆》",
     "https://zh.wikisource.org/wiki/%E5%8C%86%E5%8C%86"),
    ("朱自清", 1948, "《春》",
     "https://zh.wikisource.org/wiki/%E6%98%A5_(%E6%9C%B1%E8%87%AA%E6%B8%85)"),
    ("朱自清", 1948, "《歌聲》",
     "https://zh.wikisource.org/wiki/%E6%AD%8C%E8%81%B2"),
    # 鲁迅 (1881-1936, PD since 1986)
    ("鲁迅", 1936, "《故鄉》",
     "https://zh.wikisource.org/wiki/%E6%95%85%E9%84%89"),
    ("鲁迅", 1936, "《孔乙己》",
     "https://zh.wikisource.org/wiki/%E5%AD%94%E4%B9%99%E5%B7%B1"),
    ("鲁迅", 1936, "《社戲》",
     "https://zh.wikisource.org/wiki/%E7%A4%BE%E6%88%B2"),
    ("鲁迅", 1936, "《祝福》",
     "https://zh.wikisource.org/wiki/%E7%A5%9D%E7%A6%8F"),
    ("鲁迅", 1936, "《從百草園到三味書屋》",
     "https://zh.wikisource.org/wiki/%E5%BE%9E%E7%99%BE%E8%8D%89%E5%9C%92%E5%88%B0%E4%B8%89%E5%91%B3%E6%9B%B8%E5%B1%8B"),
    ("鲁迅", 1936, "《藥》",
     "https://zh.wikisource.org/wiki/%E8%97%A5"),
    ("鲁迅", 1936, "《狂人日記》",
     "https://zh.wikisource.org/wiki/%E7%8B%82%E4%BA%BA%E6%97%A5%E8%A8%98"),
    ("鲁迅", 1936, "《阿長與山海經》",
     "https://zh.wikisource.org/wiki/%E9%98%BF%E9%95%B7%E8%88%87%E5%B1%B1%E6%B5%B7%E7%B6%93"),
    ("鲁迅", 1936, "《風箏》",
     "https://zh.wikisource.org/wiki/%E9%A2%A8%E7%AD%9D"),
    ("鲁迅", 1936, "《雪》",
     "https://zh.wikisource.org/wiki/%E9%9B%AA_(%E9%AD%AF%E8%BF%85)"),
    ("鲁迅", 1936, "《一件小事》",
     "https://zh.wikisource.org/wiki/%E4%B8%80%E4%BB%B6%E5%B0%8F%E4%BA%8B"),
    ("鲁迅", 1936, "《傷逝》",
     "https://zh.wikisource.org/wiki/%E5%82%B7%E9%80%9D"),
    ("鲁迅", 1936, "《好的故事》",
     "https://zh.wikisource.org/wiki/%E5%A5%BD%E7%9A%84%E6%95%85%E4%BA%8B"),
    # 胡适 (1891-1962, PD since 2012)
    ("胡适", 1962, "《差不多先生傳》",
     "https://zh.wikisource.org/wiki/%E5%B7%AE%E4%B8%8D%E5%A4%9A%E5%85%88%E7%94%9F%E5%82%B3"),
    # 林徽因 (1904-1955, PD since 2005)
    ("林徽因", 1955, "《九十九度中》",
     "https://zh.wikisource.org/wiki/%E4%B9%9D%E5%8D%81%E4%B9%9D%E5%BA%A6%E4%B8%AD"),
    # 蔡元培 (1868-1940, PD since 1990)
    ("蔡元培", 1940, "《就任北京大學校長之演說》",
     "https://zh.wikisource.org/wiki/%E5%B0%B1%E4%BB%BB%E5%8C%97%E4%BA%AC%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%95%B7%E4%B9%8B%E6%BC%94%E8%AA%AA"),
]

NAV_MARKERS = (
    "維基", "维基", "wikisource", "Wikisource",
    "编辑", "編輯", "本作品", "原作者",
    "公有領域", "公有领域", "PD-",
    "doi:", "ISBN", "出版", "上一頁", "上一页",
    "目录", "本作", "Author", "License",
)


def fetch_paragraphs(url: str) -> list[str]:
    """Fetch wikisource HTML and return list of <p> bodies (cleaned, traditional)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "story-engine-eval-bot/0.1"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8")
    p_blocks = re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.DOTALL)
    paragraphs: list[str] = []
    for p in p_blocks:
        text = re.sub(r"<[^>]+>", "", p)
        text = (
            text.replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#160;", " ")
            .replace("&#8203;", "")
            .replace("​", "").replace("‌", "").replace("‍", "")
            .replace("﻿", "")
        )
        text = text.strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def pick_best_paragraph(paragraphs: list[str], min_chars: int = 50,
                        max_chars: int = 280) -> Optional[str]:
    for p in paragraphs:
        if any(m in p for m in NAV_MARKERS):
            continue
        if not (min_chars <= len(p) <= max_chars):
            continue
        return p
    return None


class BuildResult:
    """Outcome of build_drafts: drafts plus diagnostic lists for fail-hard checks."""
    def __init__(self):
        self.drafts: list[dict] = []
        self.fetch_failures: list[tuple[str, str, str]] = []   # (author, work, url, error)
        self.no_paragraph: list[tuple[str, str, str]] = []     # (author, work, url)

    @property
    def n_total_targets(self) -> int:
        return len(TARGETS)

    @property
    def n_drafts(self) -> int:
        return len(self.drafts)

    @property
    def is_complete(self) -> bool:
        return self.n_drafts == self.n_total_targets

    def summary(self) -> str:
        lines = [f"build summary: {self.n_drafts}/{self.n_total_targets} drafts"]
        if self.fetch_failures:
            lines.append(f"  fetch failures ({len(self.fetch_failures)}):")
            for au, wk, url, err in self.fetch_failures:
                lines.append(f"    [FAIL] {au} {wk}: {url} -> {err}")
        if self.no_paragraph:
            lines.append(f"  no eligible paragraph ({len(self.no_paragraph)}):")
            for au, wk, url in self.no_paragraph:
                lines.append(f"    [NO-PARA] {au} {wk}: {url}")
        return "\n".join(lines)


def build_drafts() -> BuildResult:
    """Fetch + extract + convert. Returns BuildResult with drafts + diagnostics.

    NEVER raises on per-target failure; the caller decides how strict to be.
    Per Report #7 review: callers MUST gate on `result.is_complete` before
    writing canonical outputs or merging.
    """
    result = BuildResult()
    for author, dy, work, url in TARGETS:
        try:
            paras = fetch_paragraphs(url)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            print(f"[FAIL] {url}: {err}", file=sys.stderr)
            result.fetch_failures.append((author, work, url, err))
            continue
        picked = pick_best_paragraph(paras)
        if not picked:
            print(f"[NO-PARA] {author} {work}: {len(paras)} paragraphs but none in size range",
                  file=sys.stderr)
            result.no_paragraph.append((author, work, url))
            continue
        simplified = CC_T2S.convert(picked)
        result.drafts.append({
            "author": author,
            "work": work,
            "author_death_year": dy,
            "pd_in_china_since": dy + 50,
            "source_url": url,
            "verification_status": "wikisource_html_extracted_and_trad2simp_converted",
            "fetch_at": datetime.now(timezone.utc).isoformat(),
            "_raw_traditional": picked,
            "text": simplified,
            "_text_len": len(simplified),
        })
        print(f"[OK]  {author:8s} {work:<22s} {len(simplified)} chars")
        time.sleep(1.0)  # be polite to wikisource
    return result


def merge_into_corpus(drafts: list[dict]) -> dict:
    """Merge drafts into corpus, preserving stable IDs by source_url.

    Per Report #7 review §"merge must preserve stable sample IDs":
      - existing PD entries are looked up by source_url
      - matched URLs keep their existing id (text/fetch_at refresh in place)
      - new URLs (TARGETS additions) are assigned the next available id
        (max(existing) + 1, then +2, ...)

    This makes the script idempotent for stable refreshes and additive for
    growth, never silently re-IDs a sample that the supervisor already cited.
    """
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    keep_synthetic = [
        s for s in corpus["normal_fiction"]
        if s.get("source_type") == "engineer_synthetic"
    ]
    existing_pd = [
        s for s in corpus["normal_fiction"]
        if s.get("source_type") == "public_domain_excerpt"
    ]

    # url → existing id (stable identity)
    url_to_existing_id: dict[str, str] = {
        s["source_url"]: s["id"] for s in existing_pd if s.get("source_url")
    }
    # next free numeric suffix for new URLs
    used_nums = sorted({
        int(s["id"].split("_")[-1])
        for s in existing_pd
        if s.get("id", "").startswith("normal_pd_")
    })
    next_free = (max(used_nums) + 1) if used_nums else 1

    accepted_at = "2026-04-27"
    accepted_by = (
        "engineer (Claude); fetched via urllib.request from zh.wikisource.org; "
        "trad→simp via opencc t2s"
    )

    new_pd: list[dict] = []
    new_ids_assigned: list[tuple[str, str]] = []
    preserved_ids: list[tuple[str, str]] = []

    for e in drafts:
        url = e["source_url"]
        if url in url_to_existing_id:
            sid = url_to_existing_id[url]
            preserved_ids.append((sid, url))
        else:
            sid = f"normal_pd_{next_free:03d}"
            next_free += 1
            new_ids_assigned.append((sid, url))

        new_pd.append({
            "id": sid,
            "subdomain_tag": "minguo_canonical_wikisource",
            "author": e["author"],
            "work": e["work"],
            "author_death_year": e["author_death_year"],
            "pd_in_china_since": e["pd_in_china_since"],
            "source_type": "public_domain_excerpt",
            "verification_status": e["verification_status"],
            "source_url": url,
            "source_note": (
                f"{e['author']} {e['work']}; verbatim first eligible <p> from "
                f"{url}; Traditional→Simplified via opencc t2s; "
                f"supervisor can re-verify by visiting URL and inspecting the "
                f"article's first prose paragraph."
            ),
            "fetch_at": e["fetch_at"],
            "_raw_traditional": e["_raw_traditional"],
            "text": e["text"],
            "accepted_by": accepted_by,
            "accepted_at": accepted_at,
        })

    # Sort PD entries by numeric suffix to keep file ordering stable.
    new_pd.sort(key=lambda s: int(s["id"].split("_")[-1]))

    corpus["normal_fiction"] = keep_synthetic + new_pd

    schema = corpus["schema"]
    schema["version"] = "v5-ac3-wikisource-pd"
    schema["target_size"]["normal_fiction"] = len(corpus["normal_fiction"])
    schema["current_size"]["normal_fiction"] = len(corpus["normal_fiction"])
    schema.pop("provenance_summary_v3", None)
    schema.pop("provenance_summary_v4", None)
    schema["provenance_summary_v5"] = {
        "slop": "100 engineer_synthetic",
        "normal_generic": "50 engineer_synthetic",
        "normal_fiction": {
            "engineer_synthetic": len(keep_synthetic),
            "wikisource_pd_excerpt": len(new_pd),
            "total": len(corpus["normal_fiction"]),
        },
        "wikisource_authors": sorted({e["author"] for e in new_pd}),
        "wikisource_works": sorted({e["work"] for e in new_pd}),
        "id_stability": {
            "preserved": len(preserved_ids),
            "newly_assigned": len(new_ids_assigned),
            "newly_assigned_pairs": new_ids_assigned,
        },
    }

    CORPUS_PATH.write_text(json.dumps(corpus, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    # operator log
    print(f"\nID stability:")
    print(f"  preserved (matched by source_url): {len(preserved_ids)}")
    print(f"  newly assigned: {len(new_ids_assigned)}")
    for sid, url in new_ids_assigned:
        print(f"    {sid}  {url}")
    return corpus


def main():
    parser = argparse.ArgumentParser(
        description="Reproducible builder for source-verifiable wikisource PD excerpts."
    )
    parser.add_argument("--merge", action="store_true",
                        help="after fetching, merge into slop_samples_zh.json normal_fiction; "
                             "preserves existing IDs by source_url, assigns new IDs only for "
                             "newly-added URLs. NEVER allowed with partial drafts.")
    parser.add_argument("--allow-partial", action="store_true",
                        help="permit writing the draft file even when fetches fail. "
                             "Cannot be combined with --merge — partial drafts must NEVER "
                             "rewrite the canonical corpus.")
    args = parser.parse_args()

    if args.merge and args.allow_partial:
        print("ERROR: --merge cannot be combined with --allow-partial; "
              "partial drafts must not rewrite the canonical corpus.",
              file=sys.stderr)
        sys.exit(2)

    result = build_drafts()
    print()
    print(result.summary())

    # Fail-hard gate (Report #7 review §"must fail hard on partial fetch").
    if not result.is_complete and not args.allow_partial:
        print(f"\nERROR: only {result.n_drafts}/{result.n_total_targets} targets fetched. "
              f"Re-run, or pass --allow-partial to write a debug draft (which can NOT be merged).",
              file=sys.stderr)
        sys.exit(1)

    if not result.is_complete and args.allow_partial:
        print(f"\nWARNING: --allow-partial set; writing partial draft "
              f"({result.n_drafts}/{result.n_total_targets}). "
              f"This draft is for inspection only; --merge is forbidden.",
              file=sys.stderr)

    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Tag the draft with completeness so a downstream tool can detect partials.
    draft_payload = {
        "_meta": {
            "n_drafts": result.n_drafts,
            "n_targets": result.n_total_targets,
            "complete": result.is_complete,
            "fetch_failures": [
                {"author": a, "work": w, "url": u, "error": err}
                for a, w, u, err in result.fetch_failures
            ],
            "no_paragraph": [
                {"author": a, "work": w, "url": u}
                for a, w, u in result.no_paragraph
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "drafts": result.drafts,
    }
    DRAFT_PATH.write_text(json.dumps(draft_payload, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"\nWrote draft: {DRAFT_PATH} ({result.n_drafts} entries, complete={result.is_complete})")

    if args.merge:
        # Defense in depth: merge gate even though we already exited above.
        if not result.is_complete:
            print("ERROR: refusing to merge a partial draft (defensive guard).",
                  file=sys.stderr)
            sys.exit(1)
        merged = merge_into_corpus(result.drafts)
        nf = merged["normal_fiction"]
        synth = sum(1 for s in nf if s["source_type"] == "engineer_synthetic")
        pd = sum(1 for s in nf if s["source_type"] == "public_domain_excerpt")
        print(f"\nMerged into {CORPUS_PATH}:")
        print(f"  engineer_synthetic: {synth}")
        print(f"  public_domain_excerpt: {pd}")


if __name__ == "__main__":
    main()
