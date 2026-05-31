"""Phase 1 故事 API 路由（全新精简）。

依据 phase1/00-architecture.md §3 + 01-implementation-plan.md Step 7。
端点：
  POST /                          创建故事（题材）→ 后台跑初始化管线
  GET  /                          列出故事
  GET  /{id}                      故事详情 + bible
  GET  /{id}/progress             生成进度（init / 章节生成 stage）
  GET  /{id}/characters           角色列表（含 voice_profile）
  GET  /{id}/outline              粗纲
  POST /{id}/generate             生成下一章（后台）
  GET  /{id}/chapters             章节列表
  GET  /{id}/chapters/{num}       读单章
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.deps import get_sqlite, get_llm, get_quads, get_progress_store
from backend.storage.sqlite_store import SQLiteStore
from backend.llm.client import LLMClient
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.memory.layered_memory import LayeredMemory
from backend.progress import ProgressStore
from backend.graph.phase1_init import build_init_graph
from backend.graph.phase1_chapter import build_chapter_graph

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------- request/response ----------

class CreateStoryReq(BaseModel):
    title: str = ""
    theme: str = Field(description="题材想法/一句话设定")
    requirements: str = ""
    genre: str = "男频系统流"
    target_chapters: int = 60


class CreateStoryResp(BaseModel):
    story_id: str
    status: str


class GenerateReq(BaseModel):
    target_words: int = 3500


# ---------- background runners ----------

async def _run_init(app_state, story_id: str, theme: str, requirements: str, title: str, target_chapters: int):
    store: SQLiteStore = app_state.sqlite
    llm: LLMClient = app_state.llm
    quads: KnowledgeQuads = app_state.quads
    mem: LayeredMemory = app_state.mem
    progress: ProgressStore = app_state.progress_store
    try:
        progress.start(story_id, 0)
        progress.enter_stage(story_id, "init", "生成立意/世界观/角色/大纲")
        graph = build_init_graph(llm, store, quads, mem)
        await graph.ainvoke({
            "story_id": story_id, "theme": theme, "requirements": requirements,
            "title": title, "target_chapters": target_chapters,
        })
        progress.finish_stage(story_id, "init", "bible 就绪")
    except Exception as e:
        logger.exception(f"init failed for {story_id}")
        progress.set_error(story_id, str(e)[:300])
        await store.update_story_status(story_id, "init_failed")


async def _run_chapter(app_state, story_id: str, chapter_num: int, target_words: int):
    store: SQLiteStore = app_state.sqlite
    llm: LLMClient = app_state.llm
    quads: KnowledgeQuads = app_state.quads
    mem: LayeredMemory = app_state.mem
    progress: ProgressStore = app_state.progress_store
    try:
        progress.start(story_id, chapter_num)
        progress.enter_stage(story_id, "generate", f"生成第 {chapter_num} 章")
        graph = build_chapter_graph(llm, store, quads, mem)
        await graph.ainvoke({"story_id": story_id, "chapter_num": chapter_num, "target_words": target_words})
        progress.finish_stage(story_id, "generate", f"第 {chapter_num} 章完成")
    except Exception as e:
        logger.exception(f"chapter {chapter_num} failed for {story_id}")
        progress.set_error(story_id, str(e)[:300])


# ---------- endpoints ----------

@router.post("", response_model=CreateStoryResp)
async def create_story(req: CreateStoryReq, request: Request,
                       store: SQLiteStore = Depends(get_sqlite)):
    story_id = uuid.uuid4().hex[:8]
    await store.create_story(story_id, req.title or "未命名", genre=req.genre, theme=req.theme)
    await store.update_story_status(story_id, "initializing")
    # 后台跑初始化管线
    asyncio.create_task(_run_init(
        request.app.state, story_id, req.theme, req.requirements, req.title, req.target_chapters))
    return CreateStoryResp(story_id=story_id, status="initializing")


@router.get("")
async def list_stories(store: SQLiteStore = Depends(get_sqlite)):
    return await store.list_stories()


@router.get("/{story_id}")
async def get_story(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    s = await store.get_story(story_id)
    if not s:
        raise HTTPException(404, "story not found")
    return s


@router.get("/{story_id}/progress")
async def get_progress(story_id: str, progress: ProgressStore = Depends(get_progress_store),
                       store: SQLiteStore = Depends(get_sqlite)):
    p = progress.get(story_id)
    s = await store.get_story(story_id)
    return {"progress": p, "status": s["status"] if s else None,
            "chapter_count": await store.get_chapter_count(story_id) if s else 0}


@router.get("/{story_id}/characters")
async def get_characters(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    return await store.list_characters(story_id)


@router.get("/{story_id}/outline")
async def get_outline(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    return await store.get_rough_outline(story_id)


@router.post("/{story_id}/generate")
async def generate_chapter(story_id: str, req: GenerateReq, request: Request,
                           store: SQLiteStore = Depends(get_sqlite)):
    s = await store.get_story(story_id)
    if not s:
        raise HTTPException(404, "story not found")
    if s["status"] not in ("bible_ready", "writing"):
        raise HTTPException(400, f"story not ready to generate (status={s['status']})")
    next_num = await store.get_chapter_count(story_id) + 1
    await store.update_story_status(story_id, "writing")
    asyncio.create_task(_run_chapter(request.app.state, story_id, next_num, req.target_words))
    return {"story_id": story_id, "chapter_num": next_num, "status": "generating"}


@router.get("/{story_id}/chapters")
async def list_chapters(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    return await store.list_chapters(story_id)


@router.get("/{story_id}/chapters/{chapter_num}")
async def get_chapter(story_id: str, chapter_num: int, store: SQLiteStore = Depends(get_sqlite)):
    ch = await store.get_chapter(story_id, chapter_num)
    if not ch:
        raise HTTPException(404, "chapter not found")
    return ch


@router.get("/{story_id}/foreshadowing")
async def get_foreshadowing(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    """伏笔看板：埋坑/填坑列表 + 统计。"""
    items = await store.list_foreshadowing(story_id)
    chapter_count = await store.get_chapter_count(story_id)
    for it in items:
        if it["status"] == "open":
            it["age"] = max(0, chapter_count - it["planted_chapter"])
    resolved = sum(1 for it in items if it["status"] == "resolved")
    return {
        "items": items,
        "total": len(items),
        "open": len(items) - resolved,
        "resolved": resolved,
    }


@router.get("/{story_id}/memories")
async def get_memories(story_id: str, store: SQLiteStore = Depends(get_sqlite)):
    """分层记忆看板：L0 身份核心 / L1 情感关键，按角色分组。"""
    rows = await store.list_memories(story_id)
    chars = {c["character_id"]: c["name"] for c in await store.list_characters(story_id)}
    for r in rows:
        r["character_name"] = chars.get(r["character_id"], r["character_id"])
    return {"items": rows, "counts": await store.count_memories(story_id)}
