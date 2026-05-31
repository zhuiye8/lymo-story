"""SQLite 存储层（Phase 1 重写）。

设计依据 phase1/00-architecture.md §6 + 01-implementation-plan.md Step 2。

从 0 重建：删旧 schema（json_store / world_book / scene / 旧 evaluation_batches 等），
保留 plumbing（model_configs / agent_model_bindings / llm_logs）+ quality_admin
要救活的评测表（chapter_quality_scores / chapter_quality_evaluations / slop_findings）。

Phase 1 新核心表：
  stories            故事元信息 + StoryBible JSON
  knowledge_quads    DOME 四元组 <主体,谓词,客体,章号区间>（长程一致性地基）
  characters         角色卡（含 voice_profile 对白指纹）
  character_states   角色状态随章演变
  outline_rough      DOME 双层大纲·粗纲（5 段）
  outline_detailed   DOME 双层大纲·细纲（动态展开）
  chapters           章节正文
  memories           分层记忆元数据（向量在 ChromaDB）
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import aiosqlite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(
                """
                -- ============ 故事 ============
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL DEFAULT '',
                    theme TEXT NOT NULL DEFAULT '',
                    bible_json TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'created',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                -- ============ DOME 四元组（长程一致性地基）============
                -- <subject, predicate, object, [valid_from, valid_to)>
                -- invalidate-not-delete：事实失效用 valid_to 标记，不物理删除
                CREATE TABLE IF NOT EXISTS knowledge_quads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    valid_from INTEGER NOT NULL,      -- 起始章号
                    valid_to INTEGER,                 -- 失效章号；NULL=仍有效
                    source_chapter INTEGER NOT NULL,  -- 该事实由哪章产生
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_quad_story ON knowledge_quads(story_id);
                CREATE INDEX IF NOT EXISTS idx_quad_subject ON knowledge_quads(story_id, subject);
                CREATE INDEX IF NOT EXISTS idx_quad_valid ON knowledge_quads(story_id, valid_from, valid_to);

                -- ============ 角色（含对白指纹）============
                CREATE TABLE IF NOT EXISTS characters (
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT '',          -- protagonist/antagonist/supporting
                    profile_json TEXT NOT NULL DEFAULT '{}',     -- 完整人设
                    voice_profile_json TEXT NOT NULL DEFAULT '{}', -- 对白指纹：口头禅/句式/语气/禁用词
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, character_id)
                );

                -- ============ 角色状态（随章演变）============
                CREATE TABLE IF NOT EXISTS character_states (
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    location TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    emotional_state TEXT NOT NULL DEFAULT '',
                    relationships_json TEXT NOT NULL DEFAULT '{}',  -- 对其他角色的态度
                    state_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (story_id, character_id, chapter_num)
                );

                -- ============ DOME 双层大纲·粗纲（5 段）============
                CREATE TABLE IF NOT EXISTS outline_rough (
                    story_id TEXT NOT NULL,
                    stage_num INTEGER NOT NULL,
                    stage_name TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    chapter_start INTEGER,
                    chapter_end INTEGER,
                    PRIMARY KEY (story_id, stage_num)
                );

                -- ============ DOME 双层大纲·细纲（动态展开）============
                CREATE TABLE IF NOT EXISTS outline_detailed (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    beats_json TEXT NOT NULL DEFAULT '[]',          -- 本章 beats/分镜
                    narrative_func_tags TEXT NOT NULL DEFAULT '',   -- Propp-34 中文功能标签
                    word_budget INTEGER NOT NULL DEFAULT 3500,      -- LongWriter 字数预算
                    expanded_at TEXT,
                    PRIMARY KEY (story_id, chapter_num)
                );

                -- ============ 章节正文 ============
                CREATE TABLE IF NOT EXISTS chapters (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    pov TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    word_count INTEGER NOT NULL DEFAULT 0,
                    summary TEXT NOT NULL DEFAULT '',               -- 本章压缩摘要（喂下一章上下文）
                    quality_json TEXT NOT NULL DEFAULT '{}',        -- composite/8维/slop 快照
                    is_published INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num)
                );

                -- ============ 分层记忆（向量在 ChromaDB，这里存元数据）============
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    character_id TEXT,
                    layer INTEGER NOT NULL,             -- 0 身份核心 / 1 关键记忆 / 2 场景相关 / 3 深搜
                    content TEXT NOT NULL,
                    emotional_weight REAL NOT NULL DEFAULT 0.5,
                    source_chapter INTEGER NOT NULL,
                    vector_id TEXT,                     -- ChromaDB 中的 id
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mem_story ON memories(story_id, character_id, layer);

                -- ============ plumbing：模型配置 / agent 绑定 / LLM 日志（保留）============
                CREATE TABLE IF NOT EXISTS model_configs (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    litellm_model TEXT NOT NULL,
                    api_key TEXT NOT NULL DEFAULT '',
                    api_base TEXT,
                    max_tokens INT DEFAULT 4096,
                    default_temperature REAL DEFAULT 0.7,
                    cost_per_million_input REAL DEFAULT 0,
                    cost_per_million_input_cached REAL DEFAULT 0,
                    cost_per_million_output REAL DEFAULT 0,
                    currency TEXT DEFAULT 'CNY',
                    is_active BOOLEAN DEFAULT 1,
                    provider TEXT DEFAULT 'generic',
                    provider_options_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_model_bindings (
                    agent_name TEXT PRIMARY KEY,
                    model_config_id TEXT NOT NULL,
                    temperature_override REAL,
                    max_tokens_override INT,
                    FOREIGN KEY (model_config_id) REFERENCES model_configs(id)
                );
                CREATE TABLE IF NOT EXISTS llm_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT,
                    chapter_num INT,
                    agent_name TEXT NOT NULL,
                    model_config_id TEXT NOT NULL DEFAULT '',
                    litellm_model TEXT NOT NULL,
                    system_prompt TEXT,
                    user_prompt TEXT,
                    response TEXT,
                    input_tokens INT DEFAULT 0,
                    output_tokens INT DEFAULT 0,
                    total_tokens INT DEFAULT 0,
                    cost_estimate REAL DEFAULT 0,
                    latency_ms INT DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_llm_logs_agent ON llm_logs(agent_name);
                CREATE INDEX IF NOT EXISTS idx_llm_logs_story ON llm_logs(story_id);
                CREATE INDEX IF NOT EXISTS idx_llm_logs_created ON llm_logs(created_at);

                -- ============ 质量评测（quality_admin 4 图表 backend 救活）============
                -- 不再用 evaluation_batches 隔离（Phase 0 概念），直接按 story 存在线评测
                CREATE TABLE IF NOT EXISTS chapter_quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    dimension TEXT NOT NULL,
                    score REAL NOT NULL,
                    judge_model TEXT NOT NULL DEFAULT '',
                    judged_at TEXT NOT NULL,
                    rubric_version TEXT NOT NULL DEFAULT 'SEQR-p1-wnb8'
                );
                CREATE INDEX IF NOT EXISTS idx_qscore_story ON chapter_quality_scores(story_id, chapter_num);

                CREATE TABLE IF NOT EXISTS chapter_quality_evaluations (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    composite_score REAL NOT NULL,
                    mean_quality REAL NOT NULL,
                    slop_penalty REAL NOT NULL,
                    word_count INTEGER NOT NULL DEFAULT 0,
                    rubric_version TEXT NOT NULL DEFAULT 'SEQR-p1-wnb8',
                    judged_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num)
                );

                CREATE TABLE IF NOT EXISTS slop_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    hits_json TEXT NOT NULL DEFAULT '[]',
                    weighted_penalty REAL NOT NULL DEFAULT 0,
                    detector_version TEXT NOT NULL DEFAULT 'slop-p1',
                    detected_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_slop_story ON slop_findings(story_id, chapter_num);

                -- ============ 伏笔（埋坑/填坑闭环）============
                CREATE TABLE IF NOT EXISTS foreshadowing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    description TEXT NOT NULL,              -- 伏笔内容
                    planted_chapter INTEGER NOT NULL,       -- 埋下的章
                    status TEXT NOT NULL DEFAULT 'open',    -- open 待回收 / resolved 已回收
                    resolved_chapter INTEGER,               -- 回收的章
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_foreshadow_story ON foreshadowing(story_id, status);
                """
            )
            # 轻量迁移：给既有库补列（CREATE TABLE IF NOT EXISTS 不会改已存在的表）。
            # installment_num: 该物理章属哪个剧情推进单元；installments_done: 故事已推进的单元数。
            for ddl in (
                "ALTER TABLE chapters ADD COLUMN installment_num INTEGER DEFAULT 0",
                "ALTER TABLE stories ADD COLUMN installments_done INTEGER DEFAULT 0",
            ):
                try:
                    await db.execute(ddl)
                except Exception:
                    pass  # 列已存在
            # 回填：书名 bug 之前的故事，title 卡在"未命名"但 bible.concept.title 已有 → 提上来。
            try:
                await db.execute(
                    "UPDATE stories SET title = json_extract(bible_json, '$.concept.title') "
                    "WHERE (title = '未命名' OR title = '') "
                    "AND json_extract(bible_json, '$.concept.title') IS NOT NULL "
                    "AND json_extract(bible_json, '$.concept.title') != ''"
                )
            except Exception:
                pass
            # 回填：Phase B 之前的故事每章即一个推进单元（无切分），令 installments_done=章数。
            # 仅影响 installments_done=0 且已有章节的旧故事；新故事/已跟踪故事不受影响。
            try:
                await db.execute(
                    "UPDATE stories SET installments_done = "
                    "(SELECT COUNT(*) FROM chapters WHERE chapters.story_id = stories.id) "
                    "WHERE installments_done = 0 "
                    "AND EXISTS (SELECT 1 FROM chapters WHERE chapters.story_id = stories.id)"
                )
            except Exception:
                pass
            await db.commit()

    # ===================== stories =====================

    async def create_story(self, story_id: str, title: str, *, genre: str = "", theme: str = "") -> None:
        now = _now()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO stories (id, title, genre, theme, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'created', ?, ?)",
                (story_id, title, genre, theme, now, now),
            )
            await db.commit()

    async def save_bible(self, story_id: str, bible: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE stories SET bible_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(bible, ensure_ascii=False), _now(), story_id),
            )
            await db.commit()

    async def get_story(self, story_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            row = await cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["bible"] = json.loads(d.pop("bible_json") or "{}")
            return d

    async def list_stories(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT id, title, genre, theme, status, created_at, updated_at FROM stories ORDER BY created_at DESC")
            return [dict(r) for r in await cur.fetchall()]

    async def update_story_status(self, story_id: str, status: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE stories SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), story_id),
            )
            await db.commit()

    async def update_story_title(self, story_id: str, title: str) -> None:
        """更新故事标题，并同步进 bible.concept.title，保持一致。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT bible_json FROM stories WHERE id = ?", (story_id,))
            row = await cur.fetchone()
            bible = json.loads(row["bible_json"]) if row and row["bible_json"] else {}
            if bible:
                bible.setdefault("concept", {})["title"] = title
            await db.execute(
                "UPDATE stories SET title = ?, bible_json = ?, updated_at = ? WHERE id = ?",
                (title, json.dumps(bible, ensure_ascii=False), _now(), story_id),
            )
            await db.commit()

    async def update_concept_field(self, story_id: str, field: str, value: str) -> None:
        """更新 bible.concept 下的某个字段（如 blurb）。故事尚无 bible 时静默跳过。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT bible_json FROM stories WHERE id = ?", (story_id,))
            row = await cur.fetchone()
            bible = json.loads(row["bible_json"]) if row and row["bible_json"] else {}
            if not bible:
                return
            bible.setdefault("concept", {})[field] = value
            await db.execute(
                "UPDATE stories SET bible_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(bible, ensure_ascii=False), _now(), story_id),
            )
            await db.commit()

    async def get_installments_done(self, story_id: str) -> int:
        """已推进的剧情单元数（≠物理章数；切分会让物理章多于单元）。"""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT installments_done FROM stories WHERE id = ?", (story_id,))
            row = await cur.fetchone()
            return (row[0] or 0) if row else 0

    async def bump_installments_done(self, story_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE stories SET installments_done = installments_done + 1, updated_at = ? WHERE id = ?",
                (_now(), story_id),
            )
            await db.commit()

    # ===================== chapters =====================

    async def save_chapter(
        self, story_id: str, chapter_num: int, *,
        title: str = "", pov: str = "", content: str = "",
        summary: str = "", quality: dict | None = None, installment_num: int = 0,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO chapters
                   (story_id, chapter_num, title, pov, content, word_count, summary, quality_json, installment_num, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, chapter_num) DO UPDATE SET
                     title=excluded.title, pov=excluded.pov, content=excluded.content,
                     word_count=excluded.word_count, summary=excluded.summary,
                     quality_json=excluded.quality_json, installment_num=excluded.installment_num""",
                (story_id, chapter_num, title, pov, content, len(content),
                 summary, json.dumps(quality or {}, ensure_ascii=False), installment_num, _now()),
            )
            await db.commit()

    async def get_chapter(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM chapters WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_chapters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT story_id, chapter_num, title, pov, word_count, summary, quality_json, is_published, created_at "
                "FROM chapters WHERE story_id = ? ORDER BY chapter_num",
                (story_id,),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def get_chapter_count(self, story_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT COUNT(*) FROM chapters WHERE story_id = ?", (story_id,))
            return (await cur.fetchone())[0]

    async def get_recent_summaries(self, story_id: str, before_chapter: int, limit: int = 3) -> list[dict]:
        """取最近 N 章的压缩摘要，喂下一章上下文（context cache 友好）。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT chapter_num, title, summary FROM chapters "
                "WHERE story_id = ? AND chapter_num < ? ORDER BY chapter_num DESC LIMIT ?",
                (story_id, before_chapter, limit),
            )
            rows = [dict(r) for r in await cur.fetchall()]
            return list(reversed(rows))

    # ===================== 伏笔（埋坑/填坑）=====================

    async def save_foreshadowing(self, story_id: str, chapter: int, items: list[str]) -> list[int]:
        """记录本章埋下的伏笔（status=open），返回新 id 列表。"""
        ids: list[int] = []
        now = _now()
        async with aiosqlite.connect(self.db_path) as db:
            for desc in items:
                desc = (desc or "").strip()
                if not desc:
                    continue
                cur = await db.execute(
                    "INSERT INTO foreshadowing (story_id, description, planted_chapter, status, created_at) "
                    "VALUES (?, ?, ?, 'open', ?)",
                    (story_id, desc, chapter, now),
                )
                ids.append(cur.lastrowid or 0)
            await db.commit()
        return ids

    async def get_open_foreshadowing(self, story_id: str, before_chapter: int) -> list[dict]:
        """取仍未回收的伏笔（planted_chapter < before_chapter），带 age=拖了多少章。
        越老的排前面——便于催收（埋了很久没填的坑优先回收）。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, description, planted_chapter FROM foreshadowing "
                "WHERE story_id = ? AND status = 'open' AND planted_chapter < ? "
                "ORDER BY planted_chapter ASC",
                (story_id, before_chapter),
            )
            out = []
            for r in await cur.fetchall():
                d = dict(r)
                d["age"] = max(0, before_chapter - d["planted_chapter"])
                out.append(d)
            return out

    async def resolve_foreshadowing(self, story_id: str, ids: list[int], chapter: int) -> int:
        """把指定伏笔标为已回收（resolved）。返回实际更新条数。"""
        if not ids:
            return 0
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" * len(ids))
            cur = await db.execute(
                f"UPDATE foreshadowing SET status='resolved', resolved_chapter=? "
                f"WHERE story_id=? AND status='open' AND id IN ({placeholders})",
                (chapter, story_id, *ids),
            )
            await db.commit()
            return cur.rowcount or 0

    # ===================== 分层记忆（L0-L3，元数据；向量在 ChromaDB）=====================

    async def save_memory(
        self, story_id: str, character_id: str, *, layer: int, content: str,
        emotional_weight: float, source_chapter: int, vector_id: str = "",
    ) -> int:
        """写一条记忆元数据，返回自增 id（向量库用 mem_{id} 作 vector_id 关联）。"""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                """INSERT INTO memories
                   (story_id, character_id, layer, content, emotional_weight, source_chapter, vector_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (story_id, character_id, layer, content, emotional_weight, source_chapter, vector_id, _now()),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def set_memory_vector_id(self, mem_id: int, vector_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE memories SET vector_id=? WHERE id=?", (vector_id, mem_id))
            await db.commit()

    async def count_memories(self, story_id: str) -> dict:
        """按 layer 统计记忆条数（压测/可观测用）。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT layer, COUNT(*) AS n FROM memories WHERE story_id=? GROUP BY layer",
                (story_id,),
            )
            return {f"L{r['layer']}": r["n"] for r in await cur.fetchall()}

    async def list_memories(self, story_id: str) -> list[dict]:
        """列出全部记忆（按角色 + 情感权重，供 UI 可视化）。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, character_id, layer, content, emotional_weight, source_chapter "
                "FROM memories WHERE story_id=? ORDER BY layer, emotional_weight DESC, source_chapter",
                (story_id,),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def list_foreshadowing(self, story_id: str) -> list[dict]:
        """列出全部伏笔（open + resolved），供 UI 埋坑/填坑看板。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, description, planted_chapter, status, resolved_chapter "
                "FROM foreshadowing WHERE story_id=? ORDER BY planted_chapter, id",
                (story_id,),
            )
            return [dict(r) for r in await cur.fetchall()]

    # ===================== characters =====================

    async def save_character(
        self, story_id: str, character_id: str, *,
        name: str, role: str = "", profile: dict | None = None, voice_profile: dict | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO characters
                   (story_id, character_id, name, role, profile_json, voice_profile_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, character_id) DO UPDATE SET
                     name=excluded.name, role=excluded.role,
                     profile_json=excluded.profile_json, voice_profile_json=excluded.voice_profile_json""",
                (story_id, character_id, name, role,
                 json.dumps(profile or {}, ensure_ascii=False),
                 json.dumps(voice_profile or {}, ensure_ascii=False), _now()),
            )
            await db.commit()

    async def list_characters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM characters WHERE story_id = ?", (story_id,))
            out = []
            for r in await cur.fetchall():
                d = dict(r)
                d["profile"] = json.loads(d.pop("profile_json") or "{}")
                d["voice_profile"] = json.loads(d.pop("voice_profile_json") or "{}")
                out.append(d)
            return out

    async def save_character_state(
        self, story_id: str, character_id: str, chapter_num: int, *,
        location: str = "", status: str = "", emotional_state: str = "",
        relationships: dict | None = None, state: dict | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO character_states
                   (story_id, character_id, chapter_num, location, status, emotional_state, relationships_json, state_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, character_id, chapter_num) DO UPDATE SET
                     location=excluded.location, status=excluded.status,
                     emotional_state=excluded.emotional_state,
                     relationships_json=excluded.relationships_json, state_json=excluded.state_json""",
                (story_id, character_id, chapter_num, location, status, emotional_state,
                 json.dumps(relationships or {}, ensure_ascii=False),
                 json.dumps(state or {}, ensure_ascii=False)),
            )
            await db.commit()

    async def get_latest_character_states(self, story_id: str, up_to_chapter: int) -> list[dict]:
        """每个角色取 ≤ up_to_chapter 的最新状态。"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT cs.* FROM character_states cs
                   JOIN (SELECT character_id, MAX(chapter_num) AS mx FROM character_states
                         WHERE story_id = ? AND chapter_num <= ? GROUP BY character_id) latest
                   ON cs.character_id = latest.character_id AND cs.chapter_num = latest.mx
                   WHERE cs.story_id = ?""",
                (story_id, up_to_chapter, story_id),
            )
            out = []
            for r in await cur.fetchall():
                d = dict(r)
                d["relationships"] = json.loads(d.pop("relationships_json") or "{}")
                d["state"] = json.loads(d.pop("state_json") or "{}")
                out.append(d)
            return out

    # ===================== outline (DOME 双层) =====================

    async def save_rough_outline(self, story_id: str, stages: list[dict]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM outline_rough WHERE story_id = ?", (story_id,))
            for s in stages:
                await db.execute(
                    "INSERT INTO outline_rough (story_id, stage_num, stage_name, summary, chapter_start, chapter_end) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (story_id, s["stage_num"], s.get("stage_name", ""), s.get("summary", ""),
                     s.get("chapter_start"), s.get("chapter_end")),
                )
            await db.commit()

    async def get_rough_outline(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM outline_rough WHERE story_id = ? ORDER BY stage_num", (story_id,))
            return [dict(r) for r in await cur.fetchall()]

    async def save_detailed_outline(
        self, story_id: str, chapter_num: int, *,
        beats: list | None = None, narrative_func_tags: str = "", word_budget: int = 3500,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO outline_detailed
                   (story_id, chapter_num, beats_json, narrative_func_tags, word_budget, expanded_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, chapter_num) DO UPDATE SET
                     beats_json=excluded.beats_json, narrative_func_tags=excluded.narrative_func_tags,
                     word_budget=excluded.word_budget, expanded_at=excluded.expanded_at""",
                (story_id, chapter_num, json.dumps(beats or [], ensure_ascii=False),
                 narrative_func_tags, word_budget, _now()),
            )
            await db.commit()

    async def get_detailed_outline(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM outline_detailed WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["beats"] = json.loads(d.pop("beats_json") or "[]")
            return d

    # ===================== quality 写入（喂 quality_admin 4 图表）=====================

    async def save_quality(
        self, story_id: str, chapter_num: int, *,
        dim_scores: dict[str, float], mean_quality: float, slop_penalty: float,
        composite_score: float, word_count: int, judge_model: str = "",
        slop_findings: list[dict] | None = None, rubric_version: str = "SEQR-p1-wnb8",
        detector_version: str = "slop-p1",
    ) -> None:
        now = _now()
        async with aiosqlite.connect(self.db_path) as db:
            # 逐维度分
            await db.execute(
                "DELETE FROM chapter_quality_scores WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num))
            for dim, score in dim_scores.items():
                await db.execute(
                    "INSERT INTO chapter_quality_scores (story_id, chapter_num, dimension, score, judge_model, judged_at, rubric_version) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (story_id, chapter_num, dim, score, judge_model, now, rubric_version))
            # 聚合
            await db.execute(
                """INSERT INTO chapter_quality_evaluations
                   (story_id, chapter_num, composite_score, mean_quality, slop_penalty, word_count, rubric_version, judged_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, chapter_num) DO UPDATE SET
                     composite_score=excluded.composite_score, mean_quality=excluded.mean_quality,
                     slop_penalty=excluded.slop_penalty, word_count=excluded.word_count, judged_at=excluded.judged_at""",
                (story_id, chapter_num, composite_score, mean_quality, slop_penalty, word_count, rubric_version, now))
            # slop findings
            await db.execute(
                "DELETE FROM slop_findings WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num))
            for f in (slop_findings or []):
                await db.execute(
                    "INSERT INTO slop_findings (story_id, chapter_num, category, hits_json, weighted_penalty, detector_version, detected_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (story_id, chapter_num, f["category"], json.dumps(f.get("hits", []), ensure_ascii=False),
                     f.get("weighted_penalty", 0), detector_version, now))
            await db.commit()
