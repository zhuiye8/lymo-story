"""共享 prompt 片段（Phase 1）。

依据 phase1/00-architecture.md §5.1（prompt 层 anti-slop 负指令）。
所有生成类 agent 的 system prompt 都拼接 ANTI_SLOP_ZH，从源头降低套话。
"""

# 中文 anti-slop 负指令 —— 拼进生成类 agent 的 system prompt。
# 与 slop_lexicon_zh.py 的词表对应（prompt 层预防 + 检测层兜底，双保险）。
ANTI_SLOP_ZH = """
【文风铁律 —— 必须遵守】
1. 禁用陈词滥调与 AI 腔套话：不要写"在心底深处""命运的齿轮""千丝万缕""刻骨铭心""如雷贯耳""时间的洪流""岁月的长河"等空洞大词。
2. 比喻词（仿佛/犹如/宛如/如同）一段最多用一次，能不用就不用，优先用具体动作和细节代替比喻。
3. 禁用身体语言套路：不要反复写"瞳孔骤然紧缩""心脏漏跳一拍""嘴角微微勾起""眼神变得复杂""脸色煞白""呼吸一滞"。
4. 不要堆砌抽象副词三连（"冷冷地、淡淡地、缓缓地"）和万能形容词（复杂/深邃/凌厉/锐利）。
5. show don't tell：不要直接写"他感到愤怒/悲伤/震惊"，用动作、对话、环境侧写情绪。
6. 句长有变化，不要每句都一样长；段首不要老用"但是/然而/不过"转折。
7. 用具体的、有质感的细节，不要空泛。宁可朴素准确，不要华丽空洞。
""".strip()


def with_anti_slop(system_prompt: str) -> str:
    """给生成类 prompt 拼接 anti-slop 负指令。"""
    return f"{system_prompt}\n\n{ANTI_SLOP_ZH}"
