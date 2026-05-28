import type {
  CharacterWithArc,
  ChapterDetail,
  ChapterSummary,
  ChapterVersionDetail,
  ChapterVersionSummary,
  GenerationStatus,
  KnowledgeGraphData,
  StoryBibleV2,
  StoryEvent,
  StoryResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function createStory(
  theme: string,
  requirements: string = "",
  title: string = "",
  skipInit: boolean = false,
): Promise<StoryResponse> {
  return fetchJson(`${API_BASE}/stories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, requirements, title, skip_init: skipInit }),
  });
}

export async function updateBible(
  storyId: string,
  bible: Record<string, unknown>
): Promise<{ message: string; title: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/bible`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bible),
  });
}

export async function importOutline(
  storyId: string,
  rawText: string,
  title: string = ""
): Promise<{ story_id: string; title: string; status: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/import-outline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText, title }),
  });
}

export async function listStories(): Promise<StoryResponse[]> {
  return fetchJson(`${API_BASE}/stories`);
}

export async function getStory(storyId: string): Promise<StoryResponse> {
  return fetchJson(`${API_BASE}/stories/${storyId}`);
}

export async function deleteStory(storyId: string): Promise<void> {
  await fetchJson(`${API_BASE}/stories/${storyId}`, { method: "DELETE" });
}

export async function regenerateOutline(
  storyId: string,
  userInstructions: string = ""
): Promise<{ message: string; volumes_count: number; history_count: number }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/outline/regenerate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_instructions: userInstructions }),
  });
}

export async function cloneStoryOutline(
  storyId: string,
  titleSuffix: string = "（分支）"
): Promise<{ message: string; new_story_id: string; new_title: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/clone-outline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title_suffix: titleSuffix }),
  });
}

export async function deleteChaptersFrom(
  storyId: string,
  fromChapter: number
): Promise<{ message: string; deleted_count: number; from_chapter: number }> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/from/${fromChapter}`,
    { method: "DELETE" }
  );
}

export async function getStoryBible(storyId: string): Promise<StoryBibleV2> {
  return fetchJson(`${API_BASE}/stories/${storyId}/bible`);
}

export async function listChapters(
  storyId: string
): Promise<ChapterSummary[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters`);
}

export async function getChapter(
  storyId: string,
  num: number
): Promise<ChapterDetail> {
  return fetchJson(`${API_BASE}/stories/${storyId}/chapters/${num}`);
}

export async function triggerGeneration(
  storyId: string,
  wordCount?: number
): Promise<{ message: string; chapter_num: number; word_count?: number }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(wordCount ? { word_count: wordCount } : {}),
  });
}

export async function getStatus(storyId: string): Promise<GenerationStatus> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/status`);
}

export async function cancelGeneration(
  storyId: string
): Promise<{ story_id: string; cancelled: boolean; message: string }> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/cancel`, {
    method: "POST",
  });
}

export async function publishStory(
  storyId: string,
  publish: boolean
): Promise<void> {
  await fetchJson(`${API_BASE}/stories/${storyId}/publish`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ publish }),
  });
}

export async function publishChapter(
  storyId: string,
  chapterNum: number,
  publish: boolean
): Promise<void> {
  await fetchJson(`${API_BASE}/stories/${storyId}/chapters/${chapterNum}/publish`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ publish }),
  });
}

export interface StageProgress {
  name: string;
  label: string;
  status: string; // pending / running / done / error
  detail: string;
  duration_ms: number;
}

export interface GenerationProgressData {
  story_id: string;
  chapter_num: number;
  elapsed_seconds: number;
  current_stage: string | null;
  current_stage_label: string | null;
  error: string | null;
  stages: StageProgress[];
}

export async function getProgress(storyId: string): Promise<GenerationProgressData> {
  return fetchJson(`${API_BASE}/stories/${storyId}/control/progress`);
}

export async function regenerateChapter(
  storyId: string,
  chapterNum: number,
  feedback: string,
  chaptersToInvalidate?: number[]
): Promise<{ message: string; chapter_num: number; cascade_invalidated: number[] }> {
  const body: Record<string, unknown> = { feedback };
  if (chaptersToInvalidate !== undefined) {
    body.chapters_to_invalidate = chaptersToInvalidate;
  }
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
}

export interface AffectedChapterInfo {
  chapter_num: number;
  source_version_id: number;
  dep_chapters: number[];
  memory_count: number;
  triple_count: number;
  state_count: number;
  summary_exists: boolean;
  brief: string;
}

export interface RegeneratePlanResponse {
  target_chapter: number;
  target_current_version_id: number | null;
  affected_chapters: AffectedChapterInfo[];
}

export async function getRegeneratePlan(
  storyId: string,
  chapterNum: number,
): Promise<RegeneratePlanResponse> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/regenerate/plan`,
  );
}

export async function listChapterVersions(
  storyId: string,
  chapterNum: number
): Promise<ChapterVersionSummary[]> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/versions`
  );
}

export async function getChapterVersion(
  storyId: string,
  chapterNum: number,
  versionId: number
): Promise<ChapterVersionDetail> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/versions/${versionId}`
  );
}

export async function restoreChapterVersion(
  storyId: string,
  chapterNum: number,
  versionId: number
): Promise<{ message: string; version_num: number }> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/chapters/${chapterNum}/restore/${versionId}`,
    { method: "POST" }
  );
}

export async function getCharacterArcHistory(
  storyId: string,
  characterId: string
): Promise<{ arcs: any[]; states: any[] }> {
  return fetchJson(
    `${API_BASE}/stories/${storyId}/character-arcs/${characterId}`
  );
}

// --- Visualization APIs ---

export async function getCharacters(
  storyId: string
): Promise<CharacterWithArc[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/characters`);
}

export async function getKnowledgeGraph(
  storyId: string,
  asOfChapter?: number
): Promise<KnowledgeGraphData> {
  const url = new URL(`${API_BASE}/stories/${storyId}/knowledge-graph`);
  if (asOfChapter != null) url.searchParams.set("as_of_chapter", String(asOfChapter));
  return fetchJson(url.toString());
}

export async function getEvents(storyId: string): Promise<StoryEvent[]> {
  return fetchJson(`${API_BASE}/stories/${storyId}/events`);
}

export interface VersionTreeVersion {
  id: number;
  chapter_num: number;
  version_num: number;
  title: string;
  pov: string;
  word_count: number;
  feedback: string;
  is_live: number;
  created_at: string;
}

export interface VersionTreeDep {
  chapter_num: number;
  source_version_id: number;
  depends_on_chapter: number;
  depends_on_version_id: number;
  dep_type: string;
}

export interface VersionTreeData {
  chapters: { chapter_num: number; versions: VersionTreeVersion[] }[];
  dependencies: VersionTreeDep[];
}

export async function getVersionTree(storyId: string): Promise<VersionTreeData> {
  return fetchJson(`${API_BASE}/stories/${storyId}/version-tree`);
}
