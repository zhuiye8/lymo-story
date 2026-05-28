# Phase Report: Phase 0 · Eval Baseline (Report #7)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-27 |
| Phase | Phase 0 · Evaluation Baseline (v2.3) |
| Status | green |
| Related | Report #6；Review #6 (`decisions/2026-04-27-phase-0-report-6-review.md`，accepted-with-corrections) |
| PM action needed | yes（AC2-final 监督独立评分 + AC3 final 标签 + AC5 UI 启动批准） |

## Summary

Review #6 全部 3 项 corrections + 4 项 decisions 已应用：

| 项 | 类别 | 行动 | 结果 |
|---|---|---|---|
| 1 | AC5 heatmap 漏"整章 8 行全 miss" | 从 `chapter_quality_evaluations` 推 expected chapters，每章必须有全 8 dim；missing/incomplete 都返回 ready=false | ✅ 修；regression 测试覆盖 |
| 2 | AC5 distribution 只校验 evals | 现 `evaluations_complete AND scores_complete`，failure reason 含 expected/actual 计数 | ✅ 修；regression 测试覆盖 |
| 3 | Phase-gate AC3 wording 仍 100+50+50 | v2.3 升级，AC3 sample 描述 + 标准 + Evaluation sample 三处同步；新增 `precision_pd_excerpt ≥ 0.7`；删除 "human-written" | ✅ |
| 4 | AC5 UI 启动等修 #1+#2 | 等监督批准（修完了） | 🟡 等监督 |
| 5 | AC3 final-labelled 等监督选 | 数据已 ready；等监督抽样或接受 source_url provenance | 🟡 等监督 |
| 6 | AC2-final 监督评 | artifact 等监督 | 🟡 等监督 |
| 7 | opencc 处理 | 写 `scripts/build_wikisource_pd_corpus.py`（reproducible builder）+ 加 `opencc-python-reimplemented` 到 `[dev]` | ✅ |

## Completed since Report #6

### 1. AC5 heatmap readiness（Review §"AC5 heatmap readiness misses whole missing chapters"）

**根因**：旧实现只对 `chapter_quality_scores` 表里出现过的 chapter 检查"该章是否有全 8 dim"。如果某 chapter 的 8 行 score 全部缺失，那它根本不在 `by_chapter` dict 里，`incomplete` 就是空的 → endpoint 假性 `data_ready=true` 返回 truncated 矩阵。

**改文件**：`backend/api/quality_admin.py::get_heatmap()`

```python
# 新增：从 evaluations 表推权威 chapter list
expected_chapters = [r["chapter_num"] for r in
    chapter_quality_evaluations WHERE batch=batch_id AND story_id=story_id]

# 然后逐 chapter 对账：
for c in expected_chapters:
    dims_for_c = by_chapter.get(c, {})
    if not dims_for_c:
        missing_chapters.append(c)        # 整章 8 行全 miss
    else:
        missing = [d for d in DIMENSIONS if d not in dims_for_c]
        if missing:
            incomplete_chapters[c] = missing  # 该章漏几个 dim

if missing_chapters or incomplete_chapters:
    return ready=False with detailed reason
```

Failure reason 示例：
```
heatmap requires every expected chapter (from chapter_quality_evaluations)
to have all 8 dimensions in chapter_quality_scores;
1 chapter(s) entirely absent from scores: [2]
```

### 2. AC5 distribution readiness（Review §"distribution ignores score-table completeness"）

**根因**：`per_dimension_histograms` 来自 `chapter_quality_scores`，但 readiness gate 只检查 evaluations 完整。

**改文件**：`backend/api/quality_admin.py::get_distribution()`

```python
if not (cov["evaluations_complete"] and cov["scores_complete"]):
    gaps = []
    if not cov["evaluations_complete"]:
        gaps.append(f"chapter_quality_evaluations={N} != scope_chapter_count={S}")
    if not cov["scores_complete"]:
        gaps.append(f"chapter_quality_scores={M} != expected={S*8} (S × 8 dims)")
    return ready=False, reason="...; ".join(gaps)
```

### 3. 7 个新回归测试（**新文件** `tests/test_quality_admin_readiness.py`）

每个测试构造一个临时 SQLite DB 注入特定形态的不完整数据，然后通过 `TestClient` 验证 endpoint 行为：

| 测试用例 | 验证 |
|---|---|
| `test_complete_chapter_returns_ready` | 1 章 × 8 dim 完整 → ready=true（sanity） |
| **`test_chapter_entirely_missing_from_scores`** | **2 章 evals + 仅 1 章 8 dim scores → ready=false，reason 含 chapter 2** |
| `test_chapter_missing_some_dims` | ch1 缺 continuity 维度 → ready=false，reason 含 "continuity" |
| `test_no_evaluations_for_story` | story 无 evaluation 行 → ready=false，reason 含 "evaluations" |
| `test_evaluations_and_scores_both_complete` | distribution sanity → ready=true |
| **`test_evaluations_complete_but_scores_partial`** | **evals 完整但 scores 仅 1/2 章 → ready=false，reason 含 "scores"+"expected"+具体 16/8 计数** |
| `test_evaluations_missing` | evals=0 → ready=false，reason 含 "evaluations" |

