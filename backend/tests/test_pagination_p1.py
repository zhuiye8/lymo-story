"""分页切分 + 推进单元解耦回归测试（阶段 B）。"""
import os
import tempfile

import pytest
import pytest_asyncio

from backend.graph.phase1_chapter import _split_even, _title_parts
from backend.storage.sqlite_store import SQLiteStore


def _doc(n_paras: int, para_len: int = 700) -> str:
    return "\n\n".join("字" * para_len for _ in range(n_paras))


def test_split_even_balances():
    doc = _doc(10, 700)  # ~7000 字
    parts = _split_even(doc, 2)
    assert len(parts) == 2
    a, b = len(parts[0]), len(parts[1])
    assert abs(a - b) < 1500  # 大致均分，无 runt

def test_split_even_three():
    parts = _split_even(_doc(12, 600), 3)
    assert len(parts) == 3
    assert all(len(p) > 1500 for p in parts)

def test_split_even_single_paragraph_uncuttable():
    # 单大段没有段落边界 → 不切（返回整段）
    assert _split_even("字" * 8000, 2) == ["字" * 8000]

def test_split_even_n1_is_whole():
    doc = _doc(5)
    assert _split_even(doc, 1) == [doc]

def test_title_parts():
    assert _title_parts(1, "曙光基地") == ["曙光基地"]
    assert _title_parts(2, "曙光基地") == ["曙光基地（上）", "曙光基地（下）"]
    assert _title_parts(3, "曙光基地") == ["曙光基地（一）", "曙光基地（二）", "曙光基地（三）"]


@pytest_asyncio.fixture
async def store(tmp_path):
    s = SQLiteStore(str(tmp_path / "t.db"))
    await s.initialize()
    await s.create_story("s1", "书")
    return s

@pytest.mark.asyncio
async def test_installments_counter(store):
    assert await store.get_installments_done("s1") == 0
    await store.bump_installments_done("s1")
    await store.bump_installments_done("s1")
    assert await store.get_installments_done("s1") == 2

@pytest.mark.asyncio
async def test_save_chapter_installment_num(store):
    await store.save_chapter("s1", 5, title="标题", content="正文内容", installment_num=3)
    ch = await store.get_chapter("s1", 5)
    assert ch["installment_num"] == 3
    assert ch["word_count"] == len("正文内容")
