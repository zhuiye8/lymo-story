"""阶段 B 活测：用低切分阈值强制一个推进单元切成多个物理章，验证 paginate→finalize 全链路。

复用已 init 的 stress01（有 bible）。设小目标 + 低阈值，让正常输出就触发切分。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("STORY_LITELLM_MODEL", "deepseek/deepseek-chat")
# 强制切分：目标 1500、阈值 2500 → 自然输出（~3000+）会切成 2 章
os.environ["STORY_CHAPTER_TARGET_WORDS"] = "1500"
os.environ["STORY_CHAPTER_FLOOR"] = "1000"
os.environ["STORY_CHAPTER_CEILING"] = "2000"
os.environ["STORY_CHAPTER_SPLIT_THRESHOLD"] = "2500"

from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.model_registry import ModelRegistry
from backend.llm.logger import LLMLogger
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.memory.layered_memory import LayeredMemory
from backend.graph.phase1_chapter import build_chapter_graph

SID = "stress01"


async def main():
    s = Settings()
    reg = ModelRegistry(s.sqlite_path)
    store = SQLiteStore(s.sqlite_path)
    await store.initialize()
    quads = KnowledgeQuads(s.sqlite_path)
    vector = VectorStore(s.chroma_path, embed_provider=s.embed_provider,
                         embed_model=s.embed_model, ollama_base_url=s.ollama_base_url)
    mem = LayeredMemory(store, vector)
    llm = LLMClient(s, registry=reg, llm_logger=LLMLogger(s.sqlite_path))

    story = await store.get_story(SID)
    if not story or not story.get("bible"):
        print(f"!! {SID} 无 bible，先跑 stress_10ch 或换一个已 init 的故事")
        return

    before = await store.get_chapter_count(SID)
    inst = await store.get_installments_done(SID) + 1
    start = before + 1
    print(f"配置: target={s.chapter_target_words} 阈值={s.chapter_split_threshold}")
    print(f"生成推进单元 {inst}，物理章从 {start} 起 …", flush=True)

    cg = build_chapter_graph(llm, store, quads, mem, None, s)
    await cg.ainvoke({"story_id": SID, "chapter_num": start, "installment_num": inst,
                      "target_words": s.chapter_target_words})
    await store.bump_installments_done(SID)

    after = await store.get_chapter_count(SID)
    print(f"\n物理章: {before} → {after}（本单元产出 {after - before} 章）")
    import json
    for cn in range(start, after + 1):
        ch = await store.get_chapter(SID, cn)
        q = json.loads(ch.get("quality_json") or "{}")
        print(f"  ch{cn}: 《{ch['title']}》 {ch['word_count']}字 "
              f"installment={ch['installment_num']} composite={q.get('composite_final')}")
    print(f"installments_done = {await store.get_installments_done(SID)}")


if __name__ == "__main__":
    asyncio.run(main())
