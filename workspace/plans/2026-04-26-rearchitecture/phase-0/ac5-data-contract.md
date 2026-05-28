# AC5 Data Contract Design (前端 4 图表)

| Field | Value |
|---|---|
| Author | engineer |
| Date | 2026-04-27 |
| Status | proposal — schema only, UI 待 AC2-final / AC3-final 稳定后开 |
| Related | Report #2 review §AC5；phase-gate v2.1 AC5 |

## 设计原则

1. **数据 contract 先行**：先冻结 backend → frontend 数据形状，UI 框架再选；
2. **batch-aware**：所有查询都接受 `evaluation_batch_id`，默认使用 `default_baseline_batch_id`（DB 配置项）；
3. **零计算客户端**：所有聚合（mean / variance / stdev / slope / 前后段差）在 backend 算好下发，前端只负责渲染；
4. **readiness flag**：每个端点返回 `data_ready: bool` + `reason: string`，UI 根据此判断是 render 还是 placeholder；
5. **rubric_version 显式**：所有数据带 `rubric_version` 字段，UI 在标题旁标注（不同 rubric 数据不能混画）。

## 4 个图表 + 4 个端点

| # | Chart | Endpoint | 主键聚合层级 |
|---|---|---|---|
| 1 | **趋势** (per-story composite over chapter_num) | `GET /api/admin/quality/batch/{batch_id}/trend` | story × chapter |
| 2 | **对比** (per-story × per-dim mean) | `GET /api/admin/quality/batch/{batch_id}/by-dimension` | story × dimension |
| 3 | **热区** (chapter × dim grid) | `GET /api/admin/quality/batch/{batch_id}/heatmap?story_id=X` | chapter × dimension（指定 story） |
| 4 | **分布** (composite histogram + slop histogram) | `GET /api/admin/quality/batch/{batch_id}/distribution` | batch（全局） |

所有响应共享一个 envelope：

```ts
interface QualityResponse<T> {
  batch_id: number;
  rubric_version: string;       // "SEQR-v0"
  detector_version: string;     // "v1"
  judge_model: string;          // "deepseek/deepseek-v4-pro"
  generated_at: string;         // ISO
  data_ready: boolean;
  reason?: string;              // 当 data_ready=false 时给出原因
  data: T | null;
}
```

## Chart 1: 趋势

**用途**：观察每本书的 composite/quality/slop 随 chapter_num 的变化（B 段 vs A 段、是否走低）。

**Endpoint**: `GET /api/admin/quality/batch/{batch_id}/trend`

**Response.data**:
```ts
interface TrendData {
  stories: TrendStory[];
}
interface TrendStory {
  story_id: string;
  story_title: string;
  n_chapters: number;
  chapters: TrendPoint[];
  aggregates: {
    composite: { mean: number; variance: number; stdev: number; min: number; max: number; slope_per_chapter: number; first_half_mean: number; second_half_mean: number; delta: number; };
    mean_quality: { mean: number; variance: number; stdev: number; };
    slop_penalty: { mean: number; variance: number; stdev: number; };
    word_count: { mean: number; variance: number; stdev: number; };
  };
}
interface TrendPoint {
  chapter_num: number;
  word_count: number;
  composite_score: number;
  mean_quality: number;
  slop_penalty: number;
}
```

#### Trend delta canonical algorithm (Algorithm A — symmetric exclude-middle)

> Locked-in by Report #5 review (2026-04-27). All callers (backend endpoint,
> baseline_report doc, future analytics scripts) MUST use this exact definition.

```
def half_half_delta(values: list[float]) -> tuple[fm, sm, delta]:
    n = len(values)
    if n < 2: return (0, 0, 0)
    half = n // 2
    first  = values[:half]                                # always first n//2
    second = values[-half:] if n % 2 == 0 \                # even n: last n//2
             else values[half + 1:]                        # odd n: skip middle, take last n//2
    return (mean(first), mean(second), mean(second) - mean(first))
```

| n | first range | second range | excluded |
|---|---|---|---|
| 2 | [1] | [2] | none |
| 3 | [1] | [3] | ch2 |
| 4 | [1,2] | [3,4] | none |
| 5 | [1,2] | [4,5] | ch3 |
| 8 | [1,2,3,4] | [5,6,7,8] | none |
| 9 | [1,2,3,4] | [6,7,8,9] | ch5 |

Rationale: equal-size halves with no overlap; loses 1 chapter for odd n
(minimum information sacrifice for clean comparison). Regression test in
`tests/test_quality_admin_delta.py`.

