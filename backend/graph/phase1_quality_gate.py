"""质量闸（Phase 1，Step 6 anti-slop 检测-重写-选优闭环）。

设计依据 phase1/00-architecture.md §5。
作为章节 graph 的 quality_gate 节点（write_chapter 之后、extract_memory 之前）。

四层：
  ① 确定性检测：slop 词表 + logprobs（slop_detector）
  ② 一致性检测：知识四元组冲突（quads.find_conflicts）—— 在 extract 后才有 new_quads，
     故本节点先做 slop + 字数 + critic；四元组冲突在 save 前由 extract 节点产物校验。
  ③ 局部重写：flagged_spans 用 FIM 重写 + 字数矫正（rewrite.py）
  ④ best-of-N + 异源 Critic：选最优候选 + composite 过闸判定

字数控制与 anti-slop 共用 prefix/FIM 引擎（§字数控制机制）。
"""
from __future__ import annotations

import logging

from backend.llm.client import LLMClient
from backend.quality.slop_detector import SlopDetector
from backend.quality.rewrite import rewrite_slop_paragraphs, expand_if_short, compress_if_long
from backend.quality.critic_room import run_critic_room

logger = logging.getLogger(__name__)

WORD_FLOOR = 3000
WORD_CEILING = 4500
PASS_THRESHOLD = 6.0
MAX_REWRITE_ROUNDS = 2


async def run_quality_gate(
    llm: LLMClient,
    content: str,
    *,
    target_words: int,
    scene_brief: str = "",
    use_secondary_judge: bool = True,
) -> dict:
    """对一章正文跑质量闸。返回 {content, quality, slop_findings, passed, rounds}。

    流程：
      1. 字数矫正（短则扩、长则压，保钩子）
      2. slop 检测 → 命中则局部重写（最多 MAX_REWRITE_ROUNDS 轮）
      3. 异源 Critic 评分 → composite 过闸判定
    """
    detector = SlopDetector()
    cur = content
    rounds = 0

    # ---- 1. 字数矫正（与 anti-slop 共用引擎）----
    if len(cur) < WORD_FLOOR:
        cur = await expand_if_short(llm, cur, target_words, floor=WORD_FLOOR)
    elif len(cur) > WORD_CEILING:
        cur = await compress_if_long(llm, cur, target_words, ceiling=WORD_CEILING)

    # ---- 2. slop 检测 + 局部重写循环 ----
    report = detector.detect(cur)
    while report.penalty > 0.5 and rounds < MAX_REWRITE_ROUNDS:
        rounds += 1
        before = report.penalty
        cur = await rewrite_slop_paragraphs(llm, cur, report, max_paras=3)
        report = detector.detect(cur)
        logger.info(f"[quality_gate] rewrite round {rounds}: penalty {before:.2f} -> {report.penalty:.2f}")
        if report.penalty >= before:  # 没改善就停，避免空转
            break

    # ---- 3. 异源 Critic 评分 ----
    critic = await run_critic_room(
        llm, cur, report.penalty,
        scene_brief=scene_brief, pass_threshold=PASS_THRESHOLD,
        use_secondary=use_secondary_judge,
    )

    slop_findings = [
        {"category": f.category, "hits": f.hits, "weighted_penalty": f.weighted_penalty}
        for f in report.findings
    ]
    quality = {
        "composite_score": critic.composite_score,
        "mean_quality": critic.mean_quality,
        "slop_penalty": report.penalty,
        "dim_scores": critic.aggregated_dim_scores,
        "judges": critic.judges_used,
        "word_count": len(cur),
    }
    return {
        "content": cur,
        "quality": quality,
        "slop_findings": slop_findings,
        "passed": critic.passed,
        "rounds": rounds,
    }
