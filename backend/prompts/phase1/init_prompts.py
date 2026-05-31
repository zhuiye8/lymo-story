"""初始化管线 4 个 LLM agent 的 prompt（Phase 1）。

依据 phase1/00-architecture.md §4.1。每个返回 (system, user)。
"""
from __future__ import annotations

from backend.prompts.phase1.shared import with_anti_slop


def concept_prompt(theme: str, requirements: str, title: str) -> tuple[str, str]:
    system = with_anti_slop(
        "你是资深中文网文策划。根据用户的题材想法，提炼出一本【男频系统流】网络小说的核心立意："
        "书名、题材、基调、一句话简介、200-300 字梗概（synopsis，内部用可含走向）、"
        "面向读者的作品简介（blurb，100-200 字营销文案：有钩子、突出爽点与悬念、"
        "结尾留悬念引人点进来，绝不剧透结局）、以及主角的金手指（核心特殊能力）。"
        "立意要有爽点和钩子，符合网文读者口味，但避免烂俗。"
    )
    user = (
        f"题材想法：{theme}\n"
        f"额外要求：{requirements or '无'}\n"
        f"建议书名：{title or '（你来取）'}\n\n"
        "请产出 Concept。"
    )
    return system, user


def title_prompt(genre: str, tone: str, synopsis: str, ability: str, avoid: str = "") -> tuple[str, str]:
    """只生成书名（重新生成书名用）—— 不动其它立意，基于已有设定取一个更好的书名。"""
    system = (
        "你是资深中文网文起名手。根据题材/基调/梗概/金手指，起一个吸引人的网文书名。"
        "要求：4-12 字，有钩子或记忆点，契合题材与基调，不烂俗、不堆砌。"
        "只输出书名本身，不要书名号、不要解释、不要多个候选。"
    )
    user = (
        f"题材：{genre}\n基调：{tone}\n金手指：{ability}\n梗概：{synopsis}\n"
        + (f"避免与此重复：{avoid}\n" if avoid else "")
        + "\n请只输出一个书名："
    )
    return system, user


def blurb_prompt(title: str, genre: str, tone: str, synopsis: str, ability: str) -> tuple[str, str]:
    """只生成作品简介（重新生成简介用）—— 面向读者的营销文案，不剧透结局。"""
    system = with_anti_slop(
        "你是资深中文网文编辑，专写作品简介（书封文案）。根据书名/题材/基调/梗概/金手指，"
        "写一段面向读者的作品简介：100-200 字，开头有钩子，突出爽点与核心悬念，"
        "语气契合题材基调，结尾留悬念引人点进来。绝不剧透结局、不剧透关键反转。"
        "只输出简介正文，不要标题、不要解释、不要分点。"
    )
    user = (
        f"书名：{title}\n题材：{genre}\n基调：{tone}\n金手指：{ability}\n剧情梗概（内部参考，勿照搬、勿剧透）：{synopsis}\n\n"
        "请输出作品简介："
    )
    return system, user


def world_core_prompt(concept_json: str) -> tuple[str, str]:
    """世界观第 1 步：背景 + 力量体系。"""
    system = with_anti_slop(
        "你是网文世界观架构师。基于立意，构建世界观的【背景】和【力量体系】。\n"
        "字数约束：background 150-300 字。power_system：name + levels（境界由低到高，≤8 级，每级名称 ≤15 字）"
        "+ rules（核心规则 ≤6 条，每条 ≤40 字，不要重复）。\n"
        "力量体系要有清晰升级阶梯（系统流爽点来源）。"
    )
    user = f"立意：\n{concept_json}\n\n请产出 WorldCore（仅背景 + 力量体系）。"
    return system, user


def faction_list_prompt(concept_json: str, world_core_json: str) -> tuple[str, str]:
    """世界观第 2 步：势力。"""
    system = with_anti_slop(
        "你是网文世界观架构师。基于立意和已定的背景/力量体系，设计 3-5 个主要势力。"
        "每个势力：name + description（≤60 字）+ stance（对主角立场）。"
    )
    user = f"立意：\n{concept_json}\n\n背景与力量体系：\n{world_core_json}\n\n请产出 FactionList。"
    return system, user


