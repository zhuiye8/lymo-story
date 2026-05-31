"""进度跟踪回归测试（修复：计时不冻结 / 阶段卡 pending / Phase-0 残留阶段名）。"""
import time

from backend.progress import ProgressStore, CHAPTER_STAGES, INIT_STAGES


def test_stage_lists_are_phase1():
    names = {n for n, _ in CHAPTER_STAGES}
    assert "write_chapter" in names and "outline_advance" in names
    # Phase-0 残留名不应再出现
    assert not ({"world_advance", "camera_decide", "scene_split"} & names)
    assert [n for n, _ in INIT_STAGES] == ["concept", "world_build", "character_design", "outline_plan", "assemble"]


def test_enter_stage_cascades_prior_to_done():
    ps = ProgressStore()
    ps.start("s", 1)
    ps.enter_stage("s", "scene_plan")  # 第 3 个阶段
    d = ps.get("s")
    by = {st["name"]: st["status"] for st in d["stages"]}
    assert by["load_context"] == "done" and by["outline_advance"] == "done"
    assert by["scene_plan"] == "running"
    assert by["finalize"] == "pending"
    assert d["finished"] is False


def test_finish_freezes_and_marks_all_done():
    ps = ProgressStore()
    ps.start("s", 1)
    ps.enter_stage("s", "write_chapter")
    ps.finish("s")
    d1 = ps.get("s")
    assert d1["finished"] is True
    assert all(st["status"] == "done" for st in d1["stages"])
    e1 = d1["elapsed_seconds"]
    time.sleep(0.05)
    d2 = ps.get("s")
    assert d2["elapsed_seconds"] == e1  # 已冻结，不再增长


def test_set_error_freezes_too():
    ps = ProgressStore()
    ps.start("s", 1)
    ps.enter_stage("s", "write_chapter")
    ps.set_error("s", "boom")
    d = ps.get("s")
    assert d["finished"] is True and d["error"] == "boom"
    assert any(st["status"] == "error" for st in d["stages"])


def test_init_stages_used():
    ps = ProgressStore()
    ps.start("s", 0, stages=INIT_STAGES)
    d = ps.get("s")
    assert [st["name"] for st in d["stages"]] == ["concept", "world_build", "character_design", "outline_plan", "assemble"]
