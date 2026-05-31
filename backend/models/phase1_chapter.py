"""Phase 1 章节生成管线的 Pydantic schema。

依据 phase1/00-architecture.md §4.2。
outline_advance / scene_plan / extract_memory 三个结构化 agent 的输出契约。
（write_chapter 出纯文本，不用 schema。）
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ===================== outline_advance：粗纲 → 本章细纲 =====================

class ChapterBeat(BaseModel):
    beat: str = Field(description="一个情节节拍/分镜的简述")
    purpose: str = Field(default="", description="这个 beat 的叙事作用")


class DetailedOutline(BaseModel):
    """本章细纲（DOME 动态展开）。"""
    chapter_title: str = Field(description="本章标题")
    summary: str = Field(description="本章一句话概要")
    beats: list[ChapterBeat] = Field(description="本章情节节拍，3-5 个")
    narrative_func_tags: list[str] = Field(default_factory=list, description="本章命中的叙事功能标签")


# ===================== scene_plan：本章分镜 + 字数预算 =====================

class Scene(BaseModel):
    scene_id: int = Field(description="场景序号，从 1 开始")
    pov_character: str = Field(default="", description="本场景视角角色 id")
    location: str = Field(default="", description="场景地点")
    present_characters: list[str] = Field(default_factory=list, description="在场角色 id 列表")
    goal: str = Field(description="本场景要推进的事")
    word_budget: int = Field(description="本场景字数预算（所有场景之和≈本章目标字数）")


class ScenePlan(BaseModel):
    """本章分镜规划（LongWriter 字数预算法：先分镜配额，逐场景生成）。"""
    pov: str = Field(description="本章主视角角色 id")
    scenes: list[Scene] = Field(description="本章场景列表，2-4 个")
    hook: str = Field(description="章末钩子（留给下一章的悬念）—— 网文命根子，必须有")


# ===================== extract_memory：抽本章新事实/状态变化 =====================

class ExtractedQuad(BaseModel):
    subject: str = Field(description="主体（角色/物/势力名）")
    predicate: str = Field(
        description="谓词，只能是状态类：存活状态/境界/身份/阵营/能力/持有/关系。"
                    "禁止用动词（修改/执行/发现/攻击等事件不是四元组，应写进 summary）"
    )
    object: str = Field(description="客体（状态值/能力名/物品名/\"对象=关系型\"）")
    invalidates_prior: bool = Field(
        default=False,
        description="仅单值谓语（存活状态/境界）发生变更时为 true（如境界突破、角色死亡）"
    )


class CharacterStateChange(BaseModel):
    character_id: str
    location: str = Field(default="")
    status: str = Field(default="")
    emotional_state: str = Field(default="")
    note: str = Field(default="", description="本章该角色的关键变化")


class CharacterMemory(BaseModel):
    """角色本章的情感关键记忆（L1）——喂语义记忆，维系角色情感连续性。"""
    character_id: str = Field(description="记忆所属角色 id")
    content: str = Field(description="该角色本章经历的要紧事/强情绪，一句话，含对象与感受")
    emotional_weight: float = Field(
        default=0.5,
        description="情感强度 0-1：越刻骨越高（生死/背叛/失去/重大抉择≈0.9，日常≈0.3）"
    )


class ChapterExtract(BaseModel):
    """章节后抽取：新事实四元组 + 角色状态变化 + 伏笔 + 压缩摘要。"""
    new_quads: list[ExtractedQuad] = Field(default_factory=list, description="本章新增/变更的事实")
    state_changes: list[CharacterStateChange] = Field(default_factory=list, description="角色状态变化")
    memories: list[CharacterMemory] = Field(
        default_factory=list, description="出场角色本章的情感关键记忆（每个重要角色 0-2 条）"
    )
    foreshadowing: list[str] = Field(default_factory=list, description="本章新埋下的伏笔（待回收）")
    resolved_foreshadowing: list[int] = Field(
        default_factory=list,
        description="本章回收/兑现的【待回收伏笔】的 id（只填上下文给出的 id，没回收就留空）"
    )
    summary: str = Field(description="本章 100-150 字压缩摘要（喂下一章上下文）")
