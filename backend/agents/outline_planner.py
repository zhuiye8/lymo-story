from backend.agents.base import BaseAgent
from backend.prompts.outline_planner import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_REVISE,
    build_user_prompt,
    build_revise_prompt,
)


class OutlinePlannerAgent(BaseAgent):
    name = "outline_planner"

    async def run(
        self,
        *,
        concept: dict,
        world_setting: dict,
        characters_design: dict,
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(concept, world_setting, characters_design)
        return await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=6144,
        )

    async def revise(
        self,
        *,
        concept: dict,
        world_setting: dict,
        characters_design: dict,
        current_outline: dict,
        user_instructions: str = "",
        story_id: str | None = None,
    ) -> dict:
        """Regenerate the outline based on the current one + user feedback.

        Preserves the story DNA (concept/world/characters) but produces a
        fresh volume structure. User instructions can steer direction like
        "把反派改得更复杂" or "第二卷节奏加快"."""
        user_prompt = build_revise_prompt(
            concept=concept,
            world_setting=world_setting,
            characters_design=characters_design,
            current_outline=current_outline,
            user_instructions=user_instructions,
        )
        return await self._call_json(
            SYSTEM_PROMPT_REVISE,
            user_prompt,
            story_id=story_id,
            max_tokens=6144,
        )
