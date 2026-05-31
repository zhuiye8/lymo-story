"use client";

import { use, useEffect, useMemo, useState } from "react";
import { Brain, Star } from "lucide-react";
import { getMemories } from "@/lib/api";
import type { Memory } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MemoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [items, setItems] = useState<Memory[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMemories(id)
      .then((r) => {
        setItems(r.items);
        setCounts(r.counts);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const byChar = useMemo(() => {
    const m = new Map<string, { name: string; l0: Memory[]; l1: Memory[] }>();
    for (const it of items) {
      if (!m.has(it.character_id)) m.set(it.character_id, { name: it.character_name, l0: [], l1: [] });
      const g = m.get(it.character_id)!;
      (it.layer === 0 ? g.l0 : g.l1).push(it);
    }
    return [...m.values()];
  }, [items]);

  if (loading) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8 space-y-5">
      <div className="flex items-center gap-3">
        <Brain className="size-6 text-lymo-stellar-400" />
        <h1 className="font-serif text-2xl font-bold">分层记忆</h1>
        <div className="flex gap-2">
          <Badge variant="gold" className="text-[10px]">L0 身份 {counts.L0 ?? 0}</Badge>
          <Badge variant="stellar" className="text-[10px]">L1 情感 {counts.L1 ?? 0}</Badge>
        </div>
      </div>
      <p className="text-xs text-muted-foreground -mt-2">
        L0 身份核心（恒在场）· L1 情感关键记忆（按情感权重，★=刻骨）· 语义召回喂给写作维系角色连续性
      </p>

      {byChar.length === 0 ? (
        <div className="text-muted-foreground text-sm py-16 text-center">暂无记忆（生成章节后累积）。</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {byChar.map((g) => (
            <Card key={g.name}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-serif">{g.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {g.l0.map((m) => (
                  <div key={m.id} className="text-sm rounded-md bg-lymo-gold-500/10 border border-lymo-gold-500/25 p-2.5">
                    <span className="text-[10px] text-lymo-gold-400 font-medium mr-1">身份</span>
                    {m.content}
                  </div>
                ))}
                {g.l1.length > 0 && (
                  <div className="space-y-2">
                    {g.l1.map((m) => (
                      <div key={m.id} className="text-sm flex items-start gap-2">
                        <WeightDot w={m.emotional_weight} />
                        <div className="flex-1">
                          <span className="text-muted-foreground/60 text-[11px] mr-1.5">第{m.source_chapter}章</span>
                          {m.content}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function WeightDot({ w }: { w: number }) {
  if (w >= 0.7) return <Star className="size-3.5 mt-0.5 shrink-0 text-lymo-vermilion-400 fill-lymo-vermilion-400" />;
  const color = w >= 0.5 ? "bg-lymo-gold-400" : "bg-muted-foreground/40";
  return <span className={`size-2 mt-1.5 shrink-0 rounded-full ${color}`} title={`权重 ${w}`} />;
}
