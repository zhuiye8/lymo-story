"""Phase 1 Pydantic schema（初始化管线 5 agent 的输出契约）。

依据 phase1/00-architecture.md §4.1 + 01-implementation-plan.md Step 4.1。

这些 model 直接喂 Instructor（complete_structured 的 response_model），
LLM 输出经 Pydantic 校验 + reask 自愈后返回实例。
字段用英文 key（Instructor/JSON 友好），description 用中文（喂模型理解）。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ===================== Step 1: ConceptAgent =====================

class SpecialAbility(BaseModel):
    name: str = Field(description="金手指/特殊能力名称")
    description: str = Field(description="能力描述")
    functions: list[str] = Field(default_factory=list, description="能力的具体功能列表")


class Concept(BaseModel):
    """立意层：题材/基调/梗概/金手指。"""
    title: str = Field(description="书名")
    genre: str = Field(description="题材类型，如 男频系统流")
    tone: str = Field(description="基调，如 热血爽文 / 沉稳权谋")
    one_line: str = Field(description="一句话简介")
    synopsis: str = Field(description="200-300 字故事梗概")
    special_ability: SpecialAbility = Field(description="主角的金手指/核心能力")


# ===================== Step 2: WorldBuilder =====================

class Faction(BaseModel):
    name: str = Field(description="势力/门派名称")
    description: str = Field(description="势力简介")
    stance: str = Field(default="", description="对主角的立场：盟友/敌对/中立")


class PowerSystem(BaseModel):
    name: str = Field(description="力量体系名称，如 修真境界")
    levels: list[str] = Field(default_factory=list, description="境界/等级从低到高")
    rules: list[str] = Field(default_factory=list, description="力量体系的核心规则")


class WorldRule(BaseModel):
    rule_id: str = Field(description="规则编号，如 R1")
    description: str = Field(description="世界观硬规则（不可违反的设定）")


class WorldSetting(BaseModel):
    """世界观层。"""
    background: str = Field(description="世界观背景 200-400 字")
    factions: list[Faction] = Field(default_factory=list, description="主要势力")
    power_system: PowerSystem = Field(description="力量体系")
    world_rules: list[WorldRule] = Field(default_factory=list, description="世界硬规则")


# ===================== Step 3: CharacterDesigner =====================

class VoiceProfile(BaseModel):
    """对白指纹 —— 对白区分度的抓手（直对 SEQR dialogue_distinctness）。"""
    catchphrases: list[str] = Field(default_factory=list, description="口头禅/习惯用语")
    sentence_style: str = Field(default="", description="句式特点，如 短促有力 / 文绉绉")
    tone: str = Field(default="", description="说话语气，如 傲慢 / 谦和 / 阴冷")
    vocabulary: str = Field(default="", description="用词倾向，如 爱用古语 / 满口脏话 / 书面语")
    forbidden: list[str] = Field(default_factory=list, description="这个角色绝不会说的词/方式")


class CharacterDesign(BaseModel):
    character_id: str = Field(description="角色英文/拼音 id，如 lin_fan")
    name: str = Field(description="角色姓名")
    role: str = Field(description="角色定位：protagonist/antagonist/supporting")
    gender: str = Field(default="", description="性别")
    age: str = Field(default="", description="年龄")
    appearance: str = Field(default="", description="外貌")
    personality: str = Field(description="性格")
    background: str = Field(description="背景故事")
    goals: str = Field(description="目标/动机")
    weaknesses: str = Field(default="", description="弱点/软肋")
    arc_plan: str = Field(default="", description="角色成长弧线规划")
    voice_profile: VoiceProfile = Field(description="对白指纹")


class Characters(BaseModel):
    """角色层。"""
    protagonist: CharacterDesign = Field(description="主角")
    antagonist: CharacterDesign = Field(description="主要反派")
    supporting: list[CharacterDesign] = Field(default_factory=list, description="配角（2-4 个）")


# ===================== Step 4: OutlinePlanner =====================

class Volume(BaseModel):
    volume_num: int = Field(description="卷号")
    volume_name: str = Field(description="卷名")
    chapter_start: int = Field(description="起始章号")
    chapter_end: int = Field(description="结束章号")
    main_plot: str = Field(description="本卷主线剧情")
    climax_event: str = Field(default="", description="本卷高潮事件")


class RoughStage(BaseModel):
    """DOME 粗纲·一个阶段（5 段英雄之旅/Freytag）。"""
    stage_num: int = Field(description="阶段号 1-5")
    stage_name: str = Field(description="阶段名，如 起/承/转/合 或 hero's journey 阶段")
    summary: str = Field(description="本阶段剧情概要")
    chapter_start: int = Field(description="起始章号")
    chapter_end: int = Field(description="结束章号")


class Outline(BaseModel):
    """大纲层：DOME 双层（粗纲 5 段 + 卷）+ Propp-34 叙事功能标签。"""
    rough_stages: list[RoughStage] = Field(description="5 段粗纲（英雄之旅/Freytag）")
    volumes: list[Volume] = Field(default_factory=list, description="分卷大纲")
    initial_conflicts: list[str] = Field(default_factory=list, description="开篇冲突")
    planned_arc: str = Field(description="总体故事弧线")
    narrative_func_tags: list[str] = Field(
        default_factory=list,
        description="贯穿全书的中文网文叙事功能标签，如 金手指觉醒/打脸/升级/扮猪吃虎",
    )


# ===================== StoryBible（assemble，无 LLM）=====================

class StoryBible(BaseModel):
    """完整故事圣经 V3（assemble_bible 合并产出）。"""
    bible_version: int = 3
    concept: Concept
    world: WorldSetting
    characters: Characters
    outline: Outline
    primary_pov: str = Field(default="", description="主视角角色 id")
    style_guide: str = Field(default="", description="文风指引")
