"use client";

import { use, useEffect, useState } from "react";
import { getOutline, getStory } from "@/lib/api";
import type { OutlineStage, StoryBible } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function OutlinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [stages, setStages] = useState<OutlineStage[]>([]);
  const [bible, setBible] = useState<StoryBible | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOutline(id), getStory(id)])
      .then(([o, s]) => {
        setStages(o);
        setBible((s.bible ?? {}) as StoryBible);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  const world = bible?.world ?? {};
  const ps = world.power_system ?? {};
  const levels = Array.isArray(ps.levels) ? ps.levels : [];

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-6">
      <h1 className="font-serif text-2xl font-bold">大纲与世界观</h1>

      {(world.background || ps.name) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-serif">世界观</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {world.background && <p className="text-muted-foreground leading-relaxed">{String(world.background)}</p>}
            {ps.name && (
              <div>
                <div className="text-lymo-gold-400 font-medium mb-1.5">{String(ps.name)}</div>
                {levels.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {levels.map((lv, i) => (
                      <span key={i} className="flex items-center gap-1">
                        <Badge variant="ghost" className="text-[10px]">{String(lv)}</Badge>
                        {i < levels.length - 1 && <span className="text-muted-foreground/40">→</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="font-serif text-lg font-bold mb-3">粗纲 · {stages.length} 阶段</h2>
        <div className="relative pl-6 space-y-4 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-px before:bg-border/60">
          {stages.map((s, i) => (
            <div key={i} className="relative">
              <div className="absolute -left-6 top-1.5 size-3.5 rounded-full bg-lymo-gold-500/30 border-2 border-lymo-gold-500" />
              <div className="rounded-lg border border-border/50 bg-card/30 p-4">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <h3 className="font-serif font-bold">{s.stage_name}</h3>
                  {(s.chapter_start || s.chapter_end) && (
                    <Badge variant="ghost" className="text-[10px] shrink-0">
                      第 {s.chapter_start}–{s.chapter_end} 章
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{s.summary}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
