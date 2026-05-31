// Phase 1 类型契约。对应 backend/api/phase1_stories.py + quality_admin.py 的实际返回。
// 旧 Phase 0 类型（KnowledgeGraph/VersionTree/Arc 等）已随后端移除而删除。

export interface StorySummary {
  id: string;
  title: string;
  genre: string;
  theme: string;
  status: string; // created/initializing/bible_ready/writing/...
  created_at: string;
  updated_at: string;
}

// getStory 额外带 bible（已组装的 StoryBible）
export interface StoryDetail extends StorySummary {
  bible: StoryBible | Record<string, unknown>;
}

export interface SpecialAbility {
  name?: string;
  description?: string;
  rules?: string[];
  [k: string]: unknown;
}

export interface PowerSystem {
  name?: string;
  levels?: string[];
  [k: string]: unknown;
}

export interface StoryBible {
  concept?: {
    title?: string;
    genre?: string;
    tone?: string;
    logline?: string;
    synopsis?: string;
    blurb?: string;
    selling_points?: string[];
    special_ability?: SpecialAbility;
    [k: string]: unknown;
  };
  world?: {
    background?: string;
    power_system?: PowerSystem;
    factions?: Array<Record<string, unknown>>;
    rules?: string[];
    [k: string]: unknown;
  };
  characters?: Record<string, unknown>;
  outline?: Record<string, unknown>;
  [k: string]: unknown;
}

// ---- progress ----
export interface StageInfo {
  name: string;
  label: string;
  status: string; // pending/running/done/error
  detail?: string;
  duration_ms?: number;
}

export interface GenerationProgress {
  story_id: string;
  chapter_num: number;
  elapsed_seconds: number;
  finished: boolean;
  current_stage: string | null;
  current_stage_label: string | null;
  error: string | null;
  stages: StageInfo[];
}

export interface ProgressResponse {
  progress: GenerationProgress | null;
  status: string | null;
  chapter_count: number;
}

// ---- characters ----
export interface VoiceProfile {
  tone?: string;
  catchphrases?: string[];
  sentence_style?: string;
  vocabulary?: string[];
  forbidden?: string[];
  [k: string]: unknown;
}

export interface Character {
  character_id: string;
  name: string;
  role: string;
  profile: Record<string, unknown>;
  voice_profile: VoiceProfile;
}

// ---- outline ----
export interface OutlineStage {
  stage_num?: number;
  stage_name: string;
  summary: string;
  chapter_start?: number;
  chapter_end?: number;
  [k: string]: unknown;
}

// ---- chapters ----
export interface ChapterQuality {
  composite_score?: number;
  composite_final?: number;
  mean_quality?: number;
  slop_penalty?: number;
  word_count?: number;
  consistency_conflicts?: number;
  dim_scores?: Record<string, number>;
  judges?: string[];
  [k: string]: unknown;
}

export interface ChapterSummary {
  chapter_num: number;
  title: string;
  pov: string;
  word_count: number;
  summary: string;
  quality_json: string; // 需 JSON.parse
  is_published: number;
  created_at: string;
}

export interface ChapterDetail extends ChapterSummary {
  content: string;
}

// ---- foreshadowing ----
export interface Foreshadow {
  id: number;
  description: string;
  planted_chapter: number;
  status: "open" | "resolved";
  resolved_chapter: number | null;
  age?: number;
}

export interface ForeshadowingResponse {
  items: Foreshadow[];
  total: number;
  open: number;
  resolved: number;
}

// ---- memories ----
export interface Memory {
  id: number;
  character_id: string;
  character_name: string;
  layer: number; // 0 身份核心 / 1 情感关键
  content: string;
  emotional_weight: number;
  source_chapter: number;
}

export interface MemoriesResponse {
  items: Memory[];
  counts: Record<string, number>; // {L0: n, L1: n}
}

// ---- quality dashboard ----
export interface StatBlock {
  mean?: number;
  min?: number;
  max?: number;
  std?: number;
  n?: number;
  slope_per_chapter?: number;
  first_half_mean?: number;
  second_half_mean?: number;
  delta?: number;
  [k: string]: number | undefined;
}

export interface QualityStory {
  story_id: string;
  title: string | null;
  n_chapters: number;
  avg_composite: number | null;
}

export interface TrendResponse {
  story_id: string;
  data_ready: boolean;
  reason: string | null;
  data: {
    chapters: Array<{
      chapter_num: number;
      composite_score: number;
      mean_quality: number;
      slop_penalty: number;
      word_count: number;
    }>;
    aggregates: Record<string, StatBlock>;
  } | null;
}

export interface ByDimensionResponse {
  story_id: string;
  data_ready: boolean;
  reason: string | null;
  data: {
    dimensions: string[];
    labels: Record<string, string>;
    per_dimension: Record<string, StatBlock>;
  } | null;
}

export interface HeatmapResponse {
  story_id: string;
  data_ready: boolean;
  reason: string | null;
  data: {
    chapters: number[];
    dimensions: string[];
    labels: Record<string, string>;
    matrix: number[][];
    meta: { score_range: [number, number]; color_scheme_hint: string };
  } | null;
}

export interface DistributionResponse {
  story_id: string;
  data_ready: boolean;
  reason: string | null;
  data: {
    composite_histogram: { bins: number[]; counts: number[] } | Record<string, unknown>;
    slop_histogram: { bins: number[]; counts: number[] } | Record<string, unknown>;
    totals: { n_chapters: number };
  } | null;
}
