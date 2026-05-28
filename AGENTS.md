# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project

Story Engine (狸梦小说 / Lymo Story) — a multi-agent AI system for generating Chinese fiction novels. Six specialized LLM agents coordinate via LangGraph to produce chapters with world consistency, character continuity, and narrative coherence.

All prompts and generated content are in **Chinese**. Documentation is also primarily Chinese.

## Commands

### Backend (Python, conda env "story")

```bash
conda activate story
pip install -e ".[dev]"                          # install with dev deps
uvicorn backend.main:app --reload --port 8000    # dev server

# Tests
pytest                                           # all tests
pytest tests/test_foo.py                         # single file
pytest tests/test_foo.py::test_bar -v            # single test
```

### Frontend (Next.js 16, pnpm)

```bash
cd frontend
pnpm install
pnpm run dev       # localhost:3000
pnpm run build
pnpm run lint      # eslint
```

### Reader (separate Next.js 16 app for published stories)

```bash
cd reader
pnpm install
pnpm run dev       # localhost:4000
```

### Environment

Copy `.env.example` to `.env` and set `STORY_LITELLM_MODEL` and `STORY_LITELLM_API_KEY`. All env vars use the `STORY_` prefix (Pydantic Settings in `backend/config.py`).

## Architecture

### Three-tier layout

- `backend/` — Python FastAPI. Core agent logic, LLM orchestration, storage, API.
- `frontend/` — Next.js 16 admin dashboard. Story creation, generation control, LLM management.
- `reader/` — Next.js 16 public reader. Consumes `/api/public/books/*` endpoints.

### LangGraph pipelines (backend/graph/)

**Init graph** — creates a new story:
`generate_bible (Director) → extract_characters → init_world`

**Chapter graph** — generates one chapter with retry loop:
`load_context → world_advance → plot_plan → camera_decide → load_memories → write_chapter → consistency_check → (pass: save → extract_memories | fail: retry up to 3x)`

### Six agents (backend/agents/)

Each extends `BaseAgent` with `_call_json()` / `_call_text()` wrappers. Prompts are in `backend/prompts/`.

| Agent | Role |
|-------|------|
| Director | Converts user theme → Story Bible JSON |
| World | Advances world timeline, generates events |
| Planner | Structures events into chapter beats |
| Camera | Chooses POV, filters visible events, sets pacing |
| Writer | Generates 2000-4000 char Chinese prose |
| Consistency | Validates chapter against bible/world/characters |

### Storage (backend/storage/)

- **SQLite** (`sqlite_store.py`) — stories, chapters, world states, model configs, agent bindings, LLM logs, knowledge triples, character memories
- **JSON files** (`json_store.py`) — per-story bible, characters, event graph in `data/stories/{id}/`
- **ChromaDB** (`vector_store.py`) — character memory embeddings, one collection per story

### Memory system (backend/memory/)

- **LayeredMemory** — 4-tier: L0 identity core, L1 key memories (by emotional weight), L2 scene-relevant (context filtered), L3 deep search (semantic query)
- **ChapterExtractor** — post-chapter LLM extraction of memories, relationships, state changes
- **KnowledgeGraph** — temporal RDF triples (subject-predicate-object with valid_from/valid_to chapter numbers)

### LLM layer (backend/llm/)

- **LiteLLM** gateway — supports 100+ model providers. Model configs stored in DB.
- **ModelRegistry** — per-agent model binding with temperature overrides
- **LLMLogger** — every call logged with tokens, cost, latency

### API routes (backend/api/)

- `/api/stories` — CRUD + async generation trigger
- `/api/stories/{id}/chapters` — chapter listing and reading
- `/api/stories/{id}/control` — generation status and stage-by-stage progress
- `/api/admin/models`, `/api/admin/bindings`, `/api/admin/logs` — LLM management
- `/api/public/books` — published story reader endpoints
- `/api/health` — health check

### Dependency injection (backend/deps.py)

All services (stores, LLM client, registry, logger, memory, extractor) are initialized during FastAPI lifespan and injected via `Depends()`.

## Key conventions

- **Package manager**: pnpm for frontend/reader, pip for backend (conda env "story")
- **Next.js 16 breaking changes**: Both frontend apps use Next.js 16 which differs significantly from training data. Always read `node_modules/next/dist/docs/` before modifying Next.js code.
- **Async everywhere**: Backend uses async/await throughout (FastAPI + aiosqlite). Chapter generation runs as background tasks.
- **LLM calls go through BaseAgent**: Never call LiteLLM directly. Use `_call_json()` for structured output or `_call_text()` for prose. Both handle retry and logging.
- **Graph state is the source of truth**: During pipeline execution, all inter-agent data flows through `ChapterGraphState` / `InitGraphState` (defined in `backend/models/graph_state.py`).
- **Runtime data is gitignored**: `data/` directory (SQLite DBs, JSON files, ChromaDB) is not committed.
