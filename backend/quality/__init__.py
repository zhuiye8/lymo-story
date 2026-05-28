"""SEQR v0 (Story Engine Quality Rubric) — Phase 0 evaluation baseline.

Project-local rubric. Borrows dimensions from WebNovelBench
(https://arxiv.org/html/2505.14818) and slop detection from autonovel
(https://github.com/NousResearch/autonovel/blob/master/evaluate.py),
but does not implement either paper's full methodology — see
`workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` for scope.
"""

RUBRIC_VERSION = "SEQR-v0"

# DETECTOR_VERSION is canonically defined in backend.quality.slop_detector
# and re-exported here so legacy imports (`from backend.quality import DETECTOR_VERSION`)
# always reflect the active detector. Do NOT shadow this with a local literal —
# Report #3 review (supervisor 2026-04-27) flagged the split-brain bug where
# this file said "slop-v0" while slop_detector.py was already at v1.
from backend.quality.slop_detector import DETECTOR_VERSION  # noqa: E402, F401

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

DIMENSION_LABELS_ZH = {
    "fluency": "语言流畅度",
    "dialogue_distinct": "对白独特性",
    "character_consistency": "角色一致性",
    "scene_drama": "场景戏剧性",
    "sensory_detail": "感官描写",
    "rhetoric_quality": "修辞质量",
    "continuity": "跨场景衔接",
    "overall_readability": "整体可读性",
}
