"""In-memory progress tracker for the init / chapter generation pipelines."""

import time
from dataclasses import dataclass, field


@dataclass
class StageInfo:
    name: str
    label: str
    started_at: float = 0.0
    finished_at: float = 0.0
    status: str = "pending"  # pending / running / done / error
    detail: str = ""


@dataclass
class GenerationProgress:
    story_id: str
    chapter_num: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0  # 0 = 进行中；非 0 = 已结束（冻结计时）
    stages: list[StageInfo] = field(default_factory=list)
    current_stage_index: int = -1
    error: str | None = None

    def to_dict(self) -> dict:
        # 完成/出错后用 finished_at 冻结 elapsed，不再实时增长
        end = self.finished_at or time.time()
        return {
            "story_id": self.story_id,
            "chapter_num": self.chapter_num,
            "elapsed_seconds": round(end - self.started_at, 1),
            "finished": bool(self.finished_at),
            "current_stage": self.stages[self.current_stage_index].name if 0 <= self.current_stage_index < len(self.stages) else None,
            "current_stage_label": self.stages[self.current_stage_index].label if 0 <= self.current_stage_index < len(self.stages) else None,
            "error": self.error,
            "stages": [
                {
                    "name": s.name,
                    "label": s.label,
                    "status": s.status,
                    "detail": s.detail,
                    "duration_ms": int((s.finished_at - s.started_at) * 1000) if s.finished_at and s.started_at else 0,
                }
                for s in self.stages
            ],
        }


# Phase 1 章节管线阶段（名称与 backend/graph/phase1_chapter.py 的图节点一致）
CHAPTER_STAGES = [
    ("load_context", "载入上下文"),
    ("outline_advance", "推进细纲"),
    ("scene_plan", "分镜规划"),
    ("retrieve_memory", "召回记忆"),
    ("write_chapter", "撰写正文"),
    ("paginate", "切分分章"),
    ("finalize", "抽取落库"),
]

# Phase 1 初始化管线阶段（名称与 backend/graph/phase1_init.py 的图节点一致）
INIT_STAGES = [
    ("concept", "立意"),
    ("world_build", "世界观"),
    ("character_design", "角色设计"),
    ("outline_plan", "大纲规划"),
    ("assemble", "组装落库"),
]


class ProgressStore:
    """In-memory store for generation progress (one active run per story)."""

    def __init__(self):
        self._progress: dict[str, GenerationProgress] = {}

    def start(self, story_id: str, chapter_num: int, stages: list[tuple[str, str]] | None = None) -> GenerationProgress:
        stages = stages or CHAPTER_STAGES
        progress = GenerationProgress(
            story_id=story_id,
            chapter_num=chapter_num,
            stages=[StageInfo(name=name, label=label) for name, label in stages],
        )
        self._progress[story_id] = progress
        return progress

    def enter_stage(self, story_id: str, stage_name: str, detail: str = "") -> None:
        """进入某阶段：把它之前的阶段全标 done，该阶段标 running。
        节点只需在开头调一次 enter_stage(自己的名字)，前序自动收尾。"""
        progress = self._progress.get(story_id)
        if not progress:
            return
        now = time.time()
        for i, stage in enumerate(progress.stages):
            if stage.name == stage_name:
                for j in range(i):
                    if progress.stages[j].status != "done":
                        progress.stages[j].status = "done"
                        if not progress.stages[j].finished_at:
                            progress.stages[j].finished_at = now
                stage.status = "running"
                stage.started_at = now
                stage.detail = detail
                progress.current_stage_index = i
                return

    def finish(self, story_id: str) -> None:
        """整个管线完成：剩余阶段全收尾为 done，冻结计时。"""
        progress = self._progress.get(story_id)
        if not progress:
            return
        now = time.time()
        for stage in progress.stages:
            if stage.status in ("running", "pending"):
                stage.status = "done"
                if not stage.finished_at:
                    stage.finished_at = now
        progress.finished_at = now

    def set_error(self, story_id: str, error: str) -> None:
        progress = self._progress.get(story_id)
        if not progress:
            return
        progress.error = error
        progress.finished_at = time.time()  # 出错也冻结计时
        if 0 <= progress.current_stage_index < len(progress.stages):
            progress.stages[progress.current_stage_index].status = "error"

    def get(self, story_id: str) -> dict | None:
        progress = self._progress.get(story_id)
        return progress.to_dict() if progress else None

    def clear(self, story_id: str) -> None:
        self._progress.pop(story_id, None)
