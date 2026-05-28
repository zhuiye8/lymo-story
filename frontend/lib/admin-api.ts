const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// --- Model Config ---

export interface ModelConfig {
  id: string;
  display_name: string;
  litellm_model: string;
  api_key: string;
  api_base: string | null;
  max_tokens: number;
  default_temperature: number;
  cost_per_million_input: number;
  cost_per_million_input_cached?: number;
  cost_per_million_output: number;
  currency: string;
  is_active: boolean;
  provider?: string;
  provider_options?: Record<string, string | number | boolean>;
}

export async function listModels(): Promise<ModelConfig[]> {
  return fetchJson(`${API_BASE}/admin/models`);
}

export async function createModel(config: ModelConfig): Promise<void> {
  await fetchJson(`${API_BASE}/admin/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export async function updateModel(id: string, config: ModelConfig): Promise<void> {
  await fetchJson(`${API_BASE}/admin/models/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export async function deleteModel(id: string): Promise<void> {
  await fetchJson(`${API_BASE}/admin/models/${id}`, { method: "DELETE" });
}

export interface ModelTestResult {
  success: boolean;
  model_id: string;
  litellm_model: string;
  response: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  message: string;
  error?: string;
}

export async function testModel(modelId: string): Promise<ModelTestResult> {
  return fetchJson(`${API_BASE}/admin/models/${modelId}/test`, {
    method: "POST",
  });
}

// --- DeepSeek one-click setup ---

export interface DeepSeekTierBinding {
  model_id: string;
  tier: number;
  label: string;
  desc: string;
  agents: string[];
}

export async function getDeepSeekTierBindings(): Promise<{ tier_bindings: DeepSeekTierBinding[] }> {
  return fetchJson(`${API_BASE}/admin/providers/deepseek/tier-bindings`);
}

export async function seedDeepSeek(
  apiKey: string,
  applyTierBindings: boolean = true
): Promise<{ message: string; seeded_models: { id: string; display_name: string }[]; bindings_applied: number }> {
  return fetchJson(`${API_BASE}/admin/providers/deepseek/seed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey, apply_tier_bindings: applyTierBindings }),
  });
}

// --- Agent Bindings ---

export interface AgentBinding {
  agent_name: string;
  model_config_id: string;
  model_display_name?: string;
  litellm_model?: string;
  temperature_override: number | null;
  max_tokens_override: number | null;
}

export interface BindingsResponse {
  agents: string[];
  bindings: AgentBinding[];
}

export async function getBindings(): Promise<BindingsResponse> {
  return fetchJson(`${API_BASE}/admin/bindings`);
}

export async function bindAgent(
  agentName: string,
  modelConfigId: string,
  temperatureOverride?: number | null,
  maxTokensOverride?: number | null,
): Promise<void> {
  await fetchJson(`${API_BASE}/admin/bindings/${agentName}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_config_id: modelConfigId,
      temperature_override: temperatureOverride ?? null,
      max_tokens_override: maxTokensOverride ?? null,
    }),
  });
}

export async function unbindAgent(agentName: string): Promise<void> {
  await fetchJson(`${API_BASE}/admin/bindings/${agentName}`, { method: "DELETE" });
}

// --- Logs ---

export interface LLMLogEntry {
  id: number;
  story_id: string | null;
  chapter_num: number | null;
  agent_name: string;
  model_config_id: string;
  litellm_model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_estimate: number;
  latency_ms: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface LLMLogDetail extends LLMLogEntry {
  system_prompt: string;
  user_prompt: string;
  response: string;
}

export async function getLogs(params?: {
  agent_name?: string;
  story_id?: string;
  limit?: number;
  offset?: number;
}): Promise<LLMLogEntry[]> {
  const searchParams = new URLSearchParams();
  if (params?.agent_name) searchParams.set("agent_name", params.agent_name);
  if (params?.story_id) searchParams.set("story_id", params.story_id);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());
  return fetchJson(`${API_BASE}/admin/logs?${searchParams}`);
}

export async function getLogDetail(logId: number): Promise<LLMLogDetail> {
  return fetchJson(`${API_BASE}/admin/logs/${logId}`);
}

// --- Usage ---

export interface UsageStatEntry {
  group_key: string;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
}

