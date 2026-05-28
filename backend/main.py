import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chapters, control, llm_admin, public, quality_admin, stories
from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.context_builder import ContextBuilder
from backend.memory.knowledge_graph import KnowledgeGraph
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.memory.world_book import WorldBook
from backend.services.task_registry import TaskRegistry
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    # Ensure data directories exist
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)

    # Initialize stores
    sqlite = SQLiteStore(settings.sqlite_path)
    await sqlite.initialize()
    vector = VectorStore(settings.chroma_path)

    # Initialize LLM management
    model_registry = ModelRegistry(settings.sqlite_path)
    llm_logger = LLMLogger(settings.sqlite_path)
    llm = LLMClient(settings, registry=model_registry, llm_logger=llm_logger)

    # Initialize memory system
    knowledge_graph = KnowledgeGraph(settings.sqlite_path)
    layered_memory = LayeredMemory(vector, knowledge_graph)
    chapter_extractor = ChapterExtractor(llm, vector, knowledge_graph, settings.sqlite_path, sqlite_store=sqlite)
    world_book = WorldBook(sqlite)
    context_builder = ContextBuilder(sqlite, vector, knowledge_graph, world_book)

    app.state.settings = settings
    app.state.sqlite = sqlite
    app.state.json_store = JSONStore(settings.data_dir)
    app.state.vector = vector
    app.state.model_registry = model_registry
    app.state.llm_logger = llm_logger
    app.state.progress_store = ProgressStore()
    app.state.llm = llm
    app.state.knowledge_graph = knowledge_graph
    app.state.layered_memory = layered_memory
    app.state.chapter_extractor = chapter_extractor
    app.state.plot_dedup = PlotDedupStore(settings.chroma_path)
    app.state.world_book = world_book
    app.state.context_builder = context_builder
    app.state.task_registry = TaskRegistry()

    logging.getLogger(__name__).info(
        f"Story Engine started. Default model: {settings.litellm_model} | Memory system: enabled"
    )
    yield


app = FastAPI(title="Story Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(chapters.router, prefix="/api/stories/{story_id}/chapters", tags=["chapters"])
app.include_router(control.router, prefix="/api/stories/{story_id}/control", tags=["control"])
app.include_router(llm_admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(quality_admin.router, prefix="/api/admin/quality", tags=["quality"])
app.include_router(public.router, prefix="/api/public", tags=["public"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
