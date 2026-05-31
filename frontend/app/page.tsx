"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, BookText, Loader2, Sparkles } from "lucide-react";
import { listStories, createStory } from "@/lib/api";
import type { StorySummary } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";

const STATUS: Record<string, { label: string; variant: "gold" | "stellar" | "jade" | "destructive" | "ghost" }> = {
  created: { label: "已创建", variant: "ghost" },
  initializing: { label: "初始化中", variant: "stellar" },
  bible_ready: { label: "待生成", variant: "gold" },
  writing: { label: "写作中", variant: "jade" },
  init_failed: { label: "初始化失败", variant: "destructive" },
};

function statusOf(s: string) {
  return STATUS[s] ?? { label: s, variant: "ghost" as const };
}

export default function HomePage() {
  const router = useRouter();
  const [stories, setStories] = useState<StorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [theme, setTheme] = useState("");
  const [genre, setGenre] = useState("男频系统流");
  const [requirements, setRequirements] = useState("");
  const [targetChapters, setTargetChapters] = useState(60);

  async function reload() {
    try {
      setStories(await listStories());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
    const t = setInterval(reload, 5000); // 轮询，初始化完成后状态会变
    return () => clearInterval(t);
  }, []);

  async function submit() {
    if (!theme.trim()) return;
    setSubmitting(true);
    try {
      const r = await createStory({
        theme: theme.trim(),
        genre,
        requirements: requirements.trim(),
        target_chapters: targetChapters,
      });
      setOpen(false);
      setTheme("");
      setRequirements("");
      router.push(`/stories/${r.story_id}`);
    } catch (e) {
      alert(`创建失败：${e instanceof Error ? e.message : e}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="font-serif text-3xl font-bold text-gold-grad">书斋</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            狸梦 · 多智能体中文小说生成
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="gold" size="lg">
              <Plus className="size-4 mr-1.5" />
              新建故事
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="font-serif flex items-center gap-2">
                <Sparkles className="size-4 text-lymo-gold-400" />
                新建故事
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label htmlFor="theme">题材想法 *</Label>
                <Textarea
                  id="theme"
                  placeholder="例如：落魄程序员觉醒代码编辑器系统，能改写现实的源码"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="genre">题材类型</Label>
                  <Input id="genre" value={genre} onChange={(e) => setGenre(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="chapters">目标章数</Label>
                  <Input
                    id="chapters"
                    type="number"
                    value={targetChapters}
                    onChange={(e) => setTargetChapters(parseInt(e.target.value || "60", 10))}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="req">额外要求</Label>
                <Input
                  id="req"
                  placeholder="爽文，节奏快，有脑洞"
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={submit} disabled={submitting || !theme.trim()} variant="gold">
                {submitting && <Loader2 className="size-4 mr-1.5 animate-spin" />}
                创建并初始化
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-muted-foreground text-sm">加载中…</div>
      ) : stories.length === 0 ? (
        <div className="text-center py-24 text-muted-foreground">
          <BookText className="size-10 mx-auto mb-3 opacity-40" />
          还没有故事，点击右上角新建一个吧。
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {stories.map((s) => {
            const st = statusOf(s.status);
            return (
              <Link key={s.id} href={`/stories/${s.id}`}>
                <div className="card-hover h-full rounded-xl border border-border/60 bg-card/40 p-5 flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-serif font-bold text-lg leading-snug line-clamp-2">
                      {s.title || "未命名"}
                    </h3>
                    <Badge variant={st.variant} className="shrink-0 text-[10px]">
                      {st.label}
                    </Badge>
                  </div>
                  {s.genre && <Badge variant="ghost" className="w-fit text-[10px]">{s.genre}</Badge>}
                  <p className="text-sm text-muted-foreground line-clamp-3 flex-1">
                    {s.theme || "（无题材描述）"}
                  </p>
                  <div className="text-[11px] text-muted-foreground/60">
                    {new Date(s.created_at).toLocaleString("zh-CN")}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
