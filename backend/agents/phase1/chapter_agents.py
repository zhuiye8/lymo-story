"""章节生成管线 agent（Phase 1）。

依据 phase1/00-architecture.md §4.2。
outline_advance / scene_plan / extract_memory 走 _call_structured；
write_scene 走 _call_text（纯散文）。
"""
from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.phase1_chapter import DetailedOutline, ScenePlan, ChapterExtract
from backend.prompts.phase1.chapter_prompts import (
    outline_advance_prompt, scene_plan_prompt, write_scene_prompt, extract_memory_prompt,
)


class OutlineAdvanceAgent(BaseAgent):
    name = "outline_advance"

    async def run(self, *, bible_brief: str, rough_stage: str, chapter_num: int,
                  recent_summaries: str, open_foreshadowing: str = "",
                  story_id: str | None = None) -> DetailedOutline:
        sys, usr = outline_advance_prompt(bible_brief, rough_stage, chapter_num,
                                          recent_summaries, open_foreshadowing)
        return await self._call_structured(sys, usr, DetailedOutline,
                                           story_id=story_id, chapter_num=chapter_num,
                                           temperature=0.6, max_tokens=2048)


class ScenePlanAgent(BaseAgent):
    name = "scene_plan"

    async def run(self, *, detailed_outline: str, characters_brief: str, target_words: int,
                  chapter_num: int, story_id: str | None = None) -> ScenePlan:
        sys, usr = scene_plan_prompt(detailed_outline, characters_brief, target_words)
        return await self._call_structured(sys, usr, ScenePlan,
                                           story_id=story_id, chapter_num=chapter_num,
                                           temperature=0.6, max_tokens=2048)


class SceneWriterAgent(BaseAgent):
    name = "scene_writer"

    async def run(self, *, bible_brief: str, scene_brief: str, voice_profiles: str,
                  facts_brief: str, prev_text: str, word_budget: int,
                  chapter_num: int, story_id: str | None = None,
                  revision_note: str = "") -> str:
        sys, usr = write_scene_prompt(bible_brief, scene_brief, voice_profiles,
                                      facts_brief, prev_text, word_budget, revision_note)
        # 字数预算 → max_tokens：中文约 1.6 token/字，留余量
        max_tok = int(word_budget * 2.2) + 512
        return await self._call_text(sys, usr, story_id=story_id, chapter_num=chapter_num,
                                     temperature=0.85, max_tokens=max_tok)


class MemoryExtractorAgent(BaseAgent):
    name = "memory_extractor"

    async def run(self, *, chapter_text: str, character_ids: str, chapter_num: int,
                  open_foreshadowing: str = "", story_id: str | None = None) -> ChapterExtract:
        sys, usr = extract_memory_prompt(chapter_text, character_ids, chapter_num,
                                         open_foreshadowing)
        return await self._call_structured(sys, usr, ChapterExtract,
                                           story_id=story_id, chapter_num=chapter_num,
                                           temperature=0.3, max_tokens=2048)
