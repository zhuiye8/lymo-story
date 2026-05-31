# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Story Engine (狸梦小说 / Lymo Story) — a multi-agent AI system for generating Chinese fiction novels. Specialized LLM agents coordinate via LangGraph to produce chapters with **factual consistency** (DOME quads), **character emotional continuity** (layered semantic memory), and **setup/payoff structure** (foreshadowing loop), under a deterministic anti-slop quality gate.

All prompts and generated content are in **Chinese**. Documentation is also primarily Chinese.

> **This is the Phase 1 rebuild.** The codebase was rebuilt from zero (no Phase-0 backward compat). The active code lives in `backend/**/phase1*` modules. Design docs: `phase1/00-architecture.md`, `phase1/01-implementation-plan.md`.

## Model & infra constraints (hard)

- **Only two LLM providers**: DeepSeek API (backbone) + Xiaomi MiMo API (2nd judge, subscription). No other cloud LLMs.
  - `deepseek-v4-pro` (deepseek-chat, temp 0.85) — prose (scene_writer + rewrite)
  - `deepseek-v4-flash` (deepseek-chat, temp 0.5) — structured/batch (init agents, outline/scene/extract, critic_primary)
  - `mimo-v2.5-pro` (via newapi proxy) — critic_secondary (heterogeneous de-bias; thinking disabled)
- **Embedding**: local **ollama + Qwen3-Embedding-4B** on GPU (RTX 4080 SUPER). No embedding API (DeepSeek has none).
- Model configs/bindings live in the **DB** (seeded by `scripts/seed_phase1_models.py`), not hardcoded.

## Commands

### Backend (Python, conda env "story") — run from repo root

```bash
conda activate story
pip install -e ".[dev]"                          # install with dev deps

python scripts/seed_phase1_models.py             # seed model configs + agent bindings into DB (run once / after .env model changes)
uvicorn backend.main:app --reload --port 8000    # dev server (note: backend.main, run from ROOT not backend/)

# Tests (live in backend/tests/)
pytest backend/tests/                             # all tests
pytest backend/tests/test_quads_conflict_p1.py    # single file
pytest backend/tests/test_storage_p1.py -v        # verbose
```

### Frontend (Next.js 16, pnpm) — admin dashboard

```bash
cd frontend
pnpm install
pnpm dev           # localhost:3000
pnpm run build     # production build (also typechecks)
pnpm run lint
```

### Reader (separate Next.js 16 app) — ⚠️ not yet re-aligned to Phase 1 API

```bash
cd reader && pnpm install && pnpm dev   # localhost:4000
```

### Ollama (semantic-memory embedding) — required for memory recall

```bash
ollama pull qwen3-embedding:4b   # one-time (2.5GB); ollama auto-starts as a service on Windows
```

### Environment

Copy `.env.example` to `.env`. All vars use the `STORY_` prefix (Pydantic Settings, `backend/config.py`). `.env` is gitignored — credentials never enter source.

- `STORY_LITELLM_MODEL` / `STORY_LITELLM_API_KEY` / `STORY_LITELLM_API_BASE` — DeepSeek backbone
- `STORY_MIMO_ENABLED` + `STORY_MIMO_API_KEY` / `STORY_MIMO_API_BASE` / `STORY_MIMO_MODEL` — 2nd judge (read at **seed** time → stored in DB; re-run seed after changing). `false` → single-judge degrade.
- `STORY_EMBED_PROVIDER=ollama` + `STORY_EMBED_MODEL=qwen3-embedding:4b` + `STORY_OLLAMA_BASE_URL` — semantic memory. `default` → ChromaDB all-MiniLM (CPU, weak Chinese).

## Architecture

### Three-tier layout

- `backend/` — Python FastAPI. Agents, LangGraph orchestration, memory, quality, storage, API.
- `frontend/` — Next.js 16 admin dashboard (Phase 1). Create story, generation progress, chapter reading, quality/memory/foreshadowing viz, LLM management.
- `reader/` — Next.js 16 public reader. ⚠️ still Phase-0 shape; not yet wired to the Phase 1 `/api/public/books/*` responses.

### LangGraph pipelines (backend/graph/)

**Init graph** (`phase1_init.py`) — creates a story (5 linear nodes):
`concept → world_build → character_design → outline_plan → assemble`
assemble persists: bible (`stories.bible_json`), characters (+ voice_profile), rough outline, initial DOME quads (存活/身份 baseline), and **L0 identity-core memories** per character.

**Chapter graph** (`phase1_chapter.py`) — generates one chapter (7 nodes):
`load_context → outline_advance → scene_plan → retrieve_memory → write_chapter → extract_memory → save`
- `write_chapter` does **best-of-N** (N=2): N drafts → each through the quality gate → pick highest composite.
- `retrieve_memory` surfaces DOME hard-constraints + character states + **semantic memory recall** (relevant + high-emotional) + open foreshadowing.
- `save` writes chapter/outline/quads (normalized + deduped) + character_states + foreshadowing (plant/resolve) + L1 memories + quality.

**Quality gate** (`phase1_quality_gate.py`): deterministic slop detect → word-count correction → local rewrite loop → **heterogeneous critic room** (8-dim WebNovelBench rubric).

### Agents (backend/agents/phase1/)

