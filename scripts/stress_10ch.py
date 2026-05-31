"""压测：连续生成 10 章，实测长程一致性 + 质量稳定性。

跑完汇总：
  - 每章 composite / slop / 字数 / 重写轮数 / 一致性冲突
  - 质量曲线趋势（是否随章数下滑）
  - 角色 voice 是否保持（人工抽查靠读正文）
  - 四元组增长曲线（长程记忆是否在累积）
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("STORY_LITELLM_MODEL", "deepseek/deepseek-chat")

from backend.config import Settings
from backend.llm.client import LLMClient
from backend.llm.model_registry import ModelRegistry
from backend.llm.logger import LLMLogger
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore
from backend.memory.knowledge_quads import KnowledgeQuads
from backend.memory.layered_memory import LayeredMemory
from backend.graph.phase1_init import build_init_graph
from backend.graph.phase1_chapter import build_chapter_graph

N_CHAPTERS = int(os.environ.get("STRESS_N", "10"))
STORY_ID = "stress01"


async def main():
    s = Settings()
    reg = ModelRegistry(s.sqlite_path)
    store = SQLiteStore(s.sqlite_path)
    await store.initialize()
    quads = KnowledgeQuads(s.sqlite_path)
    vector = VectorStore(
        s.chroma_path, embed_provider=s.embed_provider,
        embed_model=s.embed_model, ollama_base_url=s.ollama_base_url)
    mem = LayeredMemory(store, vector)
    llm = LLMClient(s, registry=reg, llm_logger=LLMLogger(s.sqlite_path))

    # 清理同名旧故事（含记忆/伏笔），并重置向量集合，避免跨次污染
    import aiosqlite
    async with aiosqlite.connect(s.sqlite_path) as db:
        for t in ("chapters", "characters", "character_states", "knowledge_quads",
                  "outline_rough", "outline_detailed", "chapter_quality_scores",
                  "chapter_quality_evaluations", "slop_findings", "memories",
                  "foreshadowing", "stories"):
            await db.execute(f"DELETE FROM {t} WHERE story_id = ?" if t != "stories" else "DELETE FROM stories WHERE id = ?", (STORY_ID,))
        await db.commit()
    try:
        vector.client.delete_collection(f"story_{STORY_ID}")
    except Exception:
        pass

    await store.create_story(STORY_ID, "压测书", genre="男频系统流")

    # init
    print("=== INIT ===", flush=True)
    init = build_init_graph(llm, store, quads, mem)
    await init.ainvoke({"story_id": STORY_ID,
                        "theme": "落魄程序员觉醒代码编辑器系统,能改写现实的源码",
                        "requirements": "爽文,节奏快,有脑洞", "title": "", "target_chapters": 60})
    chars = await store.list_characters(STORY_ID)
    print(f"init done: {len(chars)} 角色: {[c['name'] for c in chars]}", flush=True)

    # 连写 N 章
    cg = build_chapter_graph(llm, store, quads, mem)
    rows = []
    for n in range(1, N_CHAPTERS + 1):
        print(f"\n=== 第 {n} 章 ===", flush=True)
        try:
            await cg.ainvoke({"story_id": STORY_ID, "chapter_num": n, "target_words": 3500})
        except Exception as e:
            print(f"  第 {n} 章失败: {type(e).__name__}: {str(e)[:200]}", flush=True)
            rows.append({"ch": n, "fail": str(e)[:80]})
            continue
        ch = await store.get_chapter(STORY_ID, n)
        q = ch.get("quality_json")
        import json
        qd = json.loads(q) if q else {}
        nq = await quads.query_valid_at(STORY_ID, n + 1)
        row = {
            "ch": n, "title": ch["title"], "words": ch["word_count"],
            "composite": qd.get("composite_final", qd.get("composite_score")),
            "slop": qd.get("slop_penalty"),
            "conflicts": qd.get("consistency_conflicts", 0),
            "quads": len(nq),
        }
        rows.append(row)
        print(f"  {row['title']!r} {row['words']}字 composite={row['composite']} "
              f"slop={row['slop']} 冲突={row['conflicts']} 累计四元组={row['quads']}", flush=True)

    # 汇总
    print("\n\n=== 压测汇总 ===", flush=True)
    print(f"{'章':>3} {'字数':>5} {'composite':>9} {'slop':>5} {'冲突':>4} {'四元组':>6}  标题")
    ok_rows = [r for r in rows if "fail" not in r]
    for r in rows:
        if "fail" in r:
            print(f"{r['ch']:>3}  FAILED: {r['fail']}")
        else:
            print(f"{r['ch']:>3} {r['words']:>5} {r['composite']:>9} {r['slop']:>5} "
                  f"{r['conflicts']:>4} {r['quads']:>6}  {r['title']}")
    if ok_rows:
        comps = [r["composite"] for r in ok_rows if r["composite"] is not None]
        print(f"\n成功 {len(ok_rows)}/{N_CHAPTERS} 章")
        if comps:
            print(f"composite: 均值={sum(comps)/len(comps):.2f} 首章={comps[0]:.2f} 末章={comps[-1]:.2f} "
                  f"最低={min(comps):.2f} 最高={max(comps):.2f}")
        print(f"四元组增长: 第1章后={ok_rows[0]['quads']} → 末章后={ok_rows[-1]['quads']}")
        total_conflicts = sum(r["conflicts"] for r in ok_rows)
        print(f"累计一致性冲突: {total_conflicts}")
        # 伏笔埋坑/填坑
        async with aiosqlite.connect(s.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            fr = await (await db.execute(
                "SELECT status, COUNT(*) AS n FROM foreshadowing WHERE story_id=? GROUP BY status",
                (STORY_ID,))).fetchall()
            fc = {r["status"]: r["n"] for r in fr}
        planted = sum(fc.values())
        print(f"伏笔: 埋={planted} 已回收={fc.get('resolved',0)} 待回收={fc.get('open',0)}"
              + (f"（回收率 {fc.get('resolved',0)/planted:.0%}）" if planted else ""))
        # 分层记忆
        mc = await store.count_memories(STORY_ID)
        print(f"分层记忆: {mc}（L0身份核心 / L1情感关键）")


if __name__ == "__main__":
    asyncio.run(main())