export interface UsageResponse {
  stats: UsageStatEntry[];
  total: {
    total_calls: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_tokens: number;
    total_cost: number;
    avg_latency_ms: number;
  };
}

export async function getUsage(
  groupBy: string = "agent",
  days: number = 7,
): Promise<UsageResponse> {
  return fetchJson(`${API_BASE}/admin/usage?group_by=${groupBy}&days=${days}`);
}

// --- Generation Settings ---

export interface GenerationSettings {
  max_consistency_retries: number;
  default_chapter_word_count: number;
  chapter_consistency_threshold: number;
  chapter_max_critical: number;
  chapter_max_warnings: number;
  scene_consistency_threshold: number;
}

export async function getGenerationSettings(): Promise<GenerationSettings> {
  return fetchJson(`${API_BASE}/admin/settings`);
}

export async function updateGenerationSettings(
  settings: Partial<GenerationSettings>
): Promise<{ message: string; updated: Partial<GenerationSettings> }> {
  return fetchJson(`${API_BASE}/admin/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

// --- Quality Dashboard (AC5, Phase 0) ---

export interface QualityResponseEnvelope<T> {
  batch_id: number;
  rubric_version: string;
  detector_version: string;
  judge_model: string;
  generated_at: string;
  data_ready: boolean;
  reason?: string | null;
  data: T | null;
}

export interface BatchSummary {
  id: number;
  batch_label: string;
  rubric_version: string;
  detector_version: string;
  judge_model: string;
  scope_chapter_count: number;
  status: string;
  started_at: string;
  finished_at?: string | null;
}

export interface StatBlock {
  mean: number;
  variance: number;
  stdev: number;
  min: number;
  max: number;
}

export interface CompositeStatBlock extends StatBlock {
  slope_per_chapter: number;
  first_half_mean: number;
  second_half_mean: number;
  delta: number;
}

export interface TrendPoint {
  chapter_num: number;
  word_count: number;
  composite_score: number;
  mean_quality: number;
  slop_penalty: number;
}

export interface TrendStory {
  story_id: string;
  story_title: string;
  n_chapters: number;
  chapters: TrendPoint[];
  aggregates: {
    composite: CompositeStatBlock;
    mean_quality: StatBlock;
    slop_penalty: StatBlock;
    word_count: StatBlock;
  };
}

export interface TrendData {
  stories: TrendStory[];
}

export interface PerStoryDim {
  story_id: string;
  story_title?: string;
  n_chapters: number;
  scores: Record<string, StatBlock>;
}

export interface ByDimensionData {
  dimensions: string[];
  per_story: PerStoryDim[];
  global: PerStoryDim;
}

export interface HeatmapData {
  story_id: string;
  story_title: string;
  dimensions: string[];
  chapters: number[];
  matrix: number[][];
  meta: { score_range: [number, number]; color_scheme_hint: string };
  evidence?: Record<string, Record<string, string>>;
}

export interface HistBin {
  bin_low: number;
  bin_high: number;
  count: number;
}

export interface DistributionData {
  composite_histogram: HistBin[];
  slop_histogram: HistBin[];
  per_dimension_histograms: Record<string, HistBin[]>;
  totals: { n_chapters: number; n_stories: number };
}

const QUALITY_BASE = `${API_BASE}/admin/quality`;

export async function listQualityBatches(): Promise<{ batches: BatchSummary[] }> {
  return fetchJson(`${QUALITY_BASE}/batches`);
}

export async function getQualityTrend(
  batchId: number
): Promise<QualityResponseEnvelope<TrendData>> {
  return fetchJson(`${QUALITY_BASE}/batch/${batchId}/trend`);
}

export async function getQualityByDimension(
  batchId: number
): Promise<QualityResponseEnvelope<ByDimensionData>> {
  return fetchJson(`${QUALITY_BASE}/batch/${batchId}/by-dimension`);
}

export async function getQualityHeatmap(
  batchId: number,
  storyId: string
): Promise<QualityResponseEnvelope<HeatmapData>> {
  return fetchJson(
    `${QUALITY_BASE}/batch/${batchId}/heatmap?story_id=${encodeURIComponent(storyId)}`
  );
}

export async function getQualityDistribution(
  batchId: number
): Promise<QualityResponseEnvelope<DistributionData>> {
  return fetchJson(`${QUALITY_BASE}/batch/${batchId}/distribution`);
}
