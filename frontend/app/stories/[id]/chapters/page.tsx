"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Copy, Check, ArrowLeft, Type } from "lucide-react";
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
  // 记录哪一章、哪种内容刚被复制（body=正文 / title=章节名），两个按钮各自反馈
  const [copied, setCopied] = useState<{ num: number; kind: "body" | "title" } | null>(null);

  useEffect(() => {
    listChapters(id)
      .then(setChapters)
      .finally(() => setLoading(false));
  }, [id]);

  function flash(num: number, kind: "body" | "title") {
    setCopied({ num, kind });
    setTimeout(() => setCopied((c) => (c && c.num === num && c.kind === kind ? null : c)), 1800);
  }

  async function copyBody(num: number) {
    try {
      const ch = await getChapter(id, num);   // 列表无正文，复制时即时拉取
      await navigator.clipboard.writeText(ch.content);
      flash(num, "body");
    } catch {
      alert("复制失败，请打开该章手动复制");
    }
  }

  async function copyTitle(num: number, title: string) {
    try {
      await navigator.clipboard.writeText(title);   // 章节名列表已有，无需拉取
      flash(num, "title");
    } catch {
      alert("复制失败");
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <Link
        href={`/stories/${id}`}
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="size-3" /> 返回仪表盘
      </Link>
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
                  onClick={() => copyTitle(c.chapter_num, c.title)}
                  title="复制章节名"
                  className="shrink-0 p-1.5 rounded-md text-muted-foreground/60 hover:text-lymo-gold-400 hover:bg-secondary/50 transition-colors"
                >
                  {copied?.num === c.chapter_num && copied.kind === "title" ? (
                    <Check className="size-4 text-lymo-jade-400" />
                  ) : (
                    <Type className="size-4" />
                  )}
                </button>
                <button
                  onClick={() => copyBody(c.chapter_num)}
                  title="复制正文"
                  className="shrink-0 p-1.5 rounded-md text-muted-foreground/60 hover:text-lymo-gold-400 hover:bg-secondary/50 transition-colors"
                >
                  {copied?.num === c.chapter_num && copied.kind === "body" ? (
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
