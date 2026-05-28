# Phase Report: Phase 0 · Eval Baseline (Report #9)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-28 |
| Phase | Phase 0 · Evaluation Baseline (v2.3) |
| Status | green |
| Related | Report #8；Review #8 (`decisions/2026-04-27-phase-0-report-8-review.md`，accepted-with-corrections) |
| PM action needed | yes（AC2-final 监督独立评分 + AC5 UI smoke 验收） |

## Summary

Review #8 全部 lint 错误修完。监督上次确认了 **AC3 final pass for Phase 0**（wording: `source-verifiable public-domain excerpt precision`）。本轮工作集中在 AC5 UI 的 react-hooks lint 修复。

| 项 | 行动 | 结果 |
|---|---|---|
| 1 | quality 页面 `react-hooks/set-state-in-effect`（5 个 setter 同步在 effect body） | 重构为 freshness check：`envelope.batch_id === batchId` 派生 current；effect 只在 `.then()` 异步回调内 setter | ✅ |
| 2 | `react-hooks/exhaustive-deps` warning（ByDimensionChart） | `dims/stories` 内联进 `useMemo`，deps 简化为 `[data]` | ✅ |
| 3 | 监督指定的 targeted lint | 重新跑 `pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx` | ✅ exit 0，无输出 |

## Completed since Report #8

### 1. Quality 页面 effect 重构（Review §"AC5 UI has new lint errors"）

**根因**：`react-hooks/set-state-in-effect`（react-hooks plugin v6+）禁止在 useEffect body 同步调用 setState。旧实现为了"换 batch 时重置"在 effect 头部 `setTrend(null); setByDim(null); setDistrib(null); setHeatmap(null); setStoryId(null);`，这违反规则。

**改文件**：`frontend/app/admin/quality/page.tsx`

**重构方案**：从 envelope 派生 freshness，去掉所有同步 reset。

```ts
// 旧（违规）：
useEffect(() => {
  if (batchId == null) return;
  setTrend(null);    // ❌ set-state-in-effect
  setByDim(null);    // ❌
  setDistrib(null);  // ❌
  setHeatmap(null);  // ❌
  setStoryId(null);  // ❌
  Promise.all([getQualityTrend(batchId).then(setTrend), ...]);
}, [batchId]);

// 新（合规）：
useEffect(() => {
  if (batchId == null) return;
  let cancelled = false;
  getQualityTrend(batchId).then((r) => { if (!cancelled) setTrend(r); }).catch(...);
  getQualityByDimension(batchId).then((r) => { if (!cancelled) setByDim(r); }).catch(...);
  getQualityDistribution(batchId).then((r) => { if (!cancelled) setDistrib(r); }).catch(...);
  return () => { cancelled = true; };
}, [batchId]);

// 在渲染层用 freshness check 决定显示哪一份数据：
const trendCurrent = trend?.batch_id === batchId ? trend : null;
// 同理 byDimCurrent / distribCurrent
```

**Heatmap 状态**：旧 `heatmap` 直接存 envelope；新 `heatmap` 存 `{batchId, storyId, envelope}` 三元组，渲染时严格匹配当前 `(batchId, storyId)`。

**好处**：
- 0 set-state-in-effect 违反
- 切 batch 时旧数据被自动归类为 stale → 渲染层用 `<Loading>` placeholder（同样的 UX）
- race condition 用 `cancelled` flag 兜底（Strict Mode 下也安全）
- 不需要 reducer 或 `useReducer` 大改

**所有 effects 现在都满足规则**：
- `useEffect(() => { ... fetch().then(setX) ... }, [...])`
- 唯一会改变 state 的代码路径在 `.then()` 异步回调里，不在 effect body 同步路径

### 2. ByDimensionChart deps 修正

```ts
// 旧：
const dims = data.dimensions;
const stories = [...data.per_story, data.global];
const option = useMemo(() => ({ ... uses dims/stories ... }), [data, dims, stories]);
// dims/stories 是 data 的派生，每次 render 重新计算 → useMemo 实际从未命中缓存

// 新：
const option = useMemo(() => {
  const dims = data.dimensions;
  const stories = [...data.per_story, data.global];
  return { ... };
}, [data]);
```

