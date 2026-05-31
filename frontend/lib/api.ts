// Phase 1 API 客户端。对应 backend/api/phase1_stories.py（/api/stories）
// + quality_admin.py（/api/admin/quality）。旧 Phase 0 函数已全部移除。
import type {
  StorySummary,
  StoryDetail,
  ProgressResponse,
  Character,
  OutlineStage,
  ChapterSummary,
  ChapterDetail,
  ForeshadowingResponse,
  MemoriesResponse,
  QualityStory,
  TrendResponse,
  ByDimensionResponse,
  HeatmapResponse,
  DistributionResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

// ---------------- stories ----------------

export interface CreateStoryInput {
  theme: string;
  requirements?: string;
  genre?: string;
  target_chapters?: number;
  title?: string;
}

export async function createStory(
  input: CreateStoryInput,
): Promise<{ story_id: string; status: string }> {
  return fetchJson(`${API_BASE}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function listStories(): Promise<StorySummary[]> {
  return fetchJson(`${API_BASE}/stories`);
}

export async function getStory(storyId: string): Promise<StoryDetail> {
  return fetchJson(`${API_BASE}/stories/${storyId}`);
}

export async function renameStory(
  storyId: string,
  title: string,
): Promise<{ story_id: string; title: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/title`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export async function regenerateTitle(
  storyId: string,
): Promise<{ story_id: string; title: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/regenerate-title`, {
    method: "POST",
  });
}

export async function updateBlurb(
  storyId: string,
  blurb: string,
): Promise<{ story_id: string; blurb: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/blurb`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blurb }),
  });
}

export async function regenerateBlurb(
  storyId: string,
): Promise<{ story_id: string; blurb: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/regenerate-blurb`, {
    method: "POST",
  });
}

export async function getProgress(storyId: string): Promise<ProgressResponse> {
  return fetchJson(`${API_BASE}/stories/${storyId}/progress`);
}

export async function getCharacters(storyId: string): Promise<Character[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/characters`);
}

export async function getOutline(storyId: string): Promise<OutlineStage[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/outline`);
}

export async function generateChapter(
  storyId: string,
  targetWords = 3500,
): Promise<{ story_id: string; chapter_num: number; status: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_words: targetWords }),
  });
}

export async function listChapters(storyId: string): Promise<ChapterSummary[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters`);
}

export async function getChapter(
  storyId: string,
  num: number,
): Promise<ChapterDetail> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters/${num}`);
}

export async function getForeshadowing(
  storyId: string,
): Promise<ForeshadowingResponse> {
  return fetchJson(`${API_BASE}/stories/${storyId}/foreshadowing`);
}

export async function getMemories(storyId: string): Promise<MemoriesResponse> {
  return fetchJson(`${API_BASE}/stories/${storyId}/memories`);
}

// ---------------- quality dashboard ----------------

const Q_BASE = `${API_BASE}/admin/quality`;

export async function listQualityStories(): Promise<{ stories: QualityStory[] }> {
  return fetchJson(`${Q_BASE}/stories`);
}

export async function getQualityTrend(storyId: string): Promise<TrendResponse> {
  return fetchJson(`${Q_BASE}/story/${storyId}/trend`);
}

export async function getQualityByDimension(
  storyId: string,
): Promise<ByDimensionResponse> {
  return fetchJson(`${Q_BASE}/story/${storyId}/by-dimension`);
}

export async function getQualityHeatmap(
  storyId: string,
): Promise<HeatmapResponse> {
  return fetchJson(`${Q_BASE}/story/${storyId}/heatmap`);
}

export async function getQualityDistribution(
  storyId: string,
): Promise<DistributionResponse> {
  return fetchJson(`${Q_BASE}/story/${storyId}/distribution`);
}

// 解析章节 quality_json（字符串）→ 对象
export function parseQuality(raw: string | undefined | null): Record<string, unknown> {
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}
