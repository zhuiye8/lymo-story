# Phase Report: Phase 0 · Eval Baseline (Report #8)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-27 |
| Phase | Phase 0 · Evaluation Baseline (v2.3) |
| Status | green |
| Related | Report #7；Review #7 (`decisions/2026-04-27-phase-0-report-7-review.md`，accepted-with-corrections) |
| PM action needed | yes（AC2-final 监督独立评分 + AC3 final 标签 + AC5 UI 验收） |

## Summary

Review #7 全部 2 项 corrections 已修，外加监督批准的 **AC5 UI 已上线**：

| 项 | 类别 | 行动 | 结果 |
|---|---|---|---|
| 1 | Wikisource builder 部分 fetch 不能 silently 通过 | 加 `BuildResult` 三元组（drafts + failures + no-paragraph）；默认要求 100% 否则 exit 1；新增 `--allow-partial` flag（永禁 `--merge` 配合） | ✅ 4 个 CLI 行为测试覆盖 |
| 2 | merge churn 现有 PD IDs | 按 `source_url` 匹配现有 id；新 URL 才取 `max+1`；schema 记录 `id_stability.preserved/newly_assigned` | ✅ 4 个 ID 稳定性测试覆盖；live merge 实测 21/21 preserved + 0 newly_assigned |
| 3（监督批准）| AC5 UI 启动 | `frontend/app/admin/quality/page.tsx` + `admin-api.ts` 加 5 个 quality helper；`echarts-for-react` 渲染 4 图；从 `/admin` 顶部链接 | ✅ `pnpm run build` 通过（`/admin/quality` 静态预渲染） |

## Completed since Report #7

### 1. Builder fail-hard 模式（Review §"must fail hard on partial fetch"）

**改文件**：`scripts/build_wikisource_pd_corpus.py`

**新数据结构**：

```python
class BuildResult:
    drafts: list[dict]
    fetch_failures: list[(author, work, url, error)]
    no_paragraph: list[(author, work, url)]
    @property
    def is_complete(self) -> bool: return len(self.drafts) == len(TARGETS)
    def summary(self) -> str: ...  # 报告每个失败/无段落的目标
```

**CLI 行为**：

| 场景 | 旧行为 | 新行为 |
|---|---|---|
| 21/21 fetch | exit 0 + 写 draft | exit 0 + 写 draft（带 `_meta.complete=true`） |
| 20/21 fetch（默认） | **exit 0 + 写部分 draft**（沉默错误） | **exit 1**，stderr 报"only 20/21 fetched"，**不写 draft** |
| 20/21 fetch + `--allow-partial` | n/a | exit 0，写带 `_meta.complete=false` 的 debug draft |
| `--merge` + 部分 draft | 静默用部分数据 merge | 第一次检查时 exit 1（fail-hard gate）；defense-in-depth 二次检查 |
| `--merge --allow-partial` | n/a | 顶层立即 exit 2，`partial drafts must not rewrite the canonical corpus` |

**Draft schema 升级**：

```json
{
  "_meta": {
    "n_drafts": 20,
    "n_targets": 21,
    "complete": false,
    "fetch_failures": [{"author": "...", "work": "...", "url": "...", "error": "URLError: ..."}],
    "no_paragraph": [],
    "generated_at": "2026-04-27T..."
  },
  "drafts": [...]
}
```

下游工具（如未来的 calibrate 自动重新拉数）可读 `_meta.complete` 判断是否能信。

### 2. Stable IDs by source_url（Review §"merge must preserve stable sample IDs"）

**改文件**：`scripts/build_wikisource_pd_corpus.py::merge_into_corpus()`

**算法**：

```python
url_to_existing_id = {s.source_url: s.id for s in existing_pd}
used_nums = sorted({int(s.id.split("_")[-1]) for s in existing_pd})
next_free = max(used_nums) + 1  # for newly added URLs only

for draft in drafts:
    if draft.source_url in url_to_existing_id:
        sid = url_to_existing_id[draft.source_url]   # PRESERVE
    else:
        sid = f"normal_pd_{next_free:03d}"           # NEW
        next_free += 1
```

Schema 增量：

```json
"provenance_summary_v5.id_stability": {
  "preserved": 21,
  "newly_assigned": 0,
  "newly_assigned_pairs": []
}
```