### 3. Targeted lint 实测

监督要求的命令：
```bash
$ pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx
$ echo $?
0
```

无任何输出 + exit 0 = clean。其他文件的 131 个 pre-existing 错误未触动。

### 4. Build 实测

```bash
$ pnpm run build
✓ Compiled successfully
Route (app)
├ ○ /admin                ← 修订（顶部加质量仪表盘链接，未影响 lint）
├ ○ /admin/logs
├ ○ /admin/quality        ← 重构后仍 prerender 为 static
```

## Files changed since Report #8

| 文件 | 类型 | 说明 |
|---|---|---|
| `frontend/app/admin/quality/page.tsx` | 重构 | effect 去 synchronous setter；envelope.batch_id 派生 freshness；HeatmapState 三元组；ByDimensionChart deps 简化 |

无其他文件改动。

## Verification

```
✓ pnpm exec eslint app/admin/quality/page.tsx lib/admin-api.ts app/admin/page.tsx
  → exit 0, no output (clean)
✓ pnpm run build
  → /admin/quality 静态预渲染
✓ python -m compileall -q backend scripts tests
✓ pytest tests/ -q
  → 35 passed (17 delta + 7 readiness + 11 builder)
✓ python scripts/calibrate_slop_detector.py --threshold 0.5
  → recall=0.97 / precision_overall=0.97 / precision_pd_excerpt=0.97
  → AC3 PASS (pd_excerpt only, independent): True
```

## Updated AC matrix

| AC | 标准 | 实测 | Status |
|---|---|---|---|
| AC1 | scope×8 严格全覆盖 | 168/168 | ✅ Pass |
| AC1b | scope 严格全覆盖 | 21/21 | ✅ Pass |
| AC2-bootstrap | 5 章 per-dim ρ | mean=0.45 | ✅ Done |
| **AC2-final** | 监督独立评 1 章 | artifact 等监督 | 🟡 等监督（Phase 0 唯一硬阻塞） |
| **AC3** | recall≥0.8 + 三 precision 各≥0.7 | 0.97 / 0.97 / 0.97 / 0.97 | ✅ **Pass**（Review #8 已 final 通过） |
| AC4 | mean cost ≤ ¥0.10 | ¥0.055 | ✅ Pass |
| **AC5** | 4 图表 contract + readiness + UI | backend done + 35 测试 + frontend lint clean | 🟡 等监督 UI smoke 验收 |
| AC6 | mean / variance / stdev / trend | 已含；live-DB regression 通过 | ✅ Pass |

## Asks（监督决策点）

1. **AC2-final 评分**（**Phase 0 收口的唯一硬阻塞**）：artifact `data/baselines/ac2-final-calibration-batch-2.json`
2. **AC5 UI smoke 验收**：lint 已 clean，监督是否：
   - (a) 启动 `uvicorn backend.main:app --reload --port 8000` + `cd frontend && pnpm run dev` 后浏览器实测 `/admin/quality`
   - (b) 仅审 build artifact + 35 个回归测试就视为通过
   - (c) 工程师上传截图

## Default if no answer

- 2026-04-30 23:59 前监督未回 → 工程师按以下默认推进：
  - (1) AC2-final：等监督，**不擅自代填**
  - (2) AC5 UI：维持当前实现，不擅自加 feature
- 工程师在 inbox 留 `[Auto-Executed]` 报告

## What's Next

按 phase-gate v2.3，Phase 0 → Phase 1 收口剩余项：
- **AC2-final 监督独立评分**（硬阻塞）
- AC5 UI smoke 验收

工程师层面所有 AC 都已 ready 或 Pass：8 AC 中 AC1/AC1b/AC2-bootstrap/AC3/AC4/AC6 已 Pass，AC2-final 等监督，AC5 等 UI 验收。监督做完 AC2-final 后，Phase 0 立即可收口，进 Phase 1（SceneCard + anti-cliché judge prompt + detector v1.1 frequency-aware tier1）。
