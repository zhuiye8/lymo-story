import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.config import Settings
from backend.agents.outline_parser import OutlineParserAgent
from backend.deps import (
    get_chapter_extractor, get_context_builder, get_json_store,
    get_knowledge_graph, get_layered_memory, get_llm, get_plot_dedup,
    get_progress_store, get_settings, get_sqlite, get_task_registry,
    get_vector, get_world_book,
)
from backend.services.task_registry import TaskRegistry
from backend.models.story_bible import extract_characters_from_bible
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.context_builder import ContextBuilder
from backend.memory.knowledge_graph import KnowledgeGraph
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.memory.world_book import WorldBook
from backend.progress import ProgressStore
from backend.graph.chapter_graph import build_chapter_graph
from backend.graph.init_graph import build_init_graph
from backend.llm.client import LLMClient
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

router = APIRouter()


class CreateStoryRequest(BaseModel):
    theme: str
    requirements: str = ""
    title: str = ""  # optional: user-specified book name
    skip_init: bool = False  # True for import-outline mode (skip 4-agent pipeline)


class GenerateRequest(BaseModel):
    word_count: int | None = None  # Override default_chapter_word_count


class ImportOutlineRequest(BaseModel):
    raw_text: str
    title: str = ""


class StoryResponse(BaseModel):
    story_id: str
    title: str
    theme: str
    status: str
    chapter_count: int = 0
    is_published: bool = False


async def _run_init(
    story_id: str,
    theme: str,
    requirements: str,
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    title: str = "",
    world_book: WorldBook | None = None,
):
    """Background task: initialize a story."""
    try:
        graph = build_init_graph(llm, title=title, world_book=world_book)
        compiled = graph.compile()
        result = await compiled.ainvoke({
            "story_id": story_id,
            "user_theme": theme,
            "user_requirements": requirements,
            "concept": None,
            "world_setting": None,
            "characters_design": None,
            "outline": None,
            "story_bible": None,
            "characters": [],
            "initial_world_state": None,
        })

        bible = result.get("story_bible", {})
        characters = result.get("characters", [])
        world_state = result.get("initial_world_state", {})

        # Persist
        json_store.save_story_bible(story_id, bible)
        json_store.save_characters(story_id, characters)
        json_store.save_event_graph(story_id, [])
        await sqlite.save_world_state(story_id, world_state, 0)
        await sqlite.update_story(story_id, title=bible.get("title", ""), status="bible_ready")
    except asyncio.CancelledError:
        logging.getLogger(__name__).warning(f"Init cancelled for {story_id}")
        await sqlite.update_story(story_id, status="error: 用户已停止初始化")
        raise
    except Exception as e:
        await sqlite.update_story(story_id, status=f"error: {str(e)[:200]}")


async def _run_chapter(
    story_id: str,
    chapter_num: int,
    llm: LLMClient,
    settings: Settings,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    vector: VectorStore,
    progress_store: ProgressStore | None = None,
    layered_memory: LayeredMemory | None = None,
    chapter_extractor: ChapterExtractor | None = None,
    human_feedback: str | None = None,
    plot_dedup: PlotDedupStore | None = None,
    word_count: int | None = None,
    context_builder: ContextBuilder | None = None,
):
    """Background task: generate one chapter."""
    if progress_store:
        progress_store.start(story_id, chapter_num)
    try:
        await sqlite.update_story(story_id, status="generating")
        graph = build_chapter_graph(
            llm, sqlite, json_store, vector,
            progress_store, layered_memory, chapter_extractor,
            plot_dedup, context_builder,
            chapter_consistency_threshold=settings.chapter_consistency_threshold,
            chapter_max_critical=settings.chapter_max_critical,
            chapter_max_warnings=settings.chapter_max_warnings,
            scene_consistency_threshold=settings.scene_consistency_threshold,
        )
        compiled = graph.compile()

        await compiled.ainvoke({
            "story_id": story_id,
            "chapter_num": chapter_num,
            "story_bible": {},
            "world_state": {},
            "event_history": [],
            "character_profiles": [],
            "new_events": [],
            "storylines": [],
            "plot_structure": None,
            "camera_decision": None,
            "chapter_draft": "",
            "consistency_result": None,
            "consistency_pass": False,
            "retry_count": 0,
            "target_word_count": word_count or settings.default_chapter_word_count,
            "max_retries": settings.max_consistency_retries,
            "memory_contexts": {},
            "context_bundle": {},
            "upstream_dependencies": [],
            "scenes": [],
            "current_scene_idx": 0,
            "scene_contents": [],
            "scene_retry_count": {},
            "scene_consistency_results": [],
            "scene_context_bundle": {},
            "current_version_id": 0,
            "error_message": "",
            "human_feedback": human_feedback,
        })

        await sqlite.update_story(story_id, status="bible_ready")
    except asyncio.CancelledError:
        logging.getLogger(__name__).warning(
            f"Chapter generation cancelled for {story_id} ch{chapter_num}"
        )
        if progress_store:
            progress_store.set_error(story_id, "用户已停止")
        await sqlite.update_story(story_id, status="bible_ready")
        raise  # propagate cancellation
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logging.getLogger(__name__).error(f"Chapter generation failed for {story_id}:\n{tb}")
        if progress_store:
            progress_store.set_error(story_id, str(e)[:200])
        # Store full traceback in status for debugging (truncated)
        error_detail = f"{str(e)[:100]} | {tb[-300:]}"
        await sqlite.update_story(story_id, status=f"error: {error_detail[:400]}")


