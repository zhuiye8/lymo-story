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
    Concept, WorldSetting, WorldCore, FactionList, WorldRuleList,
    Characters, CharacterDesign, CharacterRoster,
    Outline, OutlineSkeleton, VolumeList, StoryBible,
)
from backend.prompts.phase1.init_prompts import (
    concept_prompt, title_prompt, blurb_prompt, world_core_prompt, faction_list_prompt, world_rule_prompt,
    character_roster_prompt, single_character_prompt,
    outline_skeleton_prompt, volume_list_prompt,
)

logger = logging.getLogger(__name__)


def _dump(model) -> str:
    return model.model_dump_json(indent=2)


class ConceptAgent(BaseAgent):
    name = "concept"

    async def run(self, *, theme: str, requirements: str = "", title: str = "", story_id: str | None = None) -> Concept:
        sys, usr = concept_prompt(theme, requirements, title)
        return await self._call_structured(sys, usr, Concept, story_id=story_id, temperature=0.7, max_tokens=2048)

    async def gen_title(self, *, genre: str, tone: str, synopsis: str, ability: str,
                        avoid: str = "", story_id: str | None = None) -> str:
        """只重生成书名（基于已有设定），返回纯书名字符串。"""
        sys, usr = title_prompt(genre, tone, synopsis, ability, avoid)
        raw = await self._call_text(sys, usr, story_id=story_id, temperature=0.95, max_tokens=64)
        t = (raw or "").strip().splitlines()[0] if raw.strip() else ""
        return t.strip().strip("《》\"'“” ·").strip()[:30]

    async def gen_blurb(self, *, title: str, genre: str, tone: str, synopsis: str,
                        ability: str, story_id: str | None = None) -> str:
        """只重生成作品简介（面向读者的营销文案），返回纯文本。"""
        sys, usr = blurb_prompt(title, genre, tone, synopsis, ability)
        raw = await self._call_text(sys, usr, story_id=story_id, temperature=0.9, max_tokens=512)
        return (raw or "").strip()


class WorldBuilderAgent(BaseAgent):
    """3 步：背景+力量体系 → 势力 → 世界规则。每步小而稳，聚合成 WorldSetting。"""
    name = "world_builder"

    async def run(self, *, concept: Concept, story_id: str | None = None) -> WorldSetting:
        c_json = _dump(concept)
        # 步骤 1：背景 + 力量体系
        sys1, usr1 = world_core_prompt(c_json)
        core = await self._call_structured(sys1, usr1, WorldCore, story_id=story_id,
                                           temperature=0.7, max_tokens=2048)
        core_json = _dump(core)
        # 步骤 2：势力
        sys2, usr2 = faction_list_prompt(c_json, core_json)
        flist = await self._call_structured(sys2, usr2, FactionList, story_id=story_id,
                                            temperature=0.7, max_tokens=2048)
        # 步骤 3：世界规则
        sys3, usr3 = world_rule_prompt(c_json, core_json)
        rlist = await self._call_structured(sys3, usr3, WorldRuleList, story_id=story_id,
                                            temperature=0.6, max_tokens=1536)
        return WorldSetting(
            background=core.background, power_system=core.power_system,
            factions=flist.factions, world_rules=rlist.world_rules,
        )


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
                                            story_id=story_id, temperature=0.8, max_tokens=4096)
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
    """2 步：骨架（粗纲+弧线+标签）→ 分卷。聚合成 Outline。"""
    name = "outline_planner"

    async def run(self, *, concept: Concept, world: WorldSetting, characters: Characters,
                  target_chapters: int = 60, story_id: str | None = None) -> Outline:
        # 步骤 1：骨架
        sys1, usr1 = outline_skeleton_prompt(_dump(concept), _dump(world), _dump(characters), target_chapters)
        skel = await self._call_structured(sys1, usr1, OutlineSkeleton, story_id=story_id,
                                           temperature=0.6, max_tokens=2560)
        # 步骤 2：分卷
        sys2, usr2 = volume_list_prompt(_dump(skel), target_chapters)
        vlist = await self._call_structured(sys2, usr2, VolumeList, story_id=story_id,
                                            temperature=0.6, max_tokens=3072)
        return Outline(
            rough_stages=skel.rough_stages, volumes=vlist.volumes,
            initial_conflicts=skel.initial_conflicts, planned_arc=skel.planned_arc,
            narrative_func_tags=skel.narrative_func_tags,
        )


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
