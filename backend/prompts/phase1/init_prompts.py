"""初始化管线 4 个 LLM agent 的 prompt（Phase 1）。

依据 phase1/00-architecture.md §4.1。每个返回 (system, user)。
"""
from __future__ import annotations

from backend.prompts.phase1.shared import with_anti_slop


def concept_prompt(theme: str, requirements: str, title: str) -> tuple[str, str]:
    system = with_anti_slop(
        "你是资深中文网文策划。根据用户的题材想法，提炼出一本【男频系统流】网络小说的核心立意："
        "书名、题材、基调、一句话简介、200-300 字梗概、以及主角的金手指（核心特殊能力）。"
        "立意要有爽点和钩子，符合网文读者口味，但避免烂俗。"
    )
    user = (
        f"题材想法：{theme}\n"
        f"额外要求：{requirements or '无'}\n"
        f"建议书名：{title or '（你来取）'}\n\n"
        "请产出 Concept。"
    )
    return system, user


def world_builder_prompt(concept_json: str) -> tuple[str, str]:
    system = with_anti_slop(
        "你是网文世界观架构师。基于给定的立意，构建一个自洽的世界观："
        "背景设定、主要势力、力量体系（境界等级从低到高 + 核心规则）、以及不可违反的世界硬规则。"
        "力量体系要有清晰的升级阶梯（系统流的核心爽点来源）。"
    )
    user = f"立意：\n{concept_json}\n\n请产出 WorldSetting。"
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
        "你是人物设定师。为指定的【单个角色】设计完整设定，包括外貌/性格/背景/目标/弱点/成长弧线，"
        "以及鲜明的【对白指纹 voice_profile】：口头禅、句式、语气、用词倾向、禁用方式。\n"
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


def outline_planner_prompt(concept_json: str, world_json: str, chars_json: str, target_chapters: int) -> tuple[str, str]:
    system = with_anti_slop(
        "你是网文大纲规划师。基于立意/世界观/角色，规划全书结构：\n"
        "1. rough_stages：5 段粗纲（起承转合式或英雄之旅），每段标注章号范围；\n"
        "2. volumes：分卷大纲，每卷有主线和高潮事件；\n"
        "3. initial_conflicts：开篇冲突；planned_arc：总体弧线；\n"
        "4. narrative_func_tags：贯穿全书的中文网文叙事功能标签（如 金手指觉醒/打脸/扮猪吃虎/升级/逆袭），"
        "用于后续抗同质化检查。\n"
        "结构要有张弛节奏，主线清晰，爽点分布合理。"
    )
    user = (
        f"立意：\n{concept_json}\n\n世界观：\n{world_json}\n\n角色：\n{chars_json}\n\n"
        f"目标总章数约 {target_chapters} 章。请产出 Outline。"
    )
    return system, user