@router.post("", response_model=StoryResponse)
async def create_story(
    req: CreateStoryRequest,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
    world_book: WorldBook = Depends(get_world_book),
    task_registry: TaskRegistry = Depends(get_task_registry),
):
    story_id = str(uuid.uuid4())[:8]
    await sqlite.create_story(story_id, req.title, req.theme)

    if req.skip_init:
        # Import-outline mode: just create record, don't run 4-agent pipeline
        await sqlite.update_story(story_id, status="awaiting_outline")
    else:
        task = asyncio.create_task(
            _run_init(story_id, req.theme, req.requirements, llm, sqlite, json_store, req.title, world_book)
        )
        task_registry.register(story_id, 0, task, kind="init")

    return StoryResponse(
        story_id=story_id,
        title=req.title,
        theme=req.theme,
        status="awaiting_outline" if req.skip_init else "initializing",
        chapter_count=0,
    )


@router.get("", response_model=list[StoryResponse])
async def list_stories(sqlite: SQLiteStore = Depends(get_sqlite)):
    rows = await sqlite.list_stories()
    result = []
    for r in rows:
        count = await sqlite.get_chapter_count(r["id"])
        result.append(StoryResponse(
            story_id=r["id"],
            title=r.get("title", ""),
            theme=r["theme"],
            status=r["status"],
            chapter_count=count,
            is_published=bool(r.get("is_published", 0)),
        ))
    return result


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, sqlite: SQLiteStore = Depends(get_sqlite)):
    row = await sqlite.get_story(story_id)
    if not row:
        raise HTTPException(404, "Story not found")
    count = await sqlite.get_chapter_count(story_id)
    return StoryResponse(
        story_id=row["id"],
        title=row.get("title", ""),
        theme=row["theme"],
        status=row["status"],
        chapter_count=count,
        is_published=bool(row.get("is_published", 0)),
    )


@router.get("/{story_id}/bible")
async def get_bible(story_id: str, json_store: JSONStore = Depends(get_json_store)):
    bible = json_store.load_story_bible(story_id)
    if not bible:
        raise HTTPException(404, "Story Bible not found")
    return bible


