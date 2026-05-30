"""初始化管线 agent（Phase 1）。

依据 phase1/00-architecture.md §4.1。
4 个 LLM agent（concept/world/character/outline）用 _call_structured 返回校验对象；
assemble_bible 无 LLM，纯合并。
"""
from __future__ import annotations

import json

from backend.agents.base import BaseAgent
from backend.models.phase1 import (
    Concept, WorldSetting, Characters, Outline, StoryBible,
)
from backend.prompts.phase1.init_prompts import (
    concept_prompt, world_builder_prompt, character_designer_prompt, outline_planner_prompt,
)


def _dump(model) -> str:
    return model.model_dump_json(indent=2)


class ConceptAgent(BaseAgent):
    name = "concept"

    async def run(self, *, theme: str, requirements: str = "", title: str = "", story_id: str | None = None) -> Concept:
        sys, usr = concept_prompt(theme, requirements, title)
        return await self._call_structured(sys, usr, Concept, story_id=story_id, temperature=0.7, max_tokens=2048)


class WorldBuilderAgent(BaseAgent):
    name = "world_builder"

    async def run(self, *, concept: Concept, story_id: str | None = None) -> WorldSetting:
        sys, usr = world_builder_prompt(_dump(concept))
        return await self._call_structured(sys, usr, WorldSetting, story_id=story_id, temperature=0.7, max_tokens=3072)


class CharacterDesignerAgent(BaseAgent):
    name = "character_designer"

    async def run(self, *, concept: Concept, world: WorldSetting, story_id: str | None = None) -> Characters:
        sys, usr = character_designer_prompt(_dump(concept), _dump(world))
        return await self._call_structured(sys, usr, Characters, story_id=story_id, temperature=0.75, max_tokens=4096)


class OutlinePlannerAgent(BaseAgent):
    name = "outline_planner"

    async def run(self, *, concept: Concept, world: WorldSetting, characters: Characters,
                  target_chapters: int = 60, story_id: str | None = None) -> Outline:
        sys, usr = outline_planner_prompt(_dump(concept), _dump(world), _dump(characters), target_chapters)
        return await self._call_structured(sys, usr, Outline, story_id=story_id, temperature=0.6, max_tokens=4096)


def assemble_bible(concept: Concept, world: WorldSetting, characters: Characters, outline: Outline) -> StoryBible:
    """无 LLM：合并成完整 StoryBible V3。primary_pov 取主角 id。"""
    return StoryBible(
        concept=concept,
        world=world,
        characters=characters,
        outline=outline,
        primary_pov=characters.protagonist.character_id,
        style_guide=f"{concept.tone}；{concept.genre}",
    )
