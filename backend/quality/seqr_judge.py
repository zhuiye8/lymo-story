"""SEQR v0 LLM judge — 8-dimension Chinese chapter evaluator.

Calibration borrows autonovel's anti-virtual-high prompt rules
[verified:2026-04-26:autonovel/evaluate.py FOUNDATION_PROMPT]:
  - "9-10 must surprise you, reserve for rare works"
  - "for each dimension first state (a) gap (b) actionable improvement"
  - "err toward lower scores"
  - "every dimension must reference original-text evidence"

Output: per-dimension {score 0-10, evidence} + LLM cost/tokens.
"""
import json
import time

import litellm

from backend.llm.client import normalize_litellm_model
from backend.llm.providers import build_extra_body
from backend.quality import DIMENSIONS, RUBRIC_VERSION


SYSTEM_PROMPT = """你是中文长篇小说章节质量评审。你的任务：对单章给出 8 个维度的评分（每维 0-10）和原文证据。

# 评分维度

| 维度 key | 中文名 | 评分关注点 |
|---|---|---|
| fluency | 语言流畅度 | 句法通顺度、错别字、病句 |
| dialogue_distinct | 对白独特性 | 不同角色台词是否可分辨（语气 + 用词倾向） |
| character_consistency | 角色一致性 | 言行是否符合人设（性格 / 口头禅 / 硬约束） |
| scene_drama | 场景戏剧性 | 是否有冲突 / 转折 / 代价；避免 OVER-EXPLAIN / REDUNDANT |
| sensory_detail | 感官描写 | 视觉 / 听觉 / 触觉描写密度，避免空泛形容词 |
| rhetoric_quality | 修辞质量 | 比喻是否新鲜，避免烂用"宛如…一般"等套路 |
| continuity | 跨场景衔接 | 场景过渡自然，时间 / 空间 / 人物连贯 |
| overall_readability | 整体可读性 | 综合阅读体验 |

# 评分校准（必须严格遵守）

- **9-10 分必须真正令人惊艳，保留给极少数作品**。绝大多数好章节应在 6-8 分。
- **倾向打低分**。如果犹豫，往下打。
- 对每个维度，必须**先指出 (a) 缺陷或不足 (b) 具体可行的改进建议**，再给分。
- 每个维度必须**引用原文证据片段**（10-30 字）。
- 评分不得受字数影响（不因为长就高分）。
- 不得给出虚高、泛泛的好评。

# 输出格式（严格 JSON）

{
  "scores": {
    "fluency":              {"score": 6.5, "gap": "...", "improvement": "...", "evidence": "原文片段"},
    "dialogue_distinct":    {"score": 5.0, "gap": "...", "improvement": "...", "evidence": "..."},
    "character_consistency":{"score": 7.0, "gap": "...", "improvement": "...", "evidence": "..."},
    "scene_drama":          {"score": 4.5, "gap": "...", "improvement": "...", "evidence": "..."},
    "sensory_detail":       {"score": 5.5, "gap": "...", "improvement": "...", "evidence": "..."},
    "rhetoric_quality":     {"score": 6.0, "gap": "...", "improvement": "...", "evidence": "..."},
    "continuity":           {"score": 7.5, "gap": "...", "improvement": "...", "evidence": "..."},
    "overall_readability":  {"score": 6.0, "gap": "...", "improvement": "...", "evidence": "..."}
  },
  "summary": "对该章质量的两句话总评"
}

只输出 JSON，不要其他文字。"""


def _build_user_prompt(chapter_content: str, bible_summary: str = "") -> str:
    bible_block = f"\n## 作品设定（仅供判断 character_consistency 等参考）\n{bible_summary}\n" if bible_summary else ""
    return f"""# 待评章节正文
{bible_block}
{chapter_content}

请按 system 指令输出 JSON 评分。"""


def _summarize_bible(bible: dict | None) -> str:
    """Compress bible to ~500 chars for cost control."""
    if not bible:
        return ""
    parts = []
    if bible.get("title"):
        parts.append(f"《{bible['title']}》")
    if bible.get("genre"):
        parts.append(f"题材：{bible['genre']}")
    if bible.get("one_line_summary"):
        parts.append(f"一句话：{bible['one_line_summary']}")
    # Characters: just names + roles
    chars = []
    for c in [bible.get("protagonist"), bible.get("antagonist")]:
        if c and isinstance(c, dict):
            chars.append(f"{c.get('name','?')}({c.get('role','?')})")
    for c in (bible.get("supporting_characters") or [])[:4]:
        if c and isinstance(c, dict):
            chars.append(f"{c.get('name','?')}({c.get('role','?')})")
    if chars:
        parts.append("角色：" + "、".join(chars))
    out = " ｜ ".join(parts)
    return out[:500]


