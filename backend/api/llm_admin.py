from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.config import Settings
from backend.deps import get_llm_logger, get_model_registry, get_settings
from backend.llm.client import normalize_litellm_model
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry
from backend.llm.providers import all_presets
from backend.llm.providers import deepseek as deepseek_provider

router = APIRouter()

# Active agents that can be configured with model bindings
VALID_AGENTS = [
    # Init pipeline
    "concept", "world_builder", "character_designer", "outline_planner",
    "outline_parser",
    # Chapter pipeline
    "world", "planner", "camera", "consistency", "titler", "character_arc",
    # Scene-level (Phase 4)
    "scene_splitter", "scene_writer", "scene_consistency",
    # Helpers (Phase 3/5)
    "extractor", "character_reviewer",
]

# Deprecated agents — kept so historical logs/stats still display correctly,
# but no longer configurable for model binding.
DEPRECATED_AGENTS = ["director", "writer", "outline_enricher"]


# --- Request/Response Models ---

class ModelConfigRequest(BaseModel):
    id: str
    display_name: str
    litellm_model: str
    api_key: str = ""
    api_base: str | None = None
    max_tokens: int = 4096
    default_temperature: float = 0.7
    cost_per_million_input: float = 0.0
    cost_per_million_input_cached: float = 0.0
    cost_per_million_output: float = 0.0
    currency: str = "CNY"
    is_active: bool = True
    provider: str = "generic"
    provider_options: dict = {}


class DeepSeekSeedRequest(BaseModel):
    api_key: str
    apply_tier_bindings: bool = True


class BulkBindRequest(BaseModel):
    # {model_id: [agent_name, ...]}
    bindings: dict[str, list[str]]


class BindAgentRequest(BaseModel):
    model_config_id: str
    temperature_override: float | None = None
    max_tokens_override: int | None = None


# --- Model Config Endpoints ---

@router.get("/models")
async def list_models(registry: ModelRegistry = Depends(get_model_registry)):
    return await registry.list_models()


