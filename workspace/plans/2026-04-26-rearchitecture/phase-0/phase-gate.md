# Phase Gate: Phase 0 · Evaluation Baseline (v2.3)

| Field | Value |
|---|---|
| Phase | Phase 0 · Evaluation Baseline |
| Author | engineer (Claude) |
| Date | 2026-04-26（v2.3 修订 2026-04-27） |
| Version | **v2.3**（详见 `change-log.md`） |
| Estimated duration | 1.5 周（约 8-10 工作日） |
| Cost ceiling | LLM ¥50 + 工程师时间 2 周 |
| Status | approved；执行中（Phase 0 收口阻塞于 AC2-final 监督独立评分） |
| Supersedes | v1 (rejected) → v2 (proposal.md，superseded) → v2.1 → v2.2 → **v2.3 (this)** |
| v2.2 changes | scope_chapter_count 动态化（删 24/192 硬编码）；AC3 双子集 (100+50+50)；DETECTOR_VERSION 单一源（slop-v1）；partial_warning 不再算 pass。源：Report #2/#3/#4 reviews. |
| v2.3 changes | AC3 升级 v5 三子集（100 slop + 50 generic + 50 project-accepted fiction + **21 wikisource public_domain_excerpt**）；标准加 `precision_pd_excerpt ≥ 0.7`；禁用"human-written"表述（除非真补独立人写样本）；AC5 readiness 严格化（heatmap 按 evaluations 推 expected chapters；distribution 同时校验 evaluations 和 scores 完整）。源：Report #5/#6 reviews. |

## One-Sentence Goal

为 Story Engine 建立一套**项目本地的中文小说自动评测基线（SEQR v0）**，对当前数据库中所有已生成章节做基线评分入库（基线 batch 实测 21 章），使后续每个 Phase 可在历史数据上做内部纵向对比。

> **v2.2 修正（Report #3 review）**：删除"24 章"硬编码 —— 实际章节数由 `chapters` 表当时存量决定（基线 batch 2 = 21 章 = 9 + 8 + 4）。所有 AC 改用 `evaluation_batches.scope_chapter_count` 动态校验，不再固定 24 / 192。

## Non-Goals

- 不优化任何写作 prompt（属 Phase 1）
- 不改 KG / WorldBook / LayeredMemory（属 Phase 2）
- 不引入新的 critic / writer agent（属 Phase 1+）
- 不修改 init pipeline 或 chapter graph
- 不做读者人群模拟（属 Phase 6）
- **不冒用论文命名**：本 rubric 命名为 SEQR v0，不声称是 WebNovelBench 或 HNES
- **不和外部 leaderboard 对齐**：仅做内部纵向对比

## Artifact Schema

### 命名澄清（v2 新增）