class SEQRJudge:
    """LLM-based 8-dimension chapter judge.

    Uses LiteLLM directly (not BaseAgent) because this runs offline against
    arbitrary chapters and we need full control over model/pricing fields.
    """

    def __init__(
        self,
        judge_model: str,
        api_key: str | None = None,
        api_base: str | None = None,
        thinking: str | None = None,
        cost_per_million_input: float = 0,
        cost_per_million_output: float = 0,
        max_tokens: int = 4096,
        timeout: int = 60,
    ):
        self.judge_model_raw = judge_model
        self.judge_model = normalize_litellm_model(judge_model, api_base)
        self.api_key = api_key
        self.api_base = api_base
        self.thinking = thinking  # 'enabled' | 'disabled' | None
        self.cost_in = cost_per_million_input
        self.cost_out = cost_per_million_output
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def evaluate(self, chapter_content: str, bible: dict | None = None) -> dict:
        """Evaluate one chapter. Returns full result dict including raw LLM output for audit.

        Result schema:
          {
            "scores": {dim_key: float, ...},          # only the score field, flat
            "evidence": {dim_key: str, ...},
            "details": {dim_key: {gap, improvement, evidence}},  # full per-dim
            "summary": str,
            "raw_response": str,
            "input_tokens": int,
            "output_tokens": int,
            "cost_cny": float,
            "latency_ms": int,
            "judge_model": str,
            "rubric_version": "SEQR-v0",
            "error": str | None,
          }
        """
        sys_p = SYSTEM_PROMPT
        usr_p = _build_user_prompt(chapter_content, _summarize_bible(bible))

        kwargs: dict = {
            "model": self.judge_model,
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": usr_p},
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.2,
            "timeout": self.timeout,
            "response_format": {"type": "json_object"},
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.thinking in ("enabled", "disabled"):
            extra = build_extra_body("deepseek", {"thinking": self.thinking})
            if extra:
                kwargs["extra_body"] = extra

        start = time.time()
        try:
            resp = await litellm.acompletion(**kwargs)
            latency_ms = int((time.time() - start) * 1000)
            content = resp.choices[0].message.content or ""
            usage = resp.usage
            input_tokens = usage.prompt_tokens or 0
            output_tokens = usage.completion_tokens or 0
            cost = input_tokens / 1_000_000 * self.cost_in + output_tokens / 1_000_000 * self.cost_out

            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(l for l in lines if not l.strip().startswith("```"))
            parsed = json.loads(text)

            scores_raw = parsed.get("scores", {})
            scores: dict[str, float] = {}
            evidence: dict[str, str] = {}
            details: dict[str, dict] = {}
            for d in DIMENSIONS:
                cell = scores_raw.get(d) or {}
                if isinstance(cell, dict):
                    sc = float(cell.get("score", 0) or 0)
                    ev = str(cell.get("evidence", "") or "")
                    details[d] = {
                        "gap": str(cell.get("gap", "")),
                        "improvement": str(cell.get("improvement", "")),
                        "evidence": ev,
                    }
                else:
                    sc = float(cell or 0)
                    ev = ""
                    details[d] = {"gap": "", "improvement": "", "evidence": ""}
                scores[d] = max(0.0, min(10.0, sc))
                evidence[d] = ev

            return {
                "scores": scores,
                "evidence": evidence,
                "details": details,
                "summary": str(parsed.get("summary", "")),
                "raw_response": content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cny": round(cost, 6),
                "latency_ms": latency_ms,
                "judge_model": self.judge_model,
                "rubric_version": RUBRIC_VERSION,
                "error": None,
            }
        except Exception as e:
            return {
                "scores": {d: 0.0 for d in DIMENSIONS},
                "evidence": {d: "" for d in DIMENSIONS},
                "details": {d: {"gap": "", "improvement": "", "evidence": ""} for d in DIMENSIONS},
                "summary": "",
                "raw_response": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_cny": 0.0,
                "latency_ms": int((time.time() - start) * 1000),
                "judge_model": self.judge_model,
                "rubric_version": RUBRIC_VERSION,
                "error": str(e)[:500],
            }
