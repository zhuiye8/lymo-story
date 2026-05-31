"use client";

import { use, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import {
  getQualityTrend,
  getQualityByDimension,
  getQualityHeatmap,
} from "@/lib/api";
import type { TrendResponse, ByDimensionResponse, HeatmapResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// echarts 需在客户端渲染（canvas），SSR 关闭
const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const AXIS = "#6b7785";
const GRID = "rgba(107,119,133,0.15)";

export default function QualityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [byDim, setByDim] = useState<ByDimensionResponse | null>(null);
  const [heat, setHeat] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getQualityTrend(id).catch(() => null),
      getQualityByDimension(id).catch(() => null),
      getQualityHeatmap(id).catch(() => null),
    ])
      .then(([t, d, h]) => {
        setTrend(t);
        setByDim(d);
        setHeat(h);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  if (!trend?.data_ready) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="font-serif text-2xl font-bold mb-4">质量分析</h1>
        <div className="text-muted-foreground text-sm py-16 text-center">
          {trend?.reason ?? "暂无质量数据"}（生成章节后累积）。
        </div>
      </div>
    );
  }

  const agg = trend.data!.aggregates.composite ?? {};
  const chapters = trend.data!.chapters;

  const trendOption: EChartsOption = {
    grid: { left: 40, right: 16, top: 30, bottom: 28 },
    legend: { data: ["综合分", "slop 惩罚"], textStyle: { color: AXIS }, top: 0 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: chapters.map((c) => `第${c.chapter_num}章`),
      axisLine: { lineStyle: { color: GRID } },
      axisLabel: { color: AXIS, fontSize: 10 },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 10,
      splitLine: { lineStyle: { color: GRID } },
      axisLabel: { color: AXIS, fontSize: 10 },
    },
    series: [
      {
        name: "综合分",
        type: "line",
        smooth: true,
        data: chapters.map((c) => c.composite_score),
        itemStyle: { color: "#d4a84b" },
        areaStyle: { color: "rgba(212,168,75,0.12)" },
      },
      {
        name: "slop 惩罚",
        type: "bar",
        data: chapters.map((c) => c.slop_penalty),
        itemStyle: { color: "rgba(199,62,58,0.5)" },
      },
    ],
  };

  const dims = byDim?.data;
  const radarOption: EChartsOption | null = dims
    ? {
        tooltip: {},
        radar: {
          indicator: dims.dimensions.map((d) => ({
            name: dims.labels[d] ?? d,
            max: 10,
          })),
          axisName: { color: AXIS, fontSize: 10 },
          splitLine: { lineStyle: { color: GRID } },
          splitArea: { show: false },
          axisLine: { lineStyle: { color: GRID } },
        },
        series: [
          {
            type: "radar",
            data: [
              {
                value: dims.dimensions.map((d) => dims.per_dimension[d]?.mean ?? 0),
                name: "维度均分",
                itemStyle: { color: "#5a8fd4" },
                areaStyle: { color: "rgba(90,143,212,0.18)" },
              },
            ],
          },
        ],
      }
    : null;

  const hm = heat?.data;
  const heatOption: EChartsOption | null = hm
    ? {
        grid: { left: 70, right: 16, top: 10, bottom: 60 },
        tooltip: { position: "top" },
        xAxis: {
          type: "category",
          data: hm.chapters.map((c) => `第${c}章`),
          axisLabel: { color: AXIS, fontSize: 9, rotate: 45 },
          splitArea: { show: true },
        },
        yAxis: {
          type: "category",
          data: hm.dimensions.map((d) => hm.labels[d] ?? d),
          axisLabel: { color: AXIS, fontSize: 9 },
          splitArea: { show: true },
        },
        visualMap: {
          min: 0,
          max: 10,
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: 0,
          inRange: { color: ["#c73e3a", "#d4a84b", "#5aa67d"] },
          textStyle: { color: AXIS },
        },
        series: [
          {
            type: "heatmap",
            data: hm.matrix.flatMap((row, ci) => row.map((v, di) => [ci, di, v])),
            label: { show: false },
          },
        ],
      }
    : null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-bold">质量分析</h1>
        <div className="flex gap-2">
          <Badge variant="gold" className="text-[10px]">均分 {agg.mean?.toFixed(2)}</Badge>
          <Badge variant={(agg.delta ?? 0) >= 0 ? "jade" : "destructive"} className="text-[10px]">
            趋势 {(agg.delta ?? 0) >= 0 ? "+" : ""}{agg.delta?.toFixed(2)}
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-1"><CardTitle className="text-base font-serif">综合分趋势</CardTitle></CardHeader>
        <CardContent>
          <ReactECharts option={trendOption} style={{ height: 260 }} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {radarOption && (
          <Card>
            <CardHeader className="pb-1"><CardTitle className="text-base font-serif">八维度均分</CardTitle></CardHeader>
            <CardContent>
              <ReactECharts option={radarOption} style={{ height: 300 }} />
            </CardContent>
          </Card>
        )}
        {heatOption && (
          <Card>
            <CardHeader className="pb-1"><CardTitle className="text-base font-serif">章节×维度热力</CardTitle></CardHeader>
            <CardContent>
              <ReactECharts option={heatOption} style={{ height: 300 }} />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
