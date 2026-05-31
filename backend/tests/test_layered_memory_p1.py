"""分层记忆 LayeredMemory 回归测试（Phase 1 §6.4）。

验证：L0 身份种子 / L1 情感记忆双写（SQLite + ChromaDB）、按角色召回、
情感权重排序、去重。embedding 用 ChromaDB 默认（本地 CPU）。
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore
from backend.memory.layered_memory import LayeredMemory


@pytest_asyncio.fixture
async def mem(tmp_path):
    store = SQLiteStore(str(tmp_path / "t.db"))
    await store.initialize()
    await store.create_story("s1", "书")
    vector = VectorStore(str(tmp_path / "chroma"))
    return LayeredMemory(store, vector), store


@pytest.mark.asyncio
async def test_seed_identity_is_l0(mem):
    lm, store = mem
    mid = await lm.seed_identity("s1", "chenmo", "我是陈默，落魄程序员，想逆袭")
    assert mid > 0
    counts = await store.count_memories("s1")
    assert counts.get("L0") == 1

@pytest.mark.asyncio
async def test_remember_l1_and_vector_id(mem):
    lm, store = mem
    mid = await lm.remember("s1", "chenmo", "被房东当众催租，记恨在心",
                            chapter=1, emotional_weight=0.8)
    assert mid > 0
    # vector_id 应被回填
    import aiosqlite
    async with aiosqlite.connect(store.db_path) as db:
        db.row_factory = aiosqlite.Row
        r = await (await db.execute("SELECT layer, vector_id FROM memories WHERE id=?", (mid,))).fetchone()
    assert r["layer"] == 1 and r["vector_id"] == f"mem_{mid}"

@pytest.mark.asyncio
async def test_remember_batch_skips_empty(mem):
    lm, store = mem
    n = await lm.remember_batch("s1", [
        {"character_id": "chenmo", "content": "尝到系统甜头", "emotional_weight": 0.6},
        {"character_id": "", "content": "无主体应跳过"},
        {"character_id": "zhaoxue", "content": "  "},  # 空内容跳过
    ], chapter=2)
    assert n == 1
    assert (await store.count_memories("s1")).get("L1") == 1

@pytest.mark.asyncio
async def test_recall_returns_character_memories(mem):
    lm, _ = mem
    await lm.seed_identity("s1", "chenmo", "我是陈默，程序员")
    await lm.remember("s1", "chenmo", "被房东赵德柱当众催租，记恨在心", chapter=1, emotional_weight=0.9)
    await lm.remember("s1", "chenmo", "用现实编辑器改了早餐摊余额", chapter=1, emotional_weight=0.5)
    await lm.remember("s1", "zhaoxue", "在安全局发现异常写入", chapter=2, emotional_weight=0.7)
    recalled = await lm.recall("s1", ["chenmo"], "房租 房东 催债")
    texts = " ".join(m["text"] for m in recalled)
    assert recalled  # 有召回
    assert all(m["character_id"] == "chenmo" for m in recalled)  # 只召回该角色
    assert "催租" in texts  # 高情感关键记忆必在（L1 路不依赖 embedding 质量）

@pytest.mark.asyncio
async def test_recall_dedup(mem):
    lm, _ = mem
    # 高权重记忆会同时被语义路和情感路命中，须去重
    await lm.remember("s1", "chenmo", "被背叛，刻骨铭心", chapter=1, emotional_weight=0.95)
    recalled = await lm.recall("s1", ["chenmo"], "背叛")
    texts = [m["text"] for m in recalled]
    assert len(texts) == len(set(texts))  # 无重复
