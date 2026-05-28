import json
import logging
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)


def _parse_row(row: dict) -> dict:
    """Normalize a model_configs row — parse JSON fields, provide defaults."""
    r = dict(row)
    opts = r.get("provider_options_json") or "{}"
    try:
        r["provider_options"] = json.loads(opts) if isinstance(opts, str) else (opts or {})
    except Exception:
        r["provider_options"] = {}
    r.setdefault("provider", "generic")
    r.setdefault("cost_per_million_input_cached", 0)
    return r


class ModelRegistry:
    """Manages model configurations and agent-model bindings from SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list_models(self, active_only: bool = False) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM model_configs"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_at DESC"
            cursor = await db.execute(query)
            return [_parse_row(row) for row in await cursor.fetchall()]

    async def get_model(self, model_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM model_configs WHERE id = ?", (model_id,))
            row = await cursor.fetchone()
            return _parse_row(row) if row else None

    async def save_model(self, config: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        provider_opts = config.get("provider_options") or {}
        if isinstance(provider_opts, dict):
            provider_opts_json = json.dumps(provider_opts, ensure_ascii=False)
        elif isinstance(provider_opts, str):
            provider_opts_json = provider_opts
        else:
            provider_opts_json = "{}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO model_configs
                   (id, display_name, litellm_model, api_key, api_base,
                    max_tokens, default_temperature,
                    cost_per_million_input, cost_per_million_input_cached,
                    cost_per_million_output, currency, is_active,
                    provider, provider_options_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    config["id"],
                    config["display_name"],
                    config["litellm_model"],
                    config.get("api_key", ""),
                    config.get("api_base"),
                    config.get("max_tokens", 4096),
                    config.get("default_temperature", 0.7),
                    config.get("cost_per_million_input", 0),
                    config.get("cost_per_million_input_cached", 0),
                    config.get("cost_per_million_output", 0),
                    config.get("currency", "CNY"),
                    config.get("is_active", True),
                    config.get("provider", "generic"),
                    provider_opts_json,
                    config.get("created_at", now),
                ),
            )
            await db.commit()

    async def delete_model(self, model_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM agent_model_bindings WHERE model_config_id = ?", (model_id,))
            await db.execute("DELETE FROM model_configs WHERE id = ?", (model_id,))
            await db.commit()

    async def get_bindings(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT b.*, m.display_name as model_display_name,
                          m.litellm_model, m.provider
                   FROM agent_model_bindings b
                   LEFT JOIN model_configs m ON b.model_config_id = m.id"""
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def bind_agent(
        self,
        agent_name: str,
        model_config_id: str,
        temperature_override: float | None = None,
        max_tokens_override: int | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO agent_model_bindings
                   (agent_name, model_config_id, temperature_override, max_tokens_override)
                   VALUES (?, ?, ?, ?)""",
                (agent_name, model_config_id, temperature_override, max_tokens_override),
            )
            await db.commit()

    async def unbind_agent(self, agent_name: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM agent_model_bindings WHERE agent_name = ?", (agent_name,))
            await db.commit()

    async def get_model_for_agent(self, agent_name: str) -> dict | None:
        """Get the resolved model config for a specific agent.

        Returns dict with model config + any binding overrides, or None if no binding.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT m.*, b.temperature_override, b.max_tokens_override
                   FROM agent_model_bindings b
                   JOIN model_configs m ON b.model_config_id = m.id
                   WHERE b.agent_name = ? AND m.is_active = 1""",
                (agent_name,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = _parse_row(row)
            # Apply overrides
            if result.get("temperature_override") is not None:
                result["default_temperature"] = result["temperature_override"]
            if result.get("max_tokens_override") is not None:
                result["max_tokens"] = result["max_tokens_override"]
            return result

    # --- Preset seeding + one-click tier binding ---

    async def seed_preset(self, preset: dict, api_key: str = "") -> dict:
        """Insert a preset, or update the api_key of an existing one.

        - If the model does NOT exist: create it with the supplied api_key.
        - If the model EXISTS and a new api_key is supplied: update only the
          api_key (preserves any user customizations to prices, max_tokens, etc.).
        - If the model EXISTS and no api_key is supplied: no-op.
        """
        existing = await self.get_model(preset["id"])
        if existing:
            if api_key and existing.get("api_key") != api_key:
                existing["api_key"] = api_key
                await self.save_model(existing)
                existing["_updated"] = True
            return existing

        cfg = {
            "id": preset["id"],
            "display_name": preset["display_name"],
            "litellm_model": preset["litellm_model"],
            "api_key": api_key or preset.get("api_key", ""),
            "api_base": preset.get("api_base"),
            "max_tokens": preset.get("max_tokens", 4096),
            "default_temperature": preset.get("default_temperature", 0.7),
            "cost_per_million_input": preset.get("cost_per_million_input", 0),
            "cost_per_million_input_cached": preset.get("cost_per_million_input_cached", 0),
            "cost_per_million_output": preset.get("cost_per_million_output", 0),
            "currency": preset.get("currency", "CNY"),
            "is_active": preset.get("is_active", True),
            "provider": preset.get("provider", "generic"),
            "provider_options": preset.get("provider_options", {}),
        }
        await self.save_model(cfg)
        cfg["_created"] = True
        return cfg

    async def bind_many(self, bindings: dict[str, list[str]]) -> int:
        """Apply {model_id: [agent, ...]} bindings in bulk. Returns count applied.

        Skips agents whose model_id does not exist.
        """
        count = 0
        for model_id, agents in bindings.items():
            model = await self.get_model(model_id)
            if not model:
                logger.warning(f"[ModelRegistry] Skipping binding — model {model_id} not found")
                continue
            for agent in agents:
                await self.bind_agent(agent, model_id)
                count += 1
        return count