def world_rule_prompt(concept_json: str, world_core_json: str) -> tuple[str, str]:
    """世界观第 3 步：世界硬规则。"""
    system = with_anti_slop(
        "你是网文世界观架构师。基于立意和力量体系，制定 3-6 条不可违反的世界硬规则"
        "（限制金手指、设定红线等，避免后续剧情崩坏）。每条 rule_id + description（≤50 字）。"
    )
    user = f"立意：\n{concept_json}\n\n背景与力量体系：\n{world_core_json}\n\n请产出 WorldRuleList。"
    return system, user


def character_roster_prompt(concept_json: str, world_json: str) -> tuple[str, str]:
    """第一步：只定角色名单（轻量，避免一次输出过大）。"""
    system = with_anti_slop(
        "你是选角导演。基于立意和世界观，列出本书的核心角色名单："
        "1 个主角(protagonist)、1 个主要反派(antagonist)、2-4 个配角(supporting)。"
        "每个角色给 id、姓名、定位、一句话作用即可，不要展开详细设定。"
        "角色之间要有戏剧张力和关系网。"
    )
    user = (
        f"立意：\n{concept_json}\n\n世界观：\n{world_json}\n\n"
        "请产出 CharacterRoster（4-6 个角色名单）。"
    )
    return system, user


def single_character_prompt(
    concept_json: str, world_json: str, roster_brief: str, entry_json: str, existing_voices: str
) -> tuple[str, str]:
    """第二步：为单个角色出完整设定（逐个调用，每次输出小而稳）。"""
    system = with_anti_slop(
        "你是人物设定师。为指定的【单个角色】设计完整设定。\n"
        "【字数硬约束 —— 必须遵守，超长会被系统截断报废】：\n"
        "  appearance ≤ 60 字；personality ≤ 120 字；background ≤ 150 字；"
        "goals ≤ 80 字；weaknesses ≤ 80 字；arc_plan ≤ 120 字。\n"
        "  voice_profile：catchphrases ≤ 4 条（每条 ≤ 12 字）；其余字段各 ≤ 40 字；forbidden ≤ 4 条。\n"
        "精炼传神，不要堆砌。\n"
        "关键：这个角色的对白指纹必须与【已有角色的对白指纹】明显不同，确保读者盲读对白能分辨是谁。"
        "主角要有成长空间和软肋，反派要有可信动机。"
    )
    user = (
        f"立意：\n{concept_json}\n\n世界观：\n{world_json}\n\n"
        f"【全部角色名单】\n{roster_brief}\n\n"
        f"【已有角色的对白指纹（你设计的必须与这些不同）】\n{existing_voices or '（暂无，你是第一个）'}\n\n"
        f"【本次要设计的角色】\n{entry_json}\n\n"
        "请产出这一个角色的完整 CharacterDesign（含 voice_profile）。"
    )
    return system, user


def outline_skeleton_prompt(concept_json: str, world_json: str, chars_json: str, target_chapters: int) -> tuple[str, str]:
    """大纲第 1 步：骨架（5 段粗纲 + 弧线 + 冲突 + 标签）。"""
    system = with_anti_slop(
        "你是网文大纲规划师。基于立意/世界观/角色，规划全书【骨架】：\n"
        "1. rough_stages：5 段粗纲（起承转合式或英雄之旅），每段 stage_num/stage_name/summary(≤80字)/章号范围；\n"
        "2. initial_conflicts：2-4 个开篇冲突；planned_arc：总体弧线（≤120 字）；\n"
        "3. narrative_func_tags：4-8 个中文网文叙事功能标签（金手指觉醒/打脸/扮猪吃虎/升级/逆袭 等）。\n"
        "结构有张弛节奏，主线清晰。"
    )
    user = (
        f"立意：\n{concept_json}\n\n世界观：\n{world_json}\n\n角色：\n{chars_json}\n\n"
        f"目标总章数约 {target_chapters} 章。请产出 OutlineSkeleton（不含分卷）。"
    )
    return system, user


def volume_list_prompt(skeleton_json: str, target_chapters: int) -> tuple[str, str]:
    """大纲第 2 步：分卷。"""
    system = with_anti_slop(
        "你是网文大纲规划师。基于已定的粗纲骨架，拆分成分卷。"
        "每卷：volume_num/volume_name/章号范围/main_plot(≤100字)/climax_event(≤40字)。"
        "分卷章号要覆盖全书且与粗纲阶段呼应。"
    )
    user = f"粗纲骨架：\n{skeleton_json}\n\n目标总章数约 {target_chapters} 章。请产出 VolumeList。"
    return system, user
