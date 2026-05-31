import chromadb


def _normalize_meta(metadata: dict) -> dict:
    """Ensure all metadata values are ChromaDB-compatible (str, int, float, bool)."""
    clean = {}
    for k, v in metadata.items():
        if isinstance(v, list):
            clean[k] = ",".join(str(x) for x in v)
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif v is None:
            clean[k] = ""
        else:
            clean[k] = str(v)
    return clean


class VectorStore:
    def __init__(self, chroma_path: str, *, embed_provider: str = "default",
                 embed_model: str = "", ollama_base_url: str = "http://localhost:11434"):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self._embed_fn = self._build_embed_fn(embed_provider, embed_model, ollama_base_url)

    @staticmethod
    def _build_embed_fn(provider: str, model: str, ollama_url: str):
        """选 embedding function。默认 None=chromadb 内置 all-MiniLM（CPU）。
        provider=ollama → Qwen3-Embedding 等本地 GPU 模型（中文 SOTA）。"""
        if provider == "ollama" and model:
            from chromadb.utils import embedding_functions as ef
            return ef.OllamaEmbeddingFunction(url=ollama_url, model_name=model)
        return None

    def get_collection(self, story_id: str) -> chromadb.Collection:
        kwargs: dict = {"name": f"story_{story_id}", "metadata": {"hnsw:space": "cosine"}}
        if self._embed_fn is not None:
            kwargs["embedding_function"] = self._embed_fn
        return self.client.get_or_create_collection(**kwargs)

    def add_memory(
        self,
        story_id: str,
        memory_id: str,
        text: str,
        metadata: dict,
        source_version_id: int | None = None,
    ) -> None:
        clean_meta = _normalize_meta(metadata)
        clean_meta.setdefault("doc_type", "memory")
        clean_meta.setdefault("is_active", True)
        if source_version_id is not None:
            clean_meta["source_version_id"] = int(source_version_id)

        collection = self.get_collection(story_id)
        collection.upsert(
            ids=[memory_id],
            documents=[text],
            metadatas=[clean_meta],
        )

    def add_scene_text(
        self,
        story_id: str,
        chapter_num: int,
        scene_idx: int,
        content: str,
        metadata: dict,
        source_version_id: int | None = None,
    ) -> None:
        """Store a scene's raw text for later semantic retrieval (Phase 4)."""
        clean_meta = _normalize_meta(metadata)
        clean_meta["doc_type"] = "scene_text"
        clean_meta["chapter"] = chapter_num
        clean_meta["scene_idx"] = scene_idx
        clean_meta.setdefault("is_active", True)
        if source_version_id is not None:
            clean_meta["source_version_id"] = int(source_version_id)

        scene_id = f"scene_ch{chapter_num}_s{scene_idx}_v{source_version_id or 0}"
        collection = self.get_collection(story_id)
        collection.upsert(
            ids=[scene_id],
            documents=[content],
            metadatas=[clean_meta],
        )

    def query_memories(
        self,
        story_id: str,
        query_text: str,
        character_id: str | None = None,
        category: str | None = None,
        n_results: int = 5,
        min_emotional_weight: float | None = None,
        only_active: bool = True,
        doc_type: str = "memory",
    ) -> list[dict]:
        collection = self.get_collection(story_id)
        kwargs: dict = {
            "query_texts": [query_text],
            "n_results": n_results,
        }

        where_conditions = [{"doc_type": doc_type}]
        if only_active:
            where_conditions.append({"is_active": True})
        if character_id:
            where_conditions.append({"character_id": character_id})
        if category:
            where_conditions.append({"category": category})
        if min_emotional_weight is not None:
            where_conditions.append({"emotional_weight": {"$gte": min_emotional_weight}})

        if len(where_conditions) == 1:
            kwargs["where"] = where_conditions[0]
        else:
            kwargs["where"] = {"$and": where_conditions}

        try:
            results = collection.query(**kwargs)
        except Exception:
            return []

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "id": results["ids"][0][i],
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return memories

    def query_scene_texts(
        self,
        story_id: str,
        query_text: str,
        n_results: int = 3,
        only_active: bool = True,
    ) -> list[dict]:
        """Query scene-level raw text chunks."""
        return self.query_memories(
            story_id=story_id,
            query_text=query_text,
            n_results=n_results,
            only_active=only_active,
            doc_type="scene_text",
        )

    def query_by_emotional_weight(
        self,
        story_id: str,
        character_id: str,
        top_k: int = 10,
        only_active: bool = True,
    ) -> list[dict]:
        """Get top-K memories ranked by emotional weight for L1 loading."""
        collection = self.get_collection(story_id)
        try:
            where: dict = {"$and": [
                {"character_id": character_id},
                {"doc_type": "memory"},
            ]}
            if only_active:
                where["$and"].append({"is_active": True})
            results = collection.get(
                where=where,
                include=["documents", "metadatas"],
            )
        except Exception:
            return []

        if not results or not results["documents"]:
            return []

        memories = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            memories.append({
                "id": results["ids"][i],
                "text": doc,
                "metadata": meta,
                "emotional_weight": meta.get("emotional_weight", 0.5) if isinstance(meta.get("emotional_weight"), (int, float)) else 0.5,
            })

        memories.sort(key=lambda m: m["emotional_weight"], reverse=True)
        return memories[:top_k]

    def _update_metadata(
        self,
        story_id: str,
        where: dict,
        updates: dict,
    ) -> int:
        """Bulk update metadata fields on matching docs. Returns count updated."""
        collection = self.get_collection(story_id)
        try:
            found = collection.get(where=where, include=["metadatas", "documents"])
        except Exception:
            return 0
        if not found or not found.get("ids"):
            return 0

        ids = found["ids"]
        docs = found.get("documents") or [None] * len(ids)
        metas = found.get("metadatas") or [{} for _ in ids]
        new_metas = []
        for m in metas:
            merged = dict(m or {})
            merged.update(updates)
            new_metas.append(_normalize_meta(merged))
        try:
            collection.update(ids=ids, documents=docs, metadatas=new_metas)
        except Exception:
            # Some chroma versions reject documents=None; retry without
            collection.update(ids=ids, metadatas=new_metas)
        return len(ids)

    def mark_memories_active(
        self,
        story_id: str,
        chapter_num: int,
        version_id: int,
        active: bool,
    ) -> int:
        """Mark all memories tied to (chapter_num, version_id) as active or inactive."""
        where = {"$and": [
            {"chapter": chapter_num},
            {"source_version_id": int(version_id)},
        ]}
        return self._update_metadata(story_id, where, {"is_active": active})

    def mark_memories_by_version(
        self,
        story_id: str,
        version_id: int,
        active: bool,
    ) -> int:
        """Mark all memories from a specific version regardless of chapter."""
        where = {"source_version_id": int(version_id)}
        return self._update_metadata(story_id, where, {"is_active": active})

    def delete_by_version(
        self,
        story_id: str,
        version_id: int,
    ) -> int:
        """Hard delete all docs (memories + scenes) from a version."""
        collection = self.get_collection(story_id)
        try:
            found = collection.get(where={"source_version_id": int(version_id)})
            ids = found.get("ids") or []
            if ids:
                collection.delete(ids=ids)
            return len(ids)
        except Exception:
            return 0

    def delete_ids(self, story_id: str, ids: list[str]) -> int:
        """按 vector_id 列表硬删（章节重写清理用）。返回尝试删除数。"""
        if not ids:
            return 0
        collection = self.get_collection(story_id)
        try:
            collection.delete(ids=ids)
            return len(ids)
        except Exception:
            return 0
