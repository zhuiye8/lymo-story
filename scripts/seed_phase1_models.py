"""配置 Phase 1 的模型 + agent 绑定（幂等，可重复跑）。

依据 phase1/00-architecture.md §模型绑定层。
模型：
  - deepseek-v4-pro    散文主力（Writer/scene_writer + 改写）
  - deepseek-v4-flash  批量/结构化（init agents + 细纲/分镜/抽取 + 主评委）
  - mimo-v2.5-pro      第二评委（经 newapi 代理，订阅期）

绑定：
  - 生成结构类 agent → v4-flash
  - scene_writer / 改写 → v4-pro
  - critic_primary → v4-flash（弱异源）
  - critic_secondary → mimo（真异源去偏）
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Settings
from backend.llm.model_registry import ModelRegistry

# MiMo 凭证从 .env（Settings，STORY_ 前缀）读，不硬编码进源码：
#   STORY_MIMO_ENABLED=true  STORY_MIMO_API_KEY=...  STORY_MIMO_API_BASE=http://<proxy>/v1
# .env 已 gitignored，与 DeepSeek key 同等安全姿态。


async def main():
    s = Settings()
    MIMO_ENABLED = s.mimo_enabled and bool(s.mimo_api_key) and bool(s.mimo_api_base)
    if s.mimo_enabled and not (s.mimo_api_key and s.mimo_api_base):
        print("WARN: STORY_MIMO_ENABLED=true 但缺 key/base，跳过 MiMo（单评委降级）")
    reg = ModelRegistry(s.sqlite_path)
    ds_key = s.litellm_api_key
    ds_base = s.litellm_api_base or "https://api.deepseek.com"

    models = [
        {
            "id": "deepseek-v4-pro", "display_name": "DeepSeek V4 Pro（散文主力）",
            "litellm_model": "deepseek/deepseek-chat", "api_key": ds_key, "api_base": ds_base,
            "max_tokens": 8192, "default_temperature": 0.85,
            "cost_per_million_input": 0.435, "cost_per_million_input_cached": 0.003625,
            "cost_per_million_output": 0.87, "currency": "USD",
            "provider": "deepseek", "provider_options": {},
        },
        {
            "id": "deepseek-v4-flash", "display_name": "DeepSeek V4 Flash（批量/结构化）",
            "litellm_model": "deepseek/deepseek-chat", "api_key": ds_key, "api_base": ds_base,
            "max_tokens": 4096, "default_temperature": 0.5,
            "cost_per_million_input": 0.14, "cost_per_million_input_cached": 0.0028,
            "cost_per_million_output": 0.28, "currency": "USD",
            "provider": "deepseek", "provider_options": {},
        },
    ]
    if MIMO_ENABLED:
        models.append({
            "id": "mimo-v2.5-pro", "display_name": "小米 MiMo V2.5 Pro（第二评委·代理）",
            "litellm_model": f"openai/{s.mimo_model}", "api_key": s.mimo_api_key, "api_base": s.mimo_api_base,
            "max_tokens": 4096, "default_temperature": 0.3,
            "cost_per_million_input": 1.0, "cost_per_million_output": 3.0, "currency": "USD",
            # provider=mimo → build_extra_body 关 thinking（reasoning 烧 token 撑爆评委 JSON）
            "provider": "mimo", "provider_options": {"thinking": "disabled"},
        })

    for m in models:
        await reg.save_model(m)
        print(f"[model] {m['id']} -> {m['litellm_model']} @ {m['api_base']}")

    # agent 绑定
    bindings = {
        # init 结构化
        "concept": "deepseek-v4-flash",
        "world_builder": "deepseek-v4-flash",
        "character_designer": "deepseek-v4-flash",
        "outline_planner": "deepseek-v4-flash",
        # chapter 结构化
        "outline_advance": "deepseek-v4-flash",
        "scene_plan": "deepseek-v4-flash",
        "memory_extractor": "deepseek-v4-flash",
        # 散文主力 + 改写
        "scene_writer": "deepseek-v4-pro",
        # 评委
        "critic_primary": "deepseek-v4-flash",
    }
    if MIMO_ENABLED:
        bindings["critic_secondary"] = "mimo-v2.5-pro"

    for agent, model_id in bindings.items():
        await reg.bind_agent(agent, model_id)
        print(f"[bind] {agent} -> {model_id}")

    secondary = "mimo-v2.5-pro" if MIMO_ENABLED else "（STORY_MIMO_ENABLED 未开 → 单评委降级）"
    print(f"\nDeepSeek base: {ds_base}")
    print(f"第二评委: {secondary}")
    print("done.")


if __name__ == "__main__":
    asyncio.run(main())
