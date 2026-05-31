"use client";

import { use, useEffect, useState } from "react";
import { getCharacters } from "@/lib/api";
import type { Character } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ROLE_LABEL: Record<string, { label: string; variant: "gold" | "destructive" | "stellar" | "ghost" }> = {
  protagonist: { label: "主角", variant: "gold" },
  antagonist: { label: "反派", variant: "destructive" },
  supporting: { label: "配角", variant: "stellar" },
};

function field(profile: Record<string, unknown>, key: string): string | null {
  const v = profile[key];
  return typeof v === "string" && v.trim() ? v : null;
}

export default function CharactersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [chars, setChars] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCharacters(id)
      .then(setChars)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-muted-foreground text-sm">加载中…</div>;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="font-serif text-2xl font-bold mb-6">角色 · {chars.length}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {chars.map((c) => {
          const role = ROLE_LABEL[c.role] ?? { label: c.role, variant: "ghost" as const };
          const vp = c.voice_profile ?? {};
          const personality = field(c.profile, "personality");
          const background = field(c.profile, "background");
          const goals = field(c.profile, "goals");
          const weaknesses = field(c.profile, "weaknesses");
          return (
            <Card key={c.character_id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-serif flex items-center gap-2">
                  {c.name}
                  <Badge variant={role.variant} className="text-[10px]">{role.label}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 text-sm">
                {personality && <Row label="性格" value={personality} />}
                {goals && <Row label="目标" value={goals} />}
                {background && <Row label="背景" value={background} />}
                {weaknesses && <Row label="软肋" value={weaknesses} />}

                {(vp.tone || vp.catchphrases?.length || vp.forbidden?.length) && (
                  <div className="mt-3 pt-3 border-t border-border/40 space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wide text-lymo-stellar-400 font-medium">对白指纹</div>
                    {vp.tone && <Row label="语气" value={vp.tone} small />}
                    {vp.sentence_style && <Row label="句式" value={vp.sentence_style} small />}
                    {vp.catchphrases && vp.catchphrases.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {vp.catchphrases.map((p, i) => (
                          <Badge key={i} variant="ghost" className="text-[10px]">{p}</Badge>
                        ))}
                      </div>
                    )}
                    {vp.forbidden && vp.forbidden.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {vp.forbidden.map((p, i) => (
                          <Badge key={i} variant="destructive" className="text-[10px]">忌：{p}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function Row({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className={small ? "text-xs" : ""}>
      <span className="text-muted-foreground">{label}：</span>
      <span className={small ? "text-muted-foreground/80" : ""}>{value}</span>
    </div>
  );
}
