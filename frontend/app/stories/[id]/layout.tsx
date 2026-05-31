"use client";

import { use, useEffect, useState } from "react";
import { DashboardSidebar } from "@/components/lymo/dashboard-sidebar";
import { getStory, getProgress } from "@/lib/api";

export default function StoryLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [title, setTitle] = useState<string>("");
  const [chapters, setChapters] = useState<number>(0);

  useEffect(() => {
    let alive = true;
    getStory(id)
      .then((s) => alive && setTitle(s.title))
      .catch(() => {});
    getProgress(id)
      .then((p) => alive && setChapters(p.chapter_count))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [id]);

  return (
    <div className="flex min-h-[calc(100vh-56px)]">
      <DashboardSidebar storyId={id} storyTitle={title} chapterCount={chapters} />
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}
