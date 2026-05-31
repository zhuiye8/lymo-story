"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { getChapter, parseQuality } from "@/lib/api";
import type { ChapterDetail, ChapterQuality } from "@/types";
import { Badge } from "@/components/ui/badge";

export default function ChapterReader({
  params,
}: {
  params: Promise<{ id: string; num: string }>;
}) {
  const { id, num } = use(params);
  const chapterNum = parseInt(num, 10);
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setChapter(null);
    setError(null);
    getChapter(id, chapterNum)
      .then(setChapter)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [id, chapterNum]);

  if (error) return <div className="p-8 text-destructive text-sm">{error}</div>;
  if (!chapter) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  const q = parseQuality(chapter.quality_json) as ChapterQuality;
  const comp = (q.composite_final ?? q.composite_score) as number | undefined;
  const paragraphs = chapter.content.split(/\n+/).filter((p) => p.trim());

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <Link
        href={`/stories/${id}/chapters`}
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="size-3" /> 章节列表
      </Link>

      <header className="mb-8 pb-5 border-b border-border/40">
        <div className="text-sm text-muted-foreground mb-1">第 {chapter.chapter_num} 章</div>
        <h1 className="font-serif text-3xl font-bold leading-snug">{chapter.title}</h1>
        <div className="flex flex-wrap items-center gap-2 mt-3">
          <Badge variant="ghost" className="text-[10px]">{chapter.word_count} 字</Badge>
          {comp != null && (
            <Badge variant={comp >= 7.5 ? "jade" : comp >= 6 ? "gold" : "destructive"} className="text-[10px]">
              质量 {comp.toFixed(2)}
            </Badge>
          )}
          {typeof q.slop_penalty === "number" && q.slop_penalty > 0 && (
            <Badge variant="destructive" className="text-[10px]">slop {q.slop_penalty.toFixed(1)}</Badge>
          )}
          {typeof q.consistency_conflicts === "number" && q.consistency_conflicts > 0 && (
            <Badge variant="destructive" className="text-[10px]">冲突 {q.consistency_conflicts}</Badge>
          )}
        </div>
      </header>

      <article className="font-serif text-[1.05rem] leading-[2] space-y-5 text-foreground/90">
        {paragraphs.map((p, i) => (
          <p key={i} className="indent-8">{p}</p>
        ))}
      </article>

      <nav className="flex items-center justify-between mt-12 pt-5 border-t border-border/40">
        {chapterNum > 1 ? (
          <Link href={`/stories/${id}/chapters/${chapterNum - 1}`}>
            <span className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
              <ChevronLeft className="size-4" /> 上一章
            </span>
          </Link>
        ) : <span />}
        <Link href={`/stories/${id}/chapters/${chapterNum + 1}`}>
          <span className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            下一章 <ChevronRight className="size-4" />
          </span>
        </Link>
      </nav>
    </div>
  );
}
