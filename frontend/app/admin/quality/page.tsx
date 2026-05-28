"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import {
  listQualityBatches,
  getQualityTrend,
  getQualityByDimension,
  getQualityHeatmap,
  getQualityDistribution,
  type BatchSummary,
  type QualityResponseEnvelope,
  type TrendData,
  type ByDimensionData,
  type HeatmapData,
  type DistributionData,
} from "@/lib/admin-api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

// Map a backend QualityResponse envelope into the data + a place-holder.
function NotReady({ reason }: { reason: string | null | undefined }) {
  return (
    <div className="flex h-72 items-center justify-center rounded border border-dashed border-neutral-700 bg-neutral-900 p-4 text-sm text-neutral-400">
      <div>
        <div className="font-medium text-neutral-200">数据未就绪</div>
        <div className="mt-1 max-w-xl text-xs leading-relaxed">{reason ?? "无具体原因。"}</div>
      </div>
    </div>
  );
}

const DIM_LABELS: Record<string, string> = {
  fluency: "语言流畅",
  dialogue_distinct: "对白独特",
  character_consistency: "角色一致",
  scene_drama: "场景戏剧",
  sensory_detail: "感官描写",
  rhetoric_quality: "修辞质量",
  continuity: "跨场景衔接",
  overall_readability: "整体可读",
};

// === Trend chart ===
function TrendChart({ data }: { data: TrendData }) {
  const option = useMemo(() => ({
    tooltip: { trigger: "axis" },
    legend: { textStyle: { color: "#d4d4d8" } },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: {
      type: "category",
      name: "章节",
      data: Array.from(
        { length: Math.max(...data.stories.map((s) => s.n_chapters), 1) },
        (_, i) => `${i + 1}`
      ),
      axisLabel: { color: "#a1a1aa" },
      nameTextStyle: { color: "#a1a1aa" },
    },
    yAxis: {
      type: "value",
      name: "Composite (0-10)",
      min: 0,
      max: 10,
      axisLabel: { color: "#a1a1aa" },
      nameTextStyle: { color: "#a1a1aa" },
    },
    series: data.stories.map((s) => ({
      name: `${s.story_title || s.story_id} (n=${s.n_chapters})`,
      type: "line",
      smooth: true,
      data: s.chapters.map((c) => c.composite_score),
    })),
  }), [data]);
  return <ReactECharts option={option} style={{ height: 360 }} />;
}

