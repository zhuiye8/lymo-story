# Phase 1 — 章节重写（重写最新推进单元）施工规划

> 状态：✅ 已实现并验证（2026-06-01）。4 层全部落地：L1 清理方法 / L2 graph 重写模式（purge 节点）/ L3 API（rewrite-latest[/info]）/ L4 前端（重写最新按钮 + 确认框）。
> 实测：重写最新单元（带修改意见）→ 完成、章号连续、installments_done 不 bump、无孤儿 记忆/四元组/质量 数据（DB 审计 VERDICT PASS）。
> 配套：`phase1/00-architecture.md` §章节循环、`phase1/02`(分页，若有)、根 `CLAUDE.md`
> 决策来源：与用户逐条确认

---

## 0. 范围与决策（已定）

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **重写单位** | **推进单元（installment）**，不是物理章 | 切分后 1 单元 = N 物理章，必须整单元一起重写 |
| **可重写范围** | **仅最新推进单元**（`installments_done == K`） | 它后面无依赖章 → 彻底消除"后续章地基被换"的级联难题；成本固定（只重跑 1 单元） |
| **修改意见** | **可选**（`revision_note`） | 有则追加"本次重写要求"，无则纯按原细纲换一稿 |
| **细纲** | **沿用原细纲**（`outline_detailed` 读回，跳过 outline_advance） | 剧情骨架不变，只改表达/强度 |
| **分镜 scene_plan** | **重跑** | 让修改意见能改变场景安排；细纲已锁剧情，分镜重排无害 |
| **清理时机** | **写成功后再清理**（write→paginate 之后、finalize 之前） | 先确保新内容生成成功，再删旧落新，危险窗口最小，无数据空洞 |
| **installments_done** | **不 bump** | 重写是重做当前单元，非推进新单元 |
| **chapter_num 起点** | **不变**（= 被删章的最小章号） | 物理章号连续，不留洞 |

---

## 1. 为什么"只重写最新单元"是正确边界

重写中间章 ch_k（后面有 ch_{k+1..n}）：后续章生成时**消费过** ch_k 产出的四元组 / 角色状态 / 记忆 / 摘要 / 伏笔。重写 ch_k 后，要么级联重写后续全部（订阅制成本灾难），要么留下事实矛盾——无解两难。

重写**最新**单元：它后面什么都没有，没有任何章依赖它 → 两难直接消失。剩下的（删旧数据、还原四元组、重跑）都有界、可控、可验证。

代价：想改前面某章，得先删掉其后章节让它变"最新"——符合写作直觉（回头改第 4 章，第 5 章本就该跟着重写）。UI 需明示，不偷偷级联。

---

## 2. 一个 installment 的全部数据写入（重写前必须清理的 7+2 类）

来源：`_persist_one`（`backend/graph/phase1_chapter.py`）。每个物理章写入：

| # | 数据 | 表/库 | 清理方式 |
|---|------|-------|---------|
| 1 | 正文+标题+摘要 | `chapters` | 按章号 DELETE（切分数会变，必删全部旧物理章再重落） |
| 2 | 细纲 | `outline_detailed` | 沿用 → 可保留（重落时覆盖同章号即可） |
| 3 | DOME 四元组（新增） | `knowledge_quads` | 删 `source_chapter ∈ 旧章号` |
| 4 | DOME 四元组（失效还原） | `knowledge_quads` | 把 `valid_to ∈ 旧章号` 还原成 NULL（仅最新单元能 invalidate 到这些章号，**无需加字段**，精确） |
| 5 | 角色状态 | `character_states` | 删 `chapter_num ∈ 旧章号`（last-write-wins，删后自然回落前章） |
| 6 | 分层记忆 | `memories` + ChromaDB | **双删**：先查旧章 memories 行拿 `vector_id` → 删 ChromaDB → 再删 SQLite 行 |
| 7 | 质量分 | `chapter_quality_scores` / `chapter_quality_evaluations` / `slop_findings` | 按章号 DELETE |
| A | 伏笔·埋的坑 | `foreshadowing` | 删 `planted_chapter ∈ 旧章号` |
| B | 伏笔·回收的坑 | `foreshadowing` | 把 `resolved_chapter ∈ 旧章号` 的 status 改回 `open`、resolved_chapter 置 NULL |

---

## 3. 排查到的隐患（务必在实现时守住）

- **坑 A 伏笔双向污染**（最隐蔽）：旧单元既"埋坑"又"回收坑"。埋的要删；回收的要**改回 open**（否则重写后这些坑永远显示已回收，但新正文已不回收）。→ 见 §2 表 A/B。
- **坑 B 向量库孤儿**：删记忆必须 **先 ChromaDB 后 SQLite**，否则先删 SQLite 就拿不到 vector_id，向量成孤儿被 recall 召回。`delete_by_version` 是 Phase-0 概念（按 source_version_id），Phase-1 要按 `mem_{id}` 列表删 → 新增 `delete_memories(ids)`。
- **坑 C 并发/重入**：重写前置 `status=writing` + 进度锁；重写中前端禁用"生成"和"重写"按钮；跑完复位。
- **坑 D installments_done 误进**：重写**绝不 bump**；chapter_num 起点不变。
- **坑 E 原子性/中途失败**：清理放在 write 成功**之后**（§0 已定），危险窗口仅"删旧+落新"这段连续执行。SQLite 跨连接无法严格原子，失败留日志可诊断 + status 出错态可重试。
- **坑 F 质量趋势连续性**：save_quality 按章号 DELETE+INSERT，覆盖同章号 → 趋势图自动更新，无需特殊处理 ✅。
- **坑 G 自我召回**：retrieve_memory 在清理前跑 → 会召回旧记忆。因清理时机定为"写后"（§0），接受此影响（记忆是情感连续性、非事实硬约束，影响极小；清理后旧记忆被新记忆取代）。

