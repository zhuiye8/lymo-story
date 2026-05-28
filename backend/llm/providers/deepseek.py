"""DeepSeek provider adapter.

DeepSeek V4 models (flash/pro) share an OpenAI-compatible API. They support
a `thinking` mode that produces a reasoning_content block before the answer,
improving quality at the cost of latency and output tokens.

- API base: https://api.deepseek.com (OpenAI-compatible)
- Litellm model prefix: `deepseek/` — but the custom base requires `openai/` prefix
  (see normalize_litellm_model in llm.client). Our PRESETS use `deepseek/` and
  set api_base=None so litellm routes via its own deepseek integration.
- Thinking: enabled by default, toggle via extra_body={"thinking":{"type":"..."}}
- Pricing (CNY / 1M tokens, as of 2026):
    v4-flash: input 1 (miss) / 0.2 (hit), output 2
    v4-pro:   input 12 (miss) / 1 (hit), output 24
"""
from __future__ import annotations

API_BASE = "https://api.deepseek.com"

# Pricing in CNY per million tokens
PRICING: dict[str, dict[str, float]] = {
    "deepseek/deepseek-v4-flash": {
        "input": 1.0,
        "input_cached": 0.2,
        "output": 2.0,
    },
    "deepseek/deepseek-v4-pro": {
        "input": 12.0,
        "input_cached": 1.0,
        "output": 24.0,
    },
    # Legacy
    "deepseek/deepseek-chat": {
        "input": 2.0,
        "input_cached": 0.5,
        "output": 8.0,
    },
    "deepseek/deepseek-reasoner": {
        "input": 4.0,
        "input_cached": 1.0,
        "output": 16.0,
    },
}


# Model presets — used for seeding model_configs and the UI quick-fill.
# Each preset produces one row in model_configs.
PRESETS: list[dict] = [
    {
        "id": "deepseek-v4-flash-fast",
        "display_name": "DeepSeek V4-Flash（快速模式）",
        "litellm_model": "deepseek/deepseek-v4-flash",
        "api_base": None,  # litellm has built-in deepseek routing
        "max_tokens": 4096,
        "default_temperature": 0.7,
        "cost_per_million_input": 1.0,
        "cost_per_million_input_cached": 0.2,
        "cost_per_million_output": 2.0,
        "currency": "CNY",
        "is_active": True,
        "provider": "deepseek",
        "provider_options": {"thinking": "disabled"},
    },
    {
        "id": "deepseek-v4-flash-thinking",
        "display_name": "DeepSeek V4-Flash（思考模式）",
        "litellm_model": "deepseek/deepseek-v4-flash",
        "api_base": None,
        "max_tokens": 8192,
        "default_temperature": 0.7,
        "cost_per_million_input": 1.0,
        "cost_per_million_input_cached": 0.2,
        "cost_per_million_output": 2.0,
        "currency": "CNY",
        "is_active": True,
        "provider": "deepseek",
        "provider_options": {"thinking": "enabled"},
    },
    {
        "id": "deepseek-v4-pro-fast",
        "display_name": "DeepSeek V4-Pro（快速模式）",
        "litellm_model": "deepseek/deepseek-v4-pro",
        "api_base": None,
        "max_tokens": 8192,
        "default_temperature": 0.7,
        "cost_per_million_input": 12.0,
        "cost_per_million_input_cached": 1.0,
        "cost_per_million_output": 24.0,
        "currency": "CNY",
        "is_active": True,
        "provider": "deepseek",
        "provider_options": {"thinking": "disabled"},
    },
    {
        "id": "deepseek-v4-pro-thinking",
        "display_name": "DeepSeek V4-Pro（思考模式 · 最强）",
        "litellm_model": "deepseek/deepseek-v4-pro",
        "api_base": None,
        "max_tokens": 16384,
        "default_temperature": 0.7,
        "cost_per_million_input": 12.0,
        "cost_per_million_input_cached": 1.0,
        "cost_per_million_output": 24.0,
        "currency": "CNY",
        "is_active": True,
        "provider": "deepseek",
        "provider_options": {"thinking": "enabled"},
    },
]


def build_extra_body(options: dict) -> dict | None:
    """Construct extra_body for a DeepSeek call from provider_options.

    Supported options:
      thinking: "enabled" | "disabled"  (default: enabled at API level)
    """
    if not options:
        return None
    extra: dict = {}
    thinking = options.get("thinking")
    if thinking in ("enabled", "disabled"):
        extra["thinking"] = {"type": thinking}
    return extra or None


def cost(model: str, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0) -> float:
    """Compute cost in CNY for a DeepSeek call."""
    p = PRICING.get(model)
    if not p:
        return 0.0
    uncached = max(0, input_tokens - cached_input_tokens)
    return (
        uncached / 1_000_000 * p["input"]
        + cached_input_tokens / 1_000_000 * p["input_cached"]
        + output_tokens / 1_000_000 * p["output"]
    )


# Preset binding suggestions for one-click "推荐配置"
# Tier 1 = 一次性/全书受益 → pro+thinking（不计成本）
# Tier 2 = 主力写作 → flash+thinking（性价比最高的创作模型）
# Tier 3 = 辅助/校验 → flash-fast（快+便宜）
TIER_BINDINGS: dict[str, list[str]] = {
    "deepseek-v4-pro-thinking": [
        # 一次性 Agent（init 管线 + 大纲导入）
        "concept",
        "world_builder",
        "character_designer",
        "outline_planner",
        "outline_parser",
    ],
    "deepseek-v4-flash-thinking": [
        # 主力创作
        "scene_writer",
    ],
    "deepseek-v4-flash-fast": [
        # 辅助/校验/快速任务
        "world",
        "planner",
        "camera",
        "scene_splitter",
        "scene_consistency",
        "consistency",
        "titler",
        "character_arc",
        "extractor",
        "character_reviewer",
    ],
}
