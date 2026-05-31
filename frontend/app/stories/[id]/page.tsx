"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Play, Loader2, CheckCircle2, AlertCircle, Circle, BookOpen } from "lucide-react";
import { getStory, getProgress, generateChapter, listChapters, parseQuality } from "@/lib/api";
import type { StoryDetail, ProgressResponse, ChapterSummary, StoryBible } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function StageRow({ status, label, detail }: { status: string; label: string; detail?: string }) {
  const Icon =
    status === "done" ? CheckCircle2 : status === "running" ? Loader2 : status === "error" ? AlertCircle : Circle;
  const color =
    status === "done"
      ? "text-lymo-jade-400"
      : status === "running"
      ? "text-lymo-gold-400"
      : status === "error"
      ? "text-destructive"
      : "text-muted-foreground/40";
  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <Icon className={`size-4 shrink-0 ${color} ${status === "running" ? "animate-spin" : ""}`} />
      <span className={status === "pending" ? "text-muted-foreground/50 text-sm" : "text-sm"}>{label}</span>
      {detail && <span className="text-xs text-muted-foreground/60 truncate">· {detail}</span>}
    </div>
  );
}

export default function Dashboard({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [prog, setProg] = useState<ProgressResponse | null>(null);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [targetWords, setTargetWords] = useState(3500);

  const refresh = useCallback(async () => {
    const [s, p, chs] = await Promise.all([
      getStory(id),
      getProgress(id),
      listChapters(id).catch(() => []),
    ]);
    setStory(s);
    setProg(p);
    setChapters(chs);
  }, [id]);

  const status = prog?.status ?? story?.status ?? "";
  // 是否真的在生成：看进度对象是否"未完成"，而不是看 story.status（status 完成后会复位）
  const generating = !!prog?.progress && !prog.progress.finished && !prog.progress.error;

  useEffect(() => {
    refresh().catch(() => {});
    const t = setInterval(() => refresh().catch(() => {}), generating ? 1500 : 4000);
    return () => clearInterval(t);
  }, [refresh, generating]);

  async function onGenerate() {
    setBusy(true);
    try {
      await generateChapter(id, targetWords);
      await refresh();
    } catch (e) {
      alert(`生成失败：${e instanceof Error ? e.message : e}`);
    } finally {
      setBusy(false);
    }
  }

  if (!story) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  const bible = (story.bible ?? {}) as StoryBible;
  const concept = bible.concept ?? {};
  const ability = concept.special_ability ?? {};
  const ready = status === "bible_ready" || status === "writing";
  const lastComposite = chapters.length
    ? (parseQuality(chapters[chapters.length - 1].quality_json).composite_final as number | undefined)
    : undefined;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold">{story.title || "未命名"}</h1>
          <div className="flex items-center gap-2 mt-2">
            {story.genre && <Badge variant="ghost" className="text-[10px]">{story.genre}</Badge>}
            <Badge variant={ready ? "gold" : "stellar"} className="text-[10px]">{status}</Badge>
          </div>
        </div>
        <div className="flex items-end gap-2 shrink-0">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-muted-foreground">单章目标字数</label>
            <Input
              type="number"
              value={targetWords}
              min={1500}
              step={500}
              disabled={generating}
              onChange={(e) => setTargetWords(parseInt(e.target.value || "3500", 10))}
              className="h-10 w-24 text-sm tabular-nums"
            />
          </div>
          <Button onClick={onGenerate} disabled={!ready || busy || generating} variant="gold" size="lg">
            {busy || generating ? <Loader2 className="size-4 mr-1.5 animate-spin" /> : <Play className="size-4 mr-1.5" />}
            {generating ? "生成中…" : `生成第 ${prog?.chapter_count ? prog.chapter_count + 1 : 1} 章`}
          </Button>
        </div>
      </div>

      {/* 立意卡片 */}
      {(concept.logline || ability.name) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-serif">立意</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {concept.logline && <p className="text-muted-foreground">{String(concept.logline)}</p>}
            {ability.name && (
              <div>
                <span className="text-lymo-gold-400 font-medium">金手指：</span>
                {String(ability.name)}
                {ability.description ? <span className="text-muted-foreground"> — {String(ability.description)}</span> : null}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 统计 */}
      <div className="grid grid-cols-3 gap-3">
        <Stat label="已写章节" value={prog?.chapter_count ?? 0} />
        <Stat label="最新质量分" value={lastComposite != null ? lastComposite.toFixed(2) : "—"} />
        <Stat label="目标章数" value={(bible.outline as Record<string, unknown>)?.target_chapters as number ?? "—"} />
      </div>

      {/* 生成进度 */}
      {prog?.progress && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-serif flex items-center justify-between">
              <span>第 {prog.progress.chapter_num} 章 · 生成管线</span>
              <span className="text-xs font-normal flex items-center gap-2">
                {prog.progress.error ? (
                  <Badge variant="destructive" className="text-[10px]">出错</Badge>
                ) : prog.progress.finished ? (
                  <Badge variant="jade" className="text-[10px]">已完成</Badge>
                ) : (
                  <Badge variant="gold" className="text-[10px]">生成中</Badge>
                )}
                <span className="text-muted-foreground tabular-nums">{prog.progress.elapsed_seconds}s</span>
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {prog.progress.error ? (
              <div className="text-destructive text-sm flex items-center gap-2">
                <AlertCircle className="size-4" /> {prog.progress.error}
              </div>
            ) : (
              <div className="divide-y divide-border/30">
                {prog.progress.stages.map((s) => (
                  <StageRow key={s.name} status={s.status} label={s.label} detail={s.detail} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 最近章节 */}
      {chapters.length > 0 && (
        <Card>
          <CardHeader className="pb-2 flex-row items-center justify-between">
            <CardTitle className="text-base font-serif">最近章节</CardTitle>
            <Link href={`/stories/${id}/chapters`} className="text-xs text-lymo-stellar-400 hover:underline">
              全部 →
            </Link>
          </CardHeader>
          <CardContent className="space-y-1">
            {chapters.slice(-5).reverse().map((c) => (
              <Link
                key={c.chapter_num}
                href={`/stories/${id}/chapters/${c.chapter_num}`}
                className="flex items-center gap-3 py-1.5 px-2 -mx-2 rounded hover:bg-secondary/40 text-sm"
              >
                <BookOpen className="size-3.5 text-muted-foreground/50" />
                <span className="text-muted-foreground tabular-nums">第{c.chapter_num}章</span>
                <span className="truncate flex-1">{c.title}</span>
                <span className="text-xs text-muted-foreground/60">{c.word_count}字</span>
              </Link>
            ))}
          </CardContent>
        </Card>
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
