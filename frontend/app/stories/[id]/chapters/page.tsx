"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen } from "lucide-react";
import { listChapters, parseQuality } from "@/lib/api";
import type { ChapterSummary } from "@/types";
import { Badge } from "@/components/ui/badge";

function scoreColor(v?: number) {
  if (v == null) return "ghost" as const;
  if (v >= 7.5) return "jade" as const;
  if (v >= 6) return "gold" as const;
  return "destructive" as const;
}

export default function ChaptersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listChapters(id)
      .then(setChapters)
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="font-serif text-2xl font-bold mb-6">章节列表</h1>
      {loading ? (
        <div className="text-muted-foreground text-sm">加载中…</div>
      ) : chapters.length === 0 ? (
        <div className="text-muted-foreground text-sm py-16 text-center">还没有章节。</div>
      ) : (
        <div className="space-y-1.5">
          {chapters.map((c) => {
            const q = parseQuality(c.quality_json);
            const comp = (q.composite_final ?? q.composite_score) as number | undefined;
            return (
              <Link
                key={c.chapter_num}
                href={`/stories/${id}/chapters/${c.chapter_num}`}
                className="card-hover flex items-center gap-3 rounded-lg border border-border/50 bg-card/30 px-4 py-3"
              >
                <BookOpen className="size-4 text-muted-foreground/50 shrink-0" />
                <span className="text-sm text-muted-foreground tabular-nums shrink-0">第 {c.chapter_num} 章</span>
                <span className="truncate flex-1 font-medium">{c.title}</span>
                <span className="text-xs text-muted-foreground/60 shrink-0">{c.word_count} 字</span>
                {comp != null && (
                  <Badge variant={scoreColor(comp)} className="text-[10px] shrink-0 tabular-nums">
                    {comp.toFixed(1)}
                  </Badge>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
