"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Copy, Check } from "lucide-react";
import { listChapters, getChapter, parseQuality } from "@/lib/api";
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
  const [copied, setCopied] = useState<number | null>(null);

  useEffect(() => {
    listChapters(id)
      .then(setChapters)
      .finally(() => setLoading(false));
  }, [id]);

  async function copyRow(num: number) {
    try {
      const ch = await getChapter(id, num);   // 列表无正文，复制时即时拉取
      await navigator.clipboard.writeText(ch.content);
      setCopied(num);
      setTimeout(() => setCopied((c) => (c === num ? null : c)), 1800);
    } catch {
      alert("复制失败，请打开该章手动复制");
    }
  }

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
              <div
                key={c.chapter_num}
                className="card-hover flex items-center gap-3 rounded-lg border border-border/50 bg-card/30 px-4 py-3"
              >
                <Link
                  href={`/stories/${id}/chapters/${c.chapter_num}`}
                  className="flex items-center gap-3 flex-1 min-w-0"
                >
                  <BookOpen className="size-4 text-muted-foreground/50 shrink-0" />
                  <span className="text-sm text-muted-foreground tabular-nums shrink-0">第 {c.chapter_num} 章</span>
                  <span className="truncate flex-1 font-medium">{c.title}</span>
                </Link>
                <span className="text-xs text-muted-foreground/60 shrink-0">{c.word_count} 字</span>
                {comp != null && (
                  <Badge variant={scoreColor(comp)} className="text-[10px] shrink-0 tabular-nums">
                    {comp.toFixed(1)}
                  </Badge>
                )}
                <button
                  onClick={() => copyRow(c.chapter_num)}
                  title="复制正文"
                  className="shrink-0 p-1.5 rounded-md text-muted-foreground/60 hover:text-lymo-gold-400 hover:bg-secondary/50 transition-colors"
                >
                  {copied === c.chapter_num ? (
                    <Check className="size-4 text-lymo-jade-400" />
                  ) : (
                    <Copy className="size-4" />
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