**Live merge 实测**（重新跑 builder 21/21 + `--merge`）：

```
ID stability:
  preserved (matched by source_url): 21
  newly assigned: 0
```

`normal_pd_001..021` 完整序列保留；之前监督 review 引用的 FP IDs（`normal_pd_005`、`009`、`018` 即朱自清《歌声》、鲁迅《祝福》《雪》的 `仿佛`）依然有效。

### 3. Builder regression 测试（**新文件** `tests/test_wikisource_builder.py`）

11 个测试用例，4 类：

| 类 | 用例 | 验证 |
|---|---|---|
| `BuildResult` | `test_complete_is_true_when_all_targets_drafted` | `is_complete` 为真当 drafts == TARGETS |
| | `test_complete_is_false_when_any_target_missing` | 缺一个为假 |
| | `test_summary_lists_failures_and_no_paragraph` | summary 列出失败/无段落 |
| `MergeIDStability` | `test_existing_url_keeps_its_id` | URL 匹配 → id 保留；text 刷新 |
| | `test_new_url_gets_next_free_id` | 新 URL → max+1, max+2... |
| | `test_engineer_synthetic_entries_unchanged` | merge 不动 synthetic |
| | `test_id_stability_metadata_recorded` | schema 记录 preserved/newly 计数 |
| `CLIFailHard` | `test_complete_fetch_exits_zero` | 21/21 → exit 0 |
| | `test_partial_fetch_without_flag_exits_nonzero` | 部分 + 默认 → exit 1，无 draft 文件 |
| | `test_partial_fetch_with_allow_partial_writes_draft` | 部分 + `--allow-partial` → exit 0，draft 带 `complete=false` |
| | `test_merge_with_allow_partial_is_rejected` | 二者组合顶层 exit 2 |

CLI 测试通过 `subprocess.run` 跑 builder 子进程，注入 mock `build_drafts()` 返回任意 `(n_drafts, n_total)`，验证退出码 + 文件副作用。

**实测**：`pytest tests/test_wikisource_builder.py -v` → **11 passed**

完整测试套件：

```
$ pytest tests/ -q
35 passed, 1 warning in 7.87s
（17 delta + 7 readiness + 11 builder）
```

### 4. AC5 UI 启动（Review §"AC5 UI: approved to start"）

**新文件**：

| 路径 | 用途 |
|---|---|
| `frontend/app/admin/quality/page.tsx` | 质量仪表盘（≈340 行 client component） |
| `frontend/lib/admin-api.ts` 追加 | 5 个 quality API helper + 完整 TypeScript 类型 |
| `frontend/app/admin/page.tsx` 修订 | 顶部加 `质量仪表盘` 链接到 `/admin/quality` |

**架构**：

```
QualityDashboardPage (client)
├── batch picker (select)
├── ① 趋势 chart (TrendChart)            ← echarts line + per-story aggregates table
├── ② 对比 chart (ByDimensionChart)      ← echarts bar (per-story × 8 dim + 全部小说 group)
├── ③ 热区 chart (HeatmapChart)          ← echarts heatmap, story 选择驱动重新拉
└── ④ 分布 chart (DistributionChart)     ← echarts dual-grid bar (composite + slop histograms)
```

**关键设计**：

- 所有 4 个 endpoints 用 `Promise.all` 并发拉
- 任一 endpoint 返回 `data_ready=false` → 渲染 `<NotReady>` placeholder + 完整 `reason` 字符串（不模糊 fallback）
- Heatmap story 选择驱动单独的拉取（避免同时拉所有 story 的热图）
- 每个 batch picker option 显示 `#id label scope=N status`
- envelope 元数据（rubric_version / detector_version / judge_model）显示在右侧

**实测**：

```
$ pnpm run build
✓ Compiled successfully
Route (app)
├ ○ /admin
├ ○ /admin/logs
├ ○ /admin/quality   ← 新增，static prerendered

$ pnpm run lint  # 我的新文件 0 错（其他 131 个 pre-existing 错误未触动）
```

后端 readiness gate 已严格化（Report #6/7 修过），前端 placeholder 处理 `reason` 字段，监督要的"`data_ready=false` 作为硬 placeholder 状态"已实现。

## Files changed since Report #7

