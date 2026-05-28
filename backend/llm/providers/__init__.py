"""Provider-specific adapters for LLM providers.

Each provider module exposes:
  - PRESETS: list of model preset dicts (for UI quick-fill + seed data)
  - build_extra_body(options: dict) -> dict | None: per-provider extra params
  - resolve_model_name(litellm_model: str, api_base: str | None) -> str
"""
from backend.llm.providers import deepseek

PROVIDERS = {
    "deepseek": deepseek,
}


def get_provider(name: str):
    """Get provider module by name. Returns None if unknown."""
    return PROVIDERS.get(name)


def all_presets() -> list[dict]:
    """All presets from all providers, flat."""
    out = []
    for name, mod in PROVIDERS.items():
        for preset in getattr(mod, "PRESETS", []):
            p = dict(preset)
            p.setdefault("provider", name)
            out.append(p)
    return out


def build_extra_body(provider: str, options: dict | None) -> dict | None:
    """Compute extra_body for a provider. Returns None if not applicable."""
    if not provider or provider == "generic":
        return None
    mod = get_provider(provider)
    if not mod or not hasattr(mod, "build_extra_body"):
        return None
    return mod.build_extra_body(options or {})
