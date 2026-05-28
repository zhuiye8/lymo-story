"""Slop detector — Chinese-localised port of autonovel slop_score.

Source: https://github.com/NousResearch/autonovel/blob/master/evaluate.py
[verified:2026-04-26]

Output: list of (category, hits, raw_score, weighted_penalty) per chapter,
plus a final 0-3 slop_penalty applied to SEQR composite.

Categories:
  tier1_banned       : Chinese cliché phrases (烂用比喻 / 套话)
  tier2_cluster      : abstract / vague filler words; only counted when ≥3 in one paragraph
  structural         : "不仅仅是…更是…" structural tics
  fiction_tell       : 中文 LLM 小说俗套（瞳孔紧缩 / 嘴角勾起 / 心脏漏跳）
  show_vs_tell       : 显式情绪标注 ("他感到愤怒" 等)
  sentence_cv        : sentence-length coefficient of variation (< 0.3 penalised)
  em_dash_density    : 破折号 / em-dash 密度
  transition_ratio   : 段首转折词比例

Versions:
  v0 (2026-04-26): bootstrap port, calibrated against 25+12 sample set.
  v1 (2026-04-27): regex fixes per AC3 calibration FN analysis (Report #2):
      - fiction_tell: 心脏漏跳了一拍 / 嘴角微微勾起 / 眼神变得复杂 / 瞳孔骤然紧缩 now match
      - structural: 不仅仅关乎X，更关乎Y now matches (was 是-only)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import mean, stdev


# Single source of truth for detector version — re-exported from backend.quality.
# Naming convention: keep the "slop-" prefix from v0 for backward-compatible
# string matching in DB queries / log scrapers.
DETECTOR_VERSION = "slop-v1"


# ---- v0 word lists (will be calibrated against samples_zh.json) ----

TIER1_BANNED_ZH: list[str] = [
    # 烂用比喻
    "宛如", "犹如", "仿佛", "如同",
    # 滥用心理描写
    "在心底深处", "心中暗想", "脑海深处",
    # 句式滥用
    "不仅仅是", "更是",
    # 套话
    "千丝万缕", "千头万绪", "万千思绪",
    # 成语堆砌
    "刻骨铭心", "如雷贯耳", "震耳欲聋",
    # 大词
    "命运的齿轮", "时间的洪流", "岁月的长河",
]

TIER2_SUSPICIOUS_ZH: list[str] = [
    # 抽象名词
    "气息", "气场", "气氛", "氛围",
    # 大词
    "命运", "宿命", "缘分",
    # 模糊副词
    "冷冷地", "淡淡地", "轻轻地", "缓缓地", "渐渐地",
    # 万能形容
    "复杂", "深邃", "凌厉", "锐利",
]

# Chinese fiction AI tells — regex-based
# v1 fixes (Report #2 AC3 FN analysis):
#   - 瞳孔: add 骤然/猛然/猛地 prefixes (was missing 瞳孔骤然紧缩)
#   - 心脏: add 漏跳/猛跳/停跳 compound forms (was missing 心脏漏跳了一拍)
#   - 嘴角: change [微微]? char-class bug to (?:微微|微|轻)? non-cap group (was missing 嘴角微微勾起)
#   - 眼神: change [变得]? char-class bug to (?:变得)? non-cap group (was missing 眼神变得复杂)
FICTION_AI_TELLS_ZH: list[str] = [
    r"瞳孔(?:骤然|猛然|猛地|微微|微|一)?[紧]?[缩]",
    r"心脏(?:漏跳|猛跳|停跳|漏|停|猛)了一?[拍跳下]",
    r"嘴角(?:微微|微|轻轻|轻)?(?:勾起|勾|上扬|扬起|扬|上翘|翘)",
    r"眼神(?:变得)?(?:复杂|深邃|凌厉|锐利)",
    r"血液?(?:几乎)?(?:凝固|凝住)",
    r"呼吸(?:为之)?(?:一窒|一滞|急促)",
    r"心头一[紧凉颤]",
    r"脸色(?:变得|微微)?(?:煞白|惨白|铁青)",
]

# Structural AI tics
# v1 fix: 不仅仅是X更是Y was 是-only; expand to 关乎/在于/为了/代表/意味着
STRUCTURAL_AI_TICS: list[str] = [
    r"不(?:仅仅|只)(?:是|关乎|在于|为了|代表|意味着).{2,30}(?:更|而)(?:是|关乎|在于|为了|代表|意味着)",
    r"(?:不|没)有.{2,20}，[却但].{2,20}",
    r"在.{2,15}的同时，.{2,15}",
]

# Show-vs-tell — explicit emotion labels
TELLING_PATTERNS: list[str] = [
    r"(?:他|她|它|我|你)(?:感到|觉得|心想)(?:很|非常|十分)?(?:愤怒|悲伤|高兴|难过|害怕|惊讶|焦虑|紧张|失望|喜悦)",
    r"(?:愤怒|悲伤|高兴|难过|害怕|惊讶)地",
]


@dataclass
class SlopFinding:
    category: str
    hits: list[str] = field(default_factory=list)  # actual matched substrings
    raw_score: float = 0.0
    weighted_penalty: float = 0.0


def _split_sentences_zh(text: str) -> list[str]:
    """Crude Chinese sentence split on . ! ? 。！？"""
    parts = re.split(r"[。！？.!?]", text)
    return [p.strip() for p in parts if p.strip()]


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n") if p.strip()]


# ---- Detector ----

class SlopDetector:
    """SlopDetector v0 — Chinese localisation of autonovel slop_score.

    Tunables (penalties capped per category):
      TIER1: hit*1.5, max 4.0
      TIER2: clusters*1.0, max 2.0
      FICTION: hit*0.3, max 2.0
      STRUCTURAL: hit*0.5, max 1.5
      TELL: hit*0.3, max 2.0
      SENTENCE_CV: 0-1.0 if cv<0.3
      EM_DASH: per-1k>15 → up to 1.0
      TRANSITION: ratio>0.3 → up to 1.0
    """

    def detect(self, text: str) -> list[SlopFinding]:
        findings: list[SlopFinding] = []

        # Tier 1
        t1_hits = []
        for w in TIER1_BANNED_ZH:
            for m in re.finditer(re.escape(w), text):
                t1_hits.append(m.group(0))
        if t1_hits:
            findings.append(SlopFinding(
                category="tier1_banned",
                hits=t1_hits[:50],
                raw_score=len(t1_hits),
                weighted_penalty=min(len(t1_hits) * 1.5, 4.0),
            ))

        # Tier 2 — cluster per paragraph
        t2_clusters = 0
        t2_hits: list[str] = []
        for para in _split_paragraphs(text):
            para_hits = []
            for w in TIER2_SUSPICIOUS_ZH:
                if w in para:
                    para_hits.append(w)
            if len(set(para_hits)) >= 3:
                t2_clusters += 1
                t2_hits.extend(para_hits[:5])
        if t2_clusters > 0:
            findings.append(SlopFinding(
                category="tier2_cluster",
                hits=t2_hits[:30],
                raw_score=t2_clusters,
                weighted_penalty=min(t2_clusters * 1.0, 2.0),
            ))

        # Fiction AI tells
        f_hits: list[str] = []
        for pat in FICTION_AI_TELLS_ZH:
            for m in re.finditer(pat, text):
                f_hits.append(m.group(0))
        if f_hits:
            findings.append(SlopFinding(
                category="fiction_tell",
                hits=f_hits[:30],
                raw_score=len(f_hits),
                weighted_penalty=min(len(f_hits) * 0.3, 2.0),
            ))

        # Structural tics
        s_hits: list[str] = []
        for pat in STRUCTURAL_AI_TICS:
            for m in re.finditer(pat, text):
                s_hits.append(m.group(0))
        if s_hits:
            findings.append(SlopFinding(
                category="structural",
                hits=s_hits[:20],
                raw_score=len(s_hits),
                weighted_penalty=min(len(s_hits) * 0.5, 1.5),
            ))

        # Show-vs-tell
        tell_hits: list[str] = []
        for pat in TELLING_PATTERNS:
            for m in re.finditer(pat, text):
                tell_hits.append(m.group(0))
        if tell_hits:
            findings.append(SlopFinding(
                category="show_vs_tell",
                hits=tell_hits[:30],
                raw_score=len(tell_hits),
                weighted_penalty=min(len(tell_hits) * 0.3, 2.0),
            ))

        # Sentence-length coefficient of variation
        sentences = _split_sentences_zh(text)
        if len(sentences) >= 8:
            lengths = [len(s) for s in sentences]
            m_len = mean(lengths)
            sd = stdev(lengths) if len(lengths) > 1 else 0.0
            cv = sd / m_len if m_len > 0 else 0.0
            if cv < 0.3:
                # cv 0.3 → 0; cv 0.0 → 1.0
                penalty = max(0.0, (0.3 - cv) / 0.3) * 1.0
                findings.append(SlopFinding(
                    category="sentence_cv",
                    hits=[f"cv={cv:.3f}"],
                    raw_score=cv,
                    weighted_penalty=round(penalty, 3),
                ))

        # Em-dash density per 1000 chars
        n_em = len(re.findall(r"——|—|--", text))
        text_len = max(1, len(text))
        density = (n_em / text_len) * 1000
        if density > 15:
            penalty = min((density - 15) * 0.05, 1.0)
            findings.append(SlopFinding(
                category="em_dash_density",
                hits=[f"density_per_1000={density:.1f}"],
                raw_score=density,
                weighted_penalty=round(penalty, 3),
            ))

        # Transition ratio (段首转折词)
        TRANSITIONS = ["但是", "然而", "不过", "可是", "只是", "否则", "因此", "所以"]
        paras = _split_paragraphs(text)
        if paras:
            with_trans = 0
            for p in paras:
                head = p[:6]
                if any(t in head for t in TRANSITIONS):
                    with_trans += 1
            ratio = with_trans / len(paras)
            if ratio > 0.3:
                penalty = min((ratio - 0.3) * 4.0, 1.0)
                findings.append(SlopFinding(
                    category="transition_ratio",
                    hits=[f"ratio={ratio:.3f}"],
                    raw_score=ratio,
                    weighted_penalty=round(penalty, 3),
                ))

        return findings

    @staticmethod
    def total_penalty(findings: list[SlopFinding]) -> float:
        """Cap total slop penalty at 3.0 (the SEQR composite max deduction)."""
        return round(min(sum(f.weighted_penalty for f in findings), 3.0), 3)
