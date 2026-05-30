"""异源 Critic Room（评委团）。

设计依据 phase1/00-architecture.md §5.4 + §7。

戒律：判官必须与生成模型【异源】——Writer 用 deepseek-v4-pro 生成，
Critic 不能也用 v4-pro 自评（self-correction 在推理上会掉分，调研 R16 结论）。
  - 主评委：deepseek-v4-flash（便宜、与 v4-pro 同厂但不同档，弱异源）
  - 第二评委：MiMo（订阅期内，真异源去偏；过期后降级为单评委 + 确定性规则兜底）

Step 1 只建 schema + 接口骨架；实现（实际调 LLM 评分 + 多评委聚合）在 Step 6 填。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.quality.rubric import DIMENSIONS, DIMENSION_GUIDE_ZH, composite_score


class DimensionScore(BaseModel):
    """单维度评分 + 简短理由（评委逐维输出）。"""
    dimension: str
    score: float = Field(ge=0, le=10)
    reason: str = ""


class CriticVerdict(BaseModel):
    """单个评委对一章的完整评分。"""
    judge_model: str
    dim_scores: list[DimensionScore]
    overall_comment: str = ""

    def as_dim_dict(self) -> dict[str, float]:
        return {d.dimension: d.score for d in self.dim_scores}


class CriticRoomResult(BaseModel):
    """评委团聚合结果。"""
    verdicts: list[CriticVerdict]
    aggregated_dim_scores: dict[str, float]   # 多评委按维度取均值
    mean_quality: float
    slop_penalty: float
    composite_score: float
    passed: bool
    judges_used: list[str]


def aggregate_verdicts(
    verdicts: list[CriticVerdict],
    slop_penalty: float,
    *,
    pass_threshold: float,
) -> CriticRoomResult:
    """把多个评委的逐维分按维度取均值，合成 composite，判定是否过闸。

    纯函数，无 LLM 调用 —— Step 1 即可单测。
    """
    agg: dict[str, float] = {}
    for d in DIMENSIONS:
        vals = [v.as_dim_dict().get(d) for v in verdicts]
        vals = [x for x in vals if x is not None]
        agg[d] = round(sum(vals) / len(vals), 3) if vals else 0.0

    comp = composite_score(agg, slop_penalty)
    return CriticRoomResult(
        verdicts=verdicts,
        aggregated_dim_scores=agg,
        mean_quality=comp["mean_quality"],
        slop_penalty=comp["slop_penalty"],
        composite_score=comp["composite_score"],
        passed=comp["composite_score"] >= pass_threshold,
        judges_used=[v.judge_model for v in verdicts],
    )


def build_critic_prompt(chapter_text: str, scene_brief: str = "") -> tuple[str, str]:
    """构造评委的 system/user prompt（逐维度评分）。Step 6 实际调用时用。"""
    guide = "\n".join(f"- {d}（{DIMENSION_GUIDE_ZH[d]}）" for d in DIMENSIONS)
    system = (
        "你是严格的中文小说质量评审。对给定章节按 8 个维度各打 0-10 分，"
        "必须给出每个维度的简短理由，引用原文片段佐证。只评质量，不改写。\n"
        f"评分维度：\n{guide}"
    )
    user = (
        (f"【本章规划】\n{scene_brief}\n\n" if scene_brief else "")
        + f"【待评章节】\n{chapter_text}"
    )
    return system, user


# Step 6 填：async def run_critic_room(...) -> CriticRoomResult
#   - 并发调主评委(v4-flash) + 第二评委(MiMo，若订阅有效)
#   - 各自 build_critic_prompt + Instructor 结构化拿 CriticVerdict
#   - aggregate_verdicts 聚合