| 文件 | 类型 | 说明 |
|---|---|---|
| `scripts/build_wikisource_pd_corpus.py` | 重写 | `BuildResult` + fail-hard + `--allow-partial` + ID 稳定 merge |
| `tests/test_wikisource_builder.py` | **新增** | 11 个 builder regression 测试 |
| `frontend/lib/admin-api.ts` | 追加 | 5 个 quality helper + TypeScript 类型 |
| `frontend/app/admin/quality/page.tsx` | **新增** | 质量仪表盘页面 |
| `frontend/app/admin/page.tsx` | 修订 | 顶部链接到 `/admin/quality` |

## Verification

```
✓ python -m compileall -q backend scripts
✓ pytest tests/ -q                       → 35 passed
  ├─ test_quality_admin_delta.py     17 passed
  ├─ test_quality_admin_readiness.py  7 passed
  └─ test_wikisource_builder.py      11 passed
✓ python scripts/build_wikisource_pd_corpus.py --merge
  → 21/21 fetched, 21/21 IDs preserved, 0 newly_assigned
✓ python scripts/calibrate_slop_detector.py --threshold 0.5
  → recall=0.97, precision_overall=0.97, precision_pd_excerpt=0.97
  → AC3 PASS (pd_excerpt only, independent): True
✓ FastAPI TestClient: all 5 endpoints OK on batch 2
✓ pnpm run build                          → /admin/quality 静态预渲染
✓ pnpm run lint                           → 我的新文件 0 errors（pre-existing 131 未触动）
```

## Updated AC matrix

| AC | 标准 | 实测 | Status |
|---|---|---|---|
| AC1 | scope×8 严格全覆盖 | 168/168 | ✅ Pass |
| AC1b | scope 严格全覆盖 | 21/21 | ✅ Pass |
| AC2-bootstrap | 5 章 per-dim ρ | mean=0.45 | ✅ Done |
| **AC2-final** | 监督独立评 1 章 | artifact 等监督 | 🟡 等监督 |
| **AC3** | recall≥0.8 + precision_overall/fiction_mixed/pd_excerpt 各≥0.7 | 0.97 / 0.97 / 0.97 / 0.97 | 🟡 等监督 final 标签 |
| AC4 | mean cost ≤ ¥0.10 | ¥0.055 | ✅ Pass |
| **AC5** | 4 图表 contract + 严格 readiness + UI | backend 5 endpoints + 35 回归测试 + **frontend `/admin/quality` 上线** | 🟡 等监督验收 |
| AC6 | mean / variance / stdev / trend | 已含；live-DB regression 通过 | ✅ Pass |

## Asks（监督决策点）

1. **AC2-final 评分**（Phase 0 收口的唯一硬阻塞）
2. **AC3 final 标签**：现 v5 三子集（100 + 50 + 50 + 21）+ Path (b) builder 修完 + ID 稳定测试。监督是否：
   - (a) 抽样几个 wikisource URL 后接受 → AC3 final pass
   - (b) 接受 source_url + `_raw_traditional` + reproducible builder 作为 Phase 0 充分证据 → AC3 final pass
3. **AC5 UI 验收**：`/admin/quality` 路由可访问；监督是否：
   - (a) 启动 backend + frontend 浏览器实测后通过
   - (b) 仅审 build artifact + 测试 + 截图后通过

## Default if no answer

- 2026-04-30 23:59 前监督未回 → 工程师按以下默认推进：
  - (1) AC2-final：等监督，**不擅自代填**
  - (2) AC3 final：维持当前状态
  - (3) AC5 UI：维持当前 `/admin/quality` 实现，不擅自加 feature
- 工程师在 inbox 留 `[Auto-Executed]` 报告

## What's Next

按 phase-gate v2.3，Phase 0 → Phase 1 收口剩余项：
- **AC2-final 监督独立评分**（硬阻塞）
- AC3 final 标签
- AC5 UI 验收

Phase 0 评测基础设施完整：
- 5 张表 + 5 quality 模块 + 5 endpoints + **35 回归测试** + **AC5 UI 上线**
- AC3 三子集 + reproducible builder（fail-hard + ID 稳定）+ opencc dev dep
- AC6 全度量 + canonical algorithm + live-DB regression
- 工程师层面所有可控的 AC 都 ready，等监督最后 3 个动作即可收口进 Phase 1。
