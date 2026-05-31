# AGENTS.md

Agent guidance for this repository lives in **[CLAUDE.md](./CLAUDE.md)** — read it in full before working here. It is the single source of truth for architecture, commands, the Phase 1 pipeline, and conventions.

Critical reminders (see CLAUDE.md for detail):

- **Phase 1 rebuild**: active code is in `backend/**/phase1*`. No Phase-0 backward compat.
- **Run the backend from the repo root**: `uvicorn backend.main:app --reload --port 8000`. Seed first: `python scripts/seed_phase1_models.py`. Tests: `pytest backend/tests/`.
- **Only two LLM providers** (DeepSeek + MiMo) + local **ollama Qwen3-Embedding** for memory. Configure via `.env` (`STORY_` prefix); never hardcode credentials.
- **Next.js 16**: read `node_modules/next/dist/docs/` before writing any frontend code.
- **Memory model**: DOME quads = durable state facts only (controlled predicates); events → summary; emotional continuity → LayeredMemory (L0/L1, ChromaDB); foreshadowing has a plant/resolve loop.
