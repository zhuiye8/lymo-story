"""#2 一致性闭环根因修复回归测试。

核心：find_conflicts 只该把'单值谓语 + 未声明失效'的同时多值判为真冲突，
不能再把事件四元组累积、多值谓语累积、合法状态转移误判成冲突
（10 章压测里这些误报让冲突数虚高到 51）。
"""
import os
import sys
import tempfile

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.memory.predicates import (
    normalize_predicate, is_single_valued, objects_compatible,
    SINGLE_VALUED, MULTI_VALUED,
)
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.storage.sqlite_store import SQLiteStore


# ---------------- predicates 归一 ----------------

def test_canonical_passthrough():
    assert normalize_predicate("境界") == "境界"
    assert normalize_predicate("存活状态") == "存活状态"

def test_alias_maps_to_canonical():
    assert normalize_predicate("修为") == "境界"
    assert normalize_predicate("生死") == "存活状态"
    assert normalize_predicate("势力") == "阵营"
    assert normalize_predicate("功法") == "能力"
    assert normalize_predicate("法宝") == "持有"

def test_fuzzy_substring():
    assert normalize_predicate("当前境界") == "境界"
    assert normalize_predicate("持有的法宝") == "持有"

def test_event_predicates_dropped():
    # 这些动作/事件谓语必须返回 None（不进四元组）
    for verb in ("修改", "执行", "确认", "行动", "发现", "攻击", "前往", "对话", "得知"):
        assert normalize_predicate(verb) is None, f"{verb} 应被判为事件谓语"

def test_empty_dropped():
    assert normalize_predicate("") is None
    assert normalize_predicate("   ") is None

def test_single_vs_multi():
    assert is_single_valued("境界")
    assert is_single_valued("存活状态")
    assert not is_single_valued("能力")
    assert not is_single_valued("持有")
    # 身份/阵营 是多面自由文本，已移出单值（不再字符串错判矛盾）
    assert not is_single_valued("身份")
    assert not is_single_valued("阵营")
    assert "身份" in MULTI_VALUED and "阵营" in MULTI_VALUED
    assert SINGLE_VALUED.isdisjoint(MULTI_VALUED)


# ---------------- objects_compatible ----------------

def test_compatible_identical_and_containment():
    assert objects_compatible("金丹期", "金丹期")
    assert objects_compatible("Lv2权限持有者", "Lv2权限持有者（含职务）")  # 细化
    assert objects_compatible("金丹", "金丹期")  # 包含

def test_compatible_rephrase_high_overlap():
    assert objects_compatible("系统管理员Lv2权限", "Lv2权限系统管理员")  # 语序变化

def test_incompatible_opposites():
    assert not objects_compatible("存活", "死亡")
    assert not objects_compatible("金丹期", "练气期")
    assert not objects_compatible("正派", "魔教")


# ---------------- find_conflicts 精确性 ----------------

@pytest_asyncio.fixture
async def quads():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = SQLiteStore(path)
    await store.initialize()
    await store.create_story("t", "测试")
    yield KnowledgeQuads(path)
    os.unlink(path)


@pytest.mark.asyncio
async def test_real_conflict_dead_man_walking(quads):
    # 既有：林某 存活状态 死亡（仍有效）
    await quads.add_quads_batch("t", [
        {"subject": "林某", "predicate": "存活状态", "object": "死亡"}
    ], source_chapter=3)
    # 新：林某 存活状态 存活，且未声明失效 → 真冲突（死人复活）
    new = [{"subject": "林某", "predicate": "存活状态", "object": "存活", "invalidates_prior": False}]
    conflicts = await quads.find_conflicts("t", new, 5)
    assert len(conflicts) == 1
    assert conflicts[0]["kind"] == "object_mismatch"


@pytest.mark.asyncio
async def test_legit_transition_not_conflict(quads):
    # 既有：张三 境界 筑基期
    await quads.add_quads_batch("t", [
        {"subject": "张三", "predicate": "境界", "object": "筑基期"}
    ], source_chapter=2)
    # 新：张三 境界 金丹期，声明使旧值失效 → 合法突破，不是冲突
    new = [{"subject": "张三", "predicate": "境界", "object": "金丹期", "invalidates_prior": True}]
    conflicts = await quads.find_conflicts("t", new, 6)
    assert conflicts == []