> **SEQR v0**（Story Engine Quality Rubric, version 0）— 项目本地评测体系。
> 维度借鉴自 WebNovelBench [verified:2026-04-26:https://arxiv.org/html/2505.14818] 和 autonovel anti-slop [verified:2026-04-26:https://github.com/NousResearch/autonovel/blob/master/evaluate.py]，但**适配单章中文场景**。
> 不实现 CreAgentive HNES 公式（HNES 需要 human eval pipeline，Phase 0 没有）。
> 不复现 WebNovelBench 的 PCA+ECDF 长篇分布对齐（目标错位）。

### SEQR v0 八维度

| # | 维度 | 中文名 | 借鉴来源 |
|---|---|---|---|
| 1 | `fluency` | 语言流畅度 | 通用 |
| 2 | `dialogue_distinct` | 对白独特性 | WebNovelBench D4 |
| 3 | `character_consistency` | 角色一致性 | WebNovelBench D5 |
| 4 | `scene_drama` | 场景戏剧性 | autonovel anti OVER-EXPLAIN/REDUNDANT |
| 5 | `sensory_detail` | 感官描写 | WebNovelBench D2 |
| 6 | `rhetoric_quality` | 修辞质量（避免烂用比喻） | WebNovelBench D1 + 中文本地化 |
| 7 | `continuity` | 跨场景衔接 | WebNovelBench D8 |
| 8 | `overall_readability` | 整体可读性 | 通用 |

每维度 0-10 分。

### SEQR Composite Score

```
SEQR_composite = mean(8 dimension scores) - slop_penalty

其中 slop_penalty 0-3 分（最多扣 30%）
```

**等权简单可解释**，不引入 AHP 权重（避免凭感觉调权值）。如未来需要 AHP，作为 Phase 0 v3 单独提案。

### 数据库 5 张表（v2.1：加 evaluation_batches 隔离）

> **v2.1 新增（监督要求）**：每次"跑一次基线"是一个独立 batch，AC1/AC1b 必须按 batch 过滤；等式按 `scope_chapter_count` 动态计算（v2.2 删除固定 192/24 的旧表述）。

```sql
-- (0) 评测批次（v2.1 新增）
CREATE TABLE evaluation_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_label TEXT NOT NULL UNIQUE,    -- 例 "phase0-baseline-2026-04-30"
  rubric_version TEXT NOT NULL,        -- "SEQR-v0"
  judge_model TEXT NOT NULL,
  judge_options_json TEXT,
  detector_version TEXT NOT NULL DEFAULT 'slop-v0',
  description TEXT,
  scope_story_ids TEXT NOT NULL,       -- JSON 数组，本 batch 覆盖的 story
  scope_chapter_count INTEGER NOT NULL,-- 期望章节总数（AC1 等式依据）
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT DEFAULT 'running'        -- running / completed / aborted
);

-- (1) 单章每维度评分（明细）
CREATE TABLE chapter_quality_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evaluation_batch_id INTEGER NOT NULL,    -- v2.1 新增
  story_id TEXT NOT NULL,
  chapter_num INTEGER NOT NULL,
  source_version_id INTEGER,
  dimension TEXT NOT NULL,
  score REAL NOT NULL,
  evidence TEXT,
  judge_run_id INTEGER NOT NULL,
  judged_at TEXT NOT NULL,
  rubric_version TEXT NOT NULL DEFAULT 'SEQR-v0',
  FOREIGN KEY (evaluation_batch_id) REFERENCES evaluation_batches(id),
  FOREIGN KEY (judge_run_id) REFERENCES judge_runs(id),
  UNIQUE (evaluation_batch_id, story_id, chapter_num, dimension)
);
CREATE INDEX idx_quality_batch ON chapter_quality_scores(evaluation_batch_id, story_id, chapter_num);
CREATE INDEX idx_quality_dim ON chapter_quality_scores(dimension);

-- (2) 单章聚合评分
CREATE TABLE chapter_quality_evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evaluation_batch_id INTEGER NOT NULL,    -- v2.1 新增
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
  FOREIGN KEY (evaluation_batch_id) REFERENCES evaluation_batches(id),
  FOREIGN KEY (judge_run_id) REFERENCES judge_runs(id),
  UNIQUE (evaluation_batch_id, story_id, chapter_num)
);
CREATE INDEX idx_eval_batch ON chapter_quality_evaluations(evaluation_batch_id, story_id, chapter_num);

-- (3) slop 检测发现项
CREATE TABLE slop_findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evaluation_batch_id INTEGER NOT NULL,    -- v2.1 新增
  story_id TEXT NOT NULL,
  chapter_num INTEGER NOT NULL,
  source_version_id INTEGER,
  category TEXT NOT NULL,
  hits_json TEXT NOT NULL DEFAULT '[]',
  raw_score REAL NOT NULL,
  weighted_penalty REAL NOT NULL,
  detected_at TEXT NOT NULL,
  detector_version TEXT NOT NULL DEFAULT 'slop-v0',
  FOREIGN KEY (evaluation_batch_id) REFERENCES evaluation_batches(id)
);
CREATE INDEX idx_slop_batch ON slop_findings(evaluation_batch_id, story_id, chapter_num);

-- (4) 评测运行（成本 + 模型审计）
CREATE TABLE judge_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evaluation_batch_id INTEGER NOT NULL,    -- v2.1 新增
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
  finished_at TEXT,
  FOREIGN KEY (evaluation_batch_id) REFERENCES evaluation_batches(id)
);
CREATE INDEX idx_judge_batch ON judge_runs(evaluation_batch_id);
```

**Batch 用法**：
```
1. 跑一次基线 → INSERT evaluation_batches (batch_label='phase0-baseline-YYYY-MM-DD', ...)
2. 拿到 batch_id；该 batch 内所有 runs / scores / evaluations / slop 都带此 id
3. AC1/AC1b 必须 WHERE evaluation_batch_id = <baseline batch>
4. 重跑（如换 judge model）创建新 batch，不污染老数据
```

### Pydantic 评测器输出

```python
class DimensionScore(BaseModel):
    dimension: Literal["fluency","dialogue_distinct","character_consistency",
                       "scene_drama","sensory_detail","rhetoric_quality",
                       "continuity","overall_readability"]
    score: float = Field(ge=0, le=10)
    evidence: str

class ChapterEvaluation(BaseModel):
    story_id: str
    chapter_num: int
    rubric_version: str = "SEQR-v0"
    dimension_scores: list[DimensionScore]      # 8 项
    mean_quality: float
    slop_penalty: float                          # 0-3
    composite_score: float                       # = mean - slop_penalty
    word_count: int
    judge_model: str
    judge_cost_cny: float
    evaluated_at: datetime
```

### 文件产物

```
backend/quality/
├── __init__.py
├── seqr_judge.py           # 8 维度 LLM 评测器（重命名后）
├── slop_detector.py        # 反 AI 味机械检测
├── composite.py            # SEQR composite 计算（重命名后）
└── samples_zh.py           # 中文 slop 样本辅助函数

data/baselines/
├── slop_samples_zh.json    # v5 schema: 100 LLM slop + 50 generic-normal + 50 project-accepted fiction + 21 wikisource public_domain_excerpt（per-sample provenance fields）
└── baseline_report_2026-04-XX.md
```

前端：`frontend/app/stories/[id]/insights/quality/page.tsx`（新 Tab，4 个图表）

## Acceptance Criteria

每条都含**样本来源 + 样本量 + 指标 + 阈值**。

| # | Criterion | Method | Pass | Fail / Rollback Trigger |
|---|---|---|---|---|
| AC1 | 基线 batch 内 **scope_chapter_count** 章全部 8 维度评分入库（明细） | `SELECT COUNT(*) FROM chapter_quality_scores WHERE evaluation_batch_id = :baseline_batch_id` | **= scope_chapter_count × 8**（严格 100%） | `< 严格目标` 即视为不通过；< 90% × 8 触发 partial_warning |
| AC1b | 基线 batch 内 **scope_chapter_count** 章全部聚合记录入库 | `SELECT COUNT(*) FROM chapter_quality_evaluations WHERE evaluation_batch_id = :baseline_batch_id` | **= scope_chapter_count**（严格 100%） | `< 严格目标` 即视为不通过；< 90% 触发 partial_warning |
| **AC2-bootstrap** | LLM 评分 vs 工程师自评，**per-dimension** Spearman ρ | 工程师评 5 章 × 8 维度 → **每维度 5 配对** | **info-only**（不阻塞 phase）；记录每维度 ρ；ρ < 0.3 的维度需在 v0.1 调整 | 不阻塞 phase |
| **AC2-final** | 监督独立评 1 章 × 8 维度 vs LLM 评分（必须 gate，不可降级） | 监督评 1 章 8 维度；产物保存到 `data/baselines/ac2-final-calibration-<batch>.json` 含：chapter_id / rubric / human_scores / llm_scores / supervisor_conclusion | 监督主观判断"评分对该章的相对排序合理" + 产物已保存 | 监督判断不合理 OR 产物缺失 → 调维度或换 judge |
| AC3 | slop_score 中文化召回 + 精度（**v5 三子集**，禁用 "human-written" 表述） | **100 slop + 50 generic-normal + 50 project-accepted fiction-normal（engineer_synthetic）+ 21 public_domain_excerpt（wikisource source-verifiable）** | recall ≥ 0.8 **且** precision_overall ≥ 0.7 **且** precision_fiction_mixed ≥ 0.7 **且** precision_pd_excerpt ≥ 0.7（独立非合成 stress 必须独立达标） | recall < 0.5 或 precision_overall < 0.5 → slop 降级可选 |
| AC4 | 单章评测 LLM 成本（基线 batch 实测均值） | `SELECT AVG(total_cost_cny) FROM judge_runs WHERE evaluation_batch_id = :baseline_batch_id` | mean ≤ ¥0.10/章 | mean > ¥0.20/章 → 切便宜 judge |
| AC5 | 前端 4 图表正常 | 手动验证：趋势/对比/热区/分布 | 全部正常 + 数据一致 | 缺失任一 |
| AC6 | 基线报告产出 | `data/baselines/baseline_report_*.md` | 文件存在 + 含每本 mean / variance（pvariance）/ stdev（pstdev）/ trend（slope + 前后半段差） | 缺失或空白；若仅报 stdev 不报 variance（或反之）必须显式声明用词，否则视为不达标 |

**关键变化（v2）**：AC2 拆为 bootstrap（info）+ final（gate）。bootstrap 不阻塞 phase；final 由监督单点判断。

## Evaluation Method

| Item | Value |
|---|---|
| Judge model | DeepSeek-V4-Pro 关思考（**仅用于 PoC**；监督决策：AC2 修订前不锁定） |
| Evaluation sample | scope_chapter_count 章（基线 batch 实测 21 章）+ 100 LLM slop + 50 generic-normal（engineer_synthetic）+ 50 project-accepted fiction-normal（engineer_synthetic）+ 21 public_domain_excerpt（wikisource HTML 抽取 + opencc t2s） |
| Human calibration | (1) AC2-bootstrap：工程师 5 章自评（per-dim Spearman，info-only）<br>(2) AC2-final：监督独立 1 章评（gate） |
| Automated metrics | SEQR v0 八维度 + slop_score 中文版 + composite |
| Evaluation frequency | Phase 0 一次性跑全 scope_chapter_count 章（实测 21 章）；Phase 1+ 接入 chapter_graph 自动评 |
| Estimated evaluation cost | scope_chapter_count × ¥0.05（实测 21 章 = ¥1.16）；含校准 ≈ **¥3-5** |

## Cost Bound

| Category | Estimate | Ceiling | Warning threshold |
|---|---|---|---|
| LLM 评测调用（Phase 0 内） | ¥3 | ¥20 | ¥15 |
| LLM 校准对照（多模型） | ¥10 | ¥30 | ¥25 |
| 工程师时间 | 1.5 周 | 2 周 | 12 工作日 |
| 中文 slop 样本建设 | 6h | 10h | 8h |

总现金成本上限：**¥50**。
总时间上限：**2 周**。

## Rollback / Exit Conditions

| Trigger | Action |
|---|---|
| AC2-final 监督判断不合理 | 1) 调整 SEQR 维度定义；2) 换 judge model；3) 仍失败 → Phase 0 暂停，重新设计 rubric |
| AC2-bootstrap 多维度 ρ < 0.3 | **不阻塞 phase**；记录到 baseline_report 作为 v0.1 优化输入 |
| AC3 失败 | 1) 中文样本扩到 200 条重训；2) 用 LLM-as-judge 替代部分规则；3) 仍失败 → slop 降级可选 |
| AC4 失败（成本 > ¥0.20/章） | 切到 DeepSeek-V4-Flash 关思考 ≈ ¥0.02/章，AC2-final 重做 |
| 现金成本超 ¥30 | 立即暂停，向 PM 申请追加预算 |
| 工程师时间超 2 周 | 立即暂停，重新评估剩余范围 |
| Supervisor stops phase | 按 inbox 指令执行；保留已生成评分作为历史 |

