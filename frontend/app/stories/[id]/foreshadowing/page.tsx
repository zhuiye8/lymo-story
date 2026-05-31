"use client";

import { use, useEffect, useState } from "react";
import { Sparkles, CircleDot, CheckCircle2 } from "lucide-react";
import { getForeshadowing } from "@/lib/api";
import type { ForeshadowingResponse } from "@/types";
import { Badge } from "@/components/ui/badge";

export default function ForeshadowingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<ForeshadowingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getForeshadowing(id)
      .then(setData)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  const items = data?.items ?? [];
  const open = items.filter((i) => i.status === "open");
  const resolved = items.filter((i) => i.status === "resolved");
  const rate = data && data.total ? Math.round((data.resolved / data.total) * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <Sparkles className="size-6 text-lymo-gold-400" />
        <h1 className="font-serif text-2xl font-bold">伏笔 · 埋坑填坑</h1>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Stat label="埋下" value={data?.total ?? 0} />
        <Stat label="已回收" value={data?.resolved ?? 0} />
        <Stat label="回收率" value={`${rate}%`} />
      </div>

      {open.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <CircleDot className="size-4 text-lymo-gold-400" /> 待回收 · {open.length}
          </h2>
          <div className="space-y-1.5">
            {open
              .slice()
              .sort((a, b) => (b.age ?? 0) - (a.age ?? 0))
              .map((f) => (
                <div key={f.id} className="flex items-start gap-3 rounded-lg border border-lymo-gold-500/25 bg-lymo-gold-500/5 px-4 py-2.5">
                  <span className="text-sm flex-1">{f.description}</span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant="ghost" className="text-[10px]">第{f.planted_chapter}章埋</Badge>
                    {(f.age ?? 0) >= 5 && <Badge variant="destructive" className="text-[10px]">拖 {f.age} 章</Badge>}
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {resolved.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="size-4 text-lymo-jade-400" /> 已回收 · {resolved.length}
          </h2>
          <div className="space-y-1.5">
            {resolved.map((f) => (
              <div key={f.id} className="flex items-start gap-3 rounded-lg border border-border/40 bg-card/20 px-4 py-2.5 opacity-80">
                <span className="text-sm flex-1 text-muted-foreground">{f.description}</span>
                <Badge variant="jade" className="text-[10px] shrink-0">
                  {f.planted_chapter}→{f.resolved_chapter} 章
                </Badge>
              </div>
            ))}
          </div>
        </section>
      )}

      {items.length === 0 && (
        <div className="text-muted-foreground text-sm py-16 text-center">暂无伏笔（生成章节后累积）。</div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-border/60 bg-card/40 p-4 text-center">
      <div className="text-2xl font-bold font-serif text-gold-grad">{value}</div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </div>
  );
}
