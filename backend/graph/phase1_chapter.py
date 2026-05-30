"""章节生成 LangGraph（Phase 1，Step 5 裸版，质量闸 S6 再加）。

依据 phase1/00-architecture.md §3 章节循环 + §4.2。
节点：load_context → outline_advance → scene_plan → retrieve_memory
      → write_chapter（逐场景）→ extract_memory → save

字数控制（§字数控制机制）：scene_plan 给每场景配预算，逐场景生成，总字数天然落进范围。
事后矫正（prefix/FIM）留到 S6 与 anti-slop 闭环共用引擎。
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.storage.sqlite_store import SQLiteStore
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.models.phase1 import StoryBible
from backend.models.phase1_chapter import DetailedOutline, ScenePlan, ChapterExtract
from backend.agents.phase1.chapter_agents import (
    OutlineAdvanceAgent, ScenePlanAgent, SceneWriterAgent, MemoryExtractorAgent,
)

DEFAULT_TARGET_WORDS = 3500   # I4：>3000 区间软目标


class ChapterState(TypedDict, total=False):
    story_id: str
    chapter_num: int
    target_words: int
    # 中间产物
    bible_brief: str
    rough_stage: str
    recent_summaries: str
    detailed: DetailedOutline
    plan: ScenePlan
    facts_brief: str
    voice_profiles: str
    content: str
    word_count: int
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


def build_chapter_graph(llm: LLMClient, store: SQLiteStore, quads: KnowledgeQuads):
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
            "voice_profiles": "\n".join(vp_lines),
            "target_words": state.get("target_words", DEFAULT_TARGET_WORDS),
        }

    async def outline_advance(state: ChapterState) -> ChapterState:
        d = await outline_agent.run(
            bible_brief=state["bible_brief"], rough_stage=state["rough_stage"],
            chapter_num=state["chapter_num"], recent_summaries=state["recent_summaries"],
            story_id=state["story_id"])
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
        sid, cn = state["story_id"], state["chapter_num"]
        valid = await quads.query_valid_at(sid, cn)
        facts = "\n".join(f"- {q['subject']} {q['predicate']} {q['object']}" for q in valid[:40])
        return {"facts_brief": facts or "（暂无已确立事实）"}

    async def write_chapter(state: ChapterState) -> ChapterState:
        """逐场景生成，拼成整章。前一场景结尾作为下一场景上文衔接。"""
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
            prev_tail = text.strip()[-400:]  # 末 400 字作下场景衔接
        content = "\n\n".join(parts)
        return {"content": content, "word_count": len(content)}

    async def extract_memory(state: ChapterState) -> ChapterState:
        sid, cn = state["story_id"], state["chapter_num"]
        chars = await store.list_characters(sid)
        char_ids = "、".join(f"{c['name']}={c['character_id']}" for c in chars)
        ex = await extractor.run(
            chapter_text=state["content"], character_ids=char_ids,
            chapter_num=cn, story_id=sid)
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
        # 3. 新四元组（含失效处理）
        new_q = []
        for q in ex.new_quads:
            if q.invalidates_prior:
                # 该 subject+predicate 的旧有效事实在本章失效
                priors = await quads.query_subject(sid, q.subject, cn)
                for p in priors:
                    if p["predicate"] == q.predicate and p["object"] != q.object:
                        await quads.invalidate(p["id"], at_chapter=cn)
            new_q.append({"subject": q.subject, "predicate": q.predicate, "object": q.object})
        if new_q:
            await quads.add_quads_batch(sid, new_q, source_chapter=cn)
        # 4. 角色状态变化
        for sc in ex.state_changes:
            await store.save_character_state(
                sid, sc.character_id, cn,
                location=sc.location, status=sc.status, emotional_state=sc.emotional_state,
                state={"note": sc.note})
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