**Git tag 策略**：`pre-phase-0` / `post-phase-0`；DB 备份 `data/story.db.bak_pre-phase-0_<ts>`

## Dependencies

| Dependency | Type | Evidence |
|---|---|---|
| WebNovelBench 8 维度论文 | external paper | [verified:2026-04-26:https://arxiv.org/html/2505.14818] — 已亲查论文确认 8 维度 |
| autonovel slop_score 函数 | external code | [verified:2026-04-26:https://github.com/NousResearch/autonovel/blob/master/evaluate.py] |
| CreAgentive HNES（说明为何不用） | external paper | [verified:2026-04-26:https://arxiv.org/html/2509.26461] |
| DeepSeek-V4-Pro 评委可用性 | model API | [verified:2026-04-26:本地端到端测试] |
| 现有 chapters / chapter_versions 表 | internal | [verified:2026-04-26:backend/storage/sqlite_store.py] |
| 现有 LangGraph chapter pipeline | internal | [verified:2026-04-26:backend/graph/chapter_graph.py] |
| LiteLLM 统一接入层 | internal | [verified:2026-04-26:backend/llm/client.py] |
| API key 已从源码移除 | internal fix | [verified:2026-04-26:scripts/test_deepseek_v4.py 改为 env var] |
| delete-from-chapter N>1 已禁用 | internal fix | [verified:2026-04-26:backend/api/stories.py 返回 400] |

**v1 → v2**：v1 的 WebNovelBench 维度名 + HNES 公式标 [needs-review]。v2 已亲查两篇论文，升级为 [verified]，并据此**重命名为本地 SEQR v0**（不冒用论文名）。

## Standing Decisions Touched

| ID | 关系 |
|---|---|
| `arch-001` editorial office | ✅ 一致 |
| `process-001` evaluation first | ✅ 一致（本 Phase 是该决议的强制实现） |

## Ask

请监督逐项决议：

1. **整体 v2**：approve / approve-with-conditions / revision-needed / reject
2. **重命名为 SEQR v0 + 不冒用论文名**：是否接受 Option 2？还是要求实现论文真维度+权重（Option 1）？
3. **AC2-final 由监督评 1 章**：监督是否接受这一负担？或选 (a) Qwen3-235B 当金标准、(b) 工程师评 + 显式标 bootstrap-only 不做 final gate
4. **Judge LLM**：仍用 DeepSeek-V4-Pro 关思考做 PoC（按上次 review 决策）；正式锁定推到 AC2-final 通过后
5. **删除 N>1 安全 rewind**：v2 已禁用 N>1，是否单开提案做 per-chapter snapshot？还是接受现状（用户用 chapter version restore）？

## Default If No Review

> **v2.1 已 approve-with-conditions**（`decisions/2026-04-26-phase-0-v2-review.md`），本节 Default 仅适用于"已开工后监督突然失联"的边缘情形。
> AC2-final 不可降级为 bootstrap-only（监督已明确 reject）。

```text
Default action: 持续按 approve-with-conditions 推进 Phase 0
  - 5 条开工前条件 100% 应用
  - AC2-final 必须等到监督评分；不允许 bootstrap-only fallback
  - 如评分阻塞超 5 工作日，工程师可继续完成 AC1/AC3/AC4/AC5/AC6
    但不能声称 Phase 0 出口（need AC2-final + AC1）
Rollback cost: low（评分可重跑）
Post-action notice:
  - inbox/from-engineer/<date>-report-auto-executed-phase-0-v2.md
  - supervision-board.md 同步状态
```
