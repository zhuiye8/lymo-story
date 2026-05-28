"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import ModelConfigPanel from "@/components/ModelConfigPanel";
import UsageDashboard from "@/components/UsageDashboard";
import DeepSeekSetupPanel from "@/components/DeepSeekSetupPanel";
import {
  listModels, createModel, updateModel, deleteModel,
  getBindings, bindAgent, unbindAgent,
  getUsage, getGenerationSettings, updateGenerationSettings,
  type ModelConfig, type AgentBinding, type UsageResponse, type GenerationSettings,
} from "@/lib/admin-api";

import { AGENT_LABELS } from "@/lib/agent-labels";

export default function AdminPage() {
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [bindings, setBindings] = useState<AgentBinding[]>([]);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [genSettings, setGenSettings] = useState<GenerationSettings | null>(null);
  const [settingsSaving, setSettingsSaving] = useState(false);

  const refresh = useCallback(async () => {
    const [m, b, u, gs] = await Promise.all([
      listModels(),
      getBindings(),
      getUsage(),
      getGenerationSettings().catch(() => null),
    ]);
    setModels(m);
    setAgents(b.agents);
    setBindings(b.bindings);
    setUsage(u);
    if (gs) setGenSettings(gs);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleSaveModel = async (model: ModelConfig) => {
    const exists = models.find((m) => m.id === model.id);
    if (exists) {
      await updateModel(model.id, model);
    } else {
      await createModel(model);
    }
    refresh();
  };

  const handleDeleteModel = async (id: string) => {
    if (confirm(`确定删除模型 "${id}"？关联的Agent绑定也会被清除。`)) {
      await deleteModel(id);
      refresh();
    }
  };

  const handleBindAgent = async (agentName: string, modelId: string) => {
    if (modelId === "") {
      await unbindAgent(agentName);
    } else {
      await bindAgent(agentName, modelId);
    }
    refresh();
  };

  const getBindingForAgent = (agentName: string) =>
    bindings.find((b) => b.agent_name === agentName);

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">LLM 管理中心</h1>
          <p className="text-gray-500 text-sm">模型配置、Agent绑定、用量监控</p>
        </div>
        <div className="flex gap-3">
          <Link href="/admin/quality" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            质量仪表盘
          </Link>
          <Link href="/admin/logs" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            请求日志
          </Link>
          <Link href="/" className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
            返回首页
          </Link>
        </div>
      </div>

      <div className="space-y-8">
        {/* DeepSeek one-click setup */}
        <DeepSeekSetupPanel onApplied={refresh} />

        {/* Model Configuration */}
        <section className="border rounded-lg p-6">
          <ModelConfigPanel
            models={models}
            onSave={handleSaveModel}
            onDelete={handleDeleteModel}
          />
        </section>

        {/* Agent Bindings */}
        <section className="border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Agent — 模型绑定</h3>
          <p className="text-sm text-gray-500 mb-4">
            未绑定的Agent使用环境变量中的默认模型
          </p>
          <div className="space-y-3">
            {agents.map((agent) => {
              const binding = getBindingForAgent(agent);
              return (
                <div key={agent} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                  <span className="w-32 font-medium text-sm">
                    {AGENT_LABELS[agent] || agent}
                  </span>
                  <span className="text-xs text-gray-400 w-24">{agent}</span>
                  <select
                    value={binding?.model_config_id || ""}
                    onChange={(e) => handleBindAgent(agent, e.target.value)}
                    className="flex-1 p-2 border rounded text-sm"
                  >
                    <option value="">默认模型（环境变量）</option>
                    {models.filter((m) => m.is_active).map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.display_name} ({m.litellm_model})
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        </section>

        {/* Usage Dashboard */}
        <section className="border rounded-lg p-6">
          <UsageDashboard usage={usage} />
        </section>

        {/* Generation Settings — consistency thresholds */}
        {genSettings && (
          <section className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">生成参数</h3>
            <p className="text-sm text-gray-500 mb-4">
              一致性阈值控制 AI 生成的质量门槛。降低阈值可以减少重试次数（省费用），但可能放过更多一致性问题。
              修改后立即生效（运行时），重启后恢复默认。
            </p>
            <div className="grid grid-cols-2 gap-4">
              <SettingSlider
                label="整章一致性阈值"
                hint="LLM 评分低于此值 → 整章重写。范围 0-100，默认 70"
                value={genSettings.chapter_consistency_threshold}
                min={0} max={100} step={5}
                display={(v) => `${v} 分`}
                onChange={(v) => setGenSettings({ ...genSettings, chapter_consistency_threshold: v })}
              />
              <SettingSlider
                label="场景一致性阈值"
                hint="场景评分低于此值 → 该场景重写。范围 0-1，默认 0.7"
                value={genSettings.scene_consistency_threshold}
                min={0} max={1} step={0.05}
                display={(v) => `${v.toFixed(2)}`}
                onChange={(v) => setGenSettings({ ...genSettings, scene_consistency_threshold: v })}
              />
              <SettingSlider
                label="最大 critical 问题数"
                hint="整章终检中允许的 critical 级问题数。0 = 不容忍任何 critical"
                value={genSettings.chapter_max_critical}
                min={0} max={5} step={1}
                display={(v) => `${v} 个`}
                onChange={(v) => setGenSettings({ ...genSettings, chapter_max_critical: v })}
              />
              <SettingSlider
                label="最大 warning 问题数"
                hint="整章终检中允许的 warning 级问题数。超过此数 → 整章重写"
                value={genSettings.chapter_max_warnings}
                min={0} max={20} step={1}
                display={(v) => `${v} 个`}
                onChange={(v) => setGenSettings({ ...genSettings, chapter_max_warnings: v })}
              />
              <SettingSlider
                label="最大重试次数"
                hint="整章一致性不通过时最多重试几次。0 = 不重试直接保存（带警告）"
                value={genSettings.max_consistency_retries}
                min={0} max={5} step={1}
                display={(v) => `${v} 次`}
                onChange={(v) => setGenSettings({ ...genSettings, max_consistency_retries: v })}
              />
            </div>
            <div className="mt-4 flex gap-3">
              <button
                onClick={async () => {
                  setSettingsSaving(true);
                  try {
                    await updateGenerationSettings(genSettings);
                    alert("设置已保存");
                  } catch (e) {
                    alert(`保存失败: ${(e as Error).message}`);
                  } finally {
                    setSettingsSaving(false);
                  }
                }}
                disabled={settingsSaving}
                className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
              >
                {settingsSaving ? "保存中..." : "保存设置"}
              </button>
              <button
                onClick={() => {
                  setGenSettings({
                    max_consistency_retries: 2,
                    default_chapter_word_count: 3000,
                    chapter_consistency_threshold: 70,
                    chapter_max_critical: 0,
                    chapter_max_warnings: 3,
                    scene_consistency_threshold: 0.7,
                  });
                }}
                className="px-4 py-2 border rounded text-sm hover:bg-gray-50"
              >
                恢复默认
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function SettingSlider({
  label,
  hint,
  value,
  min,
  max,
  step,
  display,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: (v: number) => string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm font-mono font-bold text-blue-600">{display(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-blue-600"
      />
      <p className="text-xs text-gray-400">{hint}</p>
    </div>
  );
}