**前端图建议**：每本书一条 line（颜色按 story_id 哈希），y 轴 composite，x 轴 chapter_num；可切换 y 轴到 mean_quality / slop_penalty。

## Chart 2: 对比

**用途**：跨小说看 per-dim 强弱（哪本对话最弱、哪本场景戏剧性最高）。

**Endpoint**: `GET /api/admin/quality/batch/{batch_id}/by-dimension`

**Response.data**:
```ts
interface ByDimensionData {
  dimensions: string[];                           // 8 个维度名顺序
  per_story: PerStoryDim[];
  global: PerStoryDim;                            // 全部 story 合并
}
interface PerStoryDim {
  story_id: string | "ALL";
  story_title?: string;
  n_chapters: number;
  scores: Record<string, {                        // 维度 → { mean, variance, stdev, min, max }
    mean: number; variance: number; stdev: number; min: number; max: number;
  }>;
}
```

**前端图建议**：分组条形图，x 轴 8 维度，每组 N 个 bar（每本书一种颜色 + 全局对比 bar）。

## Chart 3: 热区

**用途**：单本书内 chapter × dimension 网格，直观看哪一章哪一维度掉链子。

**Endpoint**: `GET /api/admin/quality/batch/{batch_id}/heatmap?story_id={story_id}`

**Response.data**:
```ts
interface HeatmapData {
  story_id: string;
  story_title: string;
  dimensions: string[];                           // 8 维度顺序
  chapters: number[];                             // 1, 2, ..., n
  matrix: number[][];                             // matrix[chapter_idx][dim_idx]
  meta: {
    score_range: [number, number];                // [0, 10]
    color_scheme_hint: "RdYlGn";                  // 建议色阶
  };
  evidence?: Record<string, Record<string, string>>;  // optional: chapter → dim → judge evidence (短引文)
}
```

**前端图建议**：标准热图，hover 显示分数 + 监督 evidence（如已加载）。

## Chart 4: 分布

**用途**：composite/slop 直方图，看分布形态（正态？双峰？长尾？）。

**Endpoint**: `GET /api/admin/quality/batch/{batch_id}/distribution`

**Response.data**:
```ts
interface DistributionData {
  composite_histogram: HistBin[];
  slop_histogram: HistBin[];
  per_dimension_histograms: Record<string, HistBin[]>;  // 8 维各一组
  totals: { n_chapters: number; n_stories: number; };
}
interface HistBin {
  bin_low: number;
  bin_high: number;
  count: number;
}
```

**前端图建议**：堆叠或并排直方图；composite 与 slop 主图，per-dim 折叠到第二屏。

## Backend 实现路径（不在本文档实现，仅列必要工作量）

| 工作 | 估时 | 依赖 |
|---|---|---|
| 4 个 Pydantic response model | 0.5 d | — |
| 4 个 SQLite 聚合 query（含 variance / slope / first/second-half delta） | 1.5 d | 已有 `chapter_quality_evaluations` 表 |
| 4 个 FastAPI router 函数 + `Depends()` | 0.5 d | `backend/api/` |
| 单元测试（每个端点 1 happy + 1 empty-batch） | 1 d | — |

**工作总量约 3.5 工程师工作日**，但**不在 Phase 0 范围**——监督说 UI 等 AC2-final/AC3-final 稳定。本文档仅冻结 contract。

## 等待条件 → UI 启动 trigger

| 条件 | 状态 | trigger |
|---|---|---|
| AC2-final 监督评分完成 | 🟡 等监督填 | trigger 1 |
| AC3 v2 fiction-normal calibration | ✅ 已完成（recall=0.97, precision=1.00 overall + fiction-only） | trigger 2 |
| Rubric 字段不再增减 | ✅ SEQR-v0 8 维稳定 | trigger 3 |
| 监督显式批准启动 UI | 🟡 等批准 | trigger 4 |

**3/4 trigger 已满足**。剩 AC2-final + 监督批准。

## Open questions（监督决策点）

1. **是否加 monolithic endpoint** `GET /api/admin/quality/batch/{batch_id}/all` 一次拉所有 4 图数据？利于 SPA 一次加载，但响应 payload 大。建议 **不加**，UI 用 React Query 并发拉 4 个端点，loading 状态独立。
2. **是否用 server-sent events** 推送实时 batch 进度？建议 **暂不**，Phase 0 只展示已完成 batch。
3. **多 batch 对比图（同一 story 不同 batch 的 trend overlay）** 是否纳入 AC5？建议 **加为 stretch goal**，先做单 batch 4 图。
