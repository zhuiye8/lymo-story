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


def character_designer_prompt(concept_json: str, world_json: str) -> tuple[str, str]:
    system = with_anti_slop(
        "你是人物设定师。基于立意和世界观，设计主角、主要反派、2-4 个配角。"
        "每个角色必须有鲜明的【对白指纹 voice_profile】：口头禅、句式特点、说话语气、用词倾向、禁用方式——"
        "这是让不同角色说话能被一眼辨认的关键，务必让每个角色的 voice_profile 互不相同、各具特色。"
        "主角要有成长空间和软肋，反派要有可信的动机。"
    )
    user = (
        f"立意：\n{concept_json}\n\n世界观：\n{world_json}\n\n"
        "请产出 Characters（含每个角色的 voice_profile，确保各角色对白指纹差异明显）。"
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
