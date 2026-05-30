"""SEQR 质量评测（Phase 1）。

单一真源 re-export：rubric 维度、composite、slop 检测、critic room。
phase1/00-architecture.md §5 §7。
"""

from backend.quality.rubric import (
    RUBRIC_VERSION,
    DIMENSIONS,
    DIMENSION_LABELS_ZH,
    DIMENSION_GUIDE_ZH,
    composite_score,
)
from backend.quality.slop_detector import (
    DETECTOR_VERSION,
    SlopDetector,
    SlopReport,
    SlopFinding,
    FlaggedSpan,
)
from backend.quality.slop_lexicon_zh import LEXICON_VERSION
from backend.quality.critic_room import (
    DimensionScore,
    CriticVerdict,
    CriticRoomResult,
    aggregate_verdicts,
    build_critic_prompt,
)

__all__ = [
    "RUBRIC_VERSION",
    "DIMENSIONS",
    "DIMENSION_LABELS_ZH",
    "DIMENSION_GUIDE_ZH",
    "composite_score",
    "DETECTOR_VERSION",
    "SlopDetector",
    "SlopReport",
    "SlopFinding",
    "FlaggedSpan",
    "LEXICON_VERSION",
    "DimensionScore",
    "CriticVerdict",
    "CriticRoomResult",
    "aggregate_verdicts",
    "build_critic_prompt",
]
