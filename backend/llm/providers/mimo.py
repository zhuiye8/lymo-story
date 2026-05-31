"""小米 MiMo provider adapter（经 newapi 代理，OpenAI 兼容）。

MiMo V2.5 系列是 reasoning 模型，默认会先输出一大段 reasoning_content 再给答案。
这对结构化输出（Instructor 评委）致命：思考烧光 max_tokens，JSON 还没输出就被截断。

实测（2026-05-31）关闭 thinking 的有效方式：
  chat_template_kwargs={"enable_thinking": false}  → reasoning_content 完全为 0
（`enable_thinking: false` 顶层只能部分关；chat_template_kwargs 彻底关。）

provider_options:
  thinking: "enabled" | "disabled"（默认 disabled —— 评委/结构化场景必须关）
"""
from __future__ import annotations


def build_extra_body(options: dict) -> dict | None:
    """构造 MiMo extra_body。默认关闭 thinking（结构化输出场景）。"""
    thinking = (options or {}).get("thinking", "disabled")
    if thinking == "enabled":
        return None  # 保留 reasoning（一般不用于评委）
    # 彻底关 thinking：chat_template_kwargs.enable_thinking=false
    return {"chat_template_kwargs": {"enable_thinking": False}}