function TrendStoryAggregates({ data }: { data: TrendData }) {
  return (
    <table className="mt-3 w-full text-xs">
      <thead className="text-neutral-400">
        <tr>
          <th className="text-left">小说</th>
          <th>n</th>
          <th>composite mean</th>
          <th>variance</th>
          <th>stdev</th>
          <th>slope/章</th>
          <th>前半均值</th>
          <th>后半均值</th>
          <th>Δ</th>
        </tr>
      </thead>
      <tbody className="font-mono text-neutral-200">
        {data.stories.map((s) => {
          const a = s.aggregates.composite;
          return (
            <tr key={s.story_id} className="border-t border-neutral-800">
              <td className="py-1 text-left text-neutral-300">{s.story_title || s.story_id}</td>
              <td className="text-center">{s.n_chapters}</td>
              <td className="text-right">{a.mean.toFixed(3)}</td>
              <td className="text-right">{a.variance.toFixed(3)}</td>
              <td className="text-right">{a.stdev.toFixed(3)}</td>
              <td className="text-right">{a.slope_per_chapter > 0 ? "+" : ""}{a.slope_per_chapter.toFixed(3)}</td>
              <td className="text-right">{a.first_half_mean.toFixed(3)}</td>
              <td className="text-right">{a.second_half_mean.toFixed(3)}</td>
              <td className={`text-right ${a.delta < 0 ? "text-rose-400" : "text-emerald-400"}`}>
                {a.delta > 0 ? "+" : ""}{a.delta.toFixed(3)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// === By-dimension chart ===
function ByDimensionChart({ data }: { data: ByDimensionData }) {
  // dims/stories are derived from `data` so depending on `data` alone is sufficient.
  const option = useMemo(() => {
    const dims = data.dimensions;
    const stories = [...data.per_story, data.global];
    return {
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { textStyle: { color: "#d4d4d8" } },
      grid: { left: 50, right: 30, top: 40, bottom: 60 },
      xAxis: {
        type: "category",
        data: dims.map((d) => DIM_LABELS[d] ?? d),
        axisLabel: { color: "#a1a1aa", interval: 0, rotate: 30 },
      },
      yAxis: {
        type: "value",
        name: "维度均分",
        min: 0,
        max: 10,
        axisLabel: { color: "#a1a1aa" },
        nameTextStyle: { color: "#a1a1aa" },
      },
      series: stories.map((s) => ({
        name: s.story_id === "ALL" ? "全部小说" : (s.story_title || s.story_id),
        type: "bar",
        data: dims.map((d) => s.scores[d]?.mean ?? 0),
      })),
    };
  }, [data]);
  return <ReactECharts option={option} style={{ height: 360 }} />;
}

// === Heatmap chart ===
function HeatmapChart({ data }: { data: HeatmapData }) {
  const option = useMemo(() => {
    const dims = data.dimensions;
    const points: Array<[number, number, number]> = [];
    data.chapters.forEach((_, ri) => {
      data.matrix[ri].forEach((v, ci) => {
        points.push([ci, ri, v]);
      });
    });
    return {
      tooltip: {
        position: "top",
        formatter: (p: { data: [number, number, number] }) => {
          const [ci, ri, v] = p.data;
          const ch = data.chapters[ri];
          const dim = DIM_LABELS[dims[ci]] ?? dims[ci];
          return `第 ${ch} 章 / ${dim}<br/>分数: ${v.toFixed(2)}`;
        },
      },
      grid: { height: "70%", top: 60, left: 90, right: 30 },
      xAxis: {
        type: "category",
        data: dims.map((d) => DIM_LABELS[d] ?? d),
        axisLabel: { color: "#a1a1aa", interval: 0, rotate: 30 },
        splitArea: { show: true },
      },
      yAxis: {
        type: "category",
        data: data.chapters.map((c) => `第${c}章`),
        axisLabel: { color: "#a1a1aa" },
        splitArea: { show: true },
      },
      visualMap: {
        min: 0,
        max: 10,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 0,
        inRange: { color: ["#7f1d1d", "#fef08a", "#16a34a"] },
        textStyle: { color: "#a1a1aa" },
      },
      series: [{
        name: "分数",
        type: "heatmap",
        data: points,
        label: { show: true, fontSize: 10, color: "#0a0a0a" },
        emphasis: { itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,0.5)" } },
      }],
    };
  }, [data]);
  return <ReactECharts option={option} style={{ height: 480 }} />;
}

// === Distribution chart (composite + slop side by side) ===
function DistributionChart({ data }: { data: DistributionData }) {
  const compHist = data.composite_histogram;
  const slopHist = data.slop_histogram;
  const option = useMemo(() => ({
    tooltip: { trigger: "axis" },
    legend: { textStyle: { color: "#d4d4d8" } },
    grid: [
      { left: 50, right: 20, top: 40, height: "35%" },
      { left: 50, right: 20, top: "60%", height: "35%" },
    ],
    xAxis: [
      {
        gridIndex: 0,
        type: "category",
        data: compHist.map((b) => `${b.bin_low.toFixed(1)}-${b.bin_high.toFixed(1)}`),
        axisLabel: { color: "#a1a1aa", fontSize: 10, interval: 1 },
      },
      {
        gridIndex: 1,
        type: "category",
        data: slopHist.map((b) => `${b.bin_low.toFixed(1)}-${b.bin_high.toFixed(1)}`),
        axisLabel: { color: "#a1a1aa", fontSize: 10 },
      },
    ],
    yAxis: [
      { gridIndex: 0, type: "value", name: "章数", axisLabel: { color: "#a1a1aa" }, nameTextStyle: { color: "#a1a1aa" } },
      { gridIndex: 1, type: "value", name: "章数", axisLabel: { color: "#a1a1aa" }, nameTextStyle: { color: "#a1a1aa" } },
    ],
    series: [
      {
        name: "composite (0-10)",
        type: "bar",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: compHist.map((b) => b.count),
        itemStyle: { color: "#22c55e" },
      },
      {
        name: "slop_penalty (0-3)",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: slopHist.map((b) => b.count),
        itemStyle: { color: "#f97316" },
      },
    ],
  }), [compHist, slopHist]);
  return <ReactECharts option={option} style={{ height: 460 }} />;
}

// === Page ===
//
// Per Report #8 review §"AC5 UI has new lint errors":
//   the previous implementation called setTrend(null)/setByDim(null)/... synchronously
//   inside effects to "reset on batch change". That violates
//   react-hooks/set-state-in-effect.
//
// Refactor: derive freshness from the response envelope itself.
//   - each fetched envelope carries `batch_id`; we only render it when that
//     matches the current `batchId`. Stale data falls through `<NotReady>`.
//   - heatmap envelope adds the `story_id` from the request URL (we close
//     over it in the `.then()`) so we know which story it's for.
//   - effects only call setters from the async `.then(...)` callback; the
//     effect body itself does not synchronously call any setter, satisfying
//     the rule.

interface HeatmapState {
  batchId: number;
  storyId: string;
  envelope: QualityResponseEnvelope<HeatmapData>;
}

export default function QualityDashboardPage() {
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [batchId, setBatchId] = useState<number | null>(null);
  const [trend, setTrend] = useState<QualityResponseEnvelope<TrendData> | null>(null);
  const [byDim, setByDim] = useState<QualityResponseEnvelope<ByDimensionData> | null>(null);
  const [distrib, setDistrib] = useState<QualityResponseEnvelope<DistributionData> | null>(null);
  const [storyId, setStoryId] = useState<string | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapState | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load batches once.
  useEffect(() => {
    let cancelled = false;
    listQualityBatches()
      .then((r) => {
        if (cancelled) return;
        setBatches(r.batches);
        if (r.batches.length > 0) setBatchId(r.batches[0].id);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(`Failed to load batches: ${e.message}`);
      });
    return () => { cancelled = true; };
  }, []);

  // When batch changes, fetch the 3 batch-level endpoints in parallel.
  // No synchronous resets — `trend?.batch_id === batchId` is the freshness check.
  useEffect(() => {
    if (batchId == null) return;
    let cancelled = false;
    getQualityTrend(batchId)
      .then((r) => { if (!cancelled) setTrend(r); })
      .catch((e) => { if (!cancelled) setError(`trend: ${e.message}`); });
    getQualityByDimension(batchId)
      .then((r) => { if (!cancelled) setByDim(r); })
      .catch((e) => { if (!cancelled) setError(`by-dim: ${e.message}`); });
    getQualityDistribution(batchId)
      .then((r) => { if (!cancelled) setDistrib(r); })
      .catch((e) => { if (!cancelled) setError(`distrib: ${e.message}`); });
    return () => { cancelled = true; };
  }, [batchId]);

  // Heatmap: fetch when batchId+storyId both set.
  // Stale heatmap is filtered at render time by comparing `heatmap.batchId/storyId`.
  useEffect(() => {
    if (batchId == null || storyId == null) return;
    let cancelled = false;
    getQualityHeatmap(batchId, storyId)
      .then((r) => {
        if (cancelled) return;
        setHeatmap({ batchId, storyId, envelope: r });
      })
      .catch((e) => { if (!cancelled) setError(`heatmap: ${e.message}`); });
    return () => { cancelled = true; };
  }, [batchId, storyId]);

  // Freshness checks (envelope.batch_id matches current batchId).
  const trendCurrent = trend != null && trend.batch_id === batchId ? trend : null;
  const byDimCurrent = byDim != null && byDim.batch_id === batchId ? byDim : null;
  const distribCurrent = distrib != null && distrib.batch_id === batchId ? distrib : null;
  const heatmapCurrent =
    heatmap != null && heatmap.batchId === batchId && heatmap.storyId === storyId
      ? heatmap.envelope
      : null;

  const stories = trendCurrent?.data?.stories ?? [];
  const selectedBatch = batches.find((b) => b.id === batchId);

  return (
    <div className="min-h-screen bg-neutral-950 px-6 py-6 text-neutral-100">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-semibold">质量评测仪表盘</h1>
          <a href="/admin" className="text-sm text-neutral-400 hover:text-neutral-200">
            ← 返回 Admin
          </a>
        </div>

        {error && (
          <div className="rounded border border-rose-700 bg-rose-950 p-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        {/* Batch picker */}
        <div className="rounded border border-neutral-800 bg-neutral-900 p-4">
          <div className="flex items-center gap-3">
            <label className="text-sm text-neutral-400">评测批次：</label>
            <select
              value={batchId ?? ""}
              onChange={(e) => setBatchId(Number(e.target.value))}
              className="rounded bg-neutral-800 px-3 py-1.5 text-sm text-neutral-100"
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  #{b.id} {b.batch_label} (scope={b.scope_chapter_count}, {b.status})
                </option>
              ))}
            </select>
            {selectedBatch && (
              <div className="ml-auto text-xs text-neutral-400">
                rubric: <span className="text-neutral-200">{selectedBatch.rubric_version}</span>
                <span className="mx-2">·</span>
                detector: <span className="text-neutral-200">{selectedBatch.detector_version}</span>
                <span className="mx-2">·</span>
                judge: <span className="text-neutral-200">{selectedBatch.judge_model}</span>
              </div>
            )}
          </div>
        </div>

        {/* Trend */}
        <section className="rounded border border-neutral-800 bg-neutral-900 p-4">
          <h2 className="mb-3 text-base font-medium">① 趋势 · per-story composite over chapters</h2>
          {!trendCurrent ? (
            <div className="text-sm text-neutral-500">加载中…</div>
          ) : !trendCurrent.data_ready || !trendCurrent.data ? (
            <NotReady reason={trendCurrent.reason} />
          ) : (
            <>
              <TrendChart data={trendCurrent.data} />
              <TrendStoryAggregates data={trendCurrent.data} />
            </>
          )}
        </section>

        {/* By-dimension */}
        <section className="rounded border border-neutral-800 bg-neutral-900 p-4">
          <h2 className="mb-3 text-base font-medium">② 对比 · per-story × per-dimension</h2>
          {!byDimCurrent ? (
            <div className="text-sm text-neutral-500">加载中…</div>
          ) : !byDimCurrent.data_ready || !byDimCurrent.data ? (
            <NotReady reason={byDimCurrent.reason} />
          ) : (
            <ByDimensionChart data={byDimCurrent.data} />
          )}
        </section>

        {/* Heatmap (story-scoped) */}
        <section className="rounded border border-neutral-800 bg-neutral-900 p-4">
          <div className="mb-3 flex items-center gap-3">
            <h2 className="text-base font-medium">③ 热区 · chapter × dimension</h2>
            <select
              value={storyId ?? ""}
              onChange={(e) => setStoryId(e.target.value || null)}
              className="ml-auto rounded bg-neutral-800 px-3 py-1.5 text-sm text-neutral-100"
            >
              <option value="">请选择小说…</option>
              {stories.map((s) => (
                <option key={s.story_id} value={s.story_id}>
                  {s.story_title || s.story_id} (n={s.n_chapters})
                </option>
              ))}
            </select>
          </div>
          {!storyId ? (
            <div className="text-sm text-neutral-500">从上面选择一本小说以加载热区图。</div>
          ) : !heatmapCurrent ? (
            <div className="text-sm text-neutral-500">加载中…</div>
          ) : !heatmapCurrent.data_ready || !heatmapCurrent.data ? (
            <NotReady reason={heatmapCurrent.reason} />
          ) : (
            <HeatmapChart data={heatmapCurrent.data} />
          )}
        </section>

        {/* Distribution */}
        <section className="rounded border border-neutral-800 bg-neutral-900 p-4">
          <h2 className="mb-3 text-base font-medium">④ 分布 · composite + slop histograms</h2>
          {!distribCurrent ? (
            <div className="text-sm text-neutral-500">加载中…</div>
          ) : !distribCurrent.data_ready || !distribCurrent.data ? (
            <NotReady reason={distribCurrent.reason} />
          ) : (
            <>
              <DistributionChart data={distribCurrent.data} />
              <div className="mt-2 text-xs text-neutral-400">
                共 {distribCurrent.data.totals.n_chapters} 章 / {distribCurrent.data.totals.n_stories} 部小说
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
