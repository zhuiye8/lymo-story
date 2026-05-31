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
        "你是剧情记录员。读完本章正文，分门别类抽取信息。各类信息严格归位，不要混放：\n\n"
        "1. new_quads：只记**持久状态事实**，谓词（predicate）必须从下表选，禁止用动词：\n"
        "   单值类（一个角色同时只能有一个值，**变了**才记并标 invalidates_prior=true）：\n"
        "     · 存活状态（存活/死亡/重伤/失踪/昏迷）\n"
        "     · 境界（修为/战力等阶/系统等级）\n"
        "   多值类（可累积，不必标 invalidates_prior）：\n"
        "     · 身份（当前身份/头衔/职位，object 写身份名）\n"
        "     · 阵营（所属势力/立场，object 写势力名）\n"
        "     · 能力（习得的功法/技能/系统能力，object 写能力名）\n"
        "     · 持有（获得的关键物品/法宝/系统，object 写物品名）\n"
        "     · 关系（与某角色的关系，object 写 \"对象=关系型\"，如 \"李四=师徒\"）\n"
        "   ★绝不要把动作/事件写成四元组（如 修改/执行/发现/攻击/前往/对话 都是事件，禁止）。\n"
        "   ★只在本章**新出现或确实变化**的状态才记；与前文相同的状态不要重复抽取。\n"
        "   ★object 用稳定简洁的措辞，别每章换说法（如统一写\"系统管理员\"，别一会儿加括号备注）。\n"
        "2. state_changes：出场角色本章的**易变态**（地点/即时状态/情绪）——这些不进 quad。\n"
        "3. foreshadowing：本章埋下的伏笔（待回收）。\n"
        "4. summary：100-150 字压缩摘要，承载本章**事件经过**（发生了什么、谁做了什么）。"
        "事件就写在这里，不要塞进 new_quads。不必文采，要信息密度。\n"
        "只记真实发生的，不要脑补。"
    )
    user = (
        f"【出场角色 id】{character_ids}\n"
        f"【第 {chapter_num} 章正文】\n{chapter_text}\n\n"
        "请产出 ChapterExtract。"
    )
    return system, user
