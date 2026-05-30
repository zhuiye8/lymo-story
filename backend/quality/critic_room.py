"""异源 Critic Room（评委团）。

设计依据 phase1/00-architecture.md §5.4 + §7。

戒律：判官必须与生成模型【异源】——Writer 用 deepseek-v4-pro 生成，
Critic 不能也用 v4-pro 自评（self-correction 在推理上会掉分，调研 R16 结论）。
  - 主评委：deepseek-v4-flash（便宜、与 v4-pro 同厂但不同档，弱异源）
  - 第二评委：MiMo（订阅期内，真异源去偏；过期后降级为单评委 + 确定性规则兜底）

Step 1 只建 schema + 接口骨架；实现（实际调 LLM 评分 + 多评委聚合）在 Step 6 填。
"""
from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from backend.quality.rubric import DIMENSIONS, DIMENSION_GUIDE_ZH, composite_score

logger = logging.getLogger(__name__)


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
    """构造评委的 system/user prompt（逐维度评分）。"""
    guide = "\n".join(f"- {d}（{DIMENSION_GUIDE_ZH[d]}）" for d in DIMENSIONS)
    system = (
        "你是严格的中文小说质量评审。对给定章节按 8 个维度各打 0-10 分，"
        "必须给出每个维度的简短理由，引用原文片段佐证。只评质量，不改写。\n"
        "评分要有区分度，不要全打 7 分；写得好就给高分，有硬伤就给低分。\n"
        f"评分维度（dimension 字段必须用左边的英文 key）：\n{guide}"
    )
    user = (
        (f"【本章规划】\n{scene_brief}\n\n" if scene_brief else "")
        + f"【待评章节】\n{chapter_text}"
    )
    return system, user


class _CriticOutput(BaseModel):
    """单评委的结构化输出（喂 Instructor）。"""
    dim_scores: list[DimensionScore]
    overall_comment: str = ""


async def _one_judge(llm, judge_agent_name: str, chapter_text: str, scene_brief: str) -> CriticVerdict | None:
    """跑一个评委。失败返回 None（不阻塞其他评委）。"""
    system, user = build_critic_prompt(chapter_text, scene_brief)
    try:
        out = await llm.complete_structured(
            system, user, _CriticOutput,
            agent_name=judge_agent_name, temperature=0.3, max_tokens=2048, max_retries=2)
        # 解析出实际用的模型名（用于 judges_used 记录）
        return CriticVerdict(
            judge_model=judge_agent_name,
            dim_scores=out.dim_scores,
            overall_comment=out.overall_comment,
        )
    except Exception as e:
        logger.warning(f"[critic] judge {judge_agent_name} failed: {e}")
        return None


async def run_critic_room(
    llm,
    chapter_text: str,
    slop_penalty: float,
    *,
    scene_brief: str = "",
    pass_threshold: float = 6.0,
    use_secondary: bool = True,
) -> CriticRoomResult:
    """异源评委团评分。

    主评委：agent_name='critic_primary'（registry 绑 deepseek-v4-flash）
    第二评委：agent_name='critic_secondary'（registry 绑 MiMo，订阅期）
      - 若第二评委调用失败（未配置/订阅过期）→ 自动降级为单评委。

    戒律：判官与生成模型异源（Writer 用 v4-pro，评委不用 v4-pro 自评）。
    """
    import asyncio

    tasks = [_one_judge(llm, "critic_primary", chapter_text, scene_brief)]
    if use_secondary:
        tasks.append(_one_judge(llm, "critic_secondary", chapter_text, scene_brief))

    results = await asyncio.gather(*tasks)
    verdicts = [v for v in results if v is not None]

    if not verdicts:
        # 全部评委失败 → 兜底：用 slop_penalty + 中性分（确定性规则不被污染）
        logger.error("[critic] all judges failed; falling back to neutral score")
        verdicts = [CriticVerdict(
            judge_model="fallback_neutral",
            dim_scores=[DimensionScore(dimension=d, score=6.0, reason="评委不可用，中性兜底") for d in DIMENSIONS],
            overall_comment="所有评委调用失败，使用中性兜底分。",
        )]

    return aggregate_verdicts(verdicts, slop_penalty, pass_threshold=pass_threshold)
