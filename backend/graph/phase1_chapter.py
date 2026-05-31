"""章节生成 LangGraph（Phase 1，Step 5 裸版，质量闸 S6 再加）。

依据 phase1/00-architecture.md §3 章节循环 + §4.2。
节点：load_context → outline_advance → scene_plan → retrieve_memory
      → write_chapter（逐场景）→ extract_memory → save

字数控制（§字数控制机制）：scene_plan 给每场景配预算，逐场景生成，总字数天然落进范围。
事后矫正（prefix/FIM）留到 S6 与 anti-slop 闭环共用引擎。
"""
from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.storage.sqlite_store import SQLiteStore
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.memory.layered_memory import LayeredMemory
from backend.progress import ProgressStore
from backend.models.phase1 import StoryBible
from backend.models.phase1_chapter import DetailedOutline, ChapterBeat, ScenePlan, ChapterExtract
from backend.agents.phase1.chapter_agents import (
    OutlineAdvanceAgent, ScenePlanAgent, SceneWriterAgent, MemoryExtractorAgent,
)
from backend.graph.phase1_quality_gate import run_quality_gate
from backend.quality.rewrite import soft_close, expand_if_short
from backend.config import Settings

logger = logging.getLogger(__name__)

DEFAULT_TARGET_WORDS = 3500   # I4：>3000 区间软目标
BEST_OF_N = 2                 # I3/Q3：候选数，关键章可调高


def _split_even(content: str, n: int) -> list[str]:
    """把正文按段落边界（\\n\\n）尽量均分成 n 段（每段一物理章）。
    不按字符硬切，落点都在段落边界，避免切断句子；n 段达不到则返回实际段数。"""
    paras = [p for p in content.split("\n\n") if p.strip()]
    if len(paras) <= 1 or n <= 1:
        return [content]
    total = sum(len(p) for p in paras)
    cut_targets = [total * k / n for k in range(1, n)]  # 全局累计切点
    parts: list[str] = []
    cur: list[str] = []
    acc = 0  # 全局累计长度（不随分段重置，否则 n≥3 的后续切点会错位）
    ti = 0
    for p in paras:
        cur.append(p)
        acc += len(p)
        if ti < len(cut_targets) and acc >= cut_targets[ti] and len(parts) < n - 1:
            parts.append("\n\n".join(cur))
            cur = []
            ti += 1
    if cur:
        parts.append("\n\n".join(cur))
    return parts or [content]


_CN_NUM = "一二三四五六七八九十"


def _title_parts(n: int, base_title: str) -> list[str]:
    """n 个物理章的标题：1 章原样；2 章 上/下；3+ 章 一/二/…"""
    if n <= 1:
        return [base_title]
    if n == 2:
        return [f"{base_title}（上）", f"{base_title}（下）"]
    return [f"{base_title}（{_CN_NUM[i] if i < len(_CN_NUM) else i + 1}）" for i in range(n)]


import re as _re

def _strip_part_suffix(title: str) -> str:
    """去掉分页加的 （上）/（下）/（一）… 后缀，还原推进单元的基础标题（重写沿用细纲用）。"""
    return _re.sub(r"（[上下一二三四五六七八九十\d]+）\s*$", "", title or "").strip() or title


class ChapterState(TypedDict, total=False):
    story_id: str
    chapter_num: int          # 物理章号起点（本推进单元的首个物理章）
    installment_num: int      # 剧情推进单元序号（大纲按它排，切分不影响）
    target_words: int
    rewrite: bool             # 重写模式：沿用原细纲、写后清理旧单元再落库
    revision_note: str        # 重写时的可选修改意见
    # 中间产物
    bible_brief: str
    rough_stage: str
    recent_summaries: str
    open_foreshadowing: list
    detailed: DetailedOutline
    plan: ScenePlan
    facts_brief: str
    voice_profiles: str
    content: str
    word_count: int
    quality: dict
    slop_findings: list
    parts: list               # 分页后的物理章列表 [{content, title}]


def _bible_brief(bible: dict) -> str:
    """从 bible dict 提炼喂生成的简表（控 token，context-cache 友好）。"""
    c = bible.get("concept", {})
    w = bible.get("world", {})
    ps = w.get("power_system", {})
    return (
        f"书名《{c.get('title','')}》 题材：{c.get('genre','')} 基调：{c.get('tone','')}\n"
        f"金手指：{c.get('special_ability',{}).get('name','')}\n"
        f"世界观：{w.get('background','')[:200]}\n"
        f"力量体系：{ps.get('name','')}（{'→'.join(ps.get('levels',[])[:8])}）"
    )


