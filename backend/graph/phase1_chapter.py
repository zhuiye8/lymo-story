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
from backend.models.phase1 import StoryBible
from backend.models.phase1_chapter import DetailedOutline, ScenePlan, ChapterExtract
from backend.agents.phase1.chapter_agents import (
    OutlineAdvanceAgent, ScenePlanAgent, SceneWriterAgent, MemoryExtractorAgent,
)
from backend.graph.phase1_quality_gate import run_quality_gate

logger = logging.getLogger(__name__)

DEFAULT_TARGET_WORDS = 3500   # I4：>3000 区间软目标
BEST_OF_N = 2                 # I3/Q3：候选数，关键章可调高


class ChapterState(TypedDict, total=False):
    story_id: str
    chapter_num: int
    target_words: int
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
    extract: ChapterExtract


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
                        mem: LayeredMemory):
    outline_agent = OutlineAdvanceAgent(llm)
    plan_agent = ScenePlanAgent(llm)
    writer = SceneWriterAgent(llm)
    extractor = MemoryExtractorAgent(llm)

    async def load_context(state: ChapterState) -> ChapterState:
        sid, cn = state["story_id"], state["chapter_num"]
        story = await store.get_story(sid)
        bible = story["bible"]
        rough = await store.get_rough_outline(sid)
        # 找当前章号所属的粗纲阶段
        stage = next((s for s in rough if (s["chapter_start"] or 0) <= cn <= (s["chapter_end"] or 9999)), None)
        stage_txt = f"{stage['stage_name']}：{stage['summary']}" if stage else "（无对应阶段，自由发挥推进主线）"
        recent = await store.get_recent_summaries(sid, before_chapter=cn, limit=3)
        recent_txt = "\n".join(f"第{r['chapter_num']}章 {r['title']}：{r['summary']}" for r in recent)
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
        of = state.get("open_foreshadowing") or []
        fore_txt = "\n".join(f"- (age={f['age']}) {f['description']}" for f in of)
        d = await outline_agent.run(
            bible_brief=state["bible_brief"], rough_stage=state["rough_stage"],
            chapter_num=state["chapter_num"], recent_summaries=state["recent_summaries"],
            open_foreshadowing=fore_txt, story_id=state["story_id"])
        return {"detailed": d}

    async def scene_plan(state: ChapterState) -> ChapterState:
        chars = await store.list_characters(state["story_id"])
        cbrief = "；".join(f"{c['name']}({c['character_id']},{c['role']})" for c in chars)
        p = await plan_agent.run(
            detailed_outline=state["detailed"].model_dump_json(),
            characters_brief=cbrief, target_words=state["target_words"],
            chapter_num=state["chapter_num"], story_id=state["story_id"])
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
                chapter_num=state["chapter_num"], story_id=state["story_id"])
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

    async def extract_memory(state: ChapterState) -> ChapterState:
        sid, cn = state["story_id"], state["chapter_num"]
        chars = await store.list_characters(sid)
        char_ids = "、".join(f"{c['name']}={c['character_id']}" for c in chars)
        # 给抽取器看"待回收伏笔(id: 内容)"，让它标记本章兑现了哪些
        of = state.get("open_foreshadowing") or []
        fore_txt = "\n".join(f"{f['id']}: {f['description']}" for f in of)
        ex = await extractor.run(
            chapter_text=state["content"], character_ids=char_ids,
            chapter_num=cn, open_foreshadowing=fore_txt, story_id=sid)
        return {"extract": ex}

    async def save(state: ChapterState) -> ChapterState:
        sid, cn = state["story_id"], state["chapter_num"]
        ex: ChapterExtract = state["extract"]
        plan: ScenePlan = state["plan"]
        detailed: DetailedOutline = state["detailed"]

        # 1. 章节正文 + 摘要
        await store.save_chapter(
            sid, cn, title=detailed.chapter_title, pov=plan.pov,
            content=state["content"], summary=ex.summary)
        # 2. 细纲落库
        await store.save_detailed_outline(
            sid, cn, beats=[b.model_dump() for b in detailed.beats],
            narrative_func_tags="、".join(detailed.narrative_func_tags),
            word_budget=state["target_words"])
        # 3. 归一 + 过滤四元组：只留持久状态事实，事件/动作谓语（修改/执行/…）丢弃归摘要。
        #    这是 #2 根因修复——否则事件四元组累积，撞出大量误报冲突。
        from backend.memory.predicates import (
            normalize_predicate, is_single_valued, objects_compatible,
        )
        norm_quads, dropped = [], 0
        for q in ex.new_quads:
            canon = normalize_predicate(q.predicate)
            if not canon:
                dropped += 1
                continue
            norm_quads.append({
                "subject": q.subject, "predicate": canon, "object": q.object,
                "invalidates_prior": q.invalidates_prior,
            })
        if dropped:
            logger.info(f"[save] ch{cn} 丢弃 {dropped} 个事件/非状态四元组（归摘要不入库）")

        # 4. 一致性检测（② 层，精确：单值离散谓语 + object 不兼容 + 未声明失效才算真矛盾）
        conflicts = await quads.find_conflicts(sid, norm_quads, cn) if norm_quads else []
        if conflicts:
            logger.warning(f"[save] ch{cn} 检测到 {len(conflicts)} 个真冲突: "
                           f"{[(c['new']['subject'], c['new']['predicate']) for c in conflicts[:3]]}")

        # 5. 失效处理：仅单值离散谓语的真转移（境界突破/死亡），且新旧值不兼容才失效旧值
        for q in norm_quads:
            if q["invalidates_prior"] and is_single_valued(q["predicate"]):
                priors = await quads.query_subject(sid, q["subject"], cn)
                for p in priors:
                    if (normalize_predicate(p["predicate"]) == q["predicate"]
                            and not objects_compatible(p["object"], q["object"])):
                        await quads.invalidate(p["id"], at_chapter=cn)

        # 6. 去重写入（跳过同义改写/细化，根除反复入库膨胀）
        if norm_quads:
            inserted, skipped = await quads.add_quads_deduped(sid, norm_quads, source_chapter=cn)
            if skipped:
                logger.info(f"[save] ch{cn} 去重跳过 {skipped} 个同义事实，入库 {inserted}")

        # 6b. 角色状态变化（→ character_states 表，易变态：位置/即时状态/情绪）
        for sc in ex.state_changes:
            await store.save_character_state(
                sid, sc.character_id, cn,
                location=sc.location, status=sc.status, emotional_state=sc.emotional_state,
                state={"note": sc.note})

        # 6c. 伏笔闭环：先回收本章兑现的旧坑，再记录新埋的坑（埋坑/填坑）
        if ex.resolved_foreshadowing:
            n = await store.resolve_foreshadowing(sid, ex.resolved_foreshadowing, cn)
            if n:
                logger.info(f"[save] ch{cn} 回收伏笔 {n} 个")
        if ex.foreshadowing:
            await store.save_foreshadowing(sid, cn, ex.foreshadowing)

        # 6d. 分层记忆：写入本章角色情感关键记忆（L1）→ SQLite + ChromaDB
        if ex.memories:
            try:
                wrote = await mem.remember_batch(
                    sid, [m.model_dump() for m in ex.memories], chapter=cn)
                if wrote:
                    logger.info(f"[save] ch{cn} 写入角色记忆 {wrote} 条")
            except Exception as e:
                logger.warning(f"[save] ch{cn} 记忆写入失败（不阻断）: {type(e).__name__}: {e}")

        # 7. 质量落库（喂 quality_admin 4 图表）+ 一致性冲突计入 quality
        q = state.get("quality", {})
        if q:
            # 有事实冲突 → composite 额外惩罚（一致性是硬指标）
            consistency_penalty = min(len(conflicts) * 0.5, 2.0)
            comp = q["composite_score"] - consistency_penalty
            await store.save_quality(
                sid, cn,
                dim_scores=q.get("dim_scores", {}),
                mean_quality=q.get("mean_quality", 0),
                slop_penalty=q.get("slop_penalty", 0),
                composite_score=round(comp, 3),
                word_count=q.get("word_count", state.get("word_count", 0)),
                judge_model="+".join(q.get("judges", [])),
                slop_findings=state.get("slop_findings", []),
            )
            # 把最终 quality 快照也写进章节
            await store.save_chapter(
                sid, cn, title=detailed.chapter_title, pov=plan.pov,
                content=state["content"], summary=ex.summary,
                quality={**q, "consistency_conflicts": len(conflicts), "composite_final": round(comp, 3)})
        return {}

    g = StateGraph(ChapterState)
    for name, fn in [
        ("load_context", load_context), ("outline_advance", outline_advance),
        ("scene_plan", scene_plan), ("retrieve_memory", retrieve_memory),
        ("write_chapter", write_chapter), ("extract_memory", extract_memory), ("save", save),
    ]:
        g.add_node(name, fn)
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "outline_advance")
    g.add_edge("outline_advance", "scene_plan")
    g.add_edge("scene_plan", "retrieve_memory")
    g.add_edge("retrieve_memory", "write_chapter")
    g.add_edge("write_chapter", "extract_memory")
    g.add_edge("extract_memory", "save")
    g.add_edge("save", END)
    return g.compile()