**结果**：
```
$ pytest tests/ -v
24 passed in 8.94s
（17 delta + 7 readiness）
```

包括 live-DB consistency check（验 endpoint 与 baseline_report 的 −0.3723 一致）。

### 4. Phase-gate v2.2 → v2.3（Review §"Phase gate should reflect AC3 v5 evidence standard"）

**改文件**：

| 文件 | 改动 |
|---|---|
| `phase-gate.md` header | v2.2 → v2.3，加 `v2.3 changes` 行 |
| `phase-gate.md` AC3 行 | "100+50+50 + recall≥0.8 + precision_overall≥0.7 + precision_fiction≥0.7" → "**100 slop + 50 generic-normal + 50 project-accepted fiction-normal（engineer_synthetic）+ 21 public_domain_excerpt（wikisource source-verifiable）**" + "recall≥0.8 + precision_overall≥0.7 + **precision_fiction_mixed≥0.7** + **precision_pd_excerpt≥0.7**"；显式标注"**禁用 'human-written' 表述（除非真补独立人写样本）**" |
| `phase-gate.md` Evaluation sample 行 | 同步至 v5 三子集 |
| `phase-gate.md` 文件清单注释 | slop_samples_zh.json 注释升 v5 |
| `change-log.md` | 追加 v2.3 段，列 5 项改动来源（Report #5/#6 reviews） |

### 5. opencc 路径选 (1)：reproducible builder + dev dep（Review §"opencc decision"）

监督给的两条路：
- (1) commit a reproducible Wikisource sample builder script + add to dev deps
- (2) document `slop_samples_zh.json` is a static audited corpus

工程师选 **(1)**，理由：将来若 wikisource 修订或想加新作者，可一行命令重跑（`python scripts/build_wikisource_pd_corpus.py --merge`）；监督审阅时可亲自跑 builder 验证 21 条段落能从 wikisource 重现。

**新文件**：`scripts/build_wikisource_pd_corpus.py`（≈230 行）

- 21 个 hard-coded `(author, death_year, work, url)` targets（从 `_tmp_fetch_wikisource_pd.py` 升级，加完整 docstring + argparse + `--merge` 模式）
- 每条带 docstring 的 verification path（点 URL 即可看到原文）
- `--merge` 模式：自动替换 `slop_samples_zh.json` 的 PD 部分，保留 `engineer_synthetic`
- import-time 检测 opencc 缺失，给清晰的 install 提示

**改文件**：`pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    # AC3 corpus builder: traditional→simplified conversion for
    # zh.wikisource.org public-domain excerpts.
    # Used by scripts/build_wikisource_pd_corpus.py.
    "opencc-python-reimplemented>=0.1.7",
]
```

**实测重现**：

```bash
$ python scripts/build_wikisource_pd_corpus.py
[OK]  朱自清    《背影》              134 chars
[OK]  朱自清    《荷塘月色》          113 chars
... (跳过中间)
[OK]  鲁迅      《好的故事》          61 chars
[OK]  胡适      《差不多先生傳》       81 chars
[OK]  林徽因    《九十九度中》         66 chars
[OK]  蔡元培    《就任北京大學校長之演說》 98 chars

Fetched 21 excerpts → data/baselines/_pd_excerpts_draft.json
```

幂等：再跑一次拿到的是同样的 21 条（除非 wikisource 自身修订了）。

## AC3 v5 calibration 结果（重测，证 Report #6 review 接受的数字仍站得住）

```
$ python scripts/calibrate_slop_detector.py --threshold 0.5
detector: slop-v1
slop=100, normal_generic=50, normal_fiction=71 (50 synthetic + 21 wikisource_pd)
TP=97  FN=3  FP=3  TN=118
recall=0.9700  precision_overall=0.9700
precision_generic=1.00  precision_fic_synthetic=1.00  precision_fic_pd_excerpt=0.9700
AC3 PASS (overall): True
AC3 PASS (fiction-mixed): True
AC3 PASS (pd_excerpt only, independent): True
```

3 条 PD FP 仍是 `仿佛`（朱自清《歌声》、鲁迅《祝福》《雪》），detector v1.1 frequency-aware tier1 已批 Phase 1 backlog。

## Files changed since Report #6

