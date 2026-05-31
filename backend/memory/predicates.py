"""DOME 四元组的受控谓语词表（Phase 1 #2 一致性闭环根因修复）。

问题背景：extract_memory 自由产出谓语，模型读到满章动作就抽成事件四元组
（`<墨默, 修改, 余额>` / `<墨默, 执行, 某操作>`），同(主,动词)不同宾语被
find_conflicts 全判成 object_mismatch → 10 章压测 51 个"冲突"几乎全是误报。

根因：四元组该只存**持久状态事实**，不是事件流。本模块定义受控词表 + 归一化，
让 extract 落库前把事件谓语过滤掉、把同义谓语归一，conflict 检测才有意义。

三类信息各归其位：
  - 持久状态事实  → knowledge_quads（本模块约束）：存活/境界/身份/阵营/能力/持有/关系
  - 易变态        → character_states 表：位置/情绪/即时状态（末值覆盖，无冲突概念）
  - 事件/动作/知识 → 章节 summary / foreshadowing（不进四元组）

单值 vs 多值（决定 conflict 语义）：
  - 单值谓语：一个主体同一时点只能有一个值。同时有效的多 object = 真矛盾
            （死人复活：存活=死亡 仍有效，又来 存活=存活；境界倒退同理）。
  - 多值谓语：可累积。一个主体掌握多种能力 / 持有多件法宝 / 与多人有关系都合法，
            多 object 不是冲突。
"""
from __future__ import annotations

# 单值状态谓语：变更须 invalidate 旧值；同时有效的多 object = 硬矛盾
SINGLE_VALUED: frozenset[str] = frozenset({
    "存活状态",  # 存活 / 死亡 / 重伤 / 失踪 / 昏迷
    "境界",      # 修为境界 / 战力等阶 / 系统等级
    "身份",      # 当前主身份 / 头衔 / 职位
    "阵营",      # 所属势力 / 阵营 / 立场
})

# 多值状态谓语：可累积，多 object 合法（不判冲突）
MULTI_VALUED: frozenset[str] = frozenset({
    "能力",  # 掌握的功法 / 技能 / 系统能力
    "持有",  # 持有的关键物品 / 法宝 / 系统
    "关系",  # 与某角色的关系（object 编码 "对象=关系型"，如 "李四=师徒"）
})

STATE_PREDICATES: frozenset[str] = SINGLE_VALUED | MULTI_VALUED

# 常见变体 → canonical。模型不会精确吐 canonical，这层把同义谓语收敛，
# 否则"张三|境界|筑基" 与 "张三|修为|金丹" 因谓语不同而漏检冲突。
ALIASES: dict[str, str] = {
    # 存活状态
    "生死": "存活状态", "存活": "存活状态", "死活": "存活状态",
    "状态": "存活状态", "生命状态": "存活状态", "生存状态": "存活状态",
    # 境界
    "修为": "境界", "等级": "境界", "实力": "境界", "战力": "境界",
    "等阶": "境界", "修炼境界": "境界", "修为境界": "境界", "level": "境界",
    # 身份
    "头衔": "身份", "职位": "身份", "角色": "身份", "身份地位": "身份",
    "称号": "身份", "title": "身份",
    # 阵营
    "势力": "阵营", "所属": "阵营", "归属": "阵营", "阵营归属": "阵营",
    "立场": "阵营", "派系": "阵营", "所属势力": "阵营",
    # 能力
    "技能": "能力", "功法": "能力", "掌握": "能力", "掌握能力": "能力",
    "技艺": "能力", "能力获得": "能力", "skill": "能力", "天赋": "能力",
    # 持有
    "物品": "持有", "法宝": "持有", "装备": "持有", "持有物品": "持有",
    "拥有": "持有", "道具": "持有", "所持": "持有",
    # 关系
    "人物关系": "关系", "关系网": "关系", "人际关系": "关系",
}


def normalize_predicate(p: str) -> str | None:
    """把谓语归一到 canonical 状态谓语；不是状态谓语（动作/事件）→ None（应丢弃）。

    流程：精确命中 canonical → 精确命中别名 → 子串模糊匹配 → None。
    """
    p = (p or "").strip()
    if not p:
        return None
    if p in STATE_PREDICATES:
        return p
    if p in ALIASES:
        return ALIASES[p]
    # 模糊：谓语里含 canonical 关键字（"当前境界"→境界、"持有的法宝"→持有）
    for canon in STATE_PREDICATES:
        if canon in p:
            return canon
    # 模糊：谓语里含某别名关键字
    for alias, canon in ALIASES.items():
        if alias in p:
            return canon
    return None  # 动作/事件谓语（修改/执行/发现/攻击/对话…）→ 不进四元组


def is_single_valued(canonical_predicate: str) -> bool:
    """该 canonical 谓语是否单值（单值才做'同时多值=矛盾'的冲突判定）。"""
    return canonical_predicate in SINGLE_VALUED
