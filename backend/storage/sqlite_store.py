import json
from datetime import datetime, timezone

import aiosqlite


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    theme TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'initializing',
                    is_published BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_states (
                    story_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE TABLE IF NOT EXISTS chapters (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    pov TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    events_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    is_published BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num),
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
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
                CREATE TABLE IF NOT EXISTS knowledge_triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    detail TEXT DEFAULT '',
                    valid_from INT NOT NULL,
                    valid_to INT,
                    source TEXT DEFAULT '',
                    source_version_id INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_kt_story_subject ON knowledge_triples(story_id, subject);
                CREATE INDEX IF NOT EXISTS idx_kt_story_valid ON knowledge_triples(story_id, valid_to);
                CREATE TABLE IF NOT EXISTS character_states (
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    chapter_num INT NOT NULL,
                    source_version_id INTEGER NOT NULL DEFAULT 0,
                    emotional_state TEXT DEFAULT '',
                    knowledge_summary TEXT DEFAULT '',
                    goals_update TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    state_json TEXT DEFAULT '{}',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (story_id, character_id, chapter_num, source_version_id)
                );
                CREATE TABLE IF NOT EXISTS chapter_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    version_num INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    pov TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    events_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    feedback TEXT NOT NULL DEFAULT '',
                    is_live INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE INDEX IF NOT EXISTS idx_chapter_versions_chapter
                    ON chapter_versions(story_id, chapter_num, version_num DESC);
                CREATE TABLE IF NOT EXISTS character_arcs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER,
                    arc_name TEXT NOT NULL DEFAULT '',
                    summary_json TEXT NOT NULL DEFAULT '{}',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE INDEX IF NOT EXISTS idx_character_arcs_char
                    ON character_arcs(story_id, character_id, chapter_num DESC);

                -- Phase 3: chapter summary (brief + key events + unresolved threads + tail)
                CREATE TABLE IF NOT EXISTS chapter_summaries (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER NOT NULL,
                    brief TEXT NOT NULL DEFAULT '',
                    key_events_json TEXT NOT NULL DEFAULT '[]',
                    unresolved_threads_json TEXT NOT NULL DEFAULT '[]',
                    tail_snippet TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num, source_version_id)
                );
                CREATE INDEX IF NOT EXISTS idx_summaries_active
                    ON chapter_summaries(story_id, is_active, chapter_num);

                -- Phase 2: chapter dependency tracking (for cascade invalidation)
                CREATE TABLE IF NOT EXISTS chapter_dependencies (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER NOT NULL,
                    depends_on_chapter INTEGER NOT NULL,
                    depends_on_version_id INTEGER NOT NULL,
                    dep_type TEXT NOT NULL DEFAULT 'memory',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num, source_version_id, depends_on_chapter, dep_type)
                );
                CREATE INDEX IF NOT EXISTS idx_deps_upstream
                    ON chapter_dependencies(story_id, depends_on_chapter);

                -- Phase 4: scene-level persistence
                CREATE TABLE IF NOT EXISTS chapter_scenes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER NOT NULL,
                    scene_idx INTEGER NOT NULL,
                    scene_id TEXT NOT NULL,
                    pov_character_id TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    characters_json TEXT DEFAULT '[]',
                    beats_json TEXT DEFAULT '[]',
                    purpose TEXT DEFAULT '',
                    target_words INTEGER DEFAULT 800,
                    content TEXT NOT NULL DEFAULT '',
                    consistency_score REAL DEFAULT 0,
                    consistency_issues_json TEXT DEFAULT '[]',
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_scenes_chapter
                    ON chapter_scenes(story_id, chapter_num, source_version_id, scene_idx);

                -- Phase 3: world book (keyword-triggered entries)
                CREATE TABLE IF NOT EXISTS world_book_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    entry_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    trigger_keys_json TEXT NOT NULL DEFAULT '[]',
                    priority INTEGER NOT NULL DEFAULT 0,
                    always_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE (story_id, entry_id)
                );
                CREATE INDEX IF NOT EXISTS idx_world_book_story
                    ON world_book_entries(story_id, entry_type);

                -- Phase 0: SEQR v0 quality evaluation (5 tables, batch-isolated)

                -- (0) evaluation batches — every "run a baseline" creates one row
                CREATE TABLE IF NOT EXISTS evaluation_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_label TEXT NOT NULL UNIQUE,
                    rubric_version TEXT NOT NULL,
                    judge_model TEXT NOT NULL,
                    judge_options_json TEXT,
                    -- detector_version: NO DEFAULT (Report #4 review correction).
                    -- Caller must pass the live DETECTOR_VERSION constant from
                    -- backend.quality.slop_detector. A stale literal default
                    -- caused the v1 split-brain audit pollution risk.
                    detector_version TEXT NOT NULL,
                    description TEXT,
                    scope_story_ids TEXT NOT NULL,
                    scope_chapter_count INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT DEFAULT 'running'
                );

                -- (1) per-dimension scores
                CREATE TABLE IF NOT EXISTS chapter_quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_batch_id INTEGER NOT NULL,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER,
                    dimension TEXT NOT NULL,
                    score REAL NOT NULL,
                    evidence TEXT,
                    judge_run_id INTEGER NOT NULL,
                    judged_at TEXT NOT NULL,
                    rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0',
                    UNIQUE (evaluation_batch_id, story_id, chapter_num, dimension)
                );
                CREATE INDEX IF NOT EXISTS idx_quality_batch
                    ON chapter_quality_scores(evaluation_batch_id, story_id, chapter_num);
                CREATE INDEX IF NOT EXISTS idx_quality_dim
                    ON chapter_quality_scores(dimension);

                -- (2) chapter-level aggregate
                CREATE TABLE IF NOT EXISTS chapter_quality_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_batch_id INTEGER NOT NULL,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER,
                    rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0',
                    judge_run_id INTEGER NOT NULL,
                    composite_score REAL NOT NULL,
                    mean_quality REAL NOT NULL,
                    slop_penalty REAL NOT NULL,
                    word_count INTEGER NOT NULL,
                    judged_at TEXT NOT NULL,
                    UNIQUE (evaluation_batch_id, story_id, chapter_num)
                );
                CREATE INDEX IF NOT EXISTS idx_eval_batch
                    ON chapter_quality_evaluations(evaluation_batch_id, story_id, chapter_num);

                -- (3) slop findings (mechanical detector output)
                CREATE TABLE IF NOT EXISTS slop_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_batch_id INTEGER NOT NULL,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    source_version_id INTEGER,
                    category TEXT NOT NULL,
                    hits_json TEXT NOT NULL DEFAULT '[]',
                    raw_score REAL NOT NULL,
                    weighted_penalty REAL NOT NULL,
                    detected_at TEXT NOT NULL,
                    -- detector_version: NO DEFAULT (see evaluation_batches above).
                    detector_version TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_slop_batch
                    ON slop_findings(evaluation_batch_id, story_id, chapter_num);

                -- (4) judge runs (cost + model audit)
                CREATE TABLE IF NOT EXISTS judge_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_batch_id INTEGER NOT NULL,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    judge_model TEXT NOT NULL,
                    judge_options_json TEXT,
                    rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0',
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cost_cny REAL DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_judge_batch
                    ON judge_runs(evaluation_batch_id);
            """)
            # Back-compat migrations for pre-existing columns
            for table, col, definition in [
                ("stories", "is_published", "BOOLEAN NOT NULL DEFAULT 0"),
                ("chapters", "is_published", "BOOLEAN NOT NULL DEFAULT 0"),
                ("knowledge_triples", "source_version_id", "INTEGER"),
                ("knowledge_triples", "is_active", "INTEGER NOT NULL DEFAULT 1"),
                ("character_states", "source_version_id", "INTEGER NOT NULL DEFAULT 0"),
                ("character_states", "is_active", "INTEGER NOT NULL DEFAULT 1"),
                ("character_arcs", "source_version_id", "INTEGER"),
                ("character_arcs", "is_active", "INTEGER NOT NULL DEFAULT 1"),
                ("chapter_versions", "is_live", "INTEGER NOT NULL DEFAULT 0"),
                # Provider-specific fields for model_configs
                ("model_configs", "provider", "TEXT DEFAULT 'generic'"),
                ("model_configs", "provider_options_json", "TEXT DEFAULT '{}'"),
                ("model_configs", "cost_per_million_input_cached", "REAL DEFAULT 0"),
            ]:
                try:
                    await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                except Exception:
                    pass  # Column already exists

            # Indexes that depend on columns added above. Created after ALTERs so they
            # work on both fresh schemas and migrated legacy schemas.
            for stmt in [
                "CREATE INDEX IF NOT EXISTS idx_kt_active ON knowledge_triples(story_id, is_active, valid_from)",
                "CREATE INDEX IF NOT EXISTS idx_kt_version ON knowledge_triples(source_version_id)",
                "CREATE INDEX IF NOT EXISTS idx_cs_active ON character_states(story_id, character_id, is_active, chapter_num)",
                "CREATE INDEX IF NOT EXISTS idx_character_arcs_active ON character_arcs(story_id, character_id, is_active, chapter_num DESC)",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_chapter_versions_live ON chapter_versions(story_id, chapter_num) WHERE is_live = 1",
            ]:
                try:
                    await db.execute(stmt)
                except Exception:
                    pass

            await db.commit()

            # Idempotent legacy migration: pair existing live chapters with version rows.
            await self._migrate_legacy_versions(db)

    async def _migrate_legacy_versions(self, db) -> None:
        """Ensure every chapters row has a matching chapter_versions entry with is_live=1.

        Old data (pre-version-id) may have chapters without any chapter_versions row,
        or chapter_versions without is_live. This guarantees post-migration every
        live chapter has an id we can reference from memories/triples/etc.
        """
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT story_id, chapter_num, title, pov, content, events_json, metadata_json, created_at FROM chapters")
        chapters = await cursor.fetchall()

        for ch in chapters:
            story_id = ch["story_id"]
            chapter_num = ch["chapter_num"]
            # Check if any version exists
            cur2 = await db.execute(
                "SELECT id, version_num, is_live FROM chapter_versions WHERE story_id = ? AND chapter_num = ? ORDER BY version_num DESC",
                (story_id, chapter_num),
            )
            versions = await cur2.fetchall()

            if not versions:
                # Create a legacy v1 as live
                await db.execute(
                    """INSERT INTO chapter_versions
                       (story_id, chapter_num, version_num, title, pov, content,
                        events_json, metadata_json, feedback, is_live, created_at)
                       VALUES (?, ?, 1, ?, ?, ?, ?, ?, '[legacy migration]', 1, ?)""",
                    (
                        story_id, chapter_num,
                        ch["title"], ch["pov"], ch["content"],
                        ch["events_json"], ch["metadata_json"],
                        ch["created_at"],
                    ),
                )
            else:
                live_versions = [v for v in versions if v["is_live"] == 1]
                if not live_versions:
                    # Mark the most recent version as live
                    latest_id = versions[0]["id"]
                    await db.execute(
                        "UPDATE chapter_versions SET is_live = 1 WHERE id = ?",
                        (latest_id,),
                    )

        await db.commit()

        # Backfill source_version_id on memories/triples/etc for chapters that lack them
        # Build lookup: (story_id, chapter_num) -> live version_id
        cursor = await db.execute(
            "SELECT story_id, chapter_num, id FROM chapter_versions WHERE is_live = 1"
        )
        live_rows = await cursor.fetchall()
        live_map = {(r["story_id"], r["chapter_num"]): r["id"] for r in live_rows}

        # knowledge_triples
        cursor = await db.execute(
            "SELECT id, story_id, valid_from FROM knowledge_triples WHERE source_version_id IS NULL"
        )
        for row in await cursor.fetchall():
            vid = live_map.get((row["story_id"], row["valid_from"]))
            if vid is not None:
                await db.execute(
                    "UPDATE knowledge_triples SET source_version_id = ? WHERE id = ?",
                    (vid, row["id"]),
                )

        # character_states: migration for is_active already defaults to 1; fill source_version_id when 0
        cursor = await db.execute(
            "SELECT story_id, character_id, chapter_num FROM character_states WHERE source_version_id = 0"
        )
        for row in await cursor.fetchall():
            vid = live_map.get((row["story_id"], row["chapter_num"]))
            if vid is not None:
                await db.execute(
                    "UPDATE character_states SET source_version_id = ? WHERE story_id = ? AND character_id = ? AND chapter_num = ? AND source_version_id = 0",
                    (vid, row["story_id"], row["character_id"], row["chapter_num"]),
                )

        # character_arcs
        cursor = await db.execute(
            "SELECT id, story_id, chapter_num FROM character_arcs WHERE source_version_id IS NULL"
        )
        for row in await cursor.fetchall():
            vid = live_map.get((row["story_id"], row["chapter_num"]))
            if vid is not None:
                await db.execute(
                    "UPDATE character_arcs SET source_version_id = ? WHERE id = ?",
                    (vid, row["id"]),
                )

        await db.commit()

    async def create_story(self, story_id: str, title: str, theme: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO stories (id, title, theme, status, created_at, updated_at) VALUES (?, ?, ?, 'initializing', ?, ?)",
                (story_id, title, theme, now, now),
            )
            await db.commit()

    async def get_story(self, story_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_story(self, story_id: str, **kwargs) -> None:
        now = datetime.now(timezone.utc).isoformat()
        sets = ["updated_at = ?"]
        vals = [now]
        for k, v in kwargs.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(story_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE stories SET {', '.join(sets)} WHERE id = ?", vals
            )
            await db.commit()

    async def list_stories(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM stories ORDER BY created_at DESC")
            return [dict(row) for row in await cursor.fetchall()]

    async def save_world_state(self, story_id: str, state: dict, version: int = 0) -> None:
        now = datetime.now(timezone.utc).isoformat()
        state_json = json.dumps(state, ensure_ascii=False)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO world_states (story_id, state_json, version, updated_at) VALUES (?, ?, ?, ?)",
                (story_id, state_json, version, now),
            )
            await db.commit()

    async def get_world_state(self, story_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT state_json FROM world_states WHERE story_id = ?", (story_id,)
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def save_chapter(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO chapters (story_id, chapter_num, title, pov, content, events_json, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    story_id,
                    chapter_num,
                    title,
                    pov,
                    content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    now,
                ),
            )
            await db.commit()

    async def save_chapter_and_version(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
        feedback: str = "",
    ) -> int:
        """Save chapter AND create a new live chapter_version.

        This is the Phase 1 unified writer. Steps:
        1. Demote any existing live version (is_live=0)
        2. Insert new chapter_versions row with is_live=1
        3. Upsert chapters table as materialized live view
        4. Return new version_id

        Callers should use this for all new-chapter writes and regenerations.
        """
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            # Demote old live
            await db.execute(
                "UPDATE chapter_versions SET is_live = 0 WHERE story_id = ? AND chapter_num = ? AND is_live = 1",
                (story_id, chapter_num),
            )
            # Next version_num
            cursor = await db.execute(
                "SELECT COALESCE(MAX(version_num), 0) FROM chapter_versions WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            next_version = (row[0] if row else 0) + 1

            # Insert new live version
            cursor = await db.execute(
                """INSERT INTO chapter_versions
                   (story_id, chapter_num, version_num, title, pov, content,
                    events_json, metadata_json, feedback, is_live, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    story_id, chapter_num, next_version,
                    title, pov, content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    feedback, now,
                ),
            )
            version_id = cursor.lastrowid or 0

            # Upsert chapters view
            await db.execute(
                "INSERT OR REPLACE INTO chapters (story_id, chapter_num, title, pov, content, events_json, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    story_id, chapter_num,
                    title, pov, content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    now,
                ),
            )
            await db.commit()
            return version_id

    async def get_live_version_id(self, story_id: str, chapter_num: int) -> int | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM chapter_versions WHERE story_id = ? AND chapter_num = ? AND is_live = 1",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_live_version(self, story_id: str, chapter_num: int, version_id: int) -> None:
        """Change the live version for a chapter to the given version_id."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chapter_versions SET is_live = 0 WHERE story_id = ? AND chapter_num = ? AND is_live = 1",
                (story_id, chapter_num),
            )
            await db.execute(
                "UPDATE chapter_versions SET is_live = 1 WHERE id = ?",
                (version_id,),
            )
            await db.commit()

    async def snapshot_only_version(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
        feedback: str = "",
    ) -> int:
        """Snapshot without changing live pointer. Used before regenerate to save the current content."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COALESCE(MAX(version_num), 0) FROM chapter_versions WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            next_version = (row[0] if row else 0) + 1
            cursor = await db.execute(
                """INSERT INTO chapter_versions
                   (story_id, chapter_num, version_num, title, pov, content,
                    events_json, metadata_json, feedback, is_live, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    story_id, chapter_num, next_version,
                    title, pov, content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    feedback, now,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_chapter(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chapters WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d

    async def list_chapters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT story_id, chapter_num, title, pov, length(content) as word_count, is_published, metadata_json, created_at FROM chapters WHERE story_id = ? ORDER BY chapter_num",
                (story_id,),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                meta = json.loads(d.pop("metadata_json", "{}"))
                d["has_warnings"] = bool(meta.get("consistency_warnings"))
                result.append(d)
            return result

    async def get_chapter_count(self, story_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM chapters WHERE story_id = ?", (story_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    # --- Chapter version methods ---

    async def save_chapter_version(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
        feedback: str = "",
    ) -> int:
        """(DEPRECATED: prefer save_chapter_and_version or snapshot_only_version)
        Snapshot a chapter into chapter_versions. Returns new version_num.
        """
        return await self.snapshot_only_version(
            story_id, chapter_num, title, pov, content, events, metadata, feedback
        )

    async def list_chapter_versions(
        self, story_id: str, chapter_num: int
    ) -> list[dict]:
        """List all historical versions of a chapter (most recent first)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, story_id, chapter_num, version_num, title, pov,
                          length(content) as word_count, feedback, is_live, created_at
                   FROM chapter_versions
                   WHERE story_id = ? AND chapter_num = ?
                   ORDER BY version_num DESC""",
                (story_id, chapter_num),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_chapter_version(self, version_id: int) -> dict | None:
        """Fetch a single chapter version by id with full content."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chapter_versions WHERE id = ?", (version_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d

    async def restore_chapter_version(self, version_id: int) -> dict | None:
        """Overwrite the current chapter with the given historical version.

        Before overwriting, the current live chapter is snapshotted into
        chapter_versions so the restore itself is reversible.
        Returns the restored chapter dict, or None if version not found.
        """
        version = await self.get_chapter_version(version_id)
        if not version:
            return None

        story_id = version["story_id"]
        chapter_num = version["chapter_num"]

        # Snapshot current live chapter first (non-live)
        current = await self.get_chapter(story_id, chapter_num)
        if current:
            await self.snapshot_only_version(
                story_id=story_id,
                chapter_num=chapter_num,
                title=current.get("title", ""),
                pov=current.get("pov", ""),
                content=current.get("content", ""),
                events=current.get("events_covered", []),
                metadata=current.get("metadata", {}),
                feedback=f"[restore snapshot] before restoring v{version['version_num']}",
            )

        # Flip live pointer to the restored version
        await self.set_live_version(story_id, chapter_num, version_id)

        # Update chapters materialized view
        await self.save_chapter(
            story_id=story_id,
            chapter_num=chapter_num,
            title=version.get("title", ""),
            pov=version.get("pov", ""),
            content=version.get("content", ""),
            events=version.get("events_covered", []),
            metadata=version.get("metadata", {}),
        )
        return version

    # --- Character arc methods ---

    async def save_character_arc(
        self,
        story_id: str,
        character_id: str,
        chapter_num: int,
        arc_name: str,
        summary: dict,
        source_version_id: int | None = None,
    ) -> int:
        """Persist a character arc summary. Returns the new row id."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO character_arcs
                   (story_id, character_id, chapter_num, source_version_id,
                    arc_name, summary_json, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    story_id,
                    character_id,
                    chapter_num,
                    source_version_id,
                    arc_name,
                    json.dumps(summary, ensure_ascii=False),
                    now,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_latest_character_arc(
        self, story_id: str, character_id: str
    ) -> dict | None:
        """Get the most recently stored active arc row for a character."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM character_arcs
                   WHERE story_id = ? AND character_id = ? AND is_active = 1
                   ORDER BY chapter_num DESC, id DESC
                   LIMIT 1""",
                (story_id, character_id),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["summary"] = json.loads(d.pop("summary_json", "{}"))
            return d

    async def list_character_arcs(
        self, story_id: str, character_id: str
    ) -> list[dict]:
        """List all historical active arc entries for a character (newest first)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM character_arcs
                   WHERE story_id = ? AND character_id = ? AND is_active = 1
                   ORDER BY chapter_num DESC, id DESC""",
                (story_id, character_id),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["summary"] = json.loads(d.pop("summary_json", "{}"))
                result.append(d)
            return result

    async def mark_arcs_active(self, story_id: str, chapter_num: int, version_id: int, active: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE character_arcs SET is_active = ? WHERE story_id = ? AND chapter_num = ? AND source_version_id = ?",
                (1 if active else 0, story_id, chapter_num, version_id),
            )
            await db.commit()

    async def mark_character_states_active(self, story_id: str, chapter_num: int, version_id: int, active: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE character_states SET is_active = ? WHERE story_id = ? AND chapter_num = ? AND source_version_id = ?",
                (1 if active else 0, story_id, chapter_num, version_id),
            )
            await db.commit()

    # --- Publish methods ---

    async def publish_story(self, story_id: str, publish: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE stories SET is_published = ?, updated_at = ? WHERE id = ?",
                (1 if publish else 0, now, story_id),
            )
            await db.commit()

    async def publish_chapter(self, story_id: str, chapter_num: int, publish: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chapters SET is_published = ? WHERE story_id = ? AND chapter_num = ?",
                (1 if publish else 0, story_id, chapter_num),
            )
            await db.commit()

    async def list_published_stories(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM stories WHERE is_published = 1 ORDER BY updated_at DESC"
            )
            rows = [dict(row) for row in await cursor.fetchall()]
            for r in rows:
                cursor2 = await db.execute(
                    "SELECT COUNT(*) FROM chapters WHERE story_id = ? AND is_published = 1",
                    (r["id"],),
                )
                count_row = await cursor2.fetchone()
                r["published_chapter_count"] = count_row[0] if count_row else 0
            return rows

    async def list_published_chapters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT story_id, chapter_num, title, pov, length(content) as word_count, created_at
                   FROM chapters WHERE story_id = ? AND is_published = 1
                   ORDER BY chapter_num""",
                (story_id,),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_published_chapter(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM chapters
                   WHERE story_id = ? AND chapter_num = ? AND is_published = 1""",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d

    # --- Chapter summaries (Phase 3) ---

    async def save_chapter_summary(
        self,
        story_id: str,
        chapter_num: int,
        source_version_id: int,
        brief: str,
        key_events: list[str],
        unresolved_threads: list[str],
        tail_snippet: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            # Deactivate any previous active summary for this chapter
            await db.execute(
                "UPDATE chapter_summaries SET is_active = 0 WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            await db.execute(
                """INSERT OR REPLACE INTO chapter_summaries
                   (story_id, chapter_num, source_version_id, brief,
                    key_events_json, unresolved_threads_json, tail_snippet,
                    is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    story_id, chapter_num, source_version_id, brief,
                    json.dumps(key_events, ensure_ascii=False),
                    json.dumps(unresolved_threads, ensure_ascii=False),
                    tail_snippet, now,
                ),
            )
            await db.commit()

    async def get_chapter_summary(self, story_id: str, chapter_num: int) -> dict | None:
        """Get the active summary for a chapter."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM chapter_summaries
                   WHERE story_id = ? AND chapter_num = ? AND is_active = 1
                   ORDER BY created_at DESC LIMIT 1""",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["key_events"] = json.loads(d.pop("key_events_json", "[]"))
            d["unresolved_threads"] = json.loads(d.pop("unresolved_threads_json", "[]"))
            return d

    async def list_recent_summaries(self, story_id: str, up_to_chapter: int, limit: int = 5) -> list[dict]:
        """List the last N active summaries up to and including a chapter (newest first)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM chapter_summaries
                   WHERE story_id = ? AND chapter_num <= ? AND is_active = 1
                   ORDER BY chapter_num DESC LIMIT ?""",
                (story_id, up_to_chapter, limit),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["key_events"] = json.loads(d.pop("key_events_json", "[]"))
                d["unresolved_threads"] = json.loads(d.pop("unresolved_threads_json", "[]"))
                result.append(d)
            return result

    async def mark_summary_active(self, story_id: str, chapter_num: int, version_id: int, active: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chapter_summaries SET is_active = ? WHERE story_id = ? AND chapter_num = ? AND source_version_id = ?",
                (1 if active else 0, story_id, chapter_num, version_id),
            )
            await db.commit()

    # --- Chapter dependencies (Phase 2) ---

    async def record_chapter_dependencies(
        self,
        story_id: str,
        chapter_num: int,
        source_version_id: int,
        deps: list[dict],
    ) -> None:
        """Record that chapter (chapter_num, version) depends on a list of upstream versions.

        deps: [{depends_on_chapter: int, depends_on_version_id: int, dep_type: str}]
        """
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            for d in deps:
                try:
                    await db.execute(
                        """INSERT OR REPLACE INTO chapter_dependencies
                           (story_id, chapter_num, source_version_id,
                            depends_on_chapter, depends_on_version_id, dep_type, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            story_id, chapter_num, source_version_id,
                            d["depends_on_chapter"], d["depends_on_version_id"],
                            d.get("dep_type", "memory"), now,
                        ),
                    )
                except Exception:
                    pass
            await db.commit()

    async def get_downstream_chapters(
        self, story_id: str, target_chapter: int
    ) -> list[dict]:
        """Find chapters whose current live version depends on <= target_chapter.

        Returns list of {chapter_num, source_version_id, dep_chapters: [int]}
        limited to the currently live version of each downstream chapter.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT d.chapter_num, d.source_version_id, d.depends_on_chapter, d.dep_type
                   FROM chapter_dependencies d
                   JOIN chapter_versions v
                     ON v.story_id = d.story_id
                    AND v.chapter_num = d.chapter_num
                    AND v.id = d.source_version_id
                    AND v.is_live = 1
                   WHERE d.story_id = ?
                     AND d.depends_on_chapter <= ?
                     AND d.chapter_num > ?
                   ORDER BY d.chapter_num""",
                (story_id, target_chapter, target_chapter),
            )
            rows = await cursor.fetchall()
        # Group by chapter
        grouped: dict[int, dict] = {}
        for r in rows:
            cn = r["chapter_num"]
            if cn not in grouped:
                grouped[cn] = {
                    "chapter_num": cn,
                    "source_version_id": r["source_version_id"],
                    "dep_chapters": [],
                    "dep_types": set(),
                }
            grouped[cn]["dep_chapters"].append(r["depends_on_chapter"])
            grouped[cn]["dep_types"].add(r["dep_type"])
        out = []
        for cn in sorted(grouped):
            g = grouped[cn]
            out.append({
                "chapter_num": g["chapter_num"],
                "source_version_id": g["source_version_id"],
                "dep_chapters": sorted(set(g["dep_chapters"])),
                "dep_types": sorted(g["dep_types"]),
            })
        return out

    # --- Chapter scenes (Phase 4) ---

    async def save_chapter_scene(
        self,
        story_id: str,
        chapter_num: int,
        source_version_id: int,
        scene_idx: int,
        scene_id: str,
        pov_character_id: str,
        location: str,
        characters: list[str],
        beats: list[str],
        purpose: str,
        target_words: int,
        content: str,
        consistency_score: float,
        consistency_issues: list,
        retry_count: int,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO chapter_scenes
                   (story_id, chapter_num, source_version_id, scene_idx, scene_id,
                    pov_character_id, location, characters_json, beats_json, purpose,
                    target_words, content, consistency_score, consistency_issues_json,
                    retry_count, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    story_id, chapter_num, source_version_id, scene_idx, scene_id,
                    pov_character_id, location,
                    json.dumps(characters, ensure_ascii=False),
                    json.dumps(beats, ensure_ascii=False),
                    purpose, target_words, content, consistency_score,
                    json.dumps(consistency_issues, ensure_ascii=False),
                    retry_count, now,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def list_chapter_scenes(
        self, story_id: str, chapter_num: int, source_version_id: int | None = None
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if source_version_id is None:
                # Fall back to live version
                vid = await self.get_live_version_id(story_id, chapter_num)
                if vid is None:
                    return []
                source_version_id = vid
            cursor = await db.execute(
                """SELECT * FROM chapter_scenes
                   WHERE story_id = ? AND chapter_num = ? AND source_version_id = ?
                   ORDER BY scene_idx""",
                (story_id, chapter_num, source_version_id),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["characters"] = json.loads(d.pop("characters_json", "[]"))
                d["beats"] = json.loads(d.pop("beats_json", "[]"))
                d["consistency_issues"] = json.loads(d.pop("consistency_issues_json", "[]"))
                result.append(d)
            return result

    # --- World book entries (Phase 3) ---

    async def upsert_world_book_entry(
        self,
        story_id: str,
        entry_type: str,
        entry_id: str,
        name: str,
        description: str,
        trigger_keys: list[str],
        priority: int = 0,
        always_active: bool = False,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO world_book_entries
                   (story_id, entry_type, entry_id, name, description,
                    trigger_keys_json, priority, always_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(story_id, entry_id) DO UPDATE SET
                     entry_type = excluded.entry_type,
                     name = excluded.name,
                     description = excluded.description,
                     trigger_keys_json = excluded.trigger_keys_json,
                     priority = excluded.priority,
                     always_active = excluded.always_active""",
                (
                    story_id, entry_type, entry_id, name, description,
                    json.dumps(trigger_keys, ensure_ascii=False),
                    priority, 1 if always_active else 0, now,
                ),
            )
            await db.commit()

    async def list_world_book_entries(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM world_book_entries WHERE story_id = ? ORDER BY priority DESC, entry_type, name",
                (story_id,),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["trigger_keys"] = json.loads(d.pop("trigger_keys_json", "[]"))
                d["always_active"] = bool(d.get("always_active"))
                result.append(d)
            return result

    async def clear_world_book(self, story_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM world_book_entries WHERE story_id = ?", (story_id,))
            await db.commit()
