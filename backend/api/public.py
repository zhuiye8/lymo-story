"""Reader 端只读 API（Phase 1）。

读新 schema：已发布故事 = status 含 published 标记；章节 chapters.is_published=1。
bible 从 stories.bible_json。
"""
from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_sqlite
from backend.storage.sqlite_store import SQLiteStore

router = APIRouter()


async def _published_chapters(db_path: str, story_id: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chapter_num, title, pov, word_count, content FROM chapters "
            "WHERE story_id = ? AND is_published = 1 ORDER BY chapter_num",
            (story_id,))
        return [dict(r) for r in await cur.fetchall()]


@router.get("/books")
async def list_books(store: SQLiteStore = Depends(get_sqlite)):
    stories = await store.list_stories()
    out = []
    for s in stories:
        if s.get("status") == "published":
            chs = await _published_chapters(store.db_path, s["id"])
            out.append({
                "id": s["id"], "title": s.get("title", ""), "genre": s.get("genre", ""),
                "chapter_count": len(chs), "updated_at": s.get("updated_at", ""),
            })
    return out


@router.get("/books/{book_id}")
async def get_book(book_id: str, store: SQLiteStore = Depends(get_sqlite)):
    story = await store.get_story(book_id)
    if not story or story.get("status") != "published":
        raise HTTPException(404, "Book not found")
    bible = story.get("bible", {})
    concept = bible.get("concept", {})
    chars = bible.get("characters", {})
    char_list = []
    if chars:
        for cd in [chars.get("protagonist"), chars.get("antagonist"), *(chars.get("supporting") or [])]:
            if cd:
                char_list.append({"name": cd.get("name", ""), "role": cd.get("role", "")})
    chapters = await _published_chapters(store.db_path, book_id)
    return {
        "id": story["id"], "title": story.get("title", ""),
        "genre": story.get("genre", ""),
        "synopsis": concept.get("synopsis", ""),
        "characters": char_list,
        "chapters": [
            {"chapter_num": c["chapter_num"], "title": c["title"], "pov": c["pov"], "word_count": c["word_count"]}
            for c in chapters
        ],
    }


@router.get("/books/{book_id}/chapters/{chapter_num}")
async def read_chapter(book_id: str, chapter_num: int, store: SQLiteStore = Depends(get_sqlite)):
    story = await store.get_story(book_id)
    if not story or story.get("status") != "published":
        raise HTTPException(404, "Book not found")
    chapters = await _published_chapters(store.db_path, book_id)
    nums = [c["chapter_num"] for c in chapters]
    if chapter_num not in nums:
        raise HTTPException(404, "Chapter not found or not published")
    ch = next(c for c in chapters if c["chapter_num"] == chapter_num)
    idx = nums.index(chapter_num)
    return {
        "story_id": book_id, "story_title": story.get("title", ""),
        "chapter_num": ch["chapter_num"], "title": ch["title"], "pov": ch["pov"],
        "content": ch["content"], "word_count": ch["word_count"],
        "prev_chapter": nums[idx - 1] if idx > 0 else None,
        "next_chapter": nums[idx + 1] if idx < len(nums) - 1 else None,
    }