Each extends `BaseAgent`. Structured agents use `_call_structured(response_model)` (Instructor over LiteLLM, Pydantic validation + reask); the writer uses `_call_text`. Prompts in `backend/prompts/phase1/`.

| Agent | Role | Model |
|-------|------|-------|
| ConceptAgent | theme → concept (title/genre/tone/special_ability) | flash |
| WorldBuilderAgent | world (3-step: core → factions → rules) | flash |
| CharacterDesignerAgent | roster → per-character design + voice fingerprint | flash |
| OutlinePlannerAgent | skeleton → volumes (rough outline) | flash |
| OutlineAdvanceAgent | rough stage → this chapter's detailed beats | flash |
| ScenePlanAgent | beats → scenes + per-scene word budget + hook | flash |
| SceneWriterAgent | scene → Chinese prose | **pro** |
| MemoryExtractorAgent | chapter → quads + state_changes + memories + foreshadowing + summary | flash |
| critic_primary / critic_secondary | score 8 dims | flash / **mimo** |

### Memory (backend/memory/) — three info types, each in its place

- **DOME quads** (`knowledge_quads.py` + `predicates.py`) — durable **state facts** only. Controlled predicate vocab: SINGLE_VALUED {存活状态, 境界} (conflict-checked) + MULTI_VALUED {身份, 阵营, 能力, 持有, 关系}. Event/action verbs are dropped (→ summary). `find_conflicts` flags real contradictions only (single-valued + incompatible object + not-invalidating). Invalidate-not-delete via `[valid_from, valid_to)`. Write-time dedup on compatible objects.
- **character_states** (SQLite) — volatile state (location/status/emotion), last-write-wins, no conflict concept.
- **LayeredMemory** (`layered_memory.py`) — character emotional continuity. L0 identity-core (init seed) + L1 emotional-key (per chapter, weighted) → dual-written to SQLite (`memories` table) + ChromaDB (Qwen3 vectors). L2/L3 are recall *modes* (semantic + emotional-weight).
- **Foreshadowing** (`foreshadowing` table) — plant → surface-to-planner (age-prioritized) → resolve. Events/knowledge → chapter `summary` (recent-3 window feeds context).

### Quality (backend/quality/)

- `slop_lexicon_zh.py` + `slop_detector.py` — frequency-aware Chinese slop detection (returns penalty + flagged spans for local rewrite).
- `rubric.py` — 8-dim WebNovelBench SEQR rubric + `composite_score` = mean(8) − slop − consistency penalty.
- `critic_room.py` — heterogeneous critics (DeepSeek + MiMo); judge must differ from generator. Graceful degrade to single judge.
- `rewrite.py` — slop rewrite (plain chat, NOT FIM), expand/compress (prefix-completion, preserve hook).

### LLM layer (backend/llm/)

- **LiteLLM** gateway (`client.py`) — `complete_structured` (instructor), `complete_with_logprobs`, `prefix_complete`/`fim_complete` (/beta). `providers/` adapters (`deepseek`, `mimo`) supply `build_extra_body` (MiMo: `enable_thinking=false`).
- **ModelRegistry** — per-agent model binding (reads DB).
- **LLMLogger** — every call logged (tokens/cost/latency).
- **VectorStore** (`storage/vector_store.py`) — ChromaDB; embedding function config-driven (ollama Qwen3 or default all-MiniLM).

### API routes (backend/api/)

- `/api/stories` — create / list / get(+bible) / progress / characters / outline / generate / chapters / chapters/{n} / **foreshadowing** / **memories**
- `/api/admin/quality/stories` + `/api/admin/quality/story/{id}/{trend,by-dimension,heatmap,distribution}`
- `/api/admin/*` — LLM model/binding/log management (`llm_admin.py`)
- `/api/public/books` — published reader endpoints
- `/api/health`

### Dependency injection (backend/deps.py)

Services (sqlite, vector, **mem** = LayeredMemory, llm, registry, quads, progress, task_registry) init in FastAPI lifespan (`main.py`), injected via `Depends()` / read off `app.state`.

## Key conventions

- **Package manager**: pnpm for frontend/reader, pip for backend (conda env "story").
- **Run backend from repo root** (`uvicorn backend.main:app`), not from `backend/`.
- **Seed before first run**: `python scripts/seed_phase1_models.py` populates model configs + agent bindings in the DB.
- **Next.js 16 breaking changes**: frontend apps use Next.js 16. **Always read `node_modules/next/dist/docs/` before writing Next.js code.** Pages are client components using `use(params)` + a `fetchJson` client (`frontend/lib/api.ts`), `NEXT_PUBLIC_API_URL` default `http://localhost:8000/api`.
- **Async everywhere**: FastAPI + aiosqlite. Generation runs as background tasks. ChromaDB (sync) is wrapped in `asyncio.to_thread`.
- **LLM calls go through BaseAgent**: never call LiteLLM directly. `_call_structured` (Pydantic) / `_call_text` (prose).
- **Avoid probabilistic schema failures**: split complex nested structured-output into small steps (B-refactor); don't ask the model for one giant deeply-nested object.
- **Graph state is the source of truth**: inter-node data flows through `ChapterState` / `InitState` (TypedDicts defined inline in `backend/graph/phase1_chapter.py` / `phase1_init.py`).
- **Runtime data is gitignored**: `data/` (SQLite, ChromaDB) is not committed.
- **Commit attribution**: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
