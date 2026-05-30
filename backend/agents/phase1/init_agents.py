"""初始化管线 agent（Phase 1）。

依据 phase1/00-architecture.md §4.1。
4 个 LLM agent（concept/world/character/outline）用 _call_structured 返回校验对象；
assemble_bible 无 LLM，纯合并。
"""
from __future__ import annotations

import json

import logging

from backend.agents.base import BaseAgent
from backend.models.phase1 import (
    Concept, WorldSetting, Characters, CharacterDesign, CharacterRoster, Outline, StoryBible,
)
from backend.prompts.phase1.init_prompts import (
    concept_prompt, world_builder_prompt, character_roster_prompt,
    single_character_prompt, outline_planner_prompt,
)

logger = logging.getLogger(__name__)


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
    """两阶段：先出角色名单（轻量），再逐角色出完整设定（每次输出小而稳）。

    修 Phase 0/S5 的病：一次性出全部角色含 voice_profile 会撞 max_tokens 截断。
    逐角色生成时把已生成角色的对白指纹喂进去，强制 voice 差异化。
    """
    name = "character_designer"

    async def run(self, *, concept: Concept, world: WorldSetting, story_id: str | None = None) -> Characters:
        c_json, w_json = _dump(concept), _dump(world)

        # 阶段 1：角色名单（轻量）
        sys, usr = character_roster_prompt(c_json, w_json)
        roster = await self._call_structured(sys, usr, CharacterRoster,
                                             story_id=story_id, temperature=0.7, max_tokens=1024)
        roster_brief = "\n".join(f"- {e.name}({e.character_id},{e.role})：{e.one_line}" for e in roster.entries)

        # 阶段 2：逐角色出完整设定，累积已生成的 voice 供差异化参考
        designs: list[CharacterDesign] = []
        existing_voices = ""
        for entry in roster.entries:
            sys2, usr2 = single_character_prompt(
                c_json, w_json, roster_brief, entry.model_dump_json(), existing_voices)
            cd = await self._call_structured(sys2, usr2, CharacterDesign,
                                            story_id=story_id, temperature=0.8, max_tokens=2048)
            # 强制 id/role 与名单一致（防模型漂移）
            cd.character_id = entry.character_id
            cd.role = entry.role
            designs.append(cd)
            vp = cd.voice_profile
            existing_voices += (f"- {cd.name}：语气={vp.tone}；口头禅={vp.catchphrases}；"
                                f"句式={vp.sentence_style}\n")

        # 聚合成 Characters
        prot = next((d for d in designs if d.role == "protagonist"), None)
        anta = next((d for d in designs if d.role == "antagonist"), None)
        supp = [d for d in designs if d.role not in ("protagonist", "antagonist")]
        # 兜底：名单没明确标 protagonist/antagonist 时取前两个
        if prot is None and designs:
            prot = designs[0]
            supp = [d for d in supp if d is not prot]
        if anta is None:
            rest = [d for d in designs if d is not prot]
            anta = rest[0] if rest else prot
            supp = [d for d in supp if d is not anta]
        return Characters(protagonist=prot, antagonist=anta, supporting=supp)


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
