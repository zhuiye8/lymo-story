"""SEQR Composite Score.

Project-local v0 metric. Equal-weighted mean of 8 dimensions minus slop penalty.
Not HNES (CreAgentive). Not WebNovelBench composite.
"""
from statistics import mean as _mean

from backend.quality import DIMENSIONS


def composite_score(dim_scores: dict[str, float], slop_penalty: float) -> dict:
    """Compute SEQR composite from 8 dimension scores and slop penalty.

    Args:
        dim_scores: {dimension_key: 0-10}
        slop_penalty: 0-3 (will be clamped)

    Returns:
        {mean_quality, slop_penalty, composite_score}

    composite = mean(8) - slop_penalty
    Range: roughly -3 to 10. Negative is possible if quality is very low + heavy slop.
    """
    # Validate / fill missing dims with 0
    scores = []
    for d in DIMENSIONS:
        scores.append(float(dim_scores.get(d, 0.0)))
    mq = round(_mean(scores), 3)
    sp = round(max(0.0, min(3.0, float(slop_penalty))), 3)
    return {
        "mean_quality": mq,
        "slop_penalty": sp,
        "composite_score": round(mq - sp, 3),
    }
