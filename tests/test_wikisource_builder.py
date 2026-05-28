"""Regression tests for `scripts/build_wikisource_pd_corpus.py`.

Per Report #7 review:
  - builder must fail hard on partial fetch (no silent partial drafts)
  - builder --merge must preserve stable IDs by source_url

These tests don't hit the live wikisource. They exercise the in-process
helpers (BuildResult, merge_into_corpus) directly, plus the CLI's
fail-hard exit by mocking build_drafts().

Run: pytest tests/test_wikisource_builder.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts/ to path so we can import the builder module
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))


@pytest.fixture
def builder_module():
    """Import build_wikisource_pd_corpus fresh per test (resets module-level state)."""
    import importlib
    if "build_wikisource_pd_corpus" in sys.modules:
        return importlib.reload(sys.modules["build_wikisource_pd_corpus"])
    return importlib.import_module("build_wikisource_pd_corpus")


# --- BuildResult contract ---

class TestBuildResult:
    def test_complete_is_true_when_all_targets_drafted(self, builder_module):
        r = builder_module.BuildResult()
        for au, dy, wk, url in builder_module.TARGETS:
            r.drafts.append({
                "author": au, "work": wk, "source_url": url,
                "author_death_year": dy, "pd_in_china_since": dy + 50,
                "verification_status": "wikisource_html_extracted_and_trad2simp_converted",
                "fetch_at": "2026-04-27T00:00:00Z",
                "_raw_traditional": "原文",
                "text": "原文",
                "_text_len": 2,
            })
        assert r.is_complete
        assert r.n_drafts == r.n_total_targets

    def test_complete_is_false_when_any_target_missing(self, builder_module):
        r = builder_module.BuildResult()
        # leave one target out
        for au, dy, wk, url in builder_module.TARGETS[:-1]:
            r.drafts.append({"source_url": url})
        assert not r.is_complete
        assert r.n_drafts == r.n_total_targets - 1

    def test_summary_lists_failures_and_no_paragraph(self, builder_module):
        r = builder_module.BuildResult()
        r.fetch_failures.append(("鲁迅", "《X》", "https://example/X", "URLError: timeout"))
        r.no_paragraph.append(("朱自清", "《Y》", "https://example/Y"))
        s = r.summary()
        assert "fetch failures (1)" in s
        assert "鲁迅" in s and "《X》" in s and "URLError" in s
        assert "no eligible paragraph (1)" in s
        assert "朱自清" in s and "《Y》" in s


# --- merge_into_corpus ID stability ---

@pytest.fixture
def synthetic_corpus_with_pd(tmp_path, builder_module):
    """Build a corpus file matching the live schema with a few existing PD entries.

    Existing IDs are intentionally non-sequential to verify the algorithm uses
    the URL → id map rather than position.
    """
    existing_pd = [
        {
            "id": "normal_pd_001",
            "source_url": "https://example.test/keep1",
            "source_type": "public_domain_excerpt",
            "author": "Author A", "work": "《W1》",
            "author_death_year": 1948, "pd_in_china_since": 1998,
            "verification_status": "wikisource_html_extracted_and_trad2simp_converted",
            "fetch_at": "2026-04-01T00:00:00Z",
            "_raw_traditional": "old1", "text": "旧文 1",
            "accepted_by": "x", "accepted_at": "2026-04-01",
            "subdomain_tag": "minguo_canonical_wikisource",
        },
        {
            "id": "normal_pd_007",  # gap to test next-free logic
            "source_url": "https://example.test/keep7",
            "source_type": "public_domain_excerpt",
            "author": "Author B", "work": "《W2》",
            "author_death_year": 1936, "pd_in_china_since": 1986,
            "verification_status": "wikisource_html_extracted_and_trad2simp_converted",
            "fetch_at": "2026-04-01T00:00:00Z",
            "_raw_traditional": "old7", "text": "旧文 7",
            "accepted_by": "x", "accepted_at": "2026-04-01",
            "subdomain_tag": "minguo_canonical_wikisource",
        },
    ]
    synthetic = [
        {"id": f"normal_f_{i:03d}", "source_type": "engineer_synthetic",
         "text": f"合成 {i}"}
        for i in range(1, 4)
    ]
    corpus = {
        "schema": {
            "version": "v5-ac3-wikisource-pd",
            "target_size": {"normal_fiction": 5},
            "current_size": {"normal_fiction": 5},
        },
        "slop": [],
        "normal_generic": [],
        "normal_fiction": synthetic + existing_pd,
    }
    corpus_path = tmp_path / "slop_samples_zh.json"
    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    builder_module.CORPUS_PATH = corpus_path
    return corpus_path


class TestMergeIDStability:
    def _draft(self, url: str, author: str = "Test", work: str = "《T》",
               text: str = "新文") -> dict:
        return {
            "author": author, "work": work, "source_url": url,
            "author_death_year": 1948, "pd_in_china_since": 1998,
            "verification_status": "wikisource_html_extracted_and_trad2simp_converted",
            "fetch_at": "2026-04-27T00:00:00Z",
            "_raw_traditional": text + "_trad", "text": text,
            "_text_len": len(text),
        }

    def test_existing_url_keeps_its_id(self, builder_module, synthetic_corpus_with_pd):
        """A draft with a URL that already has an ID must reuse that ID."""
        drafts = [
            self._draft("https://example.test/keep1", text="REFRESH 1"),
            self._draft("https://example.test/keep7", text="REFRESH 7"),
        ]
        result = builder_module.merge_into_corpus(drafts)
        pd_entries = [s for s in result["normal_fiction"]
                      if s["source_type"] == "public_domain_excerpt"]
        url_to_id = {s["source_url"]: s["id"] for s in pd_entries}
        assert url_to_id["https://example.test/keep1"] == "normal_pd_001"
        assert url_to_id["https://example.test/keep7"] == "normal_pd_007"
        # text was refreshed
        assert next(s for s in pd_entries
                    if s["source_url"] == "https://example.test/keep1")["text"] == "REFRESH 1"

    def test_new_url_gets_next_free_id(self, builder_module, synthetic_corpus_with_pd):
        """A new URL gets a fresh id starting from max(existing)+1."""
        drafts = [
            self._draft("https://example.test/keep1"),     # preserved
            self._draft("https://example.test/keep7"),     # preserved
            self._draft("https://example.test/new_a"),     # new
            self._draft("https://example.test/new_b"),     # new
        ]
        result = builder_module.merge_into_corpus(drafts)
        pd_entries = sorted(
            [s for s in result["normal_fiction"]
             if s["source_type"] == "public_domain_excerpt"],
            key=lambda s: s["id"]
        )
        url_to_id = {s["source_url"]: s["id"] for s in pd_entries}
        # max existing is 007, so new ids start at 008
        assert url_to_id["https://example.test/new_a"] == "normal_pd_008"
        assert url_to_id["https://example.test/new_b"] == "normal_pd_009"
        # existing IDs untouched
        assert url_to_id["https://example.test/keep1"] == "normal_pd_001"
        assert url_to_id["https://example.test/keep7"] == "normal_pd_007"

    def test_engineer_synthetic_entries_unchanged(self, builder_module,
                                                   synthetic_corpus_with_pd):
        """merge_into_corpus must not perturb engineer_synthetic entries."""
        drafts = [self._draft("https://example.test/keep1")]
        result = builder_module.merge_into_corpus(drafts)
        synth = [s for s in result["normal_fiction"]
                 if s["source_type"] == "engineer_synthetic"]
        assert len(synth) == 3
        assert {s["id"] for s in synth} == {"normal_f_001", "normal_f_002", "normal_f_003"}

    def test_id_stability_metadata_recorded(self, builder_module,
                                             synthetic_corpus_with_pd):
        """The schema metadata records preserved/newly-assigned counts so audit
        is possible without diffing the full corpus."""
        drafts = [
            self._draft("https://example.test/keep1"),     # preserved
            self._draft("https://example.test/new_a"),     # new
        ]
        result = builder_module.merge_into_corpus(drafts)
        meta = result["schema"]["provenance_summary_v5"]["id_stability"]
        assert meta["preserved"] == 1
        assert meta["newly_assigned"] == 1
        assert ("normal_pd_008", "https://example.test/new_a") in [
            tuple(p) for p in meta["newly_assigned_pairs"]
        ]


# --- CLI fail-hard behaviour ---

class TestCLIFailHard:
    """Spawn the builder with mocked build_drafts() to verify CLI exit codes
    on partial fetch."""

    def _run(self, *args: str, mock_drafts_returns,
             cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run the builder via a wrapper script that injects a fake build_drafts.

        cwd defaults to the repo root, but tests that care about the draft
        file's location should pass an explicit cwd (a tmp_path) so the
        relative DRAFT_PATH lands inside the test sandbox.
        """
        scripts_dir = (_REPO / "scripts").as_posix()
        driver = f"""
import sys
sys.path.insert(0, {scripts_dir!r})
import build_wikisource_pd_corpus as B

class FakeResult:
    def __init__(self, n_drafts, n_total):
        self.drafts = [{{
            'author': 'A', 'work': 'W', 'source_url': f'https://example.test/{{i}}',
            'author_death_year': 1948, 'pd_in_china_since': 1998,
            'verification_status': 'wikisource_html_extracted_and_trad2simp_converted',
            'fetch_at': '2026-04-27T00:00:00Z',
            '_raw_traditional': 'x', 'text': 'x', '_text_len': 1,
        }} for i in range(n_drafts)]
        self.fetch_failures = []
        self.no_paragraph = []
        self._n_total = n_total
    @property
    def n_total_targets(self): return self._n_total
    @property
    def n_drafts(self): return len(self.drafts)
    @property
    def is_complete(self): return self.n_drafts == self.n_total_targets
    def summary(self): return f'fake {{self.n_drafts}}/{{self._n_total}}'

n_drafts, n_total = {mock_drafts_returns}
B.build_drafts = lambda: FakeResult(n_drafts, n_total)
B.main()
"""
        return subprocess.run(
            [sys.executable, "-c", driver, *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(cwd if cwd is not None else _REPO),
        )

    def test_complete_fetch_exits_zero(self, tmp_path):
        (tmp_path / "data" / "baselines").mkdir(parents=True)
        r = self._run(mock_drafts_returns=(3, 3), cwd=tmp_path)
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_partial_fetch_without_flag_exits_nonzero(self, tmp_path):
        """Partial fetch without --allow-partial → exit 1, no draft written."""
        (tmp_path / "data" / "baselines").mkdir(parents=True)
        r = self._run(mock_drafts_returns=(2, 3), cwd=tmp_path)
        assert r.returncode != 0
        assert "only 2/3" in (r.stderr + r.stdout)
        draft = tmp_path / "data" / "baselines" / "_pd_excerpts_draft.json"
        assert not draft.exists(), "partial fetch must not write canonical draft"

    def test_partial_fetch_with_allow_partial_writes_draft(self, tmp_path):
        """With --allow-partial, partial draft is written for inspection."""
        (tmp_path / "data" / "baselines").mkdir(parents=True)
        r = self._run("--allow-partial", mock_drafts_returns=(2, 3), cwd=tmp_path)
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
        draft = tmp_path / "data" / "baselines" / "_pd_excerpts_draft.json"
        assert draft.exists()
        payload = json.loads(draft.read_text(encoding="utf-8"))
        assert payload["_meta"]["complete"] is False
        assert payload["_meta"]["n_drafts"] == 2
        assert payload["_meta"]["n_targets"] == 3

    def test_merge_with_allow_partial_is_rejected(self, tmp_path):
        """--merge --allow-partial combo is forbidden upfront."""
        (tmp_path / "data" / "baselines").mkdir(parents=True)
        r = self._run("--merge", "--allow-partial",
                      mock_drafts_returns=(2, 3), cwd=tmp_path)
        assert r.returncode != 0
        assert "cannot be combined" in (r.stderr + r.stdout)
