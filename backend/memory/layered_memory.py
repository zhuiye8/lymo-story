"""分层记忆编排层（Phase 1 §6.4，补回架构欠债）。

四元组（knowledge_quads）管"事实一致性"，本模块管"角色情感连续性"——
角色记得自己经历过什么、对谁是什么感受，让长篇里人物是活的而非每章重置。

分层（架构 L0-L3）：
  - L0 身份核心：init 时按角色档案种入，emotional_weight=1.0，恒在场（角色是谁）
  - L1 情感关键：逐章抽取，按 emotional_weight 排序（角色经历的要紧事/强情绪）
  这两层是**存储**层（落 memories 表 + ChromaDB 向量）。
  - L2 场景相关：召回模式——按当前场景语境过滤（present chars + query）
  - L3 语义深搜：召回模式——语义相似度检索
  这两层是**检索**模式，作用在 L0/L1 存量上。

双写：SQLite memories 表存元数据（可审计/可重建），ChromaDB 存向量（语义检索）。
embedding 用 ChromaDB 默认 all-MiniLM（本地 CPU，不吃 GPU、不调外部 API，符合约束）。
ChromaDB 调用是同步的 → 用 asyncio.to_thread 包，保持管线 async。
"""
from __future__ import annotations

import asyncio

from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore


class LayeredMemory:
    def __init__(self, store: SQLiteStore, vector: VectorStore):
        self.store = store
        self.vector = vector

    async def remember(
        self, story_id: str, character_id: str, content: str, *,
        chapter: int, emotional_weight: float = 0.5, layer: int = 1,
    ) -> int:
        """记一条记忆：SQLite 元数据 + ChromaDB 向量双写。返回 mem_id。"""
        content = (content or "").strip()
        if not content:
            return 0
        ew = max(0.0, min(1.0, float(emotional_weight)))
        mem_id = await self.store.save_memory(
            story_id, character_id, layer=layer, content=content,
            emotional_weight=ew, source_chapter=chapter,
        )
        vid = f"mem_{mem_id}"
        await asyncio.to_thread(
            self.vector.add_memory, story_id, vid, content,
            {"character_id": character_id, "layer": layer,
             "emotional_weight": ew, "chapter": chapter},
        )
        await self.store.set_memory_vector_id(mem_id, vid)
        return mem_id

    async def remember_batch(self, story_id: str, items: list[dict], *, chapter: int) -> int:
        """批量记忆。每项 {character_id, content, emotional_weight?, layer?}。返回写入数。"""
        n = 0
        for it in items:
            cid = (it.get("character_id") or "").strip()
            content = (it.get("content") or "").strip()
            if not cid or not content:
                continue
            await self.remember(
                story_id, cid, content, chapter=chapter,
                emotional_weight=it.get("emotional_weight", 0.5),
                layer=it.get("layer", 1),
            )
            n += 1
        return n

    async def seed_identity(self, story_id: str, character_id: str, content: str) -> int:
        """种 L0 身份核心记忆（init 用），恒高权重。"""
        return await self.remember(
            story_id, character_id, content, chapter=0,
            emotional_weight=1.0, layer=0,
        )

    async def recall(
        self, story_id: str, character_ids: list[str], query_text: str, *,
        per_char_semantic: int = 3, per_char_key: int = 2,
    ) -> list[dict]:
        """召回在场角色的相关记忆：L3 语义召回（按 query）+ L1 情感关键（按权重）。
        返回去重后的 [{character_id, text, emotional_weight, kind}]。"""
        seen: set[str] = set()
        out: list[dict] = []

        def _add(cid: str, m: dict, kind: str):
            key = (m.get("text") or "").strip()
            if not key or key in seen:
                return
            seen.add(key)
            meta = m.get("metadata", {})
            out.append({
                "character_id": cid,
                "text": key,
                "emotional_weight": meta.get("emotional_weight", m.get("emotional_weight", 0.5)),
                "kind": kind,
            })

        for cid in character_ids:
            if not cid:
                continue
            # L3 语义召回：与当前场景最相关
            if query_text:
                sem = await asyncio.to_thread(
                    self.vector.query_memories, story_id, query_text, cid, None, per_char_semantic,
                )
                for m in sem:
                    _add(cid, m, "semantic")
            # L1 情感关键：恒载该角色最要紧的记忆
            key = await asyncio.to_thread(
                self.vector.query_by_emotional_weight, story_id, cid, per_char_key,
            )
            for m in key:
                _add(cid, m, "key")
        return out

    async def forget_chapters(self, story_id: str, chapter_nums: list[int]) -> int:
        """删这些章产生的记忆向量（章节重写清理用）。

        ⚠️ 只删 ChromaDB 向量；对应 memories 表行由 SQLiteStore.purge_installment_chapters 删。
        必须在删 SQLite 行【之前】调用（要先从 SQLite 取 vector_id）。返回删除向量数。
        """
        if not chapter_nums:
            return 0
        vids = await self.store.get_memory_vector_ids(story_id, chapter_nums)
        if not vids:
            return 0
        return await asyncio.to_thread(self.vector.delete_ids, story_id, vids)
