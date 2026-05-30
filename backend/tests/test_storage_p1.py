"""S2 验收：Phase 1 DB schema + DOME 四元组。

phase1/01-implementation-plan.md 验收点 S2：
  建表无错；四元组能写入、按章号查有效集、检测出"死人复活"式冲突。
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.storage.sqlite_store import SQLiteStore
from backend.memory.knowledge_quads import KnowledgeQuads


@pytest_asyncio.fixture
async def store(tmp_path):
    s = SQLiteStore(str(tmp_path / "t.db"))
    await s.initialize()
    return s


@pytest_asyncio.fixture
async def kq(tmp_path):
    s = SQLiteStore(str(tmp_path / "t.db"))
    await s.initialize()
    return KnowledgeQuads(str(tmp_path / "t.db"))


class TestSchema:
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, tmp_path):
        s = SQLiteStore(str(tmp_path / "t.db"))
        await s.initialize()
        await s.initialize()  # 再跑一次不报错
        story = await s.get_story("nope")
        assert story is None


class TestStoryAndChapter:
    @pytest.mark.asyncio
    async def test_create_story_save_bible(self, store):
        await store.create_story("s1", "测试书", genre="系统流", theme="逆袭")
        await store.save_bible("s1", {"title": "测试书", "world": "玄幻"})
        s = await store.get_story("s1")
        assert s["title"] == "测试书"
        assert s["genre"] == "系统流"
        assert s["bible"]["world"] == "玄幻"

    @pytest.mark.asyncio
    async def test_chapter_roundtrip_and_summaries(self, store):
        await store.create_story("s1", "书")
        for i in range(1, 5):
            await store.save_chapter("s1", i, title=f"第{i}章", content="正文" * 100, summary=f"摘要{i}")
        assert await store.get_chapter_count("s1") == 4
        ch2 = await store.get_chapter("s1", 2)
        assert ch2["word_count"] == 200
        # 第 4 章生成时取最近 3 章摘要
        recent = await store.get_recent_summaries("s1", before_chapter=4, limit=3)
        assert [r["chapter_num"] for r in recent] == [1, 2, 3]


class TestCharacters:
    @pytest.mark.asyncio
    async def test_voice_profile_roundtrip(self, store):
        await store.create_story("s1", "书")
        await store.save_character(
            "s1", "lin", name="林凡", role="protagonist",
            profile={"age": 18},
            voice_profile={"口头禅": ["不过如此"], "句式": "短促", "禁用词": ["仿佛"]},
        )
        chars = await store.list_characters("s1")
        assert len(chars) == 1
        assert chars[0]["voice_profile"]["口头禅"] == ["不过如此"]

    @pytest.mark.asyncio
    async def test_latest_character_state(self, store):
        await store.create_story("s1", "书")
        await store.save_character_state("s1", "lin", 1, location="新手村", status="活跃")
        await store.save_character_state("s1", "lin", 3, location="主城", status="活跃")
        await store.save_character_state("s1", "wang", 2, location="王府", status="活跃")
        states = await store.get_latest_character_states("s1", up_to_chapter=5)
        by_id = {s["character_id"]: s for s in states}
        assert by_id["lin"]["chapter_num"] == 3       # 取最新
        assert by_id["lin"]["location"] == "主城"
        assert by_id["wang"]["chapter_num"] == 2


class TestOutline:
    @pytest.mark.asyncio
    async def test_rough_and_detailed(self, store):
        await store.create_story("s1", "书")
        await store.save_rough_outline("s1", [
            {"stage_num": 1, "stage_name": "起", "summary": "开局", "chapter_start": 1, "chapter_end": 10},
            {"stage_num": 2, "stage_name": "承", "summary": "发展", "chapter_start": 11, "chapter_end": 30},
        ])
        rough = await store.get_rough_outline("s1")
        assert len(rough) == 2
        assert rough[0]["stage_name"] == "起"
        await store.save_detailed_outline("s1", 1, beats=[{"beat": "觉醒系统"}], word_budget=3500)
        d = await store.get_detailed_outline("s1", 1)
        assert d["beats"][0]["beat"] == "觉醒系统"
        assert d["word_budget"] == 3500


class TestDomeQuads:
    @pytest.mark.asyncio
    async def test_add_and_query_valid_at(self, kq):
        await kq.add_quad("s1", "林凡", "拥有", "签到系统", valid_from=1, source_chapter=1)
        await kq.add_quad("s1", "林凡", "位于", "新手村", valid_from=1, valid_to=5, source_chapter=1)
        # 第 3 章：两条都有效
        v3 = await kq.query_valid_at("s1", 3)
        assert len(v3) == 2
        # 第 6 章：位于新手村已失效（valid_to=5）
        v6 = await kq.query_valid_at("s1", 6)
        objs = {q["object"] for q in v6}
        assert "签到系统" in objs
        assert "新手村" not in objs

    @pytest.mark.asyncio
    async def test_invalidate(self, kq):
        qid = await kq.add_quad("s1", "王某", "状态", "活着", valid_from=1, source_chapter=1)
        await kq.invalidate(qid, at_chapter=10)  # 第 10 章死了
        assert len(await kq.query_valid_at("s1", 9)) == 1
        assert len(await kq.query_valid_at("s1", 10)) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_dead_man_walking(self, kq):
        # 既有事实：王某 状态 死亡（第 10 章起有效）
        await kq.add_quad("s1", "王某", "状态", "死亡", valid_from=10, source_chapter=10)
        # 第 15 章新抽出："王某 状态 活跃" → 应检测为冲突
        new_quads = [{"subject": "王某", "predicate": "状态", "object": "活跃"}]
        conflicts = await kq.find_conflicts("s1", new_quads, chapter=15)
        assert len(conflicts) == 1
        assert conflicts[0]["kind"] == "object_mismatch"
        assert conflicts[0]["existing"]["object"] == "死亡"

    @pytest.mark.asyncio
    async def test_batch_and_subject_query(self, kq):
        await kq.add_quads_batch("s1", [
            {"subject": "林凡", "predicate": "境界", "object": "练气一层"},
            {"subject": "林凡", "predicate": "持有", "object": "破剑"},
        ], source_chapter=2)
        subj = await kq.query_subject("s1", "林凡", chapter=2)
        assert len(subj) == 2


class TestQualitySave:
    @pytest.mark.asyncio
    async def test_save_quality_feeds_charts(self, store):
        from backend.quality import DIMENSIONS
        await store.create_story("s1", "书")
        await store.save_chapter("s1", 1, content="x" * 3000)
        await store.save_quality(
            "s1", 1,
            dim_scores={d: 7.0 for d in DIMENSIONS},
            mean_quality=7.0, slop_penalty=1.0, composite_score=6.0, word_count=3000,
            judge_model="deepseek-v4-flash",
            slop_findings=[{"category": "always_banned", "hits": ["在心底深处"], "weighted_penalty": 1.0}],
        )
        # 验证三张表都写入了（quality_admin 4 图表依赖）
        import aiosqlite
        async with aiosqlite.connect(store.db_path) as db:
            db.row_factory = aiosqlite.Row
            n_scores = (await (await db.execute("SELECT COUNT(*) AS n FROM chapter_quality_scores WHERE story_id='s1'")).fetchone())["n"]
            n_eval = (await (await db.execute("SELECT COUNT(*) AS n FROM chapter_quality_evaluations WHERE story_id='s1'")).fetchone())["n"]
            n_slop = (await (await db.execute("SELECT COUNT(*) AS n FROM slop_findings WHERE story_id='s1'")).fetchone())["n"]
        assert n_scores == 8   # 8 维
        assert n_eval == 1
        assert n_slop == 1