@router.post("/models")
async def create_model(
    req: ModelConfigRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.save_model(req.model_dump())
    return {"message": "Model created", "id": req.id}


@router.put("/models/{model_id}")
async def update_model(
    model_id: str,
    req: ModelConfigRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    existing = await registry.get_model(model_id)
    if not existing:
        raise HTTPException(404, "Model not found")
    data = req.model_dump()
    data["id"] = model_id
    await registry.save_model(data)
    return {"message": "Model updated"}


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.delete_model(model_id)
    return {"message": "Model deleted"}


@router.post("/models/{model_id}/test")
async def test_model(
    model_id: str,
    registry: ModelRegistry = Depends(get_model_registry),
    settings: Settings = Depends(get_settings),
):
    """Send a lightweight test prompt to verify the model is reachable and working.

    Uses the same litellm call path as normal generation (including api_base
    fallback to env default), so the test result accurately reflects whether
    the model will work in practice.
    """
    import time
    import litellm as _litellm

    model = await registry.get_model(model_id)
    if not model:
        raise HTTPException(404, "Model not found")

    raw_model = model["litellm_model"]
    api_key = model.get("api_key") or settings.litellm_api_key or ""
    api_base = model.get("api_base") or settings.litellm_api_base or None
    litellm_model = normalize_litellm_model(raw_model, api_base)

    kwargs: dict = {
        "model": litellm_model,
        "messages": [
            {"role": "system", "content": "你是一个简单的测试助手。"},
            {"role": "user", "content": "请用一句话回答：1+1等于几？"},
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "timeout": 30,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base

    try:
        start = time.time()
        response = await _litellm.acompletion(**kwargs)
        latency_ms = int((time.time() - start) * 1000)
        content = response.choices[0].message.content or ""
        usage = response.usage
        return {
            "success": True,
            "model_id": model_id,
            "litellm_model": litellm_model,
            "response": content.strip()[:200],
            "latency_ms": latency_ms,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "message": f"模型可用 · {latency_ms}ms · {content.strip()[:50]}",
        }
    except Exception as e:
        return {
            "success": False,
            "model_id": model_id,
            "litellm_model": litellm_model,
            "response": "",
            "latency_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "message": f"连接失败：{str(e)[:200]}",
            "error": str(e)[:300],
        }


# --- Presets & DeepSeek one-click setup ---

@router.get("/presets")
async def list_presets():
    """List all provider presets for UI quick-fill."""
    return {"presets": all_presets()}


@router.get("/providers/deepseek/tier-bindings")
async def get_deepseek_tier_bindings():
    """Return the recommended Tier 1/2/3 binding plan for DeepSeek."""
    # Flip {model_id: [agents]} → [{model_id, tier, agents}]
    tier_info = {
        "deepseek-v4-pro-thinking":     {"tier": 1, "label": "Tier 1 · 一次性高杠杆", "desc": "init 管线 / 大纲解析 — 不计成本"},
        "deepseek-v4-flash-thinking":   {"tier": 2, "label": "Tier 2 · 主力创作",     "desc": "场景写作 — 思考模式提升 1 档质量"},
        "deepseek-v4-flash-fast":       {"tier": 3, "label": "Tier 3 · 辅助/校验",    "desc": "所有其他任务 — 快+便宜"},
    }
    result = []
    for model_id, agents in deepseek_provider.TIER_BINDINGS.items():
        info = tier_info.get(model_id, {})
        result.append({
            "model_id": model_id,
            "tier": info.get("tier"),
            "label": info.get("label", model_id),
            "desc": info.get("desc", ""),
            "agents": agents,
        })
    return {"tier_bindings": sorted(result, key=lambda x: x["tier"] or 99)}


@router.post("/providers/deepseek/seed")
async def seed_deepseek(
    req: DeepSeekSeedRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    """One-click seed all DeepSeek presets with a user-supplied API key.

    Optionally applies the Tier 1/2/3 agent bindings.
    Existing models are preserved (only api_key is filled if empty).
    """
    if not req.api_key:
        raise HTTPException(400, "api_key is required")

    created = 0
    updated = 0
    unchanged = 0
    seeded = []
    for preset in deepseek_provider.PRESETS:
        cfg = await registry.seed_preset(preset, api_key=req.api_key)
        if cfg.get("_created"):
            created += 1
        elif cfg.get("_updated"):
            updated += 1
        else:
            unchanged += 1
        seeded.append({"id": cfg["id"], "display_name": cfg["display_name"]})

    bound_count = 0
    if req.apply_tier_bindings:
        bound_count = await registry.bind_many(deepseek_provider.TIER_BINDINGS)

    parts = []
    if created:
        parts.append(f"新建 {created} 个模型")
    if updated:
        parts.append(f"更新 {updated} 个 API Key")
    if unchanged:
        parts.append(f"{unchanged} 个已同步")
    if req.apply_tier_bindings:
        parts.append(f"绑定 {bound_count} 个 Agent")

    return {
        "message": "完成：" + "，".join(parts) if parts else "无变化",
        "seeded_models": seeded,
        "bindings_applied": bound_count,
        "created": created,
        "updated": updated,
    }


@router.post("/bindings/bulk")
async def bulk_bind(
    req: BulkBindRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    """Apply multiple agent bindings at once."""
    # Validate agents
    invalid = []
    for agents in req.bindings.values():
        for a in agents:
            if a not in VALID_AGENTS:
                invalid.append(a)
    if invalid:
        raise HTTPException(400, f"Invalid agents: {invalid}")
    count = await registry.bind_many(req.bindings)
    return {"message": f"已绑定 {count} 个 Agent", "count": count}


# --- Agent Binding Endpoints ---

@router.get("/bindings")
async def get_bindings(registry: ModelRegistry = Depends(get_model_registry)):
    bindings = await registry.get_bindings()
    return {"agents": VALID_AGENTS, "bindings": bindings, "deprecated_agents": DEPRECATED_AGENTS}


@router.put("/bindings/{agent_name}")
async def bind_agent(
    agent_name: str,
    req: BindAgentRequest,
    registry: ModelRegistry = Depends(get_model_registry),
):
    if agent_name not in VALID_AGENTS:
        raise HTTPException(400, f"Invalid agent: {agent_name}")
    model = await registry.get_model(req.model_config_id)
    if not model:
        raise HTTPException(404, "Model config not found")
    await registry.bind_agent(
        agent_name, req.model_config_id,
        req.temperature_override, req.max_tokens_override,
    )
    return {"message": f"Agent '{agent_name}' bound to model '{req.model_config_id}'"}


@router.delete("/bindings/{agent_name}")
async def unbind_agent(
    agent_name: str,
    registry: ModelRegistry = Depends(get_model_registry),
):
    await registry.unbind_agent(agent_name)
    return {"message": f"Agent '{agent_name}' unbound"}


# --- Log Endpoints ---

@router.get("/logs")
async def get_logs(
    agent_name: str | None = None,
    story_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    return await llm_logger.get_logs(
        agent_name=agent_name, story_id=story_id,
        status=status, limit=limit, offset=offset,
    )


@router.get("/logs/{log_id}")
async def get_log_detail(
    log_id: int,
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    log = await llm_logger.get_log_detail(log_id)
    if not log:
        raise HTTPException(404, "Log not found")
    return log


# --- Usage Stats Endpoints ---

@router.get("/usage")
async def get_usage(
    group_by: str = Query(default="agent", pattern="^(agent|story|model)$"),
    days: int = Query(default=7, ge=1, le=90),
    llm_logger: LLMLogger = Depends(get_llm_logger),
):
    stats = await llm_logger.get_usage_stats(group_by=group_by, days=days)
    total = await llm_logger.get_total_stats(days=days)
    return {"stats": stats, "total": total}


# --- Generation Settings ---

class GenerationSettingsResponse(BaseModel):
    max_consistency_retries: int
    default_chapter_word_count: int
    chapter_consistency_threshold: int
    chapter_max_critical: int
    chapter_max_warnings: int
    scene_consistency_threshold: float


class UpdateGenerationSettings(BaseModel):
    max_consistency_retries: int | None = None
    default_chapter_word_count: int | None = None
    chapter_consistency_threshold: int | None = None
    chapter_max_critical: int | None = None
    chapter_max_warnings: int | None = None
    scene_consistency_threshold: float | None = None


@router.get("/settings", response_model=GenerationSettingsResponse)
async def get_generation_settings(settings: Settings = Depends(get_settings)):
    return GenerationSettingsResponse(
        max_consistency_retries=settings.max_consistency_retries,
        default_chapter_word_count=settings.default_chapter_word_count,
        chapter_consistency_threshold=settings.chapter_consistency_threshold,
        chapter_max_critical=settings.chapter_max_critical,
        chapter_max_warnings=settings.chapter_max_warnings,
        scene_consistency_threshold=settings.scene_consistency_threshold,
    )


@router.put("/settings")
async def update_generation_settings(
    req: UpdateGenerationSettings,
    settings: Settings = Depends(get_settings),
):
    """Update generation settings at runtime (not persisted to .env).

    Changes take effect on the next chapter generation.
    To persist across restarts, also update .env.
    """
    updated = {}
    if req.max_consistency_retries is not None:
        settings.max_consistency_retries = max(0, min(5, req.max_consistency_retries))
        updated["max_consistency_retries"] = settings.max_consistency_retries
    if req.default_chapter_word_count is not None:
        settings.default_chapter_word_count = max(500, min(8000, req.default_chapter_word_count))
        updated["default_chapter_word_count"] = settings.default_chapter_word_count
    if req.chapter_consistency_threshold is not None:
        settings.chapter_consistency_threshold = max(0, min(100, req.chapter_consistency_threshold))
        updated["chapter_consistency_threshold"] = settings.chapter_consistency_threshold
    if req.chapter_max_critical is not None:
        settings.chapter_max_critical = max(0, min(10, req.chapter_max_critical))
        updated["chapter_max_critical"] = settings.chapter_max_critical
    if req.chapter_max_warnings is not None:
        settings.chapter_max_warnings = max(0, min(20, req.chapter_max_warnings))
        updated["chapter_max_warnings"] = settings.chapter_max_warnings
    if req.scene_consistency_threshold is not None:
        settings.scene_consistency_threshold = max(0.0, min(1.0, req.scene_consistency_threshold))
        updated["scene_consistency_threshold"] = settings.scene_consistency_threshold
    return {"message": "设置已更新（运行时生效，重启后恢复默认）", "updated": updated}
