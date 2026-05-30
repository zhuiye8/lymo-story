"""Slop 检测器（Phase 1 重写）。

设计依据 phase1/00-architecture.md §5.1。

相对 Phase 0 的改动：
  1. 词表外置到 slop_lexicon_zh.py（本文件只做检测逻辑）。
  2. tier1 烂喻改频次感知（FREQ_SENSITIVE，同段 ≥2 才计）。
  3. 输出 flagged_spans（带字符 offset），供 Step 6 的 prefix/FIM 局部重写精确定位。
  4. 可选接收 logprobs，标记"模型高自信吐出的低熵套话"（slop 往往高频低熵）。

输出 SlopReport：
  - findings: 每类的命中明细
  - penalty: 0~3 的总扣分（喂 SEQR composite）
  - flagged_spans: [(start, end, category, text), ...] 供局部重写

DETECTOR_VERSION 是单一真源，backend.quality 从这里 re-export。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean, stdev

from backend.quality.slop_lexicon_zh import (
    ALWAYS_BANNED,
    FREQ_SENSITIVE,
    FREQ_THRESHOLD,
    TIER2_SUSPICIOUS,
    CLUSTER_THRESHOLD,
    FICTION_TELLS,
    STRUCTURAL,
    TELLING,
    CATEGORY_WEIGHTS,
    TOTAL_PENALTY_CAP,
    LEXICON_VERSION,
)

DETECTOR_VERSION = "slop-p1"  # Phase 1 detector


@dataclass
class FlaggedSpan:
    start: int          # 字符 offset（在原文中）
    end: int
    category: str
    text: str           # 命中的子串


@dataclass
class SlopFinding:
    category: str
    hits: list[str] = field(default_factory=list)
    raw_score: float = 0.0
    weighted_penalty: float = 0.0


@dataclass
class SlopReport:
    findings: list[SlopFinding] = field(default_factory=list)
    penalty: float = 0.0
    flagged_spans: list[FlaggedSpan] = field(default_factory=list)
    lexicon_version: str = LEXICON_VERSION
    detector_version: str = DETECTOR_VERSION


def _split_sentences_zh(text: str) -> list[str]:
    parts = re.split(r"[。！？.!?]", text)
    return [p.strip() for p in parts if p.strip()]


def _paragraph_spans(text: str) -> list[tuple[int, int, str]]:
    """返回 [(start, end, para_text), ...]，offset 是在原文中的字符位置。"""
    spans: list[tuple[int, int, str]] = []
    pos = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            start = text.find(stripped, pos)
            if start < 0:
                start = pos
            spans.append((start, start + len(stripped), stripped))
        pos += len(line) + 1
    return spans


class SlopDetector:
    """Phase 1 slop 检测器。频次感知 + flagged_spans。"""

    def detect(self, text: str) -> SlopReport:
        findings: list[SlopFinding] = []
        spans: list[FlaggedSpan] = []

        # ---- ALWAYS_BANNED：任意一次即计 ----
        ab_hits: list[str] = []
        for w in ALWAYS_BANNED:
            for m in re.finditer(re.escape(w), text):
                ab_hits.append(m.group(0))
                spans.append(FlaggedSpan(m.start(), m.end(), "always_banned", m.group(0)))
        if ab_hits:
            findings.append(self._mk("always_banned", ab_hits))

        # ---- FREQ_SENSITIVE：同段 ≥ 阈值才计；只计超出阈值的次数 ----
        fs_hits: list[str] = []
        for (p_start, _p_end, para) in _paragraph_spans(text):
            for w in FREQ_SENSITIVE:
                occ = [m for m in re.finditer(re.escape(w), para)]
                if len(occ) >= FREQ_THRESHOLD:
                    # 超阈值部分计 slop（前 FREQ_THRESHOLD-1 次视为合法修辞）
                    for m in occ[FREQ_THRESHOLD - 1:]:
                        fs_hits.append(w)
                        gs = p_start + m.start()
                        spans.append(FlaggedSpan(gs, gs + len(w), "freq_sensitive", w))
        if fs_hits:
            findings.append(self._mk("freq_sensitive", fs_hits))

        # ---- TIER2_CLUSTER：同段聚集 ≥ 阈值种 ----
        cluster_count = 0
        cl_hits: list[str] = []
        for (p_start, p_end, para) in _paragraph_spans(text):
            present = [w for w in TIER2_SUSPICIOUS if w in para]
            if len(set(present)) >= CLUSTER_THRESHOLD:
                cluster_count += 1
                cl_hits.extend(present[:5])
                spans.append(FlaggedSpan(p_start, p_end, "tier2_cluster", para[:40]))
        if cluster_count:
            f = SlopFinding(category="tier2_cluster", hits=cl_hits[:30], raw_score=cluster_count)
            w = CATEGORY_WEIGHTS["tier2_cluster"]
            f.weighted_penalty = min(cluster_count * w["per_hit"], w["cap"])
            findings.append(f)

        # ---- 正则类：FICTION_TELLS / STRUCTURAL / TELLING ----
        for cat, patterns in (
            ("fiction_tell", FICTION_TELLS),
            ("structural", STRUCTURAL),
            ("telling", TELLING),
        ):
            hits: list[str] = []
            for pat in patterns:
                for m in re.finditer(pat, text):
                    hits.append(m.group(0))
                    spans.append(FlaggedSpan(m.start(), m.end(), cat, m.group(0)))
            if hits:
                findings.append(self._mk(cat, hits))

        # ---- 数学特征：句长 CV / 破折号 / 段首转折 ----
        sentences = _split_sentences_zh(text)
        if len(sentences) >= 8:
            lengths = [len(s) for s in sentences]
            m_len = mean(lengths)
            sd = stdev(lengths) if len(lengths) > 1 else 0.0
            cv = sd / m_len if m_len > 0 else 0.0
            if cv < 0.3:
                pen = round(max(0.0, (0.3 - cv) / 0.3) * CATEGORY_WEIGHTS["sentence_cv"]["cap"], 3)
                findings.append(SlopFinding("sentence_cv", [f"cv={cv:.3f}"], cv, pen))

        n_em = len(re.findall(r"——|—|--", text))
        density = (n_em / max(1, len(text))) * 1000
        if density > 15:
            pen = round(min((density - 15) * 0.05, CATEGORY_WEIGHTS["em_dash"]["cap"]), 3)
            findings.append(SlopFinding("em_dash", [f"density={density:.1f}"], density, pen))

        TRANSITIONS = ["但是", "然而", "不过", "可是", "只是", "否则", "因此", "所以"]
        paras = [p for (_s, _e, p) in _paragraph_spans(text)]
        if paras:
            with_trans = sum(1 for p in paras if any(t in p[:6] for t in TRANSITIONS))
            ratio = with_trans / len(paras)
            if ratio > 0.3:
                pen = round(min((ratio - 0.3) * 4.0, CATEGORY_WEIGHTS["transition"]["cap"]), 3)
                findings.append(SlopFinding("transition", [f"ratio={ratio:.3f}"], ratio, pen))

        penalty = round(min(sum(f.weighted_penalty for f in findings), TOTAL_PENALTY_CAP), 3)
        spans.sort(key=lambda s: s.start)
        return SlopReport(findings=findings, penalty=penalty, flagged_spans=spans)

    @staticmethod
    def _mk(category: str, hits: list[str]) -> SlopFinding:
        w = CATEGORY_WEIGHTS[category]
        pen = min(len(hits) * w["per_hit"], w["cap"])
        return SlopFinding(category=category, hits=hits[:50], raw_score=len(hits), weighted_penalty=pen)

    # ---- 可选：用 logprobs 标记低熵高自信套话段 ----
    @staticmethod
    def flag_low_entropy_spans(
        tokens: list[str],
        token_logprobs: list[float],
        *,
        logprob_threshold: float = -0.05,
        min_run: int = 12,
    ) -> list[tuple[int, int]]:
        """在 token 序列里找"连续高自信"片段（logprob 接近 0 = 模型几乎必吐）。
        这类长连续高自信片段常是陈词滥调。返回 token-index 区间列表。
        调用方负责把 token-index 映射回字符 offset。
        """
        runs: list[tuple[int, int]] = []
        run_start = None
        for i, lp in enumerate(token_logprobs):
            if lp >= logprob_threshold:
                if run_start is None:
                    run_start = i
            else:
                if run_start is not None and i - run_start >= min_run:
                    runs.append((run_start, i))
                run_start = None
        if run_start is not None and len(token_logprobs) - run_start >= min_run:
            runs.append((run_start, len(token_logprobs)))
        return runs