@pytest.mark.asyncio
async def test_multivalued_accumulation_not_conflict(quads):
    # 多值谓语：掌握多种能力合法，不该判冲突
    await quads.add_quads_batch("t", [
        {"subject": "墨默", "predicate": "能力", "object": "代码编辑器系统"}
    ], source_chapter=1)
    new = [{"subject": "墨默", "predicate": "能力", "object": "现实改写", "invalidates_prior": False}]
    conflicts = await quads.find_conflicts("t", new, 4)
    assert conflicts == []


@pytest.mark.asyncio
async def test_event_quads_never_conflict(quads):
    # 事件谓语累积（这正是 10 章压测 51 误报的来源）→ 0 冲突
    await quads.add_quads_batch("t", [
        {"subject": "墨默", "predicate": "修改", "object": "余额为100万"}
    ], source_chapter=1)
    new = [
        {"subject": "墨默", "predicate": "修改", "object": "pricing_engine参数", "invalidates_prior": False},
        {"subject": "墨默", "predicate": "执行", "object": "某操作", "invalidates_prior": False},
    ]
    conflicts = await quads.find_conflicts("t", new, 3)
    assert conflicts == []


@pytest.mark.asyncio
async def test_alias_normalized_conflict_detected(quads):
    # 谓语同义但写法不同（修为 vs 境界）也要能检出冲突
    await quads.add_quads_batch("t", [
        {"subject": "李四", "predicate": "境界", "object": "金丹期"}
    ], source_chapter=2)
    # 新用别名"修为"，object 矛盾且未声明失效 → 应归一后检出
    new = [{"subject": "李四", "predicate": "修为", "object": "练气期", "invalidates_prior": False}]
    conflicts = await quads.find_conflicts("t", new, 5)
    assert len(conflicts) == 1


@pytest.mark.asyncio
async def test_identity_rephrase_not_conflict(quads):
    # 身份现在是多值/描述性：同角色不同措辞的身份不该算冲突（这正是 v2 压测 44 误报的主因）
    await quads.add_quads_batch("t", [
        {"subject": "墨默", "predicate": "身份", "object": "系统管理员"}
    ], source_chapter=1)
    new = [
        {"subject": "墨默", "predicate": "身份", "object": "Lv2权限持有者", "invalidates_prior": False},
        {"subject": "墨默", "predicate": "身份", "object": "protagonist", "invalidates_prior": False},
    ]
    conflicts = await quads.find_conflicts("t", new, 5)
    assert conflicts == []


@pytest.mark.asyncio
async def test_dedup_skips_compatible(quads):
    # 写入去重：同义改写不重复入库
    await quads.add_quads_batch("t", [
        {"subject": "墨默", "predicate": "境界", "object": "Lv2"}
    ], source_chapter=1)
    inserted, skipped = await quads.add_quads_deduped("t", [
        {"subject": "墨默", "predicate": "境界", "object": "Lv2"},            # 完全重复
        {"subject": "墨默", "predicate": "境界", "object": "Lv2（系统等级）"},  # 细化
        {"subject": "墨默", "predicate": "境界", "object": "Lv3"},            # 真新值
    ], source_chapter=2)
    assert inserted == 1 and skipped == 2
    valid = await quads.query_valid_at("t", 3)
    objs = sorted(q["object"] for q in valid if q["predicate"] == "境界")
    assert objs == ["Lv2", "Lv3"]


@pytest.mark.asyncio
async def test_dedup_within_batch(quads):
    # 同一批次里的两个同义事实也只入一个
    inserted, skipped = await quads.add_quads_deduped("t", [
        {"subject": "墨默", "predicate": "能力", "object": "代码编辑器"},
        {"subject": "墨默", "predicate": "能力", "object": "代码编辑器系统"},  # 同批次细化
    ], source_chapter=1)
    assert inserted == 1 and skipped == 1
