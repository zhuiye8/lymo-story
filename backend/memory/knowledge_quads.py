"""DOME 四元组读写层（Phase 1，重写 knowledge_graph.py）。

设计依据 phase1/00-architecture.md §6.1 + 01-implementation-plan.md Step 2.2。

DOME 四元组 <subject, predicate, object, [valid_from, valid_to)>：
  - 长程一致性地基（消融证据：去掉它冲突率 0.56%→4.52%）
  - invalidate-not-delete：事实失效用 valid_to 标记，不物理删除
  - 按章号查"某章时点有效的事实集"，喂生成上下文 + 检测冲突

接口：
  add_quad / add_quads_batch       写入新事实
  query_valid_at(chapter)          某章时点仍有效的所有四元组
  query_subject(subj, chapter)     某主体在某章的有效事实
  invalidate(quad_id, at)          标记失效
  find_conflicts(new_quads, chap)  检测"死人复活"式矛盾
"""
from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeQuads:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def add_quad(
        self, story_id: str, subject: str, predicate: str, object_: str,
        *, valid_from: int, source_chapter: int, valid_to: int | None = None,
        confidence: float = 1.0,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                """INSERT INTO knowledge_quads
                   (story_id, subject, predicate, object, valid_from, valid_to, source_chapter, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (story_id, subject, predicate, object_, valid_from, valid_to, source_chapter, confidence, _now()),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def add_quads_batch(self, story_id: str, quads: list[dict], *, source_chapter: int) -> int:
        """批量写入（extract_memory 节点用）。每个 quad: {subject, predicate, object, valid_from?}。"""
        n = 0
        async with aiosqlite.connect(self.db_path) as db:
            for q in quads:
                await db.execute(
                    """INSERT INTO knowledge_quads
                       (story_id, subject, predicate, object, valid_from, valid_to, source_chapter, confidence, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (story_id, q["subject"], q["predicate"], q["object"],
                     q.get("valid_from", source_chapter), q.get("valid_to"),
                     source_chapter, q.get("confidence", 1.0), _now()),
                )
                n += 1
            await db.commit()
        return n

    async def query_valid_at(self, story_id: str, chapter: int) -> list[dict]:
        """返回在第 chapter 章时点仍有效的所有四元组（valid_from ≤ chapter < valid_to|∞）。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT * FROM knowledge_quads
                   WHERE story_id = ? AND valid_from <= ?
                     AND (valid_to IS NULL OR valid_to > ?)
                   ORDER BY subject, valid_from""",
                (story_id, chapter, chapter),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def query_subject(self, story_id: str, subject: str, chapter: int) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT * FROM knowledge_quads
                   WHERE story_id = ? AND subject = ? AND valid_from <= ?
                     AND (valid_to IS NULL OR valid_to > ?)
                   ORDER BY valid_from""",
                (story_id, subject, chapter, chapter),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def invalidate(self, quad_id: int, *, at_chapter: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE knowledge_quads SET valid_to = ? WHERE id = ?",
                (at_chapter, quad_id),
            )
            await db.commit()

    async def find_conflicts(self, story_id: str, new_quads: list[dict], chapter: int) -> list[dict]:
        """检测新四元组与既有有效事实的**真**矛盾（死人复活式硬伤）。

        真冲突需同时满足（避免把合法演变/累积误判成冲突）：
          1. 谓语是**单值**状态谓语（存活/境界/身份/阵营）—— 多值谓语（能力/持有/
             关系）可累积，多 object 合法，不算冲突；
          2. 同 subject + 同 canonical 谓语，但 object 不同；
          3. 既有事实在本章仍有效；
          4. 新事实**没声明使旧值失效**（invalidates_prior=False）—— 声明失效的是
             合法状态转移（境界突破 筑基→金丹），不是矛盾。
        返回冲突列表：[{new, existing, kind}]，供 quality_gate 一致性检测用。
        """
        from backend.memory.predicates import is_single_valued, normalize_predicate

        conflicts: list[dict] = []
        existing = await self.query_valid_at(story_id, chapter)
        idx: dict[tuple[str, str], list[dict]] = {}
        for e in existing:
            canon = normalize_predicate(e["predicate"])
            if canon and is_single_valued(canon):
                idx.setdefault((e["subject"], canon), []).append(e)
        for nq in new_quads:
            # 声明失效旧值 = 合法转移，不是矛盾
            if nq.get("invalidates_prior"):
                continue
            canon = normalize_predicate(nq["predicate"])
            if not canon or not is_single_valued(canon):
                continue  # 多值/事件谓语不判冲突
            for e in idx.get((nq["subject"], canon), []):
                if e["object"] != nq["object"]:
                    conflicts.append({"new": nq, "existing": e, "kind": "object_mismatch"})
        return conflicts
