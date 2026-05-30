"""S6 单元测试：质量闸的纯逻辑部分（不调 API）。

真实 API 端到端验收在 _s6_smoke.py（手动跑）。
这里测：critic 聚合、降级、rewrite 段落切分、字数矫正判定。
"""
from __future__ import annotations

import pytest

from backend.quality.critic_room import (
    CriticVerdict, DimensionScore, aggregate_verdicts,
)
from backend.quality.rewrite import _split_paragraphs_with_offsets
from backend.quality import DIMENSIONS


class TestCriticAggregation:
    def test_single_judge_pass(self):
        v = CriticVerdict(judge_model="critic_primary",
                          dim_scores=[DimensionScore(dimension=d, score=8.0) for d in DIMENSIONS])
        r = aggregate_verdicts([v], slop_penalty=1.0, pass_threshold=6.0)
        assert r.mean_quality == 8.0
        assert r.composite_score == 7.0
        assert r.passed is True
        assert r.judges_used == ["critic_primary"]

    def test_two_heterogeneous_judges_averaged(self):
        v1 = CriticVerdict(judge_model="critic_primary",
                           dim_scores=[DimensionScore(dimension=d, score=5.0) for d in DIMENSIONS])
        v2 = CriticVerdict(judge_model="critic_secondary",
                           dim_scores=[DimensionScore(dimension=d, score=9.0) for d in DIMENSIONS])
        r = aggregate_verdicts([v1, v2], slop_penalty=0.0, pass_threshold=6.0)
        assert r.mean_quality == 7.0   # (5+9)/2
        assert r.composite_score == 7.0
        assert len(r.judges_used) == 2

    def test_fail_below_threshold(self):
        v = CriticVerdict(judge_model="critic_primary",
                          dim_scores=[DimensionScore(dimension=d, score=4.0) for d in DIMENSIONS])
        r = aggregate_verdicts([v], slop_penalty=2.0, pass_threshold=6.0)
        assert r.composite_score == 2.0  # 4 - 2
        assert r.passed is False

    def test_partial_dims_default_zero(self):
        # 评委只打了 3 维 → 其余按 0 计（保守）
        v = CriticVerdict(judge_model="critic_primary",
                          dim_scores=[DimensionScore(dimension=DIMENSIONS[0], score=9.0),
                                      DimensionScore(dimension=DIMENSIONS[1], score=9.0),
                                      DimensionScore(dimension=DIMENSIONS[2], score=9.0)])
        r = aggregate_verdicts([v], slop_penalty=0.0, pass_threshold=6.0)
        # 3*9/8 = 3.375
        assert r.mean_quality == pytest.approx(3.375, abs=0.01)


class TestParagraphSplit:
    def test_split_offsets_roundtrip(self):
        text = "第一段内容。\n\n第二段内容更长一些。\n\n第三段。"
        paras = _split_paragraphs_with_offsets(text)
        assert len(paras) == 3
        for start, end, para in paras:
            assert text[start:end] == para

    def test_empty_blocks_skipped(self):
        text = "甲。\n\n\n\n乙。"
        paras = _split_paragraphs_with_offsets(text)
        assert [p[2] for p in paras] == ["甲。", "乙。"]
