"""初始化管线 LangGraph（Phase 1）。

依据 phase1/00-architecture.md §3 初始化管线 + §4.1。
5 节点线性：concept → world_build → character_design → outline_plan → assemble+persist。

落库：把 StoryBible 拆进新 schema
  - stories.bible_json（完整 bible）
  - characters（含 voice_profile）
  - outline_rough（5 段粗纲）
  - knowledge_quads（从角色/世界设定抽初始事实）
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.storage.sqlite_store import SQLiteStore
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.memory.layered_memory import LayeredMemory
from backend.models.phase1 import Concept, WorldSetting, Characters, Outline, StoryBible
from backend.agents.phase1.init_agents import (
    ConceptAgent, WorldBuilderAgent, CharacterDesignerAgent, OutlinePlannerAgent, assemble_bible,
)


class InitState(TypedDict, total=False):
    story_id: str
    theme: str
    requirements: str
    title: str
    target_chapters: int
    concept: Concept
    world: WorldSetting
    characters: Characters
    outline: Outline
    bible: StoryBible


def build_init_graph(llm: LLMClient, store: SQLiteStore, quads: KnowledgeQuads,
                     mem: LayeredMemory):
    concept_agent = ConceptAgent(llm)
    world_agent = WorldBuilderAgent(llm)
    char_agent = CharacterDesignerAgent(llm)
    outline_agent = OutlinePlannerAgent(llm)

    async def concept_node(state: InitState) -> InitState:
        c = await concept_agent.run(
            theme=state["theme"], requirements=state.get("requirements", ""),
            title=state.get("title", ""), story_id=state["story_id"])
        return {"concept": c}

    async def world_node(state: InitState) -> InitState:
        w = await world_agent.run(concept=state["concept"], story_id=state["story_id"])
        return {"world": w}

    async def character_node(state: InitState) -> InitState:
        ch = await char_agent.run(concept=state["concept"], world=state["world"], story_id=state["story_id"])
        return {"characters": ch}

    async def outline_node(state: InitState) -> InitState:
        o = await outline_agent.run(
            concept=state["concept"], world=state["world"], characters=state["characters"],
            target_chapters=state.get("target_chapters", 60), story_id=state["story_id"])
        return {"outline": o}

    async def assemble_node(state: InitState) -> InitState:
        sid = state["story_id"]
        bible = assemble_bible(state["concept"], state["world"], state["characters"], state["outline"])

        # 1. bible 落库
        await store.save_bible(sid, bible.model_dump())

        # 2. 角色（含 voice_profile）落库
        all_chars = [bible.characters.protagonist, bible.characters.antagonist, *bible.characters.supporting]
        for cd in all_chars:
            await store.save_character(
                sid, cd.character_id, name=cd.name, role=cd.role,
                profile=cd.model_dump(exclude={"voice_profile"}),
                voice_profile=cd.voice_profile.model_dump())
            # 角色初始状态（第 0 章 = 设定基线）
            await store.save_character_state(sid, cd.character_id, 0, status="登场前", emotional_state="")
            # L0 身份核心记忆（恒在场，定义"这个角色是谁"）
            identity = "；".join(p for p in [
                f"我是{cd.name}，{cd.role}",
                f"性格：{cd.personality}" if cd.personality else "",
                f"出身：{cd.background}" if cd.background else "",
                f"我想要：{cd.goals}" if cd.goals else "",
                f"我的软肋：{cd.weaknesses}" if cd.weaknesses else "",
            ] if p)
            await mem.seed_identity(sid, cd.character_id, identity)

        # 3. 粗纲落库
        await store.save_rough_outline(sid, [s.model_dump() for s in bible.outline.rough_stages])

        # 4. 初始状态四元组（valid_from=0 设定基线）。与章节路径同一套受控谓语：
        #    只 seed 持久状态事实——存活基线（死人复活检测的 ch0 锚点）+ 初始身份。
        #    目标=动机非状态事实、境界序列=力量阶梯均已在 bible_brief，不入四元组。
        from backend.memory.predicates import normalize_predicate
        init_quads: list[dict] = []
        for cd in all_chars:
            init_quads.append({"subject": cd.name, "predicate": "存活状态", "object": "存活"})
            if cd.role:
                init_quads.append({"subject": cd.name, "predicate": "身份", "object": cd.role})
        # 防御性归一过滤（同章节路径），再去重写入
        init_quads = [{**q, "predicate": normalize_predicate(q["predicate"])}
                      for q in init_quads if normalize_predicate(q["predicate"])]
        if init_quads:
            await quads.add_quads_deduped(sid, init_quads, source_chapter=0)

        await store.update_story_status(sid, "bible_ready")
        return {"bible": bible}

    g = StateGraph(InitState)
    g.add_node("concept", concept_node)
    g.add_node("world_build", world_node)
    g.add_node("character_design", character_node)
    g.add_node("outline_plan", outline_node)
    g.add_node("assemble", assemble_node)
    g.add_edge(START, "concept")
    g.add_edge("concept", "world_build")
    g.add_edge("world_build", "character_design")
    g.add_edge("character_design", "outline_plan")
    g.add_edge("outline_plan", "assemble")
    g.add_edge("assemble", END)
    return g.compile()
