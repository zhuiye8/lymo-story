"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  ScrollText,
  LineChart,
  BookOpenText,
  Brain,
  Sparkles,
  ArrowLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface SidebarProps {
  storyId: string;
  storyTitle?: string;
  chapterCount?: number;
}

const ITEMS = [
  { slug: "", label: "仪表盘", icon: LayoutDashboard },
  { slug: "outline", label: "大纲", icon: ScrollText },
  { slug: "characters", label: "角色", icon: Users },
  { slug: "chapters", label: "章节", icon: BookOpenText },
  { slug: "quality", label: "质量", icon: LineChart },
  { slug: "memory", label: "记忆", icon: Brain },
  { slug: "foreshadowing", label: "伏笔", icon: Sparkles },
];

export function DashboardSidebar({ storyId, storyTitle, chapterCount }: SidebarProps) {
  const pathname = usePathname();
  const base = `/stories/${storyId}`;

  return (
    <aside className="w-56 shrink-0 border-r border-border/60 bg-card/30 backdrop-blur sticky top-14 h-[calc(100vh-56px)] flex flex-col">
      <div className="p-4 border-b border-border/40">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition mb-2"
        >
          <ArrowLeft className="size-3" />
          书斋
        </Link>
        <h2 className="font-serif font-bold text-base line-clamp-2 leading-snug">
          {storyTitle || "加载中..."}
        </h2>
        {typeof chapterCount === "number" && (
          <Badge variant="ghost" className="mt-2 text-[10px]">
            <BookOpenText className="size-2.5 mr-1" />
            {chapterCount} 章
          </Badge>
        )}
      </div>

      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {ITEMS.map((item) => {
          const href = item.slug ? `${base}/${item.slug}` : base;
          const active =
            item.slug === ""
              ? pathname === base
              : pathname.startsWith(`${base}/${item.slug}`);
          const Icon = item.icon;
          return (
            <Link
              key={item.slug || "root"}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
              )}
            >
              <Icon className="size-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border/40 text-[10px] text-muted-foreground/60 text-center font-serif">
        狸梦 · Lymo
      </div>
    </aside>
  );
}