def build_chapter_graph(llm: LLMClient, store: SQLiteStore, quads: KnowledgeQuads,
                        mem: LayeredMemory, progress: ProgressStore | None = None,
                        settings: Settings | None = None):
    settings = settings or Settings()
    outline_agent = OutlineAdvanceAgent(llm)
    plan_agent = ScenePlanAgent(llm)
    writer = SceneWriterAgent(llm)
    extractor = MemoryExtractorAgent(llm)

    async def load_context(state: ChapterState) -> ChapterState:
        sid, cn = state["story_id"], state["chapter_num"]      # cn = 本单元物理章起点
        inst = state.get("installment_num", cn)                # 剧情推进单元序号
        story = await store.get_story(sid)
        bible = story["bible"]
        rough = await store.get_rough_outline(sid)
        # 粗纲阶段按【推进单元】查，不用物理章号 —— 切分让物理章变多也不漂移剧情节奏
        stage = next((s for s in rough if (s["chapter_start"] or 0) <= inst <= (s["chapter_end"] or 9999)), None)
        stage_txt = f"{stage['stage_name']}：{stage['summary']}" if stage else "（无对应阶段，自由发挥推进主线）"
        recent = await store.get_recent_summaries(sid, before_chapter=cn, limit=3)
        recent_txt = "\n".join(f"- {r['title']}：{r['summary']}" for r in recent)  # 不强调物理章号，避免与单元号错位
        open_fore = await store.get_open_foreshadowing(sid, before_chapter=cn)
        # 角色对白指纹简表
        chars = await store.list_characters(sid)
        vp_lines = []
        for ch in chars:
            vp = ch.get("voice_profile", {})
            vp_lines.append(
                f"- {ch['name']}({ch['character_id']})：语气={vp.get('tone','')}；"
                f"口头禅={vp.get('catchphrases',[])}；句式={vp.get('sentence_style','')}；"
                f"禁用={vp.get('forbidden',[])}"
            )
        return {
            "bible_brief": _bible_brief(bible),
            "rough_stage": stage_txt,
            "recent_summaries": recent_txt,
            "open_foreshadowing": open_fore,
            "voice_profiles": "\n".join(vp_lines),
            "target_words": state.get("target_words", DEFAULT_TARGET_WORDS),
        }

    async def outline_advance(state: ChapterState) -> ChapterState:
        # 给细纲师看"待回收伏笔"（按 age 催收），让它在 beat 里安排填坑
        # 重写模式：沿用原细纲（从 outline_detailed 读回 beats），不重跑细纲师，剧情骨架不变
        if state.get("rewrite"):
            sid, start_cn = state["story_id"], state["chapter_num"]
            od = await store.get_detailed_outline(sid, start_cn)
            first_ch = await store.get_chapter(sid, start_cn)
            base_title = _strip_part_suffix(first_ch["title"]) if first_ch else "（重写）"
            beats = [ChapterBeat(beat=b.get("beat", ""), purpose=b.get("purpose", ""))
                     for b in (od or {}).get("beats", [])] or [ChapterBeat(beat="承接原细纲推进本章")]
            tags = (od or {}).get("narrative_func_tags", "")
            d = DetailedOutline(
                chapter_title=base_title,
                summary=(first_ch or {}).get("summary", "")[:60] or base_title,
                beats=beats,
                narrative_func_tags=tags.split("、") if tags else [],
            )
            return {"detailed": d}

        of = state.get("open_foreshadowing") or []
        fore_txt = "\n".join(f"- (age={f['age']}) {f['description']}" for f in of)
        d = await outline_agent.run(
            bible_brief=state["bible_brief"], rough_stage=state["rough_stage"],
            chapter_num=state.get("installment_num", state["chapter_num"]),
            recent_summaries=state["recent_summaries"],
            open_foreshadowing=fore_txt, story_id=state["story_id"])
        return {"detailed": d}

    async def scene_plan(state: ChapterState) -> ChapterState:
        chars = await store.list_characters(state["story_id"])
        cbrief = "；".join(f"{c['name']}({c['character_id']},{c['role']})" for c in chars)
        p = await plan_agent.run(
            detailed_outline=state["detailed"].model_dump_json(),
            characters_brief=cbrief, target_words=state["target_words"],
            chapter_num=state.get("installment_num", state["chapter_num"]),
            story_id=state["story_id"])
        return {"plan": p}

    async def retrieve_memory(state: ChapterState) -> ChapterState:
        """取本章生成的事实约束。#2 一致性闭环：把'硬约束'（角色生死/能力/位置）
        单列高亮，让 writer 主动规避矛盾，而不只是事后检测扣分。"""
        from backend.memory.predicates import is_single_valued, normalize_predicate
        sid, cn = state["story_id"], state["chapter_num"]
        valid = await quads.query_valid_at(sid, cn)

        # 单值谓语（存活/境界/身份/阵营）= 硬约束，违反即'死人复活'式硬伤
        hard_facts, soft_facts = [], []
        for q in valid:
            line = f"- {q['subject']} {q['predicate']} {q['object']}"
            canon = normalize_predicate(q["predicate"])
            if canon and is_single_valued(canon):
                hard_facts.append(line)
            else:
                soft_facts.append(line)

        # 角色最新状态（位置/状态/情绪）—— 冲突高发区
        states = await store.get_latest_character_states(sid, cn - 1) if cn > 1 else []
        state_lines = [
            f"- {st['character_id']}：位置={st.get('location','?')} 状态={st.get('status','?')}"
            for st in states if st.get("location") or st.get("status")
        ]

        # 分层记忆语义召回（架构 §6.4 L2/L3）：在场角色的相关 + 情感关键记忆，
        # 让 writer 知道角色"记得什么、在意谁"，维系情感连续性。
        plan = state["plan"]
        present = {plan.pov} | {c for sc in plan.scenes for c in sc.present_characters}
        present.discard("")
        detailed = state["detailed"]
        query_text = f"{detailed.summary}；" + "；".join(sc.goal for sc in plan.scenes)
        mem_lines = []
        try:
            recalled = await mem.recall(sid, list(present), query_text)
            for m in recalled:
                star = "★" if m["emotional_weight"] >= 0.7 else ""
                mem_lines.append(f"- {star}{m['character_id']}：{m['text']}")
        except Exception as e:
            logger.warning(f"[retrieve_memory] ch{cn} 记忆召回失败（降级）: {type(e).__name__}: {e}")

        parts = []
        if hard_facts:
            parts.append("【硬约束·绝不可违反（角色生死/能力/位置/境界等）】\n" + "\n".join(hard_facts[:25]))
        if state_lines:
            parts.append("【角色当前状态·须延续】\n" + "\n".join(state_lines[:10]))
        if mem_lines:
            parts.append("【角色记忆·须延续情感与认知（★=刻骨）】\n" + "\n".join(mem_lines[:16]))
        if soft_facts:
            parts.append("【背景事实】\n" + "\n".join(soft_facts[:20]))
        facts = "\n\n".join(parts) if parts else "（暂无已确立事实）"
        return {"facts_brief": facts}

    async def _draft_once(state: ChapterState) -> str:
        """逐场景生成一个完整章节候选。前一场景结尾作下一场景衔接。"""
        plan = state["plan"]
        parts: list[str] = []
        prev_tail = ""
        for sc in plan.scenes:
            scene_brief = (
                f"场景{sc.scene_id}｜地点：{sc.location}｜在场：{sc.present_characters}｜"
                f"视角：{sc.pov_character}｜目标：{sc.goal}"
            )
            text = await writer.run(
                bible_brief=state["bible_brief"], scene_brief=scene_brief,
                voice_profiles=state["voice_profiles"], facts_brief=state["facts_brief"],
                prev_text=prev_tail, word_budget=sc.word_budget,
                chapter_num=state["chapter_num"], story_id=state["story_id"],
                revision_note=state.get("revision_note", "") if state.get("rewrite") else "")
            parts.append(text.strip())
            prev_tail = text.strip()[-400:]
        return "\n\n".join(parts)

    async def write_chapter(state: ChapterState) -> ChapterState:
        """best-of-N：生成 N 个候选，各过质量闸（检测-重写-评分），选 composite 最高。"""
        import asyncio

        plan = state["plan"]
        scene_brief_all = "；".join(f"S{sc.scene_id}:{sc.goal}" for sc in plan.scenes)
        target = state["target_words"]

        # 1. 并发生成 N 个候选
        drafts = await asyncio.gather(*[_draft_once(state) for _ in range(BEST_OF_N)])

        # 2. 各候选过质量闸（检测-重写-字数矫正-Critic 评分）
        gate_results = await asyncio.gather(*[
            run_quality_gate(llm, d, target_words=target, scene_brief=scene_brief_all)
            for d in drafts
        ])

        # 3. 选 composite 最高的候选
        best = max(gate_results, key=lambda r: r["quality"]["composite_score"])
        logger.info(
            f"[write_chapter] best-of-{BEST_OF_N} ch{state['chapter_num']}: "
            f"composites={[round(r['quality']['composite_score'],2) for r in gate_results]} "
            f"-> picked {best['quality']['composite_score']:.2f} "
            f"(slop={best['quality']['slop_penalty']:.2f}, {best['quality']['word_count']}字, "
            f"rewrite_rounds={best['rounds']})"
        )
        return {
            "content": best["content"],
            "word_count": best["quality"]["word_count"],
            "quality": best["quality"],
            "slop_findings": best["slop_findings"],
        }

    async def paginate(state: ChapterState) -> ChapterState:
        """把一个推进单元的正文按目标字数切成 1..N 个物理章。
        ≤上限 或 <切分线 → 1 章（接受偏长，不造 runt）；否则等分（场景/段落边界）。
        非末章补软收束治戛然而止；个别仍 <floor 的小幅补足。"""
        content = state["content"]
        target = settings.chapter_target_words
        floor, ceiling, threshold = settings.chapter_floor, settings.chapter_ceiling, settings.chapter_split_threshold
        base_title = state["detailed"].chapter_title
        L = len(content)

        if L <= ceiling or L < threshold:
            return {"parts": [{"content": content, "title": base_title}]}

        n = max(2, round(L / max(target, 1)))
        chunks = _split_even(content, n)
        if len(chunks) < 2:  # 无可切段落边界（单大段）→ 接受偏长一章
            return {"parts": [{"content": content, "title": base_title}]}

        for i in range(len(chunks) - 1):           # 非末段：软收束
            chunks[i] = await soft_close(llm, chunks[i])
        for i in range(len(chunks)):               # 仍短于 floor：小幅补足（罕见）
            if len(chunks[i]) < floor:
                chunks[i] = await expand_if_short(llm, chunks[i], target, floor=floor)

        titles = _title_parts(len(chunks), base_title)
        logger.info(f"[paginate] inst{state.get('installment_num')} {L}字 → {len(chunks)} 章 {[len(c) for c in chunks]}")
        return {"parts": [{"content": c, "title": t} for c, t in zip(chunks, titles)]}

    async def _persist_one(sid, cn, text, title, pov, ex, base_quality, inst, detailed):
        """落一个物理章：正文/摘要、细纲、四元组(归一/冲突/失效/去重)、状态、伏笔、记忆、质量。"""
        from backend.memory.predicates import (
            normalize_predicate, is_single_valued, objects_compatible,
        )
        await store.save_chapter(sid, cn, title=title, pov=pov, content=text,
                                 summary=ex.summary, installment_num=inst)
        await store.save_detailed_outline(
            sid, cn, beats=[b.model_dump() for b in detailed.beats],
            narrative_func_tags="、".join(detailed.narrative_func_tags), word_budget=len(text))

        norm_quads, dropped = [], 0
        for q in ex.new_quads:
            canon = normalize_predicate(q.predicate)
            if not canon:
                dropped += 1
                continue
            norm_quads.append({"subject": q.subject, "predicate": canon, "object": q.object,
                               "invalidates_prior": q.invalidates_prior})
        conflicts = await quads.find_conflicts(sid, norm_quads, cn) if norm_quads else []
        if conflicts:
            logger.warning(f"[finalize] ch{cn} {len(conflicts)} 个真冲突: "
                           f"{[(c['new']['subject'], c['new']['predicate']) for c in conflicts[:3]]}")
        for q in norm_quads:
            if q["invalidates_prior"] and is_single_valued(q["predicate"]):
                for p in await quads.query_subject(sid, q["subject"], cn):
                    if (normalize_predicate(p["predicate"]) == q["predicate"]
                            and not objects_compatible(p["object"], q["object"])):
                        await quads.invalidate(p["id"], at_chapter=cn)
        if norm_quads:
            await quads.add_quads_deduped(sid, norm_quads, source_chapter=cn)

        for sc in ex.state_changes:
            await store.save_character_state(sid, sc.character_id, cn, location=sc.location,
                                             status=sc.status, emotional_state=sc.emotional_state,
                                             state={"note": sc.note})
        if ex.resolved_foreshadowing:
            await store.resolve_foreshadowing(sid, ex.resolved_foreshadowing, cn)
        if ex.foreshadowing:
            await store.save_foreshadowing(sid, cn, ex.foreshadowing)
        if ex.memories:
            try:
                await mem.remember_batch(sid, [m.model_dump() for m in ex.memories], chapter=cn)
            except Exception as e:
                logger.warning(f"[finalize] ch{cn} 记忆写入失败: {type(e).__name__}: {e}")

        # 质量：各物理章共享单元维度分，仅本章一致性冲突单独扣（用户选定 installment 共享）
        q = base_quality or {}
        if q:
            consistency_penalty = min(len(conflicts) * 0.5, 2.0)
            comp = q.get("composite_score", 0) - consistency_penalty
            await store.save_quality(
                sid, cn, dim_scores=q.get("dim_scores", {}), mean_quality=q.get("mean_quality", 0),
                slop_penalty=q.get("slop_penalty", 0), composite_score=round(comp, 3),
                word_count=len(text), judge_model="+".join(q.get("judges", [])), slop_findings=[])
            await store.save_chapter(sid, cn, title=title, pov=pov, content=text, summary=ex.summary,
                                     installment_num=inst,
                                     quality={**q, "word_count": len(text),
                                              "consistency_conflicts": len(conflicts),
                                              "composite_final": round(comp, 3)})

    async def finalize(state: ChapterState) -> ChapterState:
        """逐物理章：抽取记忆 + 落库。一个推进单元产出 1..N 个物理章（共享单元质量分）。"""
        sid = state["story_id"]
        start_cn = state["chapter_num"]
        inst = state.get("installment_num", start_cn)
        detailed: DetailedOutline = state["detailed"]
        plan: ScenePlan = state["plan"]
        base_quality = state.get("quality", {})
        parts = state.get("parts") or [{"content": state["content"], "title": detailed.chapter_title}]

        chars = await store.list_characters(sid)
        char_ids = "、".join(f"{c['name']}={c['character_id']}" for c in chars)

        for i, part in enumerate(parts):
            cn = start_cn + i
            # 逐章刷新待回收伏笔，使同单元内 A 埋 B 收也能衔接
            of = await store.get_open_foreshadowing(sid, before_chapter=cn)
            fore_txt = "\n".join(f"{f['id']}: {f['description']}" for f in of)
            ex = await extractor.run(chapter_text=part["content"], character_ids=char_ids,
                                     chapter_num=cn, open_foreshadowing=fore_txt, story_id=sid)
            await _persist_one(sid, cn, part["content"], part["title"], plan.pov, ex,
                               base_quality, inst, detailed)
        if len(parts) > 1:
            logger.info(f"[finalize] inst{inst} 落 {len(parts)} 物理章: {start_cn}~{start_cn + len(parts) - 1}")
        return {}

    async def purge(state: ChapterState) -> ChapterState:
        """重写模式专用：新稿已生成（state.parts），在落库前清理旧推进单元的全部痕迹。
        正常生成时为空操作。放在 write/paginate 之后、finalize 之前（写成功才清，无数据空洞）。"""
        if not state.get("rewrite"):
            return {}
        sid = state["story_id"]
        inst = state.get("installment_num", state["chapter_num"])
        nums = await store.get_installment_chapter_nums(sid, inst)
        if not nums:
            return {}
        # 1. 先删 ChromaDB 记忆向量（须在删 SQLite 行前，靠 vector_id）
        try:
            await mem.forget_chapters(sid, nums)
        except Exception as e:
            logger.warning(f"[purge] inst{inst} 向量清理失败（不阻断）: {type(e).__name__}: {e}")
        # 2. 四元组：删本单元新增 + 还原被本单元失效的更早事实
        await quads.delete_by_source(sid, nums)
        await quads.restore_invalidated_at(sid, nums)
        # 3. SQLite：章节/细纲/状态/记忆行/质量 + 伏笔（埋删、收还原）
        await store.purge_installment_chapters(sid, nums)
        logger.info(f"[purge] inst{inst} 清理旧物理章 {nums}（重写）")
        return {}

    def _staged(name, fn):
        """包一层：节点开头上报进度阶段（progress 为 None 时无副作用，如压测）。"""
        async def wrapped(state: ChapterState) -> ChapterState:
            if progress is not None:
                progress.enter_stage(state["story_id"], name)
            return await fn(state)
        return wrapped

    g = StateGraph(ChapterState)
    for name, fn in [
        ("load_context", load_context), ("outline_advance", outline_advance),
        ("scene_plan", scene_plan), ("retrieve_memory", retrieve_memory),
        ("write_chapter", write_chapter), ("paginate", paginate),
        ("purge", purge), ("finalize", finalize),
    ]:
        g.add_node(name, _staged(name, fn))
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "outline_advance")
    g.add_edge("outline_advance", "scene_plan")
    g.add_edge("scene_plan", "retrieve_memory")
    g.add_edge("retrieve_memory", "write_chapter")
    g.add_edge("write_chapter", "paginate")
    g.add_edge("paginate", "purge")       # 重写：写成功后清理旧单元；正常生成时 purge 为空操作
    g.add_edge("purge", "finalize")
    g.add_edge("finalize", END)
    return g.compile()
