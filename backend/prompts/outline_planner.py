import json

SYSTEM_PROMPT = """你是一位小说大纲规划师。你的职责是根据已确定的核心概念、世界观和角色，规划详细的分卷大纲。

你会收到完整的故事设定（概念+世界+角色），请基于此规划分卷大纲。

输出严格 JSON：
{
  "initial_conflicts": ["核心冲突1", "核心冲突2", "冲突3"],
  "planned_arc": "总体故事弧线概述（100-200字）",
  "volumes": [
    {
      "volume_num": 1,
      "volume_name": "第一卷卷名",
      "chapter_start": 1,
      "chapter_end": 30,
      "estimated_words": 60000,
      "main_plot": "本卷主线剧情（200-500字，要具体到发生了什么事）",
      "subplots": [
        "支线1：具体到谁在哪里做了什么",
        "支线2：...",
        "支线3：...",
        "支线4：...",
        "支线5：..."
      ],
      "conflicts": [
        "矛盾冲突1：具体描述",
        "矛盾冲突2：...",
        "矛盾冲突3：..."
      ],
      "new_characters": ["本卷新登场角色名"],
      "key_locations": ["关键地点1", "地点2"],
      "climax_event": "本卷高潮事件详细描述"
    }
  ]
}

要求：
1. 至少 2 卷，每卷预计 5-10 万字
2. 每卷至少 5 条支线（subplots），要具体到"谁在哪里做了什么"
3. 每卷至少 3 条矛盾冲突（conflicts）
4. 各卷之间要有节奏起伏（如第一卷铺垫、第二卷冲突升级）
5. 每卷的 climax_event 要是关键转折点
6. 所有内容必须是中文"""


def build_user_prompt(
    concept: dict,
    world_setting: dict,
    characters_design: dict,
) -> str:
    protagonist = characters_design.get("protagonist", {})
    antagonist = characters_design.get("antagonist", {})
    supporting = characters_design.get("supporting_characters", [])
    char_summary = []
    for c in [protagonist, antagonist] + supporting:
        if c:
            char_summary.append(f"- {c.get('name', '?')}（{c.get('role', '?')}）：{c.get('personality', '')[:50]}")

    return f"""## 核心概念

书名：《{concept.get('title', '')}》
题材：{concept.get('genre', '')}
基调：{concept.get('tone', '')}
梗概：{concept.get('synopsis', '')}
金手指：{concept.get('special_ability', {}).get('name', '')}
完整故事线：{concept.get('inspiration', '')}

## 世界观

{world_setting.get('world_background', '')}
势力：{json.dumps([f.get('name', '') + '(' + f.get('stance', '') + ')' for f in world_setting.get('factions', [])], ensure_ascii=False)}

## 角色

{chr(10).join(char_summary)}

请基于以上完整设定，规划分卷大纲。"""


# --- Revise prompt (based on existing outline) ---

SYSTEM_PROMPT_REVISE = """你是一位小说大纲修订师。你会收到：
1. 故事核心设定（概念、世界观、角色）— 这些保持不变
2. 已有的分卷大纲 — 作为修订基础
3. 用户的调整意图 — 重点方向

你的任务是：基于已有大纲**重新规划**一份更好的大纲，而不是微调。可以：
- 调整卷的数量和分布
- 重新设计卷内的主线/支线/冲突
- 调整节奏和高潮安排
- 按用户意图强化或改变某些方向

保留的硬约束：
- 角色、世界观、金手指不能变
- 书名、题材、基调保持一致
- 如果用户指令明确要求保留某些情节，必须保留

输出严格 JSON，格式与初版大纲一致：
{
  "initial_conflicts": [...],
  "planned_arc": "...",
  "volumes": [{volume_num, volume_name, chapter_start, chapter_end, estimated_words, main_plot, subplots, conflicts, new_characters, key_locations, climax_event}, ...]
}

质量要求：
1. 至少 2 卷，每卷预计 5-10 万字
2. 每卷至少 5 条支线，具体到"谁在哪里做了什么"
3. 每卷至少 3 条矛盾冲突
4. 节奏起伏要比原版更合理
5. 所有内容必须是中文"""


def build_revise_prompt(
    concept: dict,
    world_setting: dict,
    characters_design: dict,
    current_outline: dict,
    user_instructions: str = "",
) -> str:
    protagonist = characters_design.get("protagonist", {})
    antagonist = characters_design.get("antagonist", {})
    supporting = characters_design.get("supporting_characters", [])
    char_summary = []
    for c in [protagonist, antagonist] + supporting:
        if c:
            char_summary.append(f"- {c.get('name', '?')}（{c.get('role', '?')}）：{c.get('personality', '')[:50]}")

    # Condense existing outline
    existing_volumes = []
    for v in current_outline.get("volumes", []):
        existing_volumes.append({
            "volume_num": v.get("volume_num"),
            "volume_name": v.get("volume_name"),
            "chapter_range": f"{v.get('chapter_start', '?')}-{v.get('chapter_end', '?')}",
            "main_plot": v.get("main_plot", ""),
            "climax_event": v.get("climax_event", ""),
        })

    instructions_block = ""
    if user_instructions.strip():
        instructions_block = f"""
## 用户调整意图（优先遵守）

{user_instructions.strip()}
"""

    return f"""## 核心设定（不变）

书名：《{concept.get('title', '')}》
题材：{concept.get('genre', '')}
基调：{concept.get('tone', '')}
梗概：{concept.get('synopsis', '')}
金手指：{concept.get('special_ability', {}).get('name', '')}

## 世界观

{world_setting.get('world_background', '')}
势力：{json.dumps([f.get('name', '') + '(' + f.get('stance', '') + ')' for f in world_setting.get('factions', [])], ensure_ascii=False)}

## 角色

{chr(10).join(char_summary)}

## 已有大纲（修订基础）

初始冲突：{json.dumps(current_outline.get('initial_conflicts', []), ensure_ascii=False)}
故事弧线：{current_outline.get('planned_arc', '')}

分卷结构：
{json.dumps(existing_volumes, ensure_ascii=False, indent=2)}
{instructions_block}
请基于已有大纲和用户意图，输出更好的新版大纲。输出 JSON。"""
