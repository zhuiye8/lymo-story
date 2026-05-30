"""Agent 基类（Phase 1 升级）。

依据 phase1/01-implementation-plan.md Step 3.2。

变化：_call_structured 接受 response_model（Pydantic 类），返回校验过的实例
（底层走 LLMClient.complete_structured → Instructor from_litellm + reask）。
保留 _call_text 纯文本（Writer 散文用）。
旧 _call_json（裸 dict）保留作过渡/无 schema 场景。
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    @abstractmethod
    async def run(self, **kwargs):
        ...

    async def _call_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        *,
        story_id: str | None = None,
        chapter_num: int | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> T:
        """结构化输出：返回校验过的 Pydantic 对象（Instructor + reask 自愈）。"""
        return await self.llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
            agent_name=self.name,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )

    async def _call_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        story_id: str | None = None,
        chapter_num: int | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        return await self.llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            agent_name=self.name,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        story_id: str | None = None,
        chapter_num: int | None = None,
        retries: int = 2,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> dict:
        """无 schema 的 JSON 调用（过渡用；优先用 _call_structured）。"""
        for attempt in range(retries + 1):
            try:
                return await self.llm.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    agent_name=self.name,
                    story_id=story_id,
                    chapter_num=chapter_num,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"[{self.name}] JSON parse failed ({attempt+1}/{retries+1}): {e}")
                if attempt == retries:
                    raise
