"""S1 验收：Phase 1 slop 检测器 + rubric。

phase1/01-implementation-plan.md 验收点 S1：
  给一段已知含 slop 的中文文本，detector 正确标出 flagged_spans + penalty；
  rubric 能对一章打 8 维分。

重点验证频次感知修正（Phase 0 的核心 bug）：
  - 单次"仿佛"= 合法修辞，不扣分（鲁迅《社戏》式）
  - 同段 ≥2 次"仿佛"= slop，扣分
"""
from __future__ import annotations

import pytest

from backend.quality import (
    SlopDetector,
    composite_score,
    aggregate_verdicts,
    CriticVerdict,
    DimensionScore,
    DIMENSIONS,
)


@pytest.fixture
def det():
    return SlopDetector()


class TestFrequencySensitive:
    """频次感知：单次合法，多次才 slop（修 Phase 0 误判）。"""

    def test_single_fangfu_not_flagged(self, det):
        # 鲁迅《社戏》式单次合法比喻
        text = "淡黑的起伏的连山，仿佛是踊跃的铁的兽脊似的，都远远地向船尾跑去了。"
        report = det.detect(text)
        fs = [s for s in report.flagged_spans if s.category == "freq_sensitive"]
        assert fs == [], f"单次'仿佛'不该被标记，却标了 {fs}"

    def test_triple_fangfu_in_one_para_flagged(self, det):
        # 同段三次"仿佛"= LLM 滥用
        text = "他仿佛看见了过去，仿佛听见了呼唤，仿佛整个世界都安静了。"
        report = det.detect(text)
        fs = [s for s in report.flagged_spans if s.category == "freq_sensitive"]
        # 3 次，阈值 2，超出部分（第 2、3 次）计 = 2 次
        assert len(fs) >= 1, "同段三次'仿佛'应被标记为 slop"
        assert report.penalty > 0


class TestAlwaysBanned:
    def test_banned_phrases_flagged(self, det):
        text = "在心底深处，那段刻骨铭心的记忆如雷贯耳，命运的齿轮开始转动。"
        report = det.detect(text)
        ab = [s for s in report.flagged_spans if s.category == "always_banned"]
        hit_texts = {s.text for s in ab}
        assert "在心底深处" in hit_texts
        assert "刻骨铭心" in hit_texts
        assert "命运的齿轮" in hit_texts
        assert report.penalty > 0


class TestFictionTells:
    def test_body_language_cliche(self, det):
        text = "他瞳孔骤然紧缩，心脏漏跳了一拍，嘴角微微勾起，眼神变得复杂。"
        report = det.detect(text)
        ft = [s for s in report.flagged_spans if s.category == "fiction_tell"]
        assert len(ft) >= 3, f"应抓到多个 fiction-tell，实际 {len(ft)}"


class TestFlaggedSpans:
    def test_spans_have_valid_offsets(self, det):
        text = "在心底深处他想着。普通的一句话。瞳孔紧缩。"
        report = det.detect(text)
        for s in report.flagged_spans:
            # offset 必须能在原文里对上
            assert text[s.start:s.end] == s.text or s.category == "tier2_cluster", \
                f"span offset 对不上原文: {s}"

    def test_clean_text_no_penalty(self, det):
        # 干净的白描，无 slop
        text = "他推开门，桌上一杯凉茶。窗外在下雨，远处有人叫卖。他坐下，点了根烟。"
        report = det.detect(text)
        assert report.penalty == 0.0, f"干净文本不该有 penalty，实际 {report.penalty}: {[s.text for s in report.flagged_spans]}"


class TestPenaltyCap:
    def test_penalty_capped_at_3(self, det):
        # 极端堆砌，penalty 应 cap 到 3.0
        text = ("在心底深处" * 10) + ("命运的齿轮" * 10) + "瞳孔紧缩心脏漏跳了一拍嘴角勾起"
        report = det.detect(text)
        assert report.penalty <= 3.0


class TestRubricComposite:
    def test_composite_8dim(self):
        dim_scores = {d: 7.0 for d in DIMENSIONS}
        result = composite_score(dim_scores, slop_penalty=1.5)
        assert result["mean_quality"] == 7.0
        assert result["slop_penalty"] == 1.5
        assert result["composite_score"] == 5.5
        assert len(result["per_dim"]) == 8

    def test_missing_dims_default_zero(self):
        result = composite_score({"literary_devices": 8.0}, slop_penalty=0.0)
        # 1 维 8 分 + 7 维 0 分 = 1.0 均值
        assert result["mean_quality"] == 1.0

    def test_slop_penalty_clamped(self):
        result = composite_score({d: 5.0 for d in DIMENSIONS}, slop_penalty=99.0)
        assert result["slop_penalty"] == 3.0


class TestCriticAggregation:
    def test_two_judges_averaged(self):
        v1 = CriticVerdict(
            judge_model="deepseek-v4-flash",
            dim_scores=[DimensionScore(dimension=d, score=6.0) for d in DIMENSIONS],
        )
        v2 = CriticVerdict(
            judge_model="mimo-v2.5-pro",
            dim_scores=[DimensionScore(dimension=d, score=8.0) for d in DIMENSIONS],
        )
        result = aggregate_verdicts([v1, v2], slop_penalty=1.0, pass_threshold=5.0)
        # 两评委均值 7.0 - slop 1.0 = composite 6.0 ≥ 5.0 → pass
        assert result.mean_quality == 7.0
        assert result.composite_score == 6.0
        assert result.passed is True
        assert set(result.judges_used) == {"deepseek-v4-flash", "mimo-v2.5-pro"}

    def test_fail_below_threshold(self):
        v = CriticVerdict(
            judge_model="deepseek-v4-flash",
            dim_scores=[DimensionScore(dimension=d, score=3.0) for d in DIMENSIONS],
        )
        result = aggregate_verdicts([v], slop_penalty=2.0, pass_threshold=5.0)
        # 3.0 - 2.0 = 1.0 < 5.0 → fail
        assert result.passed is False
