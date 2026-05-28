"use client";

import { useEffect, useState } from "react";
import {
  getDeepSeekTierBindings,
  seedDeepSeek,
  type DeepSeekTierBinding,
} from "@/lib/admin-api";
import { agentLabel } from "@/lib/agent-labels";

interface Props {
  onApplied?: () => void;
}

const TIER_COLORS: Record<number, { bg: string; border: string; text: string; accent: string }> = {
  1: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-900",
    accent: "bg-amber-500",
  },
  2: {
    bg: "bg-rose-50",
    border: "border-rose-300",
    text: "text-rose-900",
    accent: "bg-rose-500",
  },
  3: {
    bg: "bg-sky-50",
    border: "border-sky-300",
    text: "text-sky-900",
    accent: "bg-sky-500",
  },
};

export default function DeepSeekSetupPanel({ onApplied }: Props) {
  const [apiKey, setApiKey] = useState("");
  const [applyBindings, setApplyBindings] = useState(true);
  const [tiers, setTiers] = useState<DeepSeekTierBinding[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    getDeepSeekTierBindings()
      .then((r) => setTiers(r.tier_bindings))
      .catch(console.error);
  }, []);

  const handleSeed = async () => {
    if (!apiKey.trim()) {
      setMessage("请输入 DeepSeek API Key");
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const r = await seedDeepSeek(apiKey.trim(), applyBindings);
      setMessage(r.message);
      setApiKey("");
      onApplied?.();
    } catch (e) {
      setMessage(`失败：${(e as Error).message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border rounded-lg bg-gradient-to-br from-indigo-50 via-white to-white p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold">
              DS
            </span>
            DeepSeek 一键分层配置
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            自动导入 4 个 V4 模型预设 + 按 Tier 1/2/3 分配 16 个 Agent
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-indigo-600 hover:underline"
        >
          {expanded ? "收起" : "展开"}
        </button>
      </div>

      {expanded && (
        <>
          {/* Tier previews */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            {tiers.map((t) => {
              const c = TIER_COLORS[t.tier] || TIER_COLORS[3];
              return (
                <div
                  key={t.model_id}
                  className={`relative rounded-lg p-3 border ${c.bg} ${c.border}`}
                >
                  <div className={`absolute top-0 left-0 w-1 h-full rounded-l ${c.accent}`} />
                  <div className="pl-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`font-bold text-sm ${c.text}`}>{t.label}</span>
                      <span className="text-[10px] font-mono text-gray-500">
                        {t.agents.length} agents
                      </span>
                    </div>
                    <div className="text-[11px] text-gray-600 mb-2">{t.desc}</div>
                    <div className="text-[10px] font-mono text-gray-500 mb-2 break-all">
                      → {t.model_id}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {t.agents.map((a) => (
                        <span
                          key={a}
                          className="text-[10px] px-1.5 py-0.5 bg-white border border-gray-300 rounded"
                          title={agentLabel(a)}
                        >
                          {agentLabel(a).split("（")[0]}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* API Key input */}
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                DeepSeek API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                disabled={submitting}
                className="w-full p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-50"
              />
              <p className="text-[10px] text-gray-400 mt-1">
                从 platform.deepseek.com 获取。会自动填入 4 个模型预设。
              </p>
            </div>

            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={applyBindings}
                onChange={(e) => setApplyBindings(e.target.checked)}
                disabled={submitting}
                className="rounded"
              />
              <span>同时应用 Tier 1/2/3 Agent 绑定（推荐）</span>
            </label>

            {message && (
              <div
                className={`text-xs p-2 rounded border ${
                  message.startsWith("失败")
                    ? "bg-red-50 border-red-200 text-red-700"
                    : "bg-emerald-50 border-emerald-200 text-emerald-700"
                }`}
              >
                {message}
              </div>
            )}

            <button
              onClick={handleSeed}
              disabled={submitting || !apiKey.trim()}
              className="w-full py-2 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {submitting ? "导入中..." : "一键导入 + 分层绑定"}
            </button>
            <p className="text-[10px] text-gray-400 text-center">
              已存在的模型不会被覆盖。可在下方「模型配置」单独微调每个模型。
            </p>
          </div>
        </>
      )}
    </div>
  );
}
