"""SEQR 评分量表（Phase 1，对齐 WebNovelBench 8 维）。

设计依据 phase1/00-architecture.md §7。

8 维逐字对齐 WebNovelBench（arXiv 2505.14818 Table 1，已 source-verified 2026-05-30）：
  D1 Use of Literary Devices          文学手法运用
  D2 Richness of Sensory Detail       感官细节丰富度
  D3 Balance of Character Presence    角色戏份平衡
  D4 Distinctiveness of Character Dialogue  对白区分度  ← 重点（SEQR 弱维）
  D5 Consistency of Characterisation  人物刻画一致性
  D6 Atmospheric and Thematic Alignment  氛围与主题契合
  D7 Contextual Appropriateness       语境恰当性
  D8 Scene-to-Scene Coherence         场景间连贯性

Composite = mean(8 维) − slop_penalty
（注：WebNovelBench 原文用 PCA+ECDF，本项目用等权均值，是 project-local 的 SEQR 度量，
  借维度定义不借其合成方法 —— 数据集 CC-BY-NC-SA 仅约束再分发，借方法无碍。）
"""
from __future__ import annotations

from statistics import mean as _mean

RUBRIC_VERSION = "SEQR-p1-wnb8"

# 维度 key（英文，对齐论文）→ 中文标签
DIMENSIONS: list[str] = [
    "literary_devices",
    "sensory_detail",
    "character_presence_balance",
    "dialogue_distinctness",
    "characterisation_consistency",
    "atmospheric_thematic",
    "contextual_appropriateness",
    "scene_coherence",
]

DIMENSION_LABELS_ZH: dict[str, str] = {
    "literary_devices": "文学手法运用",
    "sensory_detail": "感官细节丰富度",
    "character_presence_balance": "角色戏份平衡",
    "dialogue_distinctness": "对白区分度",
    "characterisation_consistency": "人物刻画一致性",
    "atmospheric_thematic": "氛围与主题契合",
    "contextual_appropriateness": "语境恰当性",
    "scene_coherence": "场景间连贯性",
}

# 给 LLM 评委的逐维度评分指引（中文，喂进 critic prompt）
DIMENSION_GUIDE_ZH: dict[str, str] = {
    "literary_devices": "比喻/象征/对仗等手法是否自然有效，而非堆砌套路或烂用比喻。",
    "sensory_detail": "视觉/听觉/嗅觉/触觉等是否具体可感，而非空泛抽象。",
    "character_presence_balance": "出场角色的戏份分配是否合理，主次得当，无角色突兀消失。",
    "dialogue_distinctness": "不同角色的对白是否各有口吻（用词/句式/语气），能否盲读辨认是谁在说。",
    "characterisation_consistency": "角色行为/性格/能力是否与既定人设一致，无崩人设。",
    "atmospheric_thematic": "场景氛围与作品主题/基调是否契合统一。",
    "contextual_appropriateness": "本章内容是否承接前文语境，无突兀、无前后矛盾。",
    "scene_coherence": "场景之间过渡是否流畅，逻辑链是否连贯。",
}

DETECTOR_FROM_RUBRIC = "see slop_detector.SlopReport"  # 标记：slop_penalty 来自 detector


def composite_score(dim_scores: dict[str, float], slop_penalty: float) -> dict:
    """SEQR composite = mean(8 维) − slop_penalty。

    Args:
        dim_scores: {dimension_key: 0-10}
        slop_penalty: 0-3（会被 clamp）
    Returns:
        {mean_quality, slop_penalty, composite_score, per_dim}
    """
    scores = [float(dim_scores.get(d, 0.0)) for d in DIMENSIONS]
    mq = round(_mean(scores), 3)
    sp = round(max(0.0, min(3.0, float(slop_penalty))), 3)
    return {
        "mean_quality": mq,
        "slop_penalty": sp,
        "composite_score": round(mq - sp, 3),
        "per_dim": {d: float(dim_scores.get(d, 0.0)) for d in DIMENSIONS},
    }
