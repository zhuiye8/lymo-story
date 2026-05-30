"""章节生成管线的 prompt（Phase 1）。

依据 phase1/00-architecture.md §4.2。每个返回 (system, user)。
"""
from __future__ import annotations

from backend.prompts.phase1.shared import with_anti_slop


def outline_advance_prompt(
    bible_brief: str, rough_stage: str, chapter_num: int, recent_summaries: str
) -> tuple[str, str]:
    system = with_anti_slop(
        "你是网文细纲师。根据全书设定、当前所处的粗纲阶段、以及前几章的剧情，"
        "把本章展开成细纲：标题、一句话概要、3-5 个情节节拍 beats、命中的叙事功能标签。"
        "要承接前文、推进主线，节奏明快。"
    )
    user = (
        f"【全书设定摘要】\n{bible_brief}\n\n"
        f"【当前粗纲阶段】\n{rough_stage}\n\n"
        f"【前几章剧情】\n{recent_summaries or '（这是第一章）'}\n\n"
        f"请为第 {chapter_num} 章产出 DetailedOutline。"
    )
    return system, user


def scene_plan_prompt(
    detailed_outline: str, characters_brief: str, target_words: int
) -> tuple[str, str]:
    system = with_anti_slop(
        "你是分镜师。把本章细纲拆成 2-4 个场景，每个场景标注：视角角色、地点、在场角色、要推进的事、"
        f"以及字数预算（所有场景预算之和约 {target_words} 字）。"
        "必须设计一个有力的【章末钩子 hook】留悬念——这是网文留住读者的命根子。"
    )
    user = (
        f"【本章细纲】\n{detailed_outline}\n\n"
        f"【角色简表】\n{characters_brief}\n\n"
        f"本章目标约 {target_words} 字。请产出 ScenePlan（场景字数预算之和≈{target_words}）。"
    )
    return system, user


def write_scene_prompt(
    bible_brief: str, scene_brief: str, voice_profiles: str,
    facts_brief: str, prev_text: str, word_budget: int
) -> tuple[str, str]:
    system = with_anti_slop(
        "你是顶尖中文网文写手。根据场景规划写出这一段正文。要求：\n"
        "1. 严格遵守每个在场角色的【对白指纹】——不同角色说话必须能一眼分辨；\n"
        "2. 遵守【已知事实】，不得与设定矛盾（角色状态/世界规则）；\n"
        "3. show don't tell，多用具体动作细节和对话，少用心理直述；\n"
        f"4. 本段约 {word_budget} 字，自然成段，不要硬凑字数也不要中途截断；\n"
        "5. 只输出正文，不要任何解释/标题/分镜标记。"
    )
    user = (
        f"【全书设定】\n{bible_brief}\n\n"
        f"【在场角色对白指纹】\n{voice_profiles}\n\n"
        f"【已知事实（不可矛盾）】\n{facts_brief}\n\n"
        f"【上文衔接】\n{prev_text or '（本章开头）'}\n\n"
        f"【本场景规划】\n{scene_brief}\n\n"
        f"请写出本场景正文（约 {word_budget} 字）。"
    )
    return system, user


def extract_memory_prompt(chapter_text: str, character_ids: str, chapter_num: int) -> tuple[str, str]:
    system = (
        "你是剧情记录员。读完本章正文，抽取：\n"
        "1. new_quads：本章新增或变更的事实（主体-谓词-客体）。若某事实使旧状态失效"
        "（如角色死亡/境界突破/地点变更），标 invalidates_prior=true；\n"
        "2. state_changes：出场角色的状态变化（地点/状态/情绪）；\n"
        "3. foreshadowing：本章埋下的伏笔；\n"
        "4. summary：100-150 字压缩摘要（用于喂后续章节，不必文采，要信息密度）。\n"
        "只记真实发生的，不要脑补。"
    )
    user = (
        f"【出场角色 id】{character_ids}\n"
        f"【第 {chapter_num} 章正文】\n{chapter_text}\n\n"
        "请产出 ChapterExtract。"
    )
    return system, user
