"""局部重写引擎（Phase 1，anti-slop 闭环 ③ + 字数矫正）。

设计依据 phase1/00-architecture.md §5.3 + §字数控制机制。

不整章重生成 —— 用 DeepSeek 的 prefix-completion / FIM 局部修：
  - slop 段重写：把含 slop 的段落挖掉，用 FIM（prefix=前文, suffix=后文）填干净的
  - 字数太短：prefix-completion 续写最单薄场景
  - 字数太长：压缩冗余段（保章末钩子，不截断）

与 anti-slop 共用同一引擎（prefix/FIM），不重复造轮子。
"""
from __future__ import annotations

import logging

from backend.llm.client import LLMClient
from backend.quality.slop_detector import SlopDetector, SlopReport
from backend.prompts.phase1.shared import ANTI_SLOP_ZH

logger = logging.getLogger(__name__)


def _split_paragraphs_with_offsets(text: str) -> list[tuple[int, int, str]]:
    """返回 [(start, end, para), ...]，按 \\n\\n 分段（与生成时的拼接一致）。"""
    spans: list[tuple[int, int, str]] = []
    pos = 0
    for block in text.split("\n\n"):
        if block.strip():
            start = text.find(block, pos)
            spans.append((start, start + len(block), block))
        pos += len(block) + 2
    return spans


async def rewrite_slop_paragraphs(
    llm: LLMClient,
    text: str,
    report: SlopReport,
    *,
    agent_name: str = "scene_writer",
    max_paras: int = 3,
) -> str:
    """对 slop 命中最重的段落做 FIM 局部重写。

    策略：把 flagged_spans 按段落聚合，挑 slop 最密集的前 max_paras 段，
    用 FIM（prefix=该段之前全文，suffix=该段之后全文）让模型重写这一段。
    """
    if not report.flagged_spans:
        return text

    paras = _split_paragraphs_with_offsets(text)
    if not paras:
        return text

    # 统计每段的 slop 命中数
    para_hits: dict[int, int] = {}
    for span in report.flagged_spans:
        for i, (ps, pe, _) in enumerate(paras):
            if ps <= span.start < pe:
                para_hits[i] = para_hits.get(i, 0) + 1
                break

    if not para_hits:
        return text

    # 挑命中最多的前 max_paras 段，从后往前改（避免 offset 失效）
    target_idxs = sorted(para_hits, key=lambda i: -para_hits[i])[:max_paras]
    target_idxs.sort(reverse=True)

    cur_text = text
    for idx in target_idxs:
        cur_paras = _split_paragraphs_with_offsets(cur_text)
        if idx >= len(cur_paras):
            continue
        ps, pe, para = cur_paras[idx]
        # 给定上下文 + 待改段 → 普通 chat 改写（FIM 不读指令，只填充，故不用 FIM）
        before_ctx = cur_text[max(0, ps - 200):ps]
        after_ctx = cur_text[pe:pe + 200]
        system = (
            "你是中文小说编辑。改写【待改段落】，去除套话/AI腔/陈词滥调，"
            "保持情节、对话、信息完全不变，与上下文衔接自然，字数相近。"
            f"只输出改写后的段落正文，不要任何解释或标记。\n\n{ANTI_SLOP_ZH}"
        )
        user = (
            f"【上文】…{before_ctx}\n\n"
            f"【待改段落】\n{para}\n\n"
            f"【下文】{after_ctx}…\n\n"
            f"请输出改写后的【待改段落】（约 {len(para)} 字，去套话，保信息）："
        )
        try:
            new_para = await llm.complete(
                system, user, agent_name=agent_name,
                max_tokens=int(len(para) * 2.5) + 256, temperature=0.8)
            new_para = new_para.strip()
            # 防退化：非空、不过短、不是模型在道歉/解释
            if new_para and len(new_para) > len(para) * 0.4 and "改写" not in new_para[:10]:
                cur_text = cur_text[:ps] + new_para + cur_text[pe:]
        except Exception as e:
            logger.warning(f"[rewrite] rewrite para {idx} failed: {e}")
    return cur_text


async def expand_if_short(
    llm: LLMClient, text: str, target_words: int, *,
    agent_name: str = "scene_writer", floor: int = 3000,
) -> str:
    """字数太短 → prefix-completion 续写（不在尾部硬接，让模型自然延展结尾前的内容）。

    用整章作 assistant prefix，让模型顺势补足。仅当 < floor 才触发。
    """
    if len(text) >= floor:
        return text
    need = target_words - len(text)
    system = (
        "你是中文网文写手，正在续写一个章节，使其更丰满。"
        "在不重复已有内容的前提下，自然地扩展场景细节、人物动作和对话，"
        f"补足约 {need} 字。保持文风一致。\n\n{ANTI_SLOP_ZH}"
    )
    try:
        cont = await llm.prefix_complete(
            system, "续写下面这一章，使其更完整充实，直接接着往下写：",
            text, agent_name=agent_name, max_tokens=int(need * 2.5) + 512, temperature=0.85)
        return (text + cont).strip()
    except Exception as e:
        logger.warning(f"[rewrite] expand failed: {e}")
        return text


async def compress_if_long(
    llm: LLMClient, text: str, target_words: int, *,
    agent_name: str = "scene_writer", ceiling: int = 4500,
) -> str:
    """字数太长 → 压缩最冗余的段落，死保章末钩子（不截断尾部）。

    仅当 > ceiling 才触发。压缩中间冗余段，保留首尾（开头钩子 + 章末钩子）。
    """
    if len(text) <= ceiling:
        return text

    paras = _split_paragraphs_with_offsets(text)
    if len(paras) < 4:
        return text  # 段太少不压，避免伤钩子

    # 保护首段 + 末段（章末钩子），压缩中间最长的 1-2 段
    middle = paras[1:-1]
    middle_sorted = sorted(range(len(middle)), key=lambda i: -len(middle[i][2]))
    over = len(text) - target_words
    to_compress = middle_sorted[:2]

    cur_text = text
    # 从后往前改，避免 offset 移位
    abs_idxs = sorted([i + 1 for i in to_compress], reverse=True)
    for idx in abs_idxs:
        cur_paras = _split_paragraphs_with_offsets(cur_text)
        if idx >= len(cur_paras) - 1 or idx == 0:
            continue
        ps, pe, para = cur_paras[idx]
        tgt_len = max(int(len(para) * 0.55), 120)
        system = (
            "你是中文小说编辑。把给定段落压缩得更精炼，删去冗余和水分，"
            f"保留关键情节、对话和信息，压到约 {tgt_len} 字。只输出压缩后的段落。\n\n{ANTI_SLOP_ZH}"
        )
        try:
            new_para = await llm.complete(system, para, agent_name=agent_name,
                                          max_tokens=int(tgt_len * 2.2) + 128, temperature=0.6)
            new_para = new_para.strip()
            if new_para and len(new_para) < len(para):
                cur_text = cur_text[:ps] + new_para + cur_text[pe:]
        except Exception as e:
            logger.warning(f"[rewrite] compress para {idx} failed: {e}")
    return cur_text