| 文件 | 类型 | 说明 |
|---|---|---|
| `backend/api/quality_admin.py` | 修订 | heatmap 从 evaluations 推权威 chapter list；distribution 同时校验 scores 完整 |
| `tests/test_quality_admin_readiness.py` | **新增** | 7 个 readiness 回归测试 |
| `workspace/plans/.../phase-gate.md` | 修订 | v2.2 → v2.3；AC3 wording 升 v5；Evaluation sample/文件清单同步 |
| `workspace/plans/.../change-log.md` | 修订 | 追加 v2.3 段 |
| `scripts/build_wikisource_pd_corpus.py` | **新增** | 上面 `_tmp_fetch_wikisource_pd.py` 的正式版 + `--merge` 模式 |
| `pyproject.toml` | 修订 | 加 `opencc-python-reimplemented>=0.1.7` 到 dev deps |

## Verification

```
✓ python -m compileall -q backend scripts
✓ pytest tests/                                  → 24 passed
  ├─ test_quality_admin_delta.py   17 passed
  └─ test_quality_admin_readiness.py 7 passed
✓ python scripts/calibrate_slop_detector.py
  → recall=0.97, precision_overall=0.97, precision_pd_excerpt=0.97
  → AC3 PASS (pd_excerpt only, independent): True
✓ python scripts/build_wikisource_pd_corpus.py
  → 21 excerpts re-fetched, idempotent
✓ FastAPI TestClient (live DB):
  - /trend, /by-dimension, /distribution → ready=true
  - /heatmap?story_id=61513478 → ready=true
  - /heatmap?story_id=bc910038 → ready=true
  - /heatmap?story_id=ff5408f9 → ready=true
✓ DB existing batches 1/2 unchanged (immutable audit trail preserved)
```

## Updated AC matrix

| AC | 标准 | 实测 | Status |
|---|---|---|---|
| AC1 | scope×8 严格全覆盖 | 168/168 | ✅ Pass |
| AC1b | scope 严格全覆盖 | 21/21 | ✅ Pass |
| AC2-bootstrap | 5 章 per-dim ρ | mean=0.45 | ✅ Done |
| **AC2-final** | 监督独立评 1 章 | artifact 等监督 | 🟡 等监督 |
| **AC3** | recall≥0.8 + precision_overall/fiction_mixed/pd_excerpt 各≥0.7 | 0.97 / 0.97 / 0.97 / 0.97 | 🟡 **数据满足，等 final 标签** |
| AC4 | mean cost ≤ ¥0.10 | ¥0.055 | ✅ Pass |
| **AC5** | 4 图表 contract + 严格 readiness（heatmap from evals + distribution scores+evals） | backend 5 endpoints + 24 回归测试，UI 等监督批 | 🟡 backend done |
| AC6 | mean / variance / stdev / trend（算法 A 锁定） | 含；live-DB regression 通过 | ✅ Pass |

## Asks（监督决策点）

1. **AC2-final 评分**（Phase 0 收口的唯一硬阻塞）：artifact `data/baselines/ac2-final-calibration-batch-2.json`
2. **AC3 final 标签**：phase-gate v2.3 的 wording 已按监督要求修。监督是否：
   - (a) 抽样 3-5 个 wikisource URL 验真后 → AC3 final pass
   - (b) 接受 source_url + `_raw_traditional` provenance + reproducible builder script 作为 Phase 0 充分证据 → AC3 final pass
   - (c) 仍要求其他 → 工程师补
3. **AC5 frontend UI 启动**：监督说 #1+#2 修完后才能开 UI。已修 + 7 readiness 回归测试覆盖 + 实测三 story heatmap 都 ready。监督批准启动 UI？

## Default if no answer

- 2026-04-30 23:59 前监督未回 → 工程师按以下默认推进：
  - (1) AC2-final：等监督，**不擅自代填**
  - (2) AC3 final：维持当前状态，不擅自再调
  - (3) AC5 UI：启动实现（contract 已锁、backend readiness 严格、24 回归测试就位）
- 工程师在 inbox 留 `[Auto-Executed]` 报告

## What's Next

按 phase-gate v2.3，剩余阻塞 Phase 0 → Phase 1 收口的项：
- **AC2-final 监督独立评分**（硬阻塞）
- AC3 final 标签（数据已满足）
- AC5 UI（监督批准则启动）

Phase 0 评测基础设施完整：
- 5 张表 + 5 quality 模块 + 5 endpoints + 24 回归测试
- AC3 三子集（100 + 50 generic + 50 fiction synthetic + **21 wikisource PD**）
- AC6 全度量 + canonical algorithm 锁定 + live-DB regression
- AC5 readiness 严格化（heatmap 按 evals 推、distribution 双校验）
- opencc 路径产品化（`scripts/build_wikisource_pd_corpus.py` + dev dep）

监督做完 AC2-final 后，Phase 0 立即可收口，进 Phase 1（SceneCard + anti-cliché judge prompt + detector v1.1 frequency-aware tier1）。