---

## 4. 流程设计（复用 chapter graph + 重写模式）

```
rewrite_latest(story_id, revision_note?):
  1. 前置校验：installments_done == K（是最新单元）；status 不在 writing；
     查出该单元物理章号区间 [start..end]（= chapters where installment_num==K）
  2. status=writing；progress.start（重写阶段标签）
  3. load_context（installment_num=K → 剧情位置与原一致）
  4. 沿用原细纲：从 outline_detailed 读回 detailed，跳过 outline_advance
  5. scene_plan（重跑，吃 revision_note）
  6. retrieve_memory（旧记忆仍在 → 接受，见坑 G）
  7. write_chapter（带可选 revision_note）→ paginate
  8. 【清理阶段 purge_installment([start..end])】：
     删 chapters / quads(source) / 还原 quads(valid_to) / character_states /
     memories(向量+SQLite) / foreshadowing(埋删+收还原) / quality
  9. finalize（重新逐物理章抽取+落库，chapter_num 从 start 起）
  10. status 复位（bible_ready）；**不 bump installments_done**
```

清理放第 8 步（write 后、finalize 前）：先确保新内容成功，再删旧落新。

---

## 5. 改动清单（施工预览）

**Store 新增**（`sqlite_store.py`，均按章号区间）：
- `get_installment_chapter_nums(sid, installment) -> list[int]`
- `delete_chapters(sid, nums)`
- `delete_quality(sid, nums)`（含 scores/evaluations/slop_findings）
- `delete_character_states(sid, nums)`
- `delete_foreshadowing_planted(sid, nums)` + `reopen_foreshadowing_resolved_at(sid, nums)`
- `get_memory_vector_ids(sid, nums)` + `delete_memories(sid, nums)`（SQLite 行）

**KnowledgeQuads 新增**（`knowledge_quads.py`）：
- `delete_by_source(sid, nums)`（删该单元新增的四元组）
- `restore_invalidated_at(sid, nums)`（valid_to ∈ nums → NULL）

**VectorStore 复用/新增**（`vector_store.py`）：
- 用 `mem_{id}` 列表删：`delete_memories(sid, vector_ids)`（或直接 collection.delete(ids=...)）

**LayeredMemory**（`layered_memory.py`）：
- `forget_chapters(sid, nums)`：聚合"查 vector_id → 删向量 → 删 SQLite 行"

**聚合**：`purge_installment(sid, nums)`（graph 内或 deps 编排，串起以上全部）

**Graph**（`phase1_chapter.py`）：
- `build_chapter_graph` 加重写模式：跳过 outline_advance（读回细纲）、retrieve 后 write、write 后 purge 再 finalize、不 bump
- 或单独 `build_rewrite_graph` 复用同名节点（倾向加参数复用，避免重复）

**prompt**（`chapter_prompts.py`）：
- `write_scene_prompt` 加可选 `revision_note` → "【本次重写要求】…"段

**API**（`phase1_stories.py`）：
- `POST /stories/{id}/rewrite-latest`，body `{revision_note?: str}`，后台任务；前置校验最新单元 + 非 writing

**前端**：
- 仪表盘 / 章节列表：「重写最新单元」按钮，显示将影响哪几章（如"将重写第 11–12 章"）+ 可选修改意见输入；重写中禁用生成/重写按钮，复用进度卡

**进度阶段**（`progress.py`）：
- 重写复用 CHAPTER_STAGES，或加一条"清理旧稿"阶段插在 paginate 与 finalize 之间

---

## 6. 验收点

- 重写后：物理章数可变（原 2 章 → 重写成 1 或 3 章），章号从 start 连续，无残留旧章
- `installments_done` 不变；剧情位置（粗纲阶段）不变
- 旧单元的四元组/状态/记忆（含向量）/质量全部清除；失效的更早四元组已还原 valid_to=NULL
- 旧单元埋的伏笔已删；旧单元回收的更早伏笔已改回 open
- ChromaDB 无孤儿向量（按 vector_id 抽查）
- 带 revision_note 时新稿明显响应该意见；不带时为原细纲的另一稿
- 重写中无法并发触发生成/二次重写；中途失败 status 可重试
- 质量趋势图章号连续、数值更新为新稿

---

## 7. 明确不做（v1 边界）

- 不支持重写非最新单元（需先删其后章节）
- 不做级联失效后续章
- 不做多版本保留/回滚（重写即覆盖，旧稿不留存）——如需"重写前备份"是后续增量