@router.put("/{story_id}/bible")
async def update_bible(
    story_id: str,
    bible: dict,
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    """Save edited story bible. Overwrites the entire bible JSON."""
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    bible["bible_version"] = 2

    # Update characters.json from bible
    characters = extract_characters_from_bible(bible)
    json_store.save_story_bible(story_id, bible)
    json_store.save_characters(story_id, characters)

    # Update story title if changed
    if bible.get("title"):
        await sqlite.update_story(story_id, title=bible["title"])

    return {"message": "Story Bible updated", "title": bible.get("title", "")}


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    """Delete a story and all its data."""
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    # Delete from SQLite
    async with __import__("aiosqlite").connect(sqlite.db_path) as db:
        await db.execute("DELETE FROM chapters WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM chapter_versions WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM world_states WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM character_states WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM character_arcs WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM knowledge_triples WHERE story_id = ?", (story_id,))
        await db.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        await db.commit()

    # Delete JSON files
    import shutil
    story_dir = json_store._story_dir(story_id)
    if story_dir.exists():
        shutil.rmtree(story_dir)

    return {"message": f"Story {story_id} deleted"}


class OutlineRegenRequest(BaseModel):
    user_instructions: str = ""


@router.post("/{story_id}/outline/regenerate")
async def regenerate_outline(
    story_id: str,
    req: OutlineRegenRequest,
    llm: LLMClient = Depends(get_llm),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    """Regenerate the volume outline based on the current bible + user instructions.

    Preserves concept/world/characters, only replaces the volumes/initial_conflicts/planned_arc.
    """
    from backend.agents.outline_planner import OutlinePlannerAgent

    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    bible = json_store.load_story_bible(story_id)
    if not bible:
        raise HTTPException(404, "Story bible not found")

    # Reconstruct concept/world/characters from bible for the agent
    concept = {
        "title": bible.get("title", ""),
        "genre": bible.get("genre", ""),
        "tone": bible.get("tone", ""),
        "synopsis": bible.get("synopsis", ""),
        "inspiration": bible.get("inspiration", ""),
        "special_ability": (bible.get("world") or {}).get("special_ability") or {},
    }
    world_setting = bible.get("world") or {}
    characters_design = {
        "protagonist": bible.get("protagonist"),
        "antagonist": bible.get("antagonist"),
        "supporting_characters": bible.get("supporting_characters") or [],
    }
    current_outline = {
        "initial_conflicts": bible.get("initial_conflicts") or [],
        "planned_arc": bible.get("planned_arc") or "",
        "volumes": bible.get("volumes") or [],
    }

    agent = OutlinePlannerAgent(llm)
    new_outline = await agent.revise(
        concept=concept,
        world_setting=world_setting,
        characters_design=characters_design,
        current_outline=current_outline,
        user_instructions=req.user_instructions,
        story_id=story_id,
    )

    # Backup old outline into bible for reversibility
    if "_outline_history" not in bible or not isinstance(bible["_outline_history"], list):
        bible["_outline_history"] = []
    bible["_outline_history"].append({
        "replaced_at": __import__("datetime").datetime.now().isoformat(),
        "user_instructions": req.user_instructions,
        "outline": current_outline,
    })
    # Keep only last 5 history entries
    bible["_outline_history"] = bible["_outline_history"][-5:]

    # Apply new outline
    bible["initial_conflicts"] = new_outline.get("initial_conflicts", [])
    bible["planned_arc"] = new_outline.get("planned_arc", "")
    bible["volumes"] = new_outline.get("volumes", [])

    json_store.save_story_bible(story_id, bible)

    return {
        "message": "大纲已重新生成",
        "volumes_count": len(bible["volumes"]),
        "history_count": len(bible["_outline_history"]),
    }


@router.post("/{story_id}/clone-outline")
async def clone_outline_to_new_story(
    story_id: str,
    req: dict | None = None,
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
    world_book: WorldBook = Depends(get_world_book),
):
    """Clone the story's bible to a brand-new story (no chapters, fresh slate).

    Clones: bible.json + characters.json + world book entries + empty event_graph.
    Does NOT clone: chapters, versions, memories, states, arcs, triples, summaries.
    """
    source = await sqlite.get_story(story_id)
    if not source:
        raise HTTPException(404, "Source story not found")

    bible = json_store.load_story_bible(story_id)
    if not bible:
        raise HTTPException(404, "Source bible not found")

    new_story_id = str(uuid.uuid4())[:8]
    title_suffix = (req or {}).get("title_suffix", "（分支）")
    new_title = (bible.get("title", "") or source.get("theme", "")) + title_suffix

    # Create new story
    await sqlite.create_story(new_story_id, new_title, source["theme"])
    await sqlite.update_story(new_story_id, status="bible_ready")

    # Clone bible with new title
    new_bible = {**bible}
    new_bible["title"] = new_title
    # Drop history (fresh slate)
    new_bible.pop("_outline_history", None)
    json_store.save_story_bible(new_story_id, new_bible)

    # Clone characters
    chars = json_store.load_characters(story_id) or []
    json_store.save_characters(new_story_id, chars)

    # Empty event graph
    json_store.save_event_graph(new_story_id, [])

    # Init world state
    initial_world = {
        "story_id": new_story_id,
        "current_time": 0,
        "time_description": "故事开始",
        "global_flags": [],
        "active_character_ids": [c.get("character_id") for c in chars if c.get("character_id")],
        "version": 0,
    }
    await sqlite.save_world_state(new_story_id, initial_world, 0)

    # Sync world book for the new story
    try:
        await world_book.sync_from_bible(new_story_id, new_bible)
    except Exception:
        pass

    return {
        "message": "已克隆大纲到新小说",
        "new_story_id": new_story_id,
        "new_title": new_title,
    }


@router.delete("/{story_id}/chapters/from/{chapter_num}")
async def delete_chapters_from(
    story_id: str,
    chapter_num: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
    vector: VectorStore = Depends(get_vector),
    json_store: JSONStore = Depends(get_json_store),
):
    """Delete chapter_num and all subsequent chapters, plus all their memories.

    SAFETY POLICY (per supervisor review 2026-04-26):
    - chapter_num == 1: full reset (delete all + reset world_state + clear event_graph)
    - chapter_num > 1: REJECTED until per-chapter world_state snapshots are
      implemented. Without snapshots, world_state and event_graph remain at
      the post-deletion-tail state and would contaminate future regeneration.
      Tracked as separate feature (not Phase 0 scope).

    Workaround for N > 1: use chapter version restore + chapter regenerate flow.
    """
    import aiosqlite
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    if chapter_num < 1:
        raise HTTPException(400, "chapter_num must be >= 1")
    if chapter_num > 1:
        raise HTTPException(
            400,
            "Deleting from chapter N>1 is currently disabled. World state and "
            "event graph would remain stale and poison regeneration. "
            "Use full reset (chapter_num=1) or chapter version restore instead. "
            "Safe rewind with per-chapter snapshots is a separate planned feature."
        )

    # Count affected
    async with aiosqlite.connect(sqlite.db_path) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM chapters WHERE story_id = ? AND chapter_num >= ?",
            (story_id, chapter_num),
        )
        row = await cur.fetchone()
        affected = row[0] if row else 0

        # Delete SQLite rows
        for table in ("chapters", "chapter_versions", "chapter_summaries",
                      "chapter_scenes", "character_states", "character_arcs"):
            await db.execute(
                f"DELETE FROM {table} WHERE story_id = ? AND chapter_num >= ?",
                (story_id, chapter_num),
            )
        # knowledge_triples: valid_from is the chapter that created them
        await db.execute(
            "DELETE FROM knowledge_triples WHERE story_id = ? AND valid_from >= ?",
            (story_id, chapter_num),
        )
        # chapter_dependencies (both as source and as depends_on)
        await db.execute(
            "DELETE FROM chapter_dependencies WHERE story_id = ? AND (chapter_num >= ? OR depends_on_chapter >= ?)",
            (story_id, chapter_num, chapter_num),
        )
        await db.commit()

    # Delete vector store entries
    try:
        collection = vector.get_collection(story_id)
        # Fetch all ids with chapter >= N
        got = collection.get(
            where={"chapter": {"$gte": chapter_num}},
            include=[],
        )
        ids = got.get("ids") or []
        if ids:
            collection.delete(ids=ids)
    except Exception:
        pass

    # If we deleted from chapter 1, also reset world state and clear event graph
    if chapter_num == 1:
        try:
            initial_world = {
                "story_id": story_id,
                "current_time": 0,
                "time_description": "故事开始",
                "global_flags": [],
                "active_character_ids": [],
                "version": 0,
            }
            await sqlite.save_world_state(story_id, initial_world, 0)
            json_store.save_event_graph(story_id, [])
        except Exception:
            pass
        await sqlite.update_story(story_id, status="bible_ready")

    return {
        "message": f"已删除从第 {chapter_num} 章起的 {affected} 个章节及相关记忆",
        "deleted_count": affected,
        "from_chapter": chapter_num,
    }


@router.put("/{story_id}/publish")
async def publish_story(
    story_id: str,
    req: dict,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    publish = bool(req.get("publish", False))
    await sqlite.publish_story(story_id, publish)
    return {"message": f"Story {'published' if publish else 'unpublished'}", "is_published": publish}


@router.post("/{story_id}/generate")
async def generate_chapter(
    story_id: str,
    background: BackgroundTasks,
    req: GenerateRequest | None = None,
    llm: LLMClient = Depends(get_llm),
    settings: Settings = Depends(get_settings),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
    vector: VectorStore = Depends(get_vector),
    progress_store: ProgressStore = Depends(get_progress_store),
    layered_memory: LayeredMemory = Depends(get_layered_memory),
    chapter_extractor: ChapterExtractor = Depends(get_chapter_extractor),
    plot_dedup: PlotDedupStore = Depends(get_plot_dedup),
    context_builder: ContextBuilder = Depends(get_context_builder),
    task_registry: TaskRegistry = Depends(get_task_registry),
):
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    # Allow retry from error state
    if story["status"] not in ("bible_ready", "completed") and not story["status"].startswith("error"):
        raise HTTPException(400, f"Story is in state '{story['status']}', cannot generate")

    if task_registry.is_running(story_id):
        raise HTTPException(409, "该小说已有生成任务在运行，请先停止再重新开始")

    word_count = (req.word_count if req and req.word_count else None) or settings.default_chapter_word_count

    chapter_num = await sqlite.get_chapter_count(story_id) + 1
    task = asyncio.create_task(
        _run_chapter(
            story_id, chapter_num, llm, settings, sqlite, json_store, vector,
            progress_store, layered_memory, chapter_extractor,
            None, plot_dedup, word_count, context_builder,
        )
    )
    task_registry.register(story_id, chapter_num, task, kind="chapter")
    return {"message": f"Generating chapter {chapter_num}", "chapter_num": chapter_num, "word_count": word_count}


# --- Visualization endpoints ---


@router.get("/{story_id}/characters")
async def get_characters(
    story_id: str,
    json_store: JSONStore = Depends(get_json_store),
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    """Get character list with latest arc summaries."""
    characters = json_store.load_characters(story_id) or []
    for char in characters:
        cid = char.get("character_id")
        if not cid:
            continue
        try:
            arc = await sqlite.get_latest_character_arc(story_id, cid)
            char["arc_summary"] = arc.get("summary") if arc else None
            char["arc_name"] = arc.get("arc_name") if arc else None
        except Exception:
            char["arc_summary"] = None
    return characters


@router.get("/{story_id}/knowledge-graph")
async def get_knowledge_graph_data(
    story_id: str,
    as_of_chapter: int | None = Query(default=None),
    json_store: JSONStore = Depends(get_json_store),
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
):
    """Get character relationship graph (nodes + edges) for visualization."""
    characters = json_store.load_characters(story_id) or []
    nodes = [
        {"id": c.get("character_id", ""), "name": c.get("name", ""), "role": c.get("role", "")}
        for c in characters
        if c.get("character_id")
    ]

    triples = await kg.get_all_relationships(story_id, as_of_chapter)
    edges = [
        {
            "source": t["subject"],
            "target": t["object"],
            "predicate": t["predicate"],
            "detail": t.get("detail", ""),
            "valid_from": t["valid_from"],
            "valid_to": t.get("valid_to"),
        }
        for t in triples
    ]

    return {"nodes": nodes, "edges": edges}


@router.get("/{story_id}/character-arcs/{character_id}")
async def get_character_arc_history(
    story_id: str,
    character_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    """Get character arc history + per-chapter emotional states."""
    arcs = await sqlite.list_character_arcs(story_id, character_id)
    # Also get per-chapter states
    async with __import__("aiosqlite").connect(sqlite.db_path) as db:
        db.row_factory = __import__("aiosqlite").Row
        cursor = await db.execute(
            """SELECT chapter_num, emotional_state, knowledge_summary, goals_update, status
               FROM character_states
               WHERE story_id = ? AND character_id = ?
               ORDER BY chapter_num""",
            (story_id, character_id),
        )
        states = [dict(row) for row in await cursor.fetchall()]
    return {"arcs": arcs, "states": states}


@router.get("/{story_id}/events")
async def get_events(
    story_id: str,
    json_store: JSONStore = Depends(get_json_store),
):
    """Get event graph for timeline visualization."""
    events = json_store.load_event_graph(story_id) or []
    return events


# --- Outline import ---


async def _run_outline_import(
    story_id: str,
    raw_text: str,
    title: str,
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
):
    """Background task: parse user outline into StoryBible V2 using rule-based parser (no LLM)."""
    try:
        await sqlite.update_story(story_id, status="parsing_outline")
        agent = OutlineParserAgent(llm=llm)
        bible = await agent.run(raw_text=raw_text, title_hint=title, story_id=story_id)

        bible["bible_version"] = 2

        # Extract characters from V2 structured fields
        characters = extract_characters_from_bible(bible)

        # Ensure top-level shortcuts for downstream agents
        world = bible.get("world", {})
        if not bible.get("world_rules"):
            bible["world_rules"] = world.get("world_rules", [])
        if not bible.get("power_system"):
            bible["power_system"] = world.get("power_system")

        # Build world state
        world_state = {
            "story_id": story_id,
            "current_time": 0,
            "time_description": "故事开始",
            "global_flags": [],
            "locations": [],
            "active_character_ids": [
                c.get("character_id") for c in characters if c.get("character_id")
            ],
            "version": 0,
        }

        # Persist
        json_store.save_story_bible(story_id, bible)
        json_store.save_characters(story_id, characters)
        json_store.save_event_graph(story_id, [])
        await sqlite.save_world_state(story_id, world_state, 0)
        await sqlite.update_story(
            story_id, title=bible.get("title", title or ""), status="bible_ready"
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logging.getLogger(__name__).error(f"Outline import failed: {tb}")
        await sqlite.update_story(story_id, status=f"error: {str(e)[:200]}")


@router.get("/{story_id}/version-tree")
async def get_version_tree(
    story_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    """Return the complete version+dependency graph for the version-tree page.

    Shape:
      {
        chapters: [
          {
            chapter_num: int,
            versions: [{id, version_num, title, word_count, is_live, feedback, created_at}]
          }
        ],
        dependencies: [{chapter_num, version_id, depends_on_chapter, depends_on_version_id, dep_type}]
      }
    """
    import aiosqlite
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    async with aiosqlite.connect(sqlite.db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT id, chapter_num, version_num, title, pov,
                      length(content) as word_count, feedback, is_live, created_at
               FROM chapter_versions
               WHERE story_id = ?
               ORDER BY chapter_num, version_num""",
            (story_id,),
        )
        version_rows = [dict(r) for r in await cur.fetchall()]

        cur = await db.execute(
            """SELECT chapter_num, source_version_id, depends_on_chapter,
                      depends_on_version_id, dep_type
               FROM chapter_dependencies
               WHERE story_id = ?""",
            (story_id,),
        )
        dep_rows = [dict(r) for r in await cur.fetchall()]

    # Group by chapter_num
    grouped: dict[int, dict] = {}
    for v in version_rows:
        cn = v["chapter_num"]
        if cn not in grouped:
            grouped[cn] = {"chapter_num": cn, "versions": []}
        grouped[cn]["versions"].append(v)

    return {
        "chapters": [grouped[k] for k in sorted(grouped)],
        "dependencies": dep_rows,
    }


@router.post("/{story_id}/import-outline")
async def import_outline(
    story_id: str,
    req: ImportOutlineRequest,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    """Import a user-pasted outline and parse it into StoryBible V2."""
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    background.add_task(
        _run_outline_import, story_id, req.raw_text, req.title, llm, sqlite, json_store
    )
    return {
        "story_id": story_id,
        "title": req.title or "(parsing...)",
        "status": "parsing_outline",
    }
