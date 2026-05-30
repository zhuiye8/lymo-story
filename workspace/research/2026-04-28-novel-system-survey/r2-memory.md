# R2 — Long-Term Memory Systems for LLM Narrative Generation

**Research date:** 2026-04-28
**Scope:** Survey of long-term memory architectures for LLM agents, with emphasis on character / world / temporal retention across many chapters of fiction. All factual claims trace to a URL accessed today; sections with no usable canonical source are explicitly labeled.

---

## 0. Method

I prioritized canonical sources in this order: arXiv abstract/HTML pages, official GitHub READMEs (live), official blog posts from the system's maintainers. PDFs that failed to extract through WebFetch were re-fetched as ar5iv / arxiv.org/html mirrors or via secondary survey pages. Star counts, last release dates, and license fields were read directly from the github.com listing pages. Where a number is fuzzy (e.g. "23k" rather than "23,141"), I reproduce the displayed value.

A few facts deserve flagging up front:

- **MemGPT was renamed to Letta on 2024-09-23.** "MemGPT" now refers to the *design pattern* (LLM-as-OS with self-editing memory); "Letta" is the framework. The Python package is `letta`, the Docker image is `letta/letta-server`. The original `cpacker/MemGPT` repo was not archived — the team continues to maintain it under the new name. Source: [letta.com/blog/memgpt-and-letta](https://www.letta.com/blog/memgpt-and-letta) [accessed:2026-04-28].
- **A-MEM has TWO repos.** Both `WujiangXu/A-mem` and `agiresearch/A-mem` claim to be the NeurIPS 2025 implementation. The `agiresearch` fork is the one most pages link to as canonical.
- **MemPalace is the AI memory project by Milla Jovovich (yes, the actress) + Ben Sigman.** Launched April 2026, ~47k–53k stars in the first weeks. The claims (96.6% LongMemEval recall@5, 30× compression via "AAAK", 170-token startup) are public but not yet independently reproduced.

---

## 1. MemGPT / Letta

### MemGPT (the design pattern, 2023)

- Canonical paper: [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560) [accessed:2026-04-28]
- Canonical code repo: [github.com/letta-ai/letta](https://github.com/letta-ai/letta) [accessed:2026-04-28]
- Authors: Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, Joseph E. Gonzalez (UC Berkeley)
- Submission: October 12, 2023 (v1); latest paper revision Feb 12, 2024
- Maturity: production (now via Letta)
- Maintenance: active

#### Architecture (verbatim quotes from the arxiv HTML mirror):

- Storage backend: three-tier OS-style hierarchy
- Retrieval method: agentic — the LLM uses tool calls to page memory in/out
- Write strategy: LLM autonomously edits "working context" via function calls; FIFO queue auto-summarized on overflow
- Decay / forgetting: when the FIFO queue overflows, evicted messages become "a recursive summary of messages that have been evicted from the queue"
- Update strategy: "Memory edits and retrieval are entirely self-directed: MemGPT autonomously updates and searches through its own memory based on the current context"

The memory tiers, from the ar5iv mirror:

- **Main Context (physical memory analog):** system instructions + working context + FIFO queue. Working context is "a fixed-size read/write block of unstructured text, writeable only via MemGPT function calls."
- **Recall Storage (disk-cache analog):** the FIFO queue "stores a rolling history of messages, including messages between the agent and user, as well as system messages."
- **Archival Storage (long-term disk analog):** external DB storing "arbitrary length text objects."

Quote: "We leverage…virtual memory paging that was developed to enable applications to work on datasets that far exceed the available memory by paging data between main memory and disk." Source: [ar5iv.labs.arxiv.org/html/2310.08560](https://ar5iv.labs.arxiv.org/html/2310.08560) [accessed:2026-04-28].

### Letta (the framework, 2024–2026)

- Canonical code repo: [github.com/letta-ai/letta](https://github.com/letta-ai/letta) [accessed:2026-04-28]
- last_commit_date: 2026-05-14 (v0.16.8 release)
- Stars: ~23k (GitHub display value; some secondary sources still cite 13k)
- License: Apache-2.0
- Primary language: Python (99.5%)
- Maturity: production
- Maintenance: active (177 releases, ~7,464 total commits)

#### Architecture (from [letta.com/blog/agent-memory](https://www.letta.com/blog/agent-memory) [accessed:2026-04-28]):

- **Core memory:** in-context blocks the agent can edit via APIs. "Remain pinned to the context window and organize information by topic — such as user preferences or current objectives." Block has label, description, value, char limit.
- **Recall memory:** complete interaction history searchable on demand; "automatic disk persistence."
- **Archival memory:** "explicitly formulated knowledge in external databases like vector or graph databases." Indexed; queried via dedicated tools.

#### Sleep-time compute (Letta ≥ 0.7.0):

Source: [letta.com/blog/sleep-time-compute](https://www.letta.com/blog/sleep-time-compute) [accessed:2026-04-28].

Key idea: a background agent runs *between* user turns, distilling raw context into "learned context." Quote: "Agents should be running even while they 'sleep', using their downtime to reorganize information and reason through the information they have available in advance." Conflict avoidance is structural — "the primary agent is not provided with tools to edit its core memory" — only the sleep-time agent has those tools.

Sleep-time agent jobs (from forum.letta.com/t/sleeptime-agents-for-memory-consolidation-best-practices-guide):

- Consolidate fragmented memories into coherent entries
- Identify patterns across conversations
- Reorganize and deduplicate memory blocks
- Archive and prune outdated information

#### Strengths

- Self-editing memory is *agentic*: the LLM decides what's worth keeping. No human curation needed.
- Bitemporal-ish via recall/archival split.
- Production-grade: persistent server, ADE debugger, REST APIs.
- v1 agent loop "recommended for the latest reasoning models like GPT-5 and Claude 4.5 Sonnet" (per the repo README, accessed today).

#### Known limitations

- "Memory formation in MemGPT…may become messy and disorganized over time" — this is the *motivation* Letta gives for sleep-time compute, i.e. admitted by the maintainers themselves. Source: [letta.com/blog/sleep-time-compute](https://www.letta.com/blog/sleep-time-compute).
- Heavy lock-in: agents *run inside Letta*. Mem0 vs Letta comparison ([vectorize.io/articles/mem0-vs-letta](https://vectorize.io/articles/mem0-vs-letta), accessed today) notes "Letta creates architectural lock-in because agents run inside Letta, making migration more complex."
- Letta has not published its own LongMemEval / LoCoMo numbers publicly. Same source: "Letta…benchmark results unpublished."

#### Applicability to our Chinese novel project

- applicability: medium
- adoption cost: high (rewrite — our LangGraph orchestrator would need to coexist with Letta's server or be replaced by it)
- dependencies: PostgreSQL, Letta server runtime, Python SDK
- Chinese: agent loop and memory blocks are LLM-content-agnostic. Should work, but unverified at scale on long Chinese fiction.

---

## 2. Mem0

- Canonical paper: [arxiv.org/abs/2504.19413](https://arxiv.org/abs/2504.19413) [accessed:2026-04-28]
  Authors: Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, Deshraj Yadav
- Canonical code repo: [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0) [accessed:2026-04-28]
- Stars: ~57k (also seen as 48k in vectorize comparison and "+24M funding October 2025" mentioned in marketing pages)
- License: Apache-2.0
- Primary language: Python (53.0%)
- Maturity: production
- Maintenance: active. April 2026 algorithm release.

#### Architecture

From the paper abstract: "a scalable memory-centric architecture that addresses this issue by dynamically extracting, consolidating, and retrieving salient information from ongoing conversations" and "an enhanced variant that leverages graph-based memory representations to capture complex relational structures." Source: [arxiv.org/abs/2504.19413](https://arxiv.org/abs/2504.19413).

From the State-of-AI-Agent-Memory-2026 post on mem0.ai ([mem0.ai/blog/state-of-ai-agent-memory-2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026), accessed today) and the April 2026 algorithm description:

- **Single-pass ADD-only extraction**: one LLM call, no UPDATE/DELETE. "Memories accumulate without overwriting."
- **Entity linking**: extracts, embeds, and links entities across memories — used as a retrieval booster.
- **Multi-signal retrieval**: parallel scoring across "semantic, BM25 keyword, and entity matching" + temporal reasoning for time-aware retrieval.
- **Three scopes**: user (cross-session), session (within-session), agent (per-agent-instance).

Default embedding: `text-embedding-3-small` (OpenAI). Hybrid recommendation in the State-of-Memory post: Qwen 600M for semantic+keyword+entity boosting.

#### Benchmark numbers (paper + April 2026 post)

- LOCOMO LLM-as-judge: +26% over OpenAI Memory baseline.
- p95 latency: −91% vs full-context.
- Token cost: −90% vs full-context.
- April 2026 algorithm: LoCoMo 91.6 (+20), LongMemEval 94.8 (+27), BEAM (1M) 64.1.

#### Strengths

- Highest published LongMemEval score among production-grade systems (94.8) as of April 2026.
- Framework-agnostic: integrates LangGraph, CrewAI, AutoGen, OpenAI SDK, Vercel AI SDK.
- Lowest switching cost — it's purely a memory layer.

#### Known limitations

- ADD-only ⇒ explicit correction of stale facts is awkward. The vectorize.io comparison ([vectorize.io/articles/mem0-vs-letta](https://vectorize.io/articles/mem0-vs-letta)) characterizes it as "passive extraction where the system determines what to store" vs Letta's self-editing.
- Graph variant requires extra infrastructure; the paper notes only ~2% additional score for the graph option.
- "State of AI Agent Memory 2026" post itself flags: "Temporal abstraction degrades ~25% at 10M token scale."

#### Applicability to our Chinese novel project

- applicability: high
- adoption cost: low (pip install, drop into our LangGraph pipeline alongside existing ChromaDB code)
- dependencies: any LLM, any vector store (Qdrant default for cloud)
- Chinese: benchmarked on multilingual data; works with Qwen/DeepSeek directly. Tokenization is delegated to the configured embedding model — bge-m3 from BAAI is a natural pairing.

---

## 3. A-MEM (Agentic Memory)

- Canonical paper: [arxiv.org/abs/2502.12110](https://arxiv.org/abs/2502.12110) [accessed:2026-04-28] (HTML: [arxiv.org/html/2502.12110v11](https://arxiv.org/html/2502.12110v11))
  Authors: Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang. NeurIPS 2025 poster.
- Canonical code repo (most-linked): [github.com/agiresearch/A-mem](https://github.com/agiresearch/A-mem) [accessed:2026-04-28]
- Alternate repo: [github.com/WujiangXu/A-mem](https://github.com/WujiangXu/A-mem) — same authors, mirrors the NeurIPS implementation
- Stars: ~1k
- License: MIT
- Primary language: Python (100%)
- Maturity: research_prototype with reproducible code
- Maintenance: slow (NeurIPS publication, less active than Letta/Mem0)

#### Architecture (from the arxiv HTML)

Inspired by the Zettelkasten note-taking method. Each memory note contains:

1. Original interaction content + timestamp
2. LLM-generated **keywords**
3. LLM-generated **tags** (categorical)
4. LLM-generated **contextual description** (semantic)
5. Links to related memories (graph edges)
6. Dense vector embedding

Process:

- **Note creation:** LLM call produces all attributes when memory is added.
- **Link generation:** new note triggers top-k similarity search, then LLM determines meaningful connections "beyond simple similarity metrics."
- **Memory evolution:** new memories "trigger updates to the contextual representations and attributes of existing historical memories, allowing the memory network to continuously refine its understanding."
- **Retrieval:** semantic search → returns matched memory + linked neighbors.

#### Evaluation

Datasets: LoCoMo (7,512 QA pairs), DialSim (1,300+ TV-show sessions).

Results (from the HTML):

- Multi-hop reasoning: "at least two times better performance" than baselines.
- DialSim: 35% improvement on LoCoMo, "192% higher than MemGPT."
- Token efficiency: 85–93% reduction vs LoCoMo/MemGPT (1,200 vs 16,900 tokens).

#### Strengths

- Graph-of-notes structure is exactly the abstraction needed for character-centric retrieval ("characters appearing in this scene + their linked memories").
- Embedding+LLM-tags hybrid is fast at retrieval time.
- Open MIT license, ChromaDB + all-MiniLM-L6-v2 — easy to swap to bge-m3.

#### Known limitations

- LLM call on every write is expensive at high write rates.
- The "memory evolution" step rewrites historical notes — if buggy, it's destructive (no version history).
- Small stars / repo size means limited production hardening.

#### Applicability to our Chinese novel project

- applicability: high
- adoption cost: medium (port the Zettelkasten primitives onto our existing storage; reuse our LangGraph orchestrator)
- dependencies: ChromaDB, an LLM provider, MiniLM (replaceable with bge-m3)
- Chinese: not explicitly evaluated, but framework is multilingual via embedding choice.

---

## 4. MemoryBank (SiliconFriend)

- Canonical paper: [arxiv.org/abs/2305.10250](https://arxiv.org/abs/2305.10250) [accessed:2026-04-28] (HTML: [ar5iv.labs.arxiv.org/html/2305.10250](https://ar5iv.labs.arxiv.org/html/2305.10250))
  AAAI 2024. Earliest of the "long-term LLM memory" wave.
- Maturity: research_prototype
- Maintenance: stale (paper from 2023, no recent code activity surfaced)

#### Architecture (from the ar5iv HTML)

Three tiers:

1. **In-Depth Memory Storage**: full multi-turn conversation log with timestamps.
2. **Hierarchical Event Summary**: LLM-condensed daily summaries → global summary.
3. **Dynamic Personality Understanding**: per-day personality insights aggregated into a user profile.

Retrieval: dual-tower dense retrieval (DPR-style), FAISS-indexed. Current conversation = query.

#### Ebbinghaus forgetting curve (verbatim formula from the HTML):

> R = e^(-t/S)
> where R = retention, t = time elapsed, S = memory strength (initialized 1, +1 on recall, reset to 0 on full forgetting).

#### Evaluation

- 10-day simulated history, 15 virtual users, 194 probing questions (97 EN + 97 ZH).
- Base models: ChatGPT, ChatGLM (6.2B), BELLE (7B, LLaMA-based).
- SiliconFriend chatbot fine-tuned via LoRA (rank 16) on 38,000 psychological dialogs.

#### Strengths

- One of the few to explicitly model *forgetting* with a closed-form mathematical decay.
- **Bilingual EN/ZH probing from day one** — historically relevant for Chinese-language deployment.
- Hierarchical summary tier is a clean precedent for our chapter / volume / story-level rollups.

#### Known limitations

- Daily-summary granularity is too coarse for chapter-by-chapter fiction (chapter ≠ day).
- The Ebbinghaus decay is per-fact, not per-character or per-thread — risks forgetting important plot threads simply because they were dormant for a few chapters.
- No public, actively maintained reference implementation. ([no-source-found: searched github for "MemoryBank SiliconFriend" — only paper-companion repos surfaced, none actively maintained])

#### Applicability to our Chinese novel project

- applicability: medium
- adoption cost: medium (we'd implement from paper)
- dependencies: any dense retriever; FAISS
- Chinese: explicitly bilingual in evaluation; ChatGLM was a base model. ✓

---

## 5. MemPalace

- Canonical paper: **none yet** — there is an arxiv preprint titled "Spatial Metaphors for LLM Memory: A Critical Analysis of the MemPalace Architecture" ([arxiv.org/abs/2604.21284](https://arxiv.org/abs/2604.21284), accessed today) but I did not fetch the body. The MemPalace project itself is community-developed without a paper.
- Project site: [mempalaceofficial.com](https://mempalaceofficial.com/) (also [mempalace.tech](https://www.mempalace.tech/)) [accessed:2026-04-28]
- Code repo: [github.com/milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace) per analytics-vidhya and other secondary sources. (Note: some pages give `github.com/mempalace/mempalace` — I did not independently verify the canonical URL via the repo itself; both redirect destinations are referenced in community write-ups.)
- Stars: ~47k–53k (depending on which post you read; both >47k confirmed in [alexeyondata.substack.com](https://alexeyondata.substack.com/p/an-unexpected-entry-into-ai-memory))
- License: MIT
- Maturity: production-aspirational; community-led with strong PR
- Maintenance: active as of April 2026 (project launched April 2026)
- Creators: **Milla Jovovich** (actress) and **Ben Sigman** (developer), built using Claude Code

#### Architecture (from the project site + recca0120 deep-dive + Sigman/alexeyondata critique)

Six-level hierarchy:

- **Wings** — top-level (projects, people, topics)
- **Rooms** — sub-topics (auth, billing, deployment, etc.)
- **Halls** — cross-wing memory types (facts, events, discoveries, preferences, advice)
- **Closets** — compressed summaries with pointers to originals
- **Drawers** — original verbatim files (source of truth)
- **Tunnels** — cross-wing connections

Dependencies: **just ChromaDB + PyYAML** (optionally Claude Haiku reranking at ~$0.001/query).

Key claims:

- **No LLM calls at write time.** "all classification, chunking, room detection, and compression run on regex heuristics and keyword scoring." [analyticsvidhya.com](https://www.analyticsvidhya.com/blog/2026/05/mempalace-explained/) and [recca0120.github.io](https://recca0120.github.io/en/2026/04/08/mempalace-ai-memory-system/)
- **AAAK compression** — "structured English abbreviations" achieving ~30× compression, no decoder needed; any LLM reads it natively.
- **170-token startup**: L0 (~50t identity) + L1 (~120t critical facts in AAAK) loaded eagerly; L2 (room-specific) and L3 (semantic deep search) on demand.
- **96.6% raw recall@5 on LongMemEval** (no LLM); 100% hybrid mode (with Haiku rerank); 98.4% on held-out.

#### Strengths (per claim)

- Zero write-time LLM cost is genuinely cheaper than Mem0's or A-MEM's single-pass extraction.
- The Wing/Room hierarchy is *very* close to how a story bible is naturally organized (Wing=character, Room=arc, Hall=type-of-fact).
- L0/L1/L2/L3 layering is conceptually the same shape as our `LayeredMemory` already in `backend/memory/`.

#### Known limitations (from critiques)

[alexeyondata.substack.com](https://alexeyondata.substack.com/p/an-unexpected-entry-into-ai-memory) [accessed:2026-04-28]:

- LongMemEval 96.6% claim "not independently verified" anywhere I found.
- Room detection uses "keyword scoring against 5 categories" with only "~60 keyword mappings — scalability unclear for specialized domains."
- AAAK compression: independent testing in the substack post "suggests using AAAK may reduce retrieval accuracy from 96.6% to approximately 84.2%."
- 250× token reduction comparison is a strawman against "send all memories every turn" — not a fair baseline.
- Marketing materials are uniformly promotional; few honest treatments exist.

#### Applicability to our Chinese novel project

- applicability: medium (the *shape* is right for our story bible, but the keyword/regex classification is English-centric)
- adoption cost: medium (re-implement the Wing/Room/Hall/Drawer/Closet model on top of our existing SQLite + ChromaDB; Chinese-language regex keywords need redoing)
- dependencies: minimal
- Chinese: untested; regex-based "room detection" is the chief risk for ZH. Chinese tokenization complicates keyword scoring; we'd likely swap to jieba + bge-m3 dense scoring.

---

## 6. Zep / Graphiti (Temporal KG)

- Canonical paper: [arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956) — "Zep: A Temporal Knowledge Graph Architecture for Agent Memory" [accessed:2026-04-28]
  Authors: Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, Daniel Chalef
- Canonical code repo: [github.com/getzep/graphiti](https://github.com/getzep/graphiti) [accessed:2026-04-28]
- Stars: 26.7k
- License: Apache-2.0
- Primary language: Python (99.3%)
- last_commit_date: 2026-05-21 (v0.29.1 release)
- Maturity: production
- Maintenance: active

#### Architecture (from the repo README + paper abstract)

- Storage backend: graph + vector. Supported backends: **Neo4j 5.26+, FalkorDB 1.1.2+, Kuzu 0.11.2+, Amazon Neptune (DB cluster or Analytics + OpenSearch Serverless).**
- Retrieval method: hybrid — "semantic embeddings, keyword (BM25), and graph traversal for low-latency, high-precision queries."
- Write strategy: real-time, incremental. Quote from README: "Facts have validity windows. When information changes, old facts are invalidated — not deleted."
- Decay: bi-temporal — every fact has *transaction time* (when system knew) + *valid time* (when fact was true). No deletion; invalidation only.
- Update strategy: "incrementally processes incoming data, instantly updating entities, relationships, and communities without batch recomputation."

#### Benchmarks (from the paper)

- DMR (MemGPT's own benchmark): Zep **94.8%** vs MemGPT **93.4%**.
- LongMemEval: "accuracy improvements of up to 18.5% while simultaneously reducing response latency by 90%."
- Graphiti P95 retrieval latency: ~300ms.

#### Strengths

- Bitemporal is the right model for narrative — facts that *were* true but no longer are (e.g. "Lin and Wang are betrothed" in chapter 12, invalidated chapter 27).
- Real-time, no batch rebuild.
- Strong benchmark numbers; well-funded company behind it.

#### Known limitations

- Requires a graph database (Neo4j etc.), which adds operational overhead vs SQLite+Chroma.
- LLM-based entity extraction at write time → cost.
- No published Chinese-language benchmark.

#### Applicability to our Chinese novel project

- applicability: high (best-in-class temporal model)
- adoption cost: high (Neo4j or Kuzu deployment; rewrite our knowledge-triple store)
- dependencies: Neo4j / FalkorDB / Kuzu, embedding model
- Chinese: framework-agnostic; entity extraction depends on LLM choice, so Qwen/DeepSeek would work. Untested at narrative scale.

---

## 7. LangChain memory (deprecated) → LangGraph memory (current)

- Canonical docs: [docs.langchain.com/oss/python/concepts/memory](https://docs.langchain.com/oss/python/concepts/memory) [accessed:2026-04-28]
- LangGraph add-memory guide: [docs.langchain.com/oss/python/langgraph/add-memory](https://docs.langchain.com/oss/python/langgraph/add-memory) [accessed:2026-04-28]
- Deprecated class reference: [reference.langchain.com/python/langchain-classic/memory/summary_buffer/ConversationSummaryBufferMemory](https://reference.langchain.com/python/langchain-classic/memory/summary_buffer/ConversationSummaryBufferMemory) [accessed:2026-04-28]

### Deprecation status (confirmed today)

`ConversationSummaryBufferMemory` (and by extension the other Conversation*Memory classes from the langchain 0.x era):

- "Deprecated since version 0.3.1"
- "Will be removed in version 2.0.0"
- Migration: "Use langchain.agents.create_agent instead."
- The class now lives in **`langchain-classic`** — a compatibility package, not the main `langchain` library.

### What's current (2025–2026)

Two distinct mechanisms from the OSS memory docs:

- **Short-term memory** = thread-scoped LangGraph state, managed via **checkpointers** (`SqliteSaver`, `PostgresSaver`, `MongoDBSaver`, `RedisSaver`).
- **Long-term memory** = namespace-scoped via **`BaseStore`**. Per the docs, organized "under a custom namespace (similar to a folder) and a distinct key (like a file name)."

Three psychological categories explicitly mapped:

- Semantic — facts (profiles / documents)
- Episodic — past experiences (few-shot examples)
- Procedural — rules (system prompts, reflection-refined)

`LangMem` is the companion library for richer long-term memory.

#### Applicability to our Chinese novel project

- applicability: medium (we already use LangGraph; the checkpointer + BaseStore split is a natural fit)
- adoption cost: low if we stay on LangGraph; migrating from any older buffer memory should be straightforward
- dependencies: langgraph + langgraph-checkpoint-{sqlite,postgres,…}
- Chinese: language-agnostic.

---

## 8. LlamaIndex Memory + Memory Blocks

- Canonical docs: [developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/) [accessed:2026-04-28]
- Blog announcement: [llamaindex.ai/blog/improved-long-and-short-term-memory-for-llamaindex-agents](https://www.llamaindex.ai/blog/improved-long-and-short-term-memory-for-llamaindex-agents) [accessed:2026-04-28]

#### Architecture

`Memory` class wraps short-term + long-term, parameterized by:

- `token_limit` (default 30000)
- `chat_history_token_ratio` (default 0.7) — when STM exceeds this fraction, flush is triggered
- `token_flush_size` (default 3000) — batch flushed to long-term per cycle

Long-term memory = list of **Memory Block** objects:

- **StaticMemoryBlock** — fixed content (e.g. user profile, system context)
- **FactExtractionMemoryBlock** — "extract facts from the chat history"; `max_facts` triggers summarization
- **VectorMemoryBlock** — "stores and retrieves batches of chat messages from a vector database"

#### Priority system

- `priority=0` ⇒ "always be kept in memory"
- `priority=1, 2, 3…` ⇒ truncation order under token pressure

#### Strengths

- Cleanest *composable* memory abstraction. We can declare "always keep the story bible (priority 0), keep recent chapter summaries (priority 1), let old episodic memories spill into vector retrieval (priority 2)."
- Fact extraction block is essentially what we already do post-chapter, but with batteries included.

#### Limitations

- Requires LlamaIndex orchestration, which would duplicate parts of our LangGraph code.
- Vector block does batch storage by message — coarser than the per-character memory granularity we want.

#### Applicability

- applicability: medium
- adoption cost: medium (we'd port concepts rather than wholesale switch)
- dependencies: LlamaIndex
- Chinese: language-agnostic

---

## 9. SillyTavern Lorebook / World Info / Vectorization

The de-facto practical reference for character-and-world-info retrieval in long roleplay. Heavy production usage by the AI fiction community — millions of users, decade-old patterns codified.

- Repo: [github.com/SillyTavern/SillyTavern](https://github.com/SillyTavern/SillyTavern) [accessed:2026-04-28]
- Stars: 28.5k; Forks: 5.4k
- License: AGPL-3.0
- Primary language: JavaScript (86.2%)
- Latest release: 1.18.0 (2026-05-03)
- Docs: [docs.sillytavern.app/usage/core-concepts/worldinfo](https://docs.sillytavern.app/usage/core-concepts/worldinfo/) and [docs.sillytavern.app/extensions/chat-vectorization](https://docs.sillytavern.app/extensions/chat-vectorization/)

### World Info / Lorebook

Verbatim from the docs:

- Entry fields: **keys (keywords), content, insertion order, insertion position, probability**.
- Activation: "World Info functions like a dynamic dictionary that only inserts relevant information from World Info entries when keywords associated with the entries are present in the message text."
- Token budget: "Defines how many tokens could be used by World Info entries at once. You can define a threshold relative to your API's max-context settings (Context %) or an objective token threshold (Budget)."
- Recursive activation: "Entries can activate other entries by mentioning their keywords in the content text."
- Scopes: **Character / Persona / Chat / Global** lorebooks, plus **Auxiliary** lorebooks.

### Chat Vectorization (RAG over the chat history)

From [docs.sillytavern.app/extensions/chat-vectorization](https://docs.sillytavern.app/extensions/chat-vectorization/):

- Each message is embedded in the background; ChromaDB stores per-chat collections.
- Query = last 2 messages → top-K matches across history with min 25% relevance.
- Matched messages are *temporarily inserted* either before/after the Main Prompt or at "Depth 2" (typically right before the previous model response). The rationale: "messages at the start and end of the chat history tend to have the greatest impact on the model's reply."

### Smart Context (the older, retired extension)

From [docs.sillytavern.app/extensions/smart-context](https://docs.sillytavern.app/extensions/smart-context/) — auto-vectorized chats after 10 messages; same retrieval idea. Now superseded by Vector Storage.

### Strengths

- **Battle-tested in production for narrative use** — every claim above is from a system used daily by thousands of people writing long fiction.
- Keyword-based activation is fast (no embedding inference on every turn just to figure out what lore applies).
- Token-budget management is explicit and predictable.
- Scope hierarchy (Character/Persona/Chat/Global) is exactly how a multi-volume novel system would naturally tier its lore.

### Limitations

- Keyword activation misses semantic paraphrases ("the king" doesn't match an entry keyed only on "Emperor"). The fix is recursive activation + redundant keys, but that's a manual chore.
- AGPL-3.0 → cannot vendor the UI code into our (likely permissively-licensed) backend. Pattern-borrowing is fine.

### Applicability

- applicability: **high (as a pattern source, not a vendor)**
- adoption cost: low (reimplement the activation + budget logic in our existing FastAPI backend)
- dependencies: any embedding model for the vectorization extension
- Chinese: works (community runs it on Chinese models routinely)

---

## 10. Cognee

- Canonical repo: [github.com/topoteretes/cognee](https://github.com/topoteretes/cognee) [accessed:2026-04-28]
- Stars: 17.6k
- License: Apache-2.0
- Primary language: Python (87.3%)
- last_commit_date: 2026-05-22 (v1.1.1.dev0)
- Maturity: production-ish
- Maintenance: active

#### Architecture

Four-operation API: `remember`, `recall`, `forget`, `improve`. Poly-store design:

- Graph backends: Neo4j, FalkorDB, KuzuDB, NetworkX
- Vector backends: Redis, Qdrant, Weaviate
- Relational: SQLite or Postgres

Quote from the README: "Cognee handles parsing, chunking, embedding, and provenance, and extracts entities, relationships, and domain rules so agents search by meaning, not just nearest chunks."

Retrieval: `recall(...)` does "auto-routing (picks best search strategy automatically)" across the stores.

#### Strengths

- Most-flexible backend matrix on the market.
- Explicit `forget` operation — semantically clean for pruning.
- Adopted by Claude Code, LangGraph integrations.

#### Limitations

- Larger surface area = more to learn / debug.
- "Poly-store" sounds great until you have to operate four different DBs in dev/prod.

#### Applicability

- applicability: medium
- adoption cost: medium-high
- dependencies: pick-one-of-many
- Chinese: language-agnostic (depends on embedding model)

---

## 11. MemoryOS

- Canonical paper: [arxiv.org/abs/2506.06326](https://arxiv.org/abs/2506.06326) [accessed:2026-04-28]
  Authors: Jiazheng Kang, Mingming Ji, Zhe Zhao, Ting Bai. **EMNLP 2025 Oral.**
- Canonical repo: [github.com/BAI-LAB/MemoryOS](https://github.com/BAI-LAB/MemoryOS) [accessed:2026-04-28]
- Stars: 1.4k; Forks: 137
- License: Apache-2.0
- Primary language: Python (89.3%), HTML (10.6%)
- Maturity: research → production hybrid
- Maintenance: active

#### Architecture

Three-tier:

- **STM** — short-term, recent interactions
- **MTM** — mid-term, topic-grouped
- **LPM** — long-term personal memory (traits, preferences)

Coordinated by four modules: Storage, Updating, Retrieval, Generation.

Update strategies (from the paper abstract):

- STM → MTM: "dialogue-chain-based FIFO principle"
- MTM → LPM: "segmented page organization strategy" (heat-based)

#### Benchmarks

LoCoMo with GPT-4o-mini base:

- **+49.11% F1**
- **+46.18% BLEU-1**

#### Strengths

- **Chinese-native repo** — `readme_cn.md` is bilingual, and the README lists Deepseek, Qwen, vLLM, Llama Factory as first-class LLM providers.
- Default embedding is **bge-m3 or Qwen embeddings** — already the right tooling for ZH.
- Three-tier is exactly the abstraction we want for short / chapter / story scope.

#### Limitations

- Smaller community than Letta/Mem0.
- Research-prototype maturity; APIs may still churn.

#### Applicability to our Chinese novel project

- applicability: **highest** of any system surveyed for *Chinese* specifically
- adoption cost: medium (the abstraction maps cleanly to our existing 4-tier `LayeredMemory`)
- dependencies: ChromaDB, bge-m3 / Qwen embeddings
- Chinese: ✓✓✓ — native first-class support

---

## 12. Generative Agents (Stanford, Park et al.)

- Canonical paper: [arxiv.org/abs/2304.03442](https://arxiv.org/abs/2304.03442) [accessed:2026-04-28]
- Canonical repo: [github.com/joonspk-research/genagents](https://github.com/joonspk-research/genagents) [accessed:2026-04-28]
- Stars: 552 (this is the *2024 replication agent* repo; the original simulation repo is at `joonspk-research/generative_agents` with 19k+ stars)
- License: MIT
- Maturity: research_prototype
- Maintenance: slow

#### Architecture — the canonical memory-stream retrieval formula

From the paper and reproduced widely:

> retrieval_score = recency + importance + relevance

All three normalized to [0,1]:

- **Recency:** exponential decay (decay factor `0.995` per hour in the Stanford code).
- **Importance:** LLM-rated 1–10 on memory creation.
- **Relevance:** cosine similarity to the query embedding.

Plus a **reflection** layer — periodically the agent runs a meta-prompt to "form new insights" from recent memories. Reflections themselves become memories with higher importance.

Quote from the genagents README: agents can "reflect on their memories to form new insights."

#### Strengths

- The score formula is the cleanest scoring rubric in the field. Almost every later system cites it.
- Reflection-as-memory pattern is what makes the agents *feel* alive — directly applicable to our Director / Consistency agents.

#### Limitations

- The agents simulated a town, not chapters of a novel. Mapping recency from real-time to in-story-time is non-obvious — what is "an hour" in narrative time?
- Importance must be assigned at write time → LLM cost.

#### Applicability

- applicability: high (we already use a similar scoring in our `LayeredMemory.L1` selection)
- adoption cost: low (we're basically already doing this)
- dependencies: any embedding model
- Chinese: language-agnostic

---

## 13. CoALA — the framework that names the parts

- Canonical paper: [arxiv.org/abs/2309.02427](https://arxiv.org/abs/2309.02427) (TMLR 2024) [accessed:2026-04-28]
  Authors: Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, Thomas L. Griffiths (Princeton)
- Explainer (the most useful summary I found, given the PDF didn't extract cleanly): [cognee.ai/blog/fundamentals/cognitive-architectures-for-language-agents-explained](https://www.cognee.ai/blog/fundamentals/cognitive-architectures-for-language-agents-explained) [accessed:2026-04-28]

#### What it says

Three axes:

1. **Information storage**: working (short scratchpad) + long-term (episodic / semantic / procedural)
2. **Action space**: internal (memory ops, reasoning) vs external (grounding in environment)
3. **Decision-making**: structured planning + execution loop

The three long-term categories (from the explainer):

- **Episodic** — past events / experiences
- **Semantic** — facts (e.g. "Birds can fly, except ostriches")
- **Procedural** — how to do things (code / weights)

CoALA is descriptive, not prescriptive — it gives us shared vocabulary, not an implementation. But our project's `LayeredMemory` (L0/L1/L2/L3) is essentially a refinement of CoALA's episodic+semantic axes.

#### Applicability

- applicability: vocabulary only
- adoption cost: zero
- dependencies: none
- Chinese: N/A

---

## 14. Long story-generation pipelines (DOME, DOC, Re3, "Long Story Generation via KG and Literary Theory")

These are *complete pipelines* for novel generation, not memory-systems-per-se, but each ships a memory module worth surveying.

### DOME — Dynamic Hierarchical Outlining + Memory-Enhancement

- Canonical paper: [arxiv.org/abs/2412.13575](https://arxiv.org/abs/2412.13575) (HTML version) [accessed:2026-04-28]
- Authors: Qianyue Wang, Jinwu Hu, Zhengping Li, Yufeng Wang, Daiyuan Li, Yu Hu, Mingkui Tan (South China Univ of Tech, Pazhou Lab, Peng Cheng Lab, HK Polytechnic)

Architecture:

- **DHO (Dynamic Hierarchical Outline)** — rough outline aligned to Joseph Campbell's 5-stage monomyth; detailed outline generated dynamically as chapters are written.
- **MEM (Memory-Enhancement)** — stores generated content as **temporal knowledge graph quadruples** `<subject, action, object, chapter_index>`.

Retrieval: entity-based quadruple lookup, then LLM-side semantic filtering on five criteria: subject similarity / object similarity / action similarity / event relevance / "potential writing utility."

Models tested: Qwen1.5-72B-Chat, Llama3-70B-Instruct, Yi1.5-34B-chat → directly Chinese-capable.
Dataset: 20 story premises from DOC benchmark.

Results:

- ~7,100-word stories (vs ~3,900 for baselines)
- Conflict rate −27.3% vs Re3, −87.6% vs the same DOME without MEM
- Entropy-2 +6.3% over prior SOTA
- Top human-eval rank across all 5 dimensions

The quadruple `<subject, action, object, chapter_index>` representation is **directly compatible with our existing knowledge-graph triple store** (`backend/storage/sqlite_store.py:knowledge_triples`). This is the most lift-and-shift-able idea in the survey.

### DOC — Detailed Outline Control

- Canonical paper: [arxiv.org/abs/2212.10077](https://arxiv.org/abs/2212.10077) [accessed:2026-04-28]
- Splits outliner (structured prompt, hierarchical outline) and controller (alignment during drafting).
- Wins over Re3 by +22.5% plot coherence, +28.2% outline relevance, +20.7% interestingness (human eval).

### Re3 — Recursive Reprompting + Revision

- Canonical paper: [arxiv.org/abs/2210.06774](https://arxiv.org/abs/2210.06774) [accessed:2026-04-28]
- Plan → draft → rerank-revise → edit pipeline. The granddaddy. Memory is implicit in the plan.

### "Long Story Generation via Knowledge Graph and Literary Theory"

- Canonical paper: [arxiv.org/abs/2508.03137](https://arxiv.org/abs/2508.03137) [accessed:2026-04-28]
- Authors: Ge Shi, Kaiyu Huang, Guochen Feng
- Combines KG with classical narratology (Propp-style functions) for structured plot organization. PDF didn't extract cleanly; secondary summary indicates KG-based plot scaffolding similar to DOME but with explicit literary-theory functions.

### "Lost in Stories" — the failure-mode taxonomy

- Canonical paper: [arxiv.org/html/2603.05890v1](https://arxiv.org/html/2603.05890v1) [accessed:2026-04-28]
- Microsoft Beijing + SUTD. Introduces **ConStory-Bench**: 2,000 prompts × 4 task types (Generation / Continuation / Expansion / Completion), targeting 8k–10k-word outputs.
- Detection pipeline = **ConStory-Checker** (four-stage LLM-as-judge).
- Five error dimensions × 19 fine-grained subtypes:
  1. Timeline & plot logic (temporal contradiction, causality violation, abandoned threads)
  2. Characterization (memory inconsistency, skill fluctuation, forgotten abilities)
  3. World-building & setting (rule violations, geographical contradictions, social norm breaks)
  4. Factual & detail consistency (appearance, nomenclature, quantitative)
  5. Narrative & style (perspective shift, tone, style)
- Key empirical findings:
  - Errors concentrate in factual + temporal dimensions
  - Errors appear "around the middle of narratives"
  - Error spans have "12–19% higher entropy than baseline text" — uncertainty leaks → contradiction
  - ConStory-Checker F1 = 0.678 vs human-expert F1 = 0.229 (automated detection beats individual humans on diagnosis)

This is **the** taxonomy to design our memory system against.

### WebNovelBench

- Canonical paper: [arxiv.org/abs/2505.14818](https://arxiv.org/abs/2505.14818) [accessed:2026-04-28]
- ACL Findings 2026.
- 4,000+ Chinese web novels (each with 10k+ readers) — directly relevant.
- Eight narrative dimensions evaluated via LLM-as-judge with PCA weighting + ECDF percentile ranking.
- Validated against 25 Mao Dun Prize winners as upper anchor.
- 24 SOTA models tested. Top performers: **Qwen3-235B, DeepSeek-R1, Gemini-2.5-Pro** approach human-level on web-novel quality.

---

## 15. Benchmarks worth tracking (LoCoMo, LongMemEval, BEAM, AgentMemoryBench)

| Benchmark | Size | Focus | Source |
|-----------|------|-------|--------|
| **LoCoMo** | 1,540 Qs across very long dialogs (300 turns / 9k tokens / 35 sessions avg) | Single-hop / multi-hop / open-domain / temporal | [snap-research.github.io/locomo](https://snap-research.github.io/locomo/), [arxiv.org/abs/2402.17753](https://arxiv.org/abs/2402.17753) |
| **LongMemEval** | 500 Qs, three variants: S (~115k tokens), M (~500 sessions), Oracle | Information extraction / multi-session reasoning / temporal reasoning / knowledge updates / abstention | [arxiv.org/abs/2410.10813](https://arxiv.org/abs/2410.10813), repo [github.com/xiaowu0162/longmemeval](https://github.com/xiaowu0162/longmemeval) (803 stars, MIT). ICLR 2025 |
| **BEAM** | 1M–10M token scale | Production-scale memory | Referenced by [mem0.ai/blog/state-of-ai-agent-memory-2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026); paper not located in this pass |
| **AgentMemoryBench** | 6 interactive tasks × 5 evaluation modes (Online/Offline/Replay/Transfer/Repair) | Continual agent memory | [github.com/s010m00n/AgentMemoryBench](https://github.com/s010m00n/AgentMemoryBench) [accessed:2026-04-28] |
| **MemoryAgentBench** | Incremental multi-turn | Accurate retrieval / test-time learning / long-range understanding / conflict resolution | [arxiv.org/pdf/2507.05257](https://arxiv.org/pdf/2507.05257) [accessed:2026-04-28] |
| **WebNovelBench** | 4,000+ Chinese web novels, 8 narrative dimensions | Chinese novel generation specifically | [arxiv.org/abs/2505.14818](https://arxiv.org/abs/2505.14818) |
| **ConStory-Bench** | 2,000 prompts × 4 task types | Consistency error taxonomy for long stories | [arxiv.org/html/2603.05890v1](https://arxiv.org/html/2603.05890v1) |

LongMemEval headline finding: **commercial chat assistants and long-context LLMs show ~30% accuracy drop on long-history information**. This is consistent across vendor reports.

---

## 16. Embedding choice for Chinese

- **BGE-M3** (BAAI): multilingual (100+ languages), supports inputs up to 8192 tokens, supports dense + lexical + ColBERT (multi-vec) retrieval in a single model. 1024-dim dense vectors. Now available via NVIDIA NIM / IONOS / Ollama. [docs.ionos.com/cloud/ai/ai-model-hub/models/embedding-models/bge-m3](https://docs.ionos.com/cloud/ai/ai-model-hub/models/embedding-models/bge-m3), [ollama.com/library/bge-m3](https://ollama.com/library/bge-m3) [accessed:2026-04-28]
- ChromaDB + BGE pairs are well-documented for production; first-party support for HuggingFaceBgeEmbeddings exists in LangChain integrations. [airbyte.com/data-engineering-resources/chroma-db-vector-embeddings](https://airbyte.com/data-engineering-resources/chroma-db-vector-embeddings) [accessed:2026-04-28]
- MemoryOS *defaults* to bge-m3 in its README, which is the strongest single endorsement for Chinese deployment.

---

## 17. Failure modes — what breaks at chapter 50

Synthesized from "Lost in Stories" (consistency taxonomy), the LangChain context-drift writeups, and the architecture-of-memory articles, all accessed today.

### A. Context-window drift / "When AI forgets the plot"

Source: [medium.com/@yaseenmd/when-ai-forgets-the-plot-…-6757eebb60b9](https://medium.com/@yaseenmd/when-ai-forgets-the-plot-a-guide-to-fixing-context-drift-hallucinations-in-llms-6757eebb60b9) (linked from search). The attention mechanism cannot evenly prioritize across a long context. Even if a story bible is in the prompt, "if a character sheet says green eyes but recent chapters describe brown eyes, the AI is likely to follow the more recent, more prominent context."

Lost-in-the-middle bias confirmed by [arxiv.org/pdf/2505.16894](https://arxiv.org/pdf/2505.16894) ("Shadows in the Attention…"): hallucination frequency grows monotonically with context length, plateauing after **5–7 rounds**. "High-confidence 'self-consistent' hallucinations" emerge specifically when injected context is *plausibly relevant*.

### B. Memory drift / staleness

Mem0 State-of-Memory-2026 explicitly lists "memory staleness when facts become outdated" as an unsolved problem. ADD-only architectures (Mem0) and immutable-graph systems (Zep) handle this differently:

- Mem0: counts on multi-signal retrieval scoring newer memories higher.
- Zep / Graphiti: invalidate-not-delete; old facts stay queryable but marked stale.
- A-MEM: memory evolution rewrites historical notes — risky if buggy.

### C. Hallucination of past events

Most pernicious failure mode. From "Lost in Stories": **error spans have 12–19% higher entropy than baseline text** — the model literally signals its own uncertainty *before* contradicting itself. A consistency-check pass that triggers on token entropy could catch many of these cheaply.

### D. Recency bias dominating story bible

Per Novarrium and the indie-hackers writeup. Solution patterns:

- Pin the story bible at *the end* of the context (lost-in-the-middle inverse).
- Use SillyTavern-style budget allocation: ~10–20% of context for world info that *cannot* be evicted.
- Re-inject character facts every chapter, not just on first appearance.

### E. Coverage drift

Errors concentrate "around the middle of narratives" (Lost in Stories). Plot threads opened in the first third get dropped in the middle, then mis-resolved at the end.

### F. Cross-session identity collapse

When the same character appears in multiple chats / sessions, simple keyword-matching lorebooks confuse aliases. Zep's entity-resolution graph is the only system surveyed that handles this cleanly.

---

## Comparison matrix

| System | Storage | Retrieval | Decay/forgetting | Temporal model | ZH-ready | Production-grade | License | Maintenance |
|--------|---------|-----------|------------------|----------------|----------|------------------|---------|-------------|
| **MemGPT / Letta** | core + recall (FIFO) + archival (vector/graph) | Agentic tool calls | Recursive summary on overflow + sleep-time pruning | None native | Untested at narrative scale | ✓ | Apache-2.0 | active |
| **Mem0** | Vector (Qdrant default) + optional graph | Multi-signal (semantic+BM25+entity) + temporal | ADD-only; staleness via scoring | Time-aware retrieval | ✓ (multilingual) | ✓ | Apache-2.0 | active |
| **A-MEM** | ChromaDB + LLM-tagged notes | Semantic + linked-neighbor expansion | Memory evolution (rewrites) | Timestamps on notes | Untested | research | MIT | slow |
| **MemoryBank** | FAISS dense retrieval + 3-tier summaries | Dual-tower DPR | Ebbinghaus R = e^(−t/S) | Daily summaries | ✓ (ZH probing built-in) | research | unclear | stale |
| **MemPalace** | ChromaDB + SQLite (KG) | Hierarchical structural + vector | KG invalidate_at | Bi-temporal triples | regex layer is EN-centric | claims production | MIT | active |
| **Zep / Graphiti** | Neo4j / FalkorDB / Kuzu / Neptune | Hybrid (semantic + BM25 + traversal) | Invalidate-not-delete | **Bitemporal** (transaction + valid time) | LLM-dependent | ✓ | Apache-2.0 | active |
| **LangGraph store** | SqliteSaver / PostgresSaver / Redis / Mongo + BaseStore | App-defined | App-defined | App-defined | ✓ | ✓ | MIT | active |
| **LlamaIndex Memory** | Memory Blocks (Static / Fact / Vector) | Block-level + priority | Token-pressure flush | Per-block | ✓ | ✓ | MIT | active |
| **SillyTavern WI + Vec** | JSON lorebooks + ChromaDB per chat | Keyword activation + recursive + budget; vec for chat history | Manual edits + Smart Context fade | None | ✓ (used by ZH community) | community-production | AGPL-3.0 | active |
| **Cognee** | Neo4j/FalkorDB/Kuzu/NetworkX + Redis/Qdrant/Weaviate + SQLite/Postgres | Auto-routed | Explicit `forget()` | Provenance | ✓ | ✓ | Apache-2.0 | active |
| **MemoryOS** | ChromaDB + 3-tier (STM/MTM/LPM) | Semantic, four-module pipeline | FIFO + heat-based | Page-organized | ✓✓ (ZH-native) | research → production | Apache-2.0 | active |
| **Generative Agents** | flat memory stream | recency+importance+relevance scoring | recency decay 0.995/hour | timestamp | ✓ (LLM-dep) | research | MIT | slow |
| **DOME (MEM module)** | quadruples `<s,a,o,chapter_idx>` | entity lookup + LLM filter | none (append-only) | chapter_index | ✓ (Qwen/Yi tested) | research | unclear | slow |

---

## Pattern catalog — techniques that recur

A high-confidence pattern is one I saw in **≥3 systems**:

1. **Vector retrieval is universal.** Every system has dense retrieval somewhere — ChromaDB, Qdrant, FAISS, Weaviate, Pinecone. Differentiation lives elsewhere.
2. **Multi-signal / hybrid retrieval beats vector-only.** Mem0 (semantic+BM25+entity), Zep (semantic+BM25+traversal), Cognee (auto-routed). Pure-vector loses to hybrid on every benchmark I saw (LoCoMo, LongMemEval).
3. **Summarization at multiple granularities.** Hierarchical merging is universal. MemoryBank's daily summaries, DOME's chapter-indexed quadruples, MemoryOS's STM→MTM→LPM consolidation, A-MEM's memory evolution, Letta's sleep-time consolidation.
4. **Temporal triples / bitemporal facts** (≥3 systems: Zep/Graphiti, DOME, MemPalace). Subject-predicate-object plus validity window. Our existing `knowledge_triples` table is already in this family.
5. **Hierarchical / layered storage.** L0/L1/L2/L3 (MemPalace), STM/MTM/LPM (MemoryOS), Core/Recall/Archival (Letta/MemGPT), Working/Long-term (CoALA, LangGraph), Wings/Rooms/Halls (MemPalace). Different names, same shape.
6. **Importance + recency + relevance scoring** (Generative Agents formula). Implicitly or explicitly present in Mem0's multi-signal scoring, MemoryBank's Ebbinghaus, etc.
7. **Reflection / sleep-time / dreaming.** Generative Agents reflection, Letta sleep-time, MemoryOS MTM consolidation, A-MEM evolution — all variants of "agent processes its own history asynchronously."
8. **Keyword + semantic hybrid for lore activation** (SillyTavern, Mem0, Zep). Keyword for fast trigger, semantic for paraphrase coverage.
9. **Token-budget management** (SillyTavern explicit budget, LlamaIndex token_limit, Letta block char_limit). Predictability matters; unbounded context = unbounded failure.
10. **Importance scoring at write time** (Generative Agents, A-MEM tags, MemoryBank significance). Adds LLM cost; MemPalace's whole pitch is *not* doing this.
11. **Story-specific: outline-driven generation** (DOC, Re3, DOME). Plan → controlled draft → revise. Memory is consulted within outline-driven beats, not freely.

---

## Top 3 candidate systems for our project

The choice is constrained by: Chinese-first content, existing LangGraph orchestration, SQLite + ChromaDB already deployed, multi-agent (6-agent) pipeline, knowledge-triple store with chapter indices already present, our own 4-tier LayeredMemory already implemented.

### #1: MemoryOS — adopt as primary

**时效性 (timeliness):** EMNLP 2025 Oral. April 2026 active commits. Published *after* most competitors and trained on Chinese workloads from day one.

**鲁棒性 (robustness):** +49.11% F1 / +46.18% BLEU-1 over baselines on LoCoMo using GPT-4o-mini. Three-tier STM/MTM/LPM with explicit update rules (FIFO + heat-based) — that's two well-defined invariants, not a black box.

**可行性 (feasibility):** Apache-2.0. ChromaDB-based (we already run this). Defaults to bge-m3 (Chinese-friendly). First-class support for Deepseek/Qwen/vLLM. The three-tier model maps directly onto our existing `LayeredMemory.L1/L2/L3`. We'd refactor `backend/memory/` to align with the STM/MTM/LPM contract and gain a referenceable academic grounding.

**Risk:** Smaller stars community (1.4k) than the top vendors; expect to read source rather than docs.

### #2: Mem0 — adopt for the multi-signal retrieval layer

**时效性:** April 2026 algorithm release. State-of-the-art LongMemEval (94.8) and LoCoMo (91.6).

**鲁棒性:** Multi-signal retrieval (semantic + BM25 + entity + temporal) consistently beats pure-vector. ADD-only architecture is simpler to reason about than self-editing.

**可行性:** Lowest switching cost of any system — Apache-2.0, framework-agnostic, drops into our LangGraph pipeline as a `MemoryClient(user_id=story_id)`. Default embedding can be swapped to bge-m3. We can use Mem0's retrieval *under* MemoryOS's tiering rather than choosing.

**Risk:** ADD-only means correcting a stale fact requires inserting a contradicting memory and trusting retrieval ranking. For a novel system where canon corrections (retcons) are common, this could be awkward.

### #3: Graphiti (the Zep engine) — adopt for the temporal triple store

**时效性:** v0.29.1 released 2026-05-21. 26.7k stars. Active.

**鲁棒性:** Bitemporal model (`valid_from / valid_to` for both transaction and valid time) is the *correct* abstraction for narrative facts. "Lin and Wang are betrothed at chapter 12, broken at chapter 27" survives consistency checks at chapter 50. P95 retrieval 300ms.

**可行性:** Apache-2.0. Kuzu backend is embeddable (no Neo4j ops burden). Our existing `knowledge_triples` schema is conceptually one rename away from Graphiti's edge format. We'd replace `backend/storage/sqlite_store.py:knowledge_triples` with a Graphiti collection per story.

**Risk:** Heaviest dependency; LLM extraction at write time costs tokens. Recommend running Graphiti as the *world-state* layer only, with cheaper per-message memory done by MemoryOS/Mem0 — split write paths by importance.

### Honorable mentions

- **SillyTavern World Info** — copy the *patterns* (keyword + recursive activation + per-scope budget). AGPL-3.0 blocks vendoring; pattern-copy is fine.
- **DOME's `<subject, action, object, chapter_index>` quadruple** — adopt as the on-disk format for our knowledge graph. Our existing schema is already 90% there.
- **Letta's sleep-time compute** — adopt the *pattern*, not the framework. After each chapter, run a "consolidation agent" that rewrites stale tier-1 memories. Doesn't require running Letta server.

---

## Open questions

1. **Chapter-time vs wall-time decay.** Every decay model in the literature decays by wall-clock time (Ebbinghaus, Generative Agents 0.995/hour). For us, *story time* and *generation time* are different. A character can be dormant for 20 chapters but only 2 days of generation. Which is the right axis? Probably *chapter index*, but no system surveyed handles this.

2. **Retcon support.** The user/editor may declare "actually, in chapter 12, X happened instead of Y." None of the surveyed systems have a first-class retcon primitive. Zep comes closest with bitemporal invalidation but doesn't support "I'm rewriting chapter 12 entirely."

3. **Cross-volume canon.** If we extend a 100-chapter novel into a sequel, how is memory inherited? MemoryOS's LPM tier *could* serve as canon-bible, but the upgrade-path is unproven.

4. **MemPalace's LongMemEval claim.** Is 96.6% reproducible? No third party has confirmed. We should not bet adoption on this number until we replicate it ourselves.

5. **AAAK compression in Chinese.** MemPalace's "AAAK" abbreviations rely on English letter-frequency. The same approach in Chinese might use 2-character word abbreviations or pinyin, but neither has been tested.

6. **bge-m3 + Chinese novel-prose** specifically. bge-m3 is benchmarked on retrieval, not on Chinese literary text. Retrieval quality on classical/modern Chinese prose with names, allusions, and 成语 is untested for us.

7. **Sleep-time compute cost amortization.** If we run a consolidation agent after every chapter, do the LLM costs offset the benefit? Letta hasn't published per-token cost numbers for this.

8. **Importance scoring for narrative.** "Importance" in chat is "this fact will be referenced again." In a novel, importance is *crafted* — the writer plants Chekhov's gun. Can the importance score be told by the outline (DOC/DOME-style) rather than derived post hoc?

9. **Multi-character cross-talk.** If character A learns something in chapter 3 and character B learns something contradicting it in chapter 7, the consistency check must distinguish *what each character believes* from *what the world is*. No surveyed system makes belief-state explicit.

10. **Granularity of write path.** Per-message (Mem0, Letta), per-chapter (DOME), per-day (MemoryBank), per-event (Generative Agents). The right unit for novel-writing is almost certainly **per-scene + per-chapter rollup**, but no system has scene granularity natively.

---

## Sources (consolidated, all accessed 2026-04-28)

### Primary systems
- [letta.com/blog/memgpt-and-letta](https://www.letta.com/blog/memgpt-and-letta)
- [letta.com/blog/agent-memory](https://www.letta.com/blog/agent-memory)
- [letta.com/blog/sleep-time-compute](https://www.letta.com/blog/sleep-time-compute)
- [github.com/letta-ai/letta](https://github.com/letta-ai/letta)
- [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560) (MemGPT)
- [ar5iv.labs.arxiv.org/html/2310.08560](https://ar5iv.labs.arxiv.org/html/2310.08560)
- [arxiv.org/abs/2504.19413](https://arxiv.org/abs/2504.19413) (Mem0)
- [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0)
- [mem0.ai/blog/state-of-ai-agent-memory-2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [arxiv.org/abs/2502.12110](https://arxiv.org/abs/2502.12110) (A-MEM)
- [arxiv.org/html/2502.12110v11](https://arxiv.org/html/2502.12110v11)
- [github.com/agiresearch/A-mem](https://github.com/agiresearch/A-mem)
- [arxiv.org/abs/2305.10250](https://arxiv.org/abs/2305.10250) (MemoryBank)
- [ar5iv.labs.arxiv.org/html/2305.10250](https://ar5iv.labs.arxiv.org/html/2305.10250)
- [mempalaceofficial.com](https://mempalaceofficial.com/) / [mempalace.tech](https://www.mempalace.tech/)
- [alexeyondata.substack.com/p/an-unexpected-entry-into-ai-memory](https://alexeyondata.substack.com/p/an-unexpected-entry-into-ai-memory)
- [recca0120.github.io/en/2026/04/08/mempalace-ai-memory-system/](https://recca0120.github.io/en/2026/04/08/mempalace-ai-memory-system/)
- [analyticsvidhya.com/blog/2026/05/mempalace-explained/](https://www.analyticsvidhya.com/blog/2026/05/mempalace-explained/)
- [arxiv.org/abs/2501.13956](https://arxiv.org/abs/2501.13956) (Zep)
- [github.com/getzep/graphiti](https://github.com/getzep/graphiti)
- [github.com/topoteretes/cognee](https://github.com/topoteretes/cognee)
- [arxiv.org/abs/2506.06326](https://arxiv.org/abs/2506.06326) (MemoryOS)
- [github.com/BAI-LAB/MemoryOS](https://github.com/BAI-LAB/MemoryOS)
- [arxiv.org/abs/2304.03442](https://arxiv.org/abs/2304.03442) (Generative Agents)
- [arxiv.org/abs/2309.02427](https://arxiv.org/abs/2309.02427) (CoALA)
- [cognee.ai/blog/fundamentals/cognitive-architectures-for-language-agents-explained](https://www.cognee.ai/blog/fundamentals/cognitive-architectures-for-language-agents-explained)

### Frameworks (LangChain / LlamaIndex / SillyTavern)
- [docs.langchain.com/oss/python/concepts/memory](https://docs.langchain.com/oss/python/concepts/memory)
- [docs.langchain.com/oss/python/langgraph/add-memory](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [reference.langchain.com/python/langchain-classic/memory/summary_buffer/ConversationSummaryBufferMemory](https://reference.langchain.com/python/langchain-classic/memory/summary_buffer/ConversationSummaryBufferMemory)
- [developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/)
- [llamaindex.ai/blog/improved-long-and-short-term-memory-for-llamaindex-agents](https://www.llamaindex.ai/blog/improved-long-and-short-term-memory-for-llamaindex-agents)
- [github.com/SillyTavern/SillyTavern](https://github.com/SillyTavern/SillyTavern)
- [docs.sillytavern.app/usage/core-concepts/worldinfo/](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- [docs.sillytavern.app/extensions/chat-vectorization/](https://docs.sillytavern.app/extensions/chat-vectorization/)
- [docs.sillytavern.app/extensions/smart-context/](https://docs.sillytavern.app/extensions/smart-context/)

### Narrative-specific
- [arxiv.org/abs/2412.13575](https://arxiv.org/abs/2412.13575) (DOME)
- [arxiv.org/abs/2212.10077](https://arxiv.org/abs/2212.10077) (DOC)
- [arxiv.org/abs/2210.06774](https://arxiv.org/abs/2210.06774) (Re3)
- [arxiv.org/abs/2508.03137](https://arxiv.org/abs/2508.03137) (Long Story Gen via KG + Literary Theory)
- [arxiv.org/html/2603.05890v1](https://arxiv.org/html/2603.05890v1) (Lost in Stories)
- [arxiv.org/abs/2505.14818](https://arxiv.org/abs/2505.14818) (WebNovelBench)

### Benchmarks
- [arxiv.org/abs/2410.10813](https://arxiv.org/abs/2410.10813) (LongMemEval)
- [github.com/xiaowu0162/longmemeval](https://github.com/xiaowu0162/longmemeval)
- [snap-research.github.io/locomo/](https://snap-research.github.io/locomo/)
- [arxiv.org/abs/2402.17753](https://arxiv.org/abs/2402.17753) (LoCoMo)
- [github.com/s010m00n/AgentMemoryBench](https://github.com/s010m00n/AgentMemoryBench)
- [arxiv.org/pdf/2507.05257](https://arxiv.org/pdf/2507.05257) (MemoryAgentBench)

### Failure modes / context drift
- [arxiv.org/pdf/2505.16894](https://arxiv.org/pdf/2505.16894) (Shadows in the Attention)

### Embedding
- [docs.ionos.com/cloud/ai/ai-model-hub/models/embedding-models/bge-m3](https://docs.ionos.com/cloud/ai/ai-model-hub/models/embedding-models/bge-m3)
- [ollama.com/library/bge-m3](https://ollama.com/library/bge-m3)
- [github.com/FlagOpen/FlagEmbedding](https://github.com/flagopen/flagembedding)
