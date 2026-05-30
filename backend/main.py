"""Story Engine FastAPI 入口（Phase 1 重写）。

精简 lifespan：只初始化 Phase 1 所需。
旧机制（KnowledgeGraph/WorldBook/ChapterExtractor/plot_dedup/json_store/
context_builder/旧 stories/chapters/control 路由）已弃用。
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import llm_admin, quality_admin, public, phase1_stories
from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.services.task_registry import TaskRegistry
from backend.progress import ProgressStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)

    sqlite = SQLiteStore(settings.sqlite_path)
    await sqlite.initialize()

    model_registry = ModelRegistry(settings.sqlite_path)
    llm_logger = LLMLogger(settings.sqlite_path)
    llm = LLMClient(settings, registry=model_registry, llm_logger=llm_logger)
    quads = KnowledgeQuads(settings.sqlite_path)

    app.state.settings = settings
    app.state.sqlite = sqlite
    app.state.vector = VectorStore(settings.chroma_path)
    app.state.model_registry = model_registry
    app.state.llm_logger = llm_logger
    app.state.llm = llm
    app.state.quads = quads
    app.state.progress_store = ProgressStore()
    app.state.task_registry = TaskRegistry()

    logging.getLogger(__name__).info(
        f"Story Engine (Phase 1) started. Default model: {settings.litellm_model}"
    )
    yield


app = FastAPI(title="Story Engine", version="1.0.0-phase1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(phase1_stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(llm_admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(quality_admin.router, prefix="/api/admin/quality", tags=["quality"])
app.include_router(public.router, prefix="/api/public", tags=["public"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
