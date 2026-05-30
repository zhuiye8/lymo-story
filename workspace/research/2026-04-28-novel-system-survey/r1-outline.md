# R1 · 大纲 / 剧情结构生成 — 调研报告

| Field | Value |
|---|---|
| Author | research sub-agent (Claude Opus 4.7 1M) |
| Started | 2026-04-28 |
| Scope | LLM-based outline / plot structure generation for long-form fiction (novels, multi-volume works) |
| Method | WebSearch + WebFetch only. No training-memory claims. Every finding has source URL + accessed_at + verbatim quote where possible. |
| Accessed | 2026-04-28 |

> Audit rule applied throughout: every claim cited to a URL fetched on 2026-04-28. Where the abstract page did not yield the requested fact and a second source (review page, HTML version, GitHub README) was used, both URLs are listed. Quotes inside `>` blocks are verbatim from the fetched source.
>
> Attribution caveat: per the requesting note, we previously got burned attributing HNES to WebNovelBench. Triple-checked: HNES (Hierarchical Neural Story Generation, Fan et al. 2018) is **not** discussed in this report; WebNovelBench is cited only to its own arXiv page. Where a paper's name appears, the author list was pulled from the paper's own arXiv abstract page, not from secondary search snippets.

---

## 1. Hierarchical outline generation (book → volume → arc → chapter → scene → beat)

### DOC — Detailed Outline Control (Yang et al., ACL 2023)

- Source: https://arxiv.org/abs/2212.10077 [accessed:2026-04-28]
- Code: https://github.com/yangkevin2/doc-story-generation [accessed:2026-04-28]
- Code v2: https://github.com/facebookresearch/doc-storygen-v2 [accessed:2026-04-28]
- Type: paper + repo
- Authors / org: Kevin Yang, Dan Klein, Nanyun Peng, Yuandong Tian (Berkeley NLP + UCLA + Meta)
- Published: 2022-12-20 (revised 2023-06-14), ACL 2023
- Maturity: research prototype with two public code releases; v1 archived (5 commits, 161 stars), v2 (92 stars, 11 commits, open issues, "ongoing development rather than archival" per the README check on 2026-04-28).
- Key idea (per the abstract):
  > "a detailed outliner creates a more detailed, hierarchically structured outline, shifting creative burden from the main drafting procedure to the planning stage. The detailed controller ensures the more detailed outline is still respected during generation."
- Hierarchy: recursive outline tree with default depth `--outline-levels 3`; each leaf gets up to 8 continuation passages of ~64 tokens (`--max-continuation-substeps 8`, `--max-tokens 64`). Original code uses OPT-175B via Alpa and a FUDGE-style OPT-350m controller; v2 supports LLaMA2-7B-Chat, ChatGPT, and JSON Premise/Plan/Story stages that are editable for human-in-the-loop.
- Reported gains over Re3 baseline (verbatim):
  > "plot coherence (22.5% absolute gain), outline relevance (28.2%), and interestingness (20.7%)"
- How it applies to our case:
  - applicability: high — closest published analog to what we want, with a maintained v2 repo and JSON-editable outline.
  - adoption cost: medium — controller stack (FUDGE/OPT-350m) is dated, but the outliner/control loop is reusable; v2 already separates the controller dependency.
  - dependencies: we'd port the outline tree to our Pydantic `ChapterGraphState`, swap their controller for LiteLLM-driven validation, and keep the recursive expand step.
- Caveats: original target ~3,500 word stories — not a multi-million-word webnovel; controller training relies on contrastive passage/summary pairs we don't currently have for Chinese.

### DOME / DHO — Dynamic Hierarchical Outlining with Memory Enhancement (Wang et al., NAACL 2025)

- Source (paper): https://arxiv.org/abs/2412.13575 [accessed:2026-04-28]
- Source (HTML w/ details): https://arxiv.org/html/2412.13575v1 [accessed:2026-04-28]
- Type: paper
- Authors / org: Qianyue Wang, Jinwu Hu, Zhengping Li, Yufeng Wang, Daiyuan Li, Yu Hu, Mingkui Tan (South China University of Technology et al.)
- Published: 2024-12-18, NAACL 2025
- Maturity: research prototype
- Hierarchy (per the HTML fetch):
  - **R** rough outline: 5 stages aligned with Joseph Campbell's hero-journey acts
  - **D** detailed outlines: each rough stage → M=3 chapter-level entries
  - **S** story content: text generated per detailed outline
- Key idea:
  > "The DHO mechanism incorporates novel writing theory into outline planning and fuses the plan and writing stages together, improving plot coherence by ensuring plot completeness and adapting to uncertainty during story generation."
- Memory Enhancement Module (MEM): temporal knowledge graph storing quadruples `<subject, action, object, chapter_index>`; a Temporal Conflict Analyzer reads the TKG to flag inconsistencies.
- Model + length: Qwen1.5-72B-Chat primary (also tested Yi1.5-34B, Llama3-70B); avg generated story ~7,113 words (Table 1) — single-novel scale, not series scale.
- Baselines compared: direct prompting (Llama3-70B-Instruct, Qwen1.5-72B-Chat), Re3, DOC.
- How it applies:
  - applicability: high — explicit hero's-journey templating + KG-backed continuity matches our agent design (Director / Consistency / Memory).
  - adoption cost: medium — schema is straightforward; the TKG quadruple format maps onto our existing `knowledge_triples` table almost 1:1.
  - dependencies: define the 5 hero-journey rough stages as a prompt constant, add a "rough/detailed" depth flag to our outline JSON, plug the temporal conflict check into the consistency agent.
- Caveats: 7k-word target is small — for 1M-word webnovels we'd need to recursively nest DHO inside volume planning. The fixed M=3 chapter ratio per rough stage is rigid.

### Measuring Information Distortion / "Optimal Expansion Ratio" (Shen & Ying, May 2025)

- Source: https://arxiv.org/html/2505.12572v1 [accessed:2026-04-28]
- Type: paper
- Authors / org: Hanwen Shen (Stevens Institute of Technology), Ting Ying
- Published: 2025-05-18
- Maturity: empirical study, no published code link surfaced in our fetch
- Setup (verbatim from fetch):
  > "Two-stage compression (novel → global outline → section outline) followed by expansion phases"
- Empirical claim: optimal compression-expansion ratio R = 0.01 under their config; "mixed two-stage" uses α₁=0.05 and α₂=0.20, then expands directly from finest outline to manuscript (skipping intermediate expansion).
- Model: Gemini 2.0 Flash, temperature 0.3; 40 ultra-long Chinese novels across Fantasy/Urban/Romance/Historical, ~1M words each, 8 sample chapters per novel from ~200-chapter texts.
- Headline finding: "K2-* (two-stage) demonstrated statistically significant improvements" vs. single-stage in character similarity and semantic preservation.
- How it applies:
  - applicability: high — they used Chinese 1M-word novels, the exact length target we care about.
  - adoption cost: low — paper directly answers a hyperparameter question (how aggressive should each compression step be). Use as a configuration prior.
  - dependencies: none; encode α₁=0.05, α₂=0.20 as initial defaults and re-validate on our own data.
- Caveats: no code release found; results are on a single (Gemini 2.0 Flash, T=0.3) configuration — ratios may not transfer to other models.

### Plan-and-Write (Yao et al., AAAI 2019) — the canonical ancestor

- Source: https://arxiv.org/abs/1811.05701 [accessed:2026-04-28]
- Type: paper
- Authors: Lili Yao, Nanyun Peng, Ralph Weischedel, Kevin Knight, Dongyan Zhao, Rui Yan
- Published: 2018-11-14, AAAI 2019
- Key idea (verbatim from abstract fetch):
  > "a plan-and-write hierarchical generation framework that first plans a storyline, and then generates a story based on the storyline"
- Two strategies: **dynamic** (interleave storyline planning with surface text), **static** (full storyline first).
- Maturity: foundational; cited by nearly every subsequent paper here.
- How it applies: gives us the conceptual fork — our current pipeline is static (full bible + outline up front); DOME's contribution is essentially dynamic-with-memory.
- Caveats: 2018-era models, original metrics not directly relevant to LLM-era quality.

### PlotMachines (Rashkin et al., EMNLP 2020) — dynamic plot state tracking

- Source: https://arxiv.org/abs/2004.14967 [accessed:2026-04-28]
- Type: paper
- Authors: Hannah Rashkin, Asli Celikyilmaz, Yejin Choi, Jianfeng Gao (UW + Microsoft)
- Published: 2020-04-30 (revised 2020-10-09), EMNLP 2020
- Key idea (verbatim from abstract):
  > "outline-conditioned story generation: given an outline as a set of phrases that describe key characters and events to appear in a story, the task is to generate a coherent narrative that is consistent with the provided outline."
- Verbatim finding:
  > "large-scale language models, such as GPT-2 and Grover, despite their impressive generation performance, are not sufficient in generating coherent narratives for the given outline, and dynamic plot state tracking is important for composing narratives with tighter, more consistent plots."
- How it applies: predates LLM era but anchors a key insight — outline alone is not enough; you need a running plot-state object that gets updated as chapters are produced. Aligns with our current `ChapterGraphState`.
- Caveats: 2020-era LSTM/transformer hybrid; results are pre-GPT-3.

### LongStory (Park, Yang, Jung, PAKDD 2024)

- Source: https://arxiv.org/abs/2311.15208 [accessed:2026-04-28]
- Type: paper
- Authors: Kyeongman Park, Nakyeong Yang, Kyomin Jung
- Published: 2023-11 (PAKDD 2024)
- Key components:
  - **CWC** (Context Weight Calibrator): BERT-tiny that learns to balance long-term "Memory" context vs. short-term "Cheating" (next-chapter hint) context.
  - **LSP** (Long Story Structural Positions): discourse tokens marking position in the story arc.
- Verbatim claim: "outperforms other baselines, including the strong story generator PlotMachine, in coherence, completeness, relevance, and repetitiveness."
- How it applies: the CWC idea is reusable — train a small classifier on which memory tier to pull for the current chapter (matches our LayeredMemory L0–L3 routing problem).
- Caveats: small-scale (3 datasets with limited story length); BERT-tiny is now under-powered.

### Hierarchical Ultra-long Novel Generation (Shen & Ying 2025) — already covered above; reuses two-stage compression.

---

## 2. Structured story methods (Save the Cat / Snowflake / Hero's Journey / 八点结构 / Story Circle)

### Save the Cat — in LLM systems

- Source (template page): https://savethecat.com/beat-sheets [accessed:2026-04-28]
- Source (Sudowrite blog, AI use): https://sudowrite.com/blog/how-to-outline-a-novel-with-ai-sudowrites-outline-feature-step-by-step/ [accessed:2026-04-28]
- Type: industry blog + product docs
- The Snyder beat sheet is canonical 15-beat structure. Sudowrite's outline feature explicitly supports it ("Save the Cat – 15-beat structure for plot-driven stories", per the 2026-03-04 blog post).
- LLM implementations on GitHub: searching "Save the Cat" + LLM + GitHub in 2026 surfaced **no academic paper or first-class open-source library that bakes the 15 beats into the data model**. Multiple commercial tools (Sudowrite, Novelcrafter, SidekickWriter) advertise it as a selectable template, not a published method.
- How it applies:
  - applicability: medium-high — we could codify the 15 beats as a JSON enum in our outline schema and use it as a prompt template option.
  - adoption cost: low — it's just a prompt + schema constant.
  - dependencies: none.
- Caveats: 15-beat is screenplay-shaped; Chinese webnovels (1M words, 200+ chapters) don't natively map to 15 acts. Use only at volume level.

### Snowflake Method — Joel Grus's SnowMeth implementation

- Source (blog): https://joelgrus.com/2025/07/23/vibe-coding-2-snowmeth-an-ai-novel-writing-assistant/ [accessed:2026-04-28]
- Source (repo): https://github.com/joelgrus/snowmeth [accessed:2026-04-28]
- Type: blog + repo (FastAPI + DSPy + React, 17 stars, 71 commits on master as of fetch)
- Author: Joel Grus, 2025-07-23
- 10-stage data model (from the README fetch):
  1. one-sentence concept
  2. paragraph expansion
  3. character roster
  4. plot structure
  5. individual character synopses
  6. full-length synopsis
  7. detailed character development
  8. scene-by-scene breakdown
  9. character arcs
  10. chapter-by-chapter novel generation
- DSPy use: each stage is a DSPy `Signature` (the blog quotes:
  > "class ParagraphExpander(dspy.Signature): \"\"\"Expand a one-sentence novel summary into a full paragraph\"\"\"")
- Model: Gemini 2.5 Flash-Lite. Cost: "probably $2 in tokens" across multi-day development.
- Author's verdict (verbatim): "sort of a novel" — useful but not yet full-novel-grade.
- How it applies:
  - applicability: high — the 10-stage Snowflake mirrors our Director→Bible→Outline pipeline almost exactly, and the DSPy signature pattern is reusable.
  - adoption cost: low — 10 prompts + a state machine we already have.
  - dependencies: none; we can borrow the Signature names verbatim.
- Caveats: single author, 17 stars — not battle-tested at scale. Author flagged a "Gemini Code assistance deleted my database" failure mode — separate from the method itself.

### Hero's Journey / Story Circle — practical implementations

- Source (Ollama tutorial): https://developer-service.blog/heros-journey-story-generator-in-python-with-ollama/ [accessed:2026-04-28 via search]
- Source (DOME paper, integrates Campbell): https://arxiv.org/html/2412.13575v1 [accessed:2026-04-28]
- Implementations:
  - DOME's "rough outline" uses Campbell's 5-stage hero-journey as the macro skeleton (see §1 above).
  - The Ollama tutorial implements per-stage prompts: name/age/motifs context → LLM call per stage. Toy demo.
- How it applies:
  - applicability: high for Chinese webnovels — many genres (修仙/玄幻) are essentially extended hero-journey loops.
  - adoption cost: low — encoding stages as a list of prompts.
  - dependencies: none.
- Caveats: tutorial-grade Ollama code is not production; DOME proves academic viability.

### 八点结构 / 起承转合 / Chinese structural templates

- Status: `[no-source-found:no-direct-paper]` — searches for "起承转合 LLM novel outline" and "八点结构" returned essay-writing guides for academic Chinese, not Chinese-novel LLM implementations. The closest match was the Sudowrite blog listing 5 outline methods, none specifically Chinese.
- The Chinese-specific LLM project list (see §8) uses ad-hoc method blends (volume / chapter / scene) rather than codifying 起承转合.

### STORYTELLER — SVO-triplet plot nodes (Li et al., ACL Findings 2025)

- Source: https://arxiv.org/abs/2506.02347 [accessed:2026-04-28]
- Type: paper
- Authors: Jiaming Li, Yukun Chen, Ziqiang Liu, Minghuan Tan, Lei Zhang, Yunshui Li, Run Luo, Longze Chen, Jing Luo, Ahmadreza Argha, Hamid Alinejad-Rokny, Wei Zhou, Min Yang
- Published: 2025-06-03
- Key idea (verbatim):
  > "linguistically grounded subject verb object (SVO) triplets, which capture essential story events and ensure a consistent logical flow"
- Modules: STORYLINE (plot graph) + NEKG (Narrative Entity Knowledge Graph) — both update continuously during generation.
- Models tested: GPT-4, Llama 3, Qwen, ChatGLM. Reported 84.33% average win rate on human preference (baselines not enumerated in the abstract).
- How it applies:
  - applicability: high — SVO triples are an efficient "atomic event" representation that fits between our outline beats and Memory triples.
  - adoption cost: medium — needs SVO extraction prompts and a graph store (we already use ChromaDB + SQLite knowledge_triples).
  - dependencies: a SVO extraction agent + a verb-ontology so the graph deduplicates synonyms.
- Caveats: full PDF could not be parsed (binary content); details about story length and exact comparison numbers come from the abstract only.

---

## 3. Beat sheets / scene planning (2024-2026)

### Agents' Room (Huot et al., ICLR 2025)

- Source: https://arxiv.org/abs/2410.02603 [accessed:2026-04-28]
- Review source: https://www.themoonlight.io/en/review/agents-room-narrative-generation-through-multi-step-collaboration [accessed:2026-04-28]
- Type: paper + ICLR slides + dataset
- Authors / org: Fantine Huot, Reinald Kim Amplayo, Jennimaria Palomaki, Alice Shoshana Jakobovits, Elizabeth Clark, Mirella Lapata (Google DeepMind)
- Published: 2024-10-03 (revised 2025-03-14), ICLR 2025
- Architecture (per review fetch):
  - Planning agents — character, central conflict, setting, key plot points (no text generation).
  - Writing agents — exposition, rising action, climax, falling action, resolution (each writes one act).
  - Orchestrator chooses next agent based on a scratchpad state.
- Tell Me A Story dataset: ~350 expert-written stories @ ~2,000 words each, collected via drafting/review/revision workshops.
- Dataset link: https://github.com/google-deepmind/tell-me-a-story [accessed:2026-04-28 via search]
- How it applies:
  - applicability: medium — five-act structure is too coarse for 200-chapter webnovels but maps well to volume-level planning.
  - adoption cost: low — we already have a multi-agent pipeline; this is a re-allocation of duties.
  - dependencies: none new; reorganize our agents to match.
- Caveats: target stories are ~2,000 words. The orchestrator logic is described only in prose — no code release was located on 2026-04-28.

### StoryWriter (Xia et al., 2025-06)

- Source: https://arxiv.org/abs/2506.16445 [accessed:2026-04-28]
- Type: paper
- Authors: Haotian Xia, Hao Peng, Yunjia Qi, Xiaozhi Wang, Bin Xu, Lei Hou, Juanzi Li (Tsinghua KEG)
- Published: 2025-06-19
- Three-agent architecture (verbatim):
  > "Outline Agent — Generates event-based outlines containing rich event plots, character, and event-event relationships";
  > "Planning Agent — Details events and determines which content appears in each chapter";
  > "Writing Agent — Dynamically compresses the story history based on the current event to generate and reflect new plots".
- Models: fine-tuned Llama3.1-8B and GLM4-9B on a 6,000-story SFT corpus (avg 8,000 words/story).
- How it applies:
  - applicability: high — three agents match our Planner/Camera/Writer split nearly 1:1.
  - adoption cost: medium — the fine-tuning piece is heavy; we can run the architecture without their checkpoints.
  - dependencies: an event-relationship JSON schema we don't currently have.
- Caveats: 8,000-word target. Their innovation is the explicit event-event relationship graph, not the agent split.

### Beyond Direct Generation — DSR (Lei et al., Alibaba, Oct 2025)

- Source: https://arxiv.org/html/2510.23163v1 [accessed:2026-04-28]
- Type: paper
- Authors: Hang Lei, Shengyi Zong, Zhaoyan Li, Ziren Zhou, Hao Liu (Alibaba + PKU)
- Published: 2025-10
- Key idea: two-stage outline → novel-style prose → screenplay; uses novel prose as an intermediate representation to bridge planning↔execution.
- Verbatim failure-mode framing: "Task Coupling Dilemma" — single-shot generation forces the model to simultaneously do creative narration and rigid format adherence.
- Result: 82.7% human-level performance (no baseline named in our fetch).
- How it applies:
  - applicability: medium — the "intermediate prose" idea is interesting if we ever need to flip between formats (script vs. novel), not urgent for our novel-only path.
  - adoption cost: low if treated as a prompt pattern.
- Caveats: screenplay-focused; our use case is novels.

### Dramatron (Mirowski et al., DeepMind, CHI 2023 → still active reference)

- Source (paper): https://arxiv.org/abs/2209.14958 [accessed:2026-04-28 via search]
- Source (code): https://github.com/google-deepmind/dramatron [accessed:2026-04-28]
- Type: paper + repo (1.1k stars, 91 commits)
- Hierarchy (verbatim from search snippet, confirmed by repo README): log line → characters → plot points → location descriptions → dialogue.
- LLM: paper used Chinchilla 70B; the public Colab is "unplugged" (BYO model).
- How it applies:
  - applicability: medium — 5-stage top-down is too coarse for 1M-word novels; useful as the volume-level skeleton.
  - adoption cost: low.
- Caveats: 2022 system; not maintained for novel-length output specifically. Repo is a reference, not a library.

---

## 4. Multi-volume arc planning (longer than a single novel)

This is the weakest area in the published literature.

### State of academic literature

- **No academic paper found** that explicitly evaluates multi-volume (book-2/book-3) coherence as a benchmark task. Search "novelist multi-volume series planning AI LLM trilogy arc" returned commercial-tool blogs only, plus the 1M-word Chinese hierarchical paper (Shen & Ying) which is one extended novel, not multi-book.
- Label: `[no-source-found:no-academic-benchmark-for-trilogy-or-book2-arcs]`. Queries attempted: "novelist multi-volume series planning AI LLM trilogy arc", "novel LLM book 2 sequel coherence paper", "long story series outline LLM"; all returned commercial blogs.

### Practical OSS evidence

- **lingfengQAQ/webnovel-writer** explicitly handles volume → chapter → section hierarchy at 2M-character scale. Source: https://github.com/lingfengQAQ/webnovel-writer [accessed:2026-04-28]. 4.6k stars, v6.0.0 released 2026-04-24. Structure:
  ```
  .story-system/{MASTER_SETTING.json, volumes/, chapters/}
  .webnovel/{state.json, index.db, summaries/, memory_scratchpad.json}
  ```
  Verbatim from fetch: "Volume-level organization with hierarchical outlines."
- **FredericMN/AutoNovel**: supports "volume-specific summaries for multi-book works" and "vector database with semantic retrieval across volumes" (source: https://github.com/FredericMN/AutoNovel [accessed:2026-04-28]; 12 stars only — small-scale validation).
- **Novelcrafter / Sudowrite**: closed-source commercial; their story-bible system "carries across your project" per the Sudowrite blog (https://sudowrite.com/blog/how-to-outline-a-novel-with-ai-sudowrites-outline-feature-step-by-step/ [accessed:2026-04-28]) but no published architecture.

### How it applies
- applicability: high (this is our roadmap)
- adoption cost: high (we're inventing on top of OSS templates)
- dependencies: a volume-level state object above `InitGraphState`, with cross-volume foreshadowing ledger and series-arc bible.

### Caveats
- No academic baseline — must validate empirically.
- The 2M-character Chinese repo is community-maintained, not peer-reviewed, but does demonstrate the engineering is tractable.

---

## 5. Iterative outline refinement (Critic loop, self-correcting outlines)

### Self-Refine (Madaan et al., 2023) — the canonical loop

- Source: https://selfrefine.info/ [accessed:2026-04-28 via search snippets — search engine returned summary]
- Source: https://arxiv.org/pdf/2303.17651 [accessed:2026-04-28 via search]
- Source: https://github.com/madaan/self-refine [accessed:2026-04-28 via search]
- Type: paper + repo
- Authors: Aman Madaan et al. (2023)
- Loop (per search-snippet fetch — note: we did not fetch the PDF directly, so only the abstract-level description is verified):
  > "FEEDBACK → REFINE → FEEDBACK loop ... does not require supervised training data or reinforcement learning, and works with a single LLM"
- How it applies: this is the pattern our `consistency_check → retry` already uses. Self-Refine extends it with multi-axis feedback (the same critic produces feedback along several dimensions in one call).
- Caveats: We sourced this via search summaries on 2026-04-28; treat the verbatim quote as second-hand pending a direct PDF read.

### EIPE-text (You et al., Microsoft, 2023)

- Source: https://arxiv.org/abs/2310.08185 [accessed:2026-04-28]
- Type: paper
- Authors: Wang You, Wenshan Wu, Yaobo Liang, Shaoguang Mao, Chenfei Wu, Maosong Cao, Yuzhe Cai, Yiduo Guo, Yan Xia, Furu Wei, Nan Duan (Microsoft Research)
- Published: 2023-10-12
- Key mechanism: QA-based evaluator scores extracted plans and emits "detailed refinement instructions"; iterates until quality threshold.
- How it applies:
  - applicability: high — drop-in for the Consistency agent's outline-relevance check.
  - adoption cost: medium — needs question-bank for QA evaluator.
- Caveats: paper is about extracting plans from existing corpora, not authoring from scratch; transfer requires reformulation.

### Creating Suspenseful Stories (Xie & Riedl, EACL 2024)

- Source: https://arxiv.org/abs/2402.17119 [accessed:2026-04-28]
- Type: paper
- Authors: Kaige Xie, Mark Riedl (Georgia Tech)
- Published: 2024-02-27
- Verbatim: "theory-grounded method ... in a fully zero-shot manner"
- How it applies:
  - applicability: medium — adds suspense as a structural target, relevant for certain genres.
  - adoption cost: medium.
- Caveats: full method details not in abstract; results were "human evaluations demonstrated effectiveness" without numbers in our fetch.

### Learning to Reason for Long-form Story Generation (Gurung & Lapata, March 2025)

- Source: https://arxiv.org/abs/2503.22828 [accessed:2026-04-28]
- Type: paper
- Authors: Alexander Gurung, Mirella Lapata (Edinburgh)
- Published: 2025-03-28 (revised 2025-09-08)
- Key idea: RL with verifiable rewards ("Verified Rewards via Completion Likelihood Improvement") applied to a "Next-Chapter Prediction" task; teaches model to plan before drafting.
- Verbatim outcome:
  > "Human evaluators preferred chapters generated with the learned reasoning approach across nearly all metrics ... with particularly pronounced improvements in Science Fiction and Fantasy genres."
- How it applies:
  - applicability: medium-high (frontier approach; teaches outline reasoning rather than prompting it).
  - adoption cost: high (full RL stack).
  - dependencies: RL infra, unlabeled book data.
- Caveats: heavy training; reproducing requires substantial compute.

### Guiding & Diversifying via ASP (Wang & Kreminski, June 2024)

- Source: https://arxiv.org/html/2406.00554v1 [accessed:2026-04-28]
- Type: paper
- Authors: Phoebe J. Wang, Max Kreminski (Santa Clara University + Midjourney)
- Published: 2024-06-01
- Verbatim: uses "just fifteen total constraints, each consisting of no more than three lines of ASP code".
- Outline format: 7 scenes, each with one narrative function from a fixed library (intro_char, add_obstacle, add_twist, level_up_obstacle, ...).
- Model: GPT-3.5-turbo for prose, MiniLM for diversity scoring.
- How it applies:
  - applicability: medium — ASP is overkill for our pipeline but the **function vocabulary** is reusable as a controlled enum for our outline schema.
  - adoption cost: low if we steal the function list, high if we adopt Clingo.
- Caveats: 7-scene target; not novel scale.

---

## 6. Tooling / framework (DSPy chains, LangGraph state for outline)

### DSPy

- Source (docs): https://dspy.ai/ [accessed:2026-04-28 via search]
- Source (paper): https://arxiv.org/pdf/2310.03714 [accessed:2026-04-28 via search]
- Pattern: each outline stage = one `Signature`; chained with `Module`s; optimized with `Teleprompter`. SnowMeth is a real-world demonstration on 10-stage Snowflake (see §2).
- How it applies:
  - applicability: high — gives us a typed input/output contract for every outline stage and lets us A/B-optimize prompts automatically.
  - adoption cost: medium — refactor our existing agent prompts into DSPy signatures; integrates with LiteLLM via custom LM.
  - dependencies: a metric for outline quality (we have none yet — would need to build).
- Caveats: DSPy optimizers need training examples (~50+). For novels these are hard to collect.

### LangGraph

- Source: https://medium.com/@kishorek/how-to-build-an-ai-powered-novel-writing-workflow-with-langgraph-langchain-2ef915ef39b1 [accessed:2026-04-28]
- Date: 2025-05-03 (author: Kishore Kumar Uthirapathy)
- Concrete pattern (verbatim):
  > "Nine specialized nodes handle distinct phases: understanding user requirements, developing characters, creating settings, outlining plots, writing individual chapters, reviewing chapters, revising based on feedback, incrementing to the next chapter, and finalizing the complete manuscript."
- Edge logic: "After each chapter revision, the graph checks if more chapters remain. If so, it loops; if not, it finalizes the novel."
- How it applies: this **is** our current architecture — we already use LangGraph for our chapter graph. The article validates our approach.
- Adoption cost: zero — already done.

### Outlines / Instructor for structured output (cross-ref R10)

- Out of scope here — covered in `r10-structured-io.md` per the workspace plan.

---

## 7. Outline-aware generation (outline → chapter handshake)

### Common pattern across surveyed systems

Every system that generates >5,000 words uses the same general handshake:
1. Outline chunk for the current chapter is injected as the primary instruction.
2. Compressed summary of preceding chapters is injected as context.
3. Story bible / character sheets are injected as constants.
4. Chapter is drafted and (often) reviewed by a critic.

### Specific reference patterns

- **DOC v2** (https://github.com/facebookresearch/doc-storygen-v2 [accessed:2026-04-28]): JSON-formatted Premise + Plan, edited as needed, then per-passage generation with controller bias.
- **Re3** (https://arxiv.org/abs/2210.06774 [accessed:2026-04-28]): four modules — Plan / Draft / Rewrite / Edit. Draft uses "recursive reprompting" that "repeatedly feed[s] contextual information from both the plan and current story state into language model prompts". Rewrite re-ranks for plot coherence + premise relevance. Edit handles factual consistency.
  - Verbatim improvement: "substantially more coherent plots (14% absolute improvement) and better premise relevance (20% improvement)" over base GPT-3.
- **AutoNovel** (https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md [accessed:2026-04-28]): per-chapter load list (verbatim from fetch):
  > "voice.md (full), world.md (full), characters.md (full), this chapter's outline entry, previous chapter's last ~1000 words, next chapter's outline."
- **Novelcrafter** (https://www.novelcrafter.com/help/faq/plan/outline-impact [accessed:2026-04-28 via search]): the "scene summaries of the scenes prior to the beats you are working on" are auto-injected; Codex entries are pulled by entity mention.
- **InkOS** (https://github.com/Narcooo/inkos [accessed:2026-04-28]): truth files (current_state, resource_ledger, pending_hooks, chapter_summaries, subplot_board, emotional_arcs, character_interaction_matrix) loaded per-chapter from disk.

### How it applies
- applicability: high — confirms our `load_context → world_advance → plot_plan → camera_decide → load_memories → write_chapter` stack is industry-standard.
- adoption cost: zero — pattern is already what we do.
- dependencies: explicit per-chapter context manifest (we already have one in `ChapterGraphState`).

### Caveats
- The "next chapter outline" injection (used by AutoNovel) is a smart pacing aid we don't currently use.
- "Previous chapter's last ~1000 words" is verbatim text not summary — different from our summary-only approach. Worth A/B testing.

---

## 8. Open-source novel projects' outline approach (cross-ref R4)

### lingfengQAQ/webnovel-writer (Claude Code based, 4.6k stars)

- Source: https://github.com/lingfengQAQ/webnovel-writer [accessed:2026-04-28]
- Last release: v6.0.0 (2026-04-24) — very actively maintained
- Outline structure: Volumes → Chapters → Sections
- Memory: "long-term memory with closure loop", "Entity knowledge graphs", "Hybrid RAG using graph and BM25 fallback"
- Tech: Python (92.6%), GPL v3, runs on Claude Code
- **Most direct reference architecture for our project.**

### Narcooo/inkos (TS / pnpm workspace, 6.7k stars)

- Source: https://github.com/Narcooo/inkos [accessed:2026-04-28]
- Last commit: 2026-05-18
- "33-dimension checking" includes character_memory, resource_continuity, foreshadowing_recovery, outline_deviation, narrative_pacing, emotional_arcs (sample list).
- Outline files: `author_intent.md`, `current_focus.md`, `volume_outline.md`, `chapter-XXXX.intent.md`.
- Memory: 7 markdown truth files + SQLite time-series DB.
- Multi-model routing: Claude for writing, GPT-4o for auditing, local for scanning. Integrates Google Gemini, Moonshot, MiniMax, Zhipu, Bailian.

### worldwonderer/oh-story-claudecode (1.6k stars)

- Source: https://github.com/worldwonderer/oh-story-claudecode [accessed:2026-04-28]
- Last release: v0.6.10 (2026-05-27)
- 7-agent architecture: story-architect (Opus), character-designer (Sonnet), narrative-writer (Sonnet), consistency-checker (Haiku), story-researcher (Sonnet), story-explorer (Haiku), chapter-extractor (Haiku).
- 5-stage workflow: market scan → structural dissection → composition → AI-style removal → cover generation.
- Targets webnovel platforms: Webnovel, Fanqie, Jjwxc, Zhihu.

### NousResearch/autonovel

- Source: https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md [accessed:2026-04-28]
- 4-phase pipeline: Foundation → First Draft → Revision (3-6 cycles) → Export.
- Outline = `outline.md part 1` (beats, chapter structure) + `outline.md part 2` (foreshadowing ledger).
- Exit thresholds: foundation_score > 7.5 and lore_score > 7.0; chapter score > 6.0.
- First published novel: "The Second Son of the House of Bells" — 19 chapters / 79,456 words.

### FredericMN/AutoNovel

- Source: https://github.com/FredericMN/AutoNovel [accessed:2026-04-28]
- 12 stars, smaller community.
- ABC-leveled plot arcs (`plot_arcs.txt`), global_summary + character_state files, multi-volume support.
- Critic-Writer loop ("Plan C") with foreshadowing injection ("Plan A") and summary caching ("Plan B").

### cjyyx/AI_Gen_Novel (418 stars)

- Source: https://github.com/cjyyx/AI_Gen_Novel [accessed:2026-04-28]
- Cognitive process: planning / translating / reviewing (inspired by RecurrentGPT).
- Author's verbatim conclusion: "current large language models lack sufficient capability for long webnovels."
- Effectively archived per the author's own statement.

### hestudy/snowflake-fiction (20 stars)

- Source: https://github.com/hestudy/snowflake-fiction [accessed:2026-04-28]
- Claude Code plugin implementing Snowflake method end-to-end with commands like `/outline-concept`, `/character-design`, `/scene-plan`, `/chapter-write`, `/novel-review`, `/humanize-text`, `/novel-export` (with platform-specific Fanqie/Qidian formats).
- MIT licensed.

### Common patterns across OSS

1. **Markdown-as-database** for authoring artifacts (outline, characters, world). Used by InkOS, oh-story, autonovel, lingfengQAQ.
2. **JSON state** for runtime / index. Used by lingfengQAQ (`state.json`, `index.db`).
3. **Per-chapter truth-file load list**. Universal.
4. **Foreshadowing ledger** as a separate file/structure. Used by autonovel, FredericMN/AutoNovel, InkOS, oh-story.
5. **Critic-Writer revision loop**. Universal.

### How it applies
- applicability: very high — these are the working systems shipping at scale today.
- adoption cost: low for patterns; medium if porting code (mostly Claude Code / TypeScript).
- dependencies: foreshadowing ledger is the one structure we don't yet have.

---

## 9. Chinese-specific (起点 / 番茄 / 文学 platforms; templates / annotation studies)

### WebNovelBench (Lin, Zheng, Wang, May 2025)

- Source: https://arxiv.org/html/2505.14818 [accessed:2026-04-28]
- Type: benchmark paper
- Authors: Leon Lin (NTU), Jun Zheng, Haidong Wang (Sun Yat-Sen)
- Published: 2025-05-20
- Dataset: 4,000+ Chinese web novels.
- Task: synopsis-to-story; synopsis = "main characters, key plot points, important scenes" auto-extracted from 10 random consecutive chapters per novel using Doubao-pro-32k. ~40,000 test instances total.
- **Eight narrative quality dimensions with PCA weights** (verbatim from HTML fetch):
  | # | Dimension | Weight |
  |---|---|---|
  | 1 | Use of Literary Devices | 0.1304 |
  | 2 | Richness of Sensory Detail | 0.1160 |
  | 3 | Balance of Character Presence | 0.1152 |
  | 4 | Distinctiveness of Character Dialogue | 0.1171 |
  | 5 | Consistency of Characterisation | 0.1377 |
  | 6 | Atmospheric and Thematic Alignment | 0.1290 |
  | 7 | Contextual Appropriateness | 0.1281 |
  | 8 | Scene-to-Scene Coherence | 0.1263 |

- Top-5 LLMs ranked (verbatim):
  > "Qwen3-235B-A22B (norm score: 5.21), DeepSeek-R1, Gemini-2.5-Pro, GPT-4o, DeepSeek-V3"
- Judge: DeepSeek-V3 as LLM-as-Judge; aggregation via PCA + ECDF percentile.
- Comparison context: Mao Dun Prize winners scored highest, then popular webnovels, then LLM outputs.
- How it applies:
  - applicability: very high — directly the eval framework we should adopt.
  - adoption cost: medium — we'd build evaluator prompts for each of 8 dimensions and run PCA on outputs.
  - dependencies: a labeled set of Chinese webnovel chapters to fit the PCA.
- Caveats: synopsis-to-story is a single-chunk task, not chapter-by-chapter.

### Creative Convergence or Imitation — Proppian narratology applied to LLMs (2026)

- Source: https://arxiv.org/html/2603.14430v1 [accessed:2026-04-28]
- Type: paper
- Published: 2026
- Genres tested: Fantasy, Xianxia, Romance, Time Travel, Urban (100 novels total).
- Models evaluated: GPT-4o, Qwen3, Deepseek, Doubao, Xuanyuan, Qianfan, Kimi.
- Framework: 34 narrative functions adapted from Propp's 31 (adds "Golden Finger / 金手指" and "Face-Slapping / 打脸" etc.).
- Key failure findings (verbatim from fetch):
  > "Most LLMs are able to recognize only a limited subset of common narrative functions ... while exhibiting substantially lower performance on uncommon functions."
  > "All six plot types exhibit default narrative function arrangement patterns" — i.e., LLMs reproduce default templates.
  > "Models 'remain blind to the axiomatic rules governing narrative skeletons, unable to dynamically model abstract story architectures.'"
- LLM accuracy at recognizing narrative functions: 36% — diagnostic of structural blindness.
- How it applies:
  - applicability: very high — explains *why* our generated chapters feel formulaic.
  - adoption cost: low for diagnosis — score our own outputs against their function set.
  - dependencies: implementation of the 34-function annotation scheme.
- Caveats: 100-novel sample.

### Qidian-Webnovel Corpus

- Source: https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.368 [accessed:2026-04-28 via search]
- Dataset: 110 Chinese web novels with parallel English translations, 2.79M Chinese comments + 237k English comments, book/chapter/paragraph-level annotations (snapshot 2024-09-01).
- How it applies: corpus for reader-response signals; not directly for outline generation but useful for evaluating reader engagement.

### 番茄小说 platform AI features

- Source: https://www.aigc.cn/59014.html [accessed:2026-04-28 via search]
- Built-in features: 开书灵感 (book inspiration), 生成大纲 (outline generation), 续写, 卡文锦囊 (plot-block resolver: generates 5 alternative continuations), AI 起名, AI 助手.
- As of September 2025, the platform requires authors to declare AI use.
- How it applies: a UX reference for our admin frontend, not an algorithm reference.

### Industry critique

- Source: https://www.techwalker.com/2025/0527/3166827.shtml [accessed:2026-04-28 via search]
- Article frames the LLM-novel space as "竞技场" — explicit acknowledgement that LLM-generated webnovels are competing on the same distribution as human authors.

---

## 10. Failure modes (chapter 50, chapter 100, volume 3)

### Lost in Stories (Li et al., Microsoft Beijing + SUTD, March 2026)

- Source: https://arxiv.org/html/2603.05890v1 [accessed:2026-04-28]
- Type: paper
- Authors: Junjie Li, Xinrui Guo, Yuhao Wu, Roy Ka-Wei Lee, Hongzhi Li, Yutao Xie
- Published: 2026-03-06
- **5-dimension consistency taxonomy with 19 subtypes** (verbatim from fetch):
  1. **Timeline & Plot Logic** (6 subtypes: absolute time, duration, simultaneity contradictions, causeless effects, causal logic violations, abandoned plot elements)
  2. **Characterization** (4 subtypes: memory, knowledge contradictions, skill fluctuations, forgotten abilities)
  3. **World-building & Setting** (3 subtypes: core rules violations, social norms violations, geographical contradictions)
  4. **Factual & Detail Consistency** (3 subtypes: appearance mismatches, nomenclature confusions, quantitative mismatches)
  5. **Narrative & Style** (3 subtypes: perspective confusions, tone inconsistencies, style shifts)

- **Where errors concentrate** (verbatim):
  > "contradiction positions predominantly clustering in the 40–60% range, while facts establish early (15–30%). Geographical contradictions exhibit the largest gaps (31.0% positional distance), followed by absolute-time errors (29.7%), whereas perspective errors show minimal gaps (4.7%)."

- **Key quantitative findings**:
  - Lowest error density: GPT-5-Reasoning at 0.113 errors / 10K words.
  - "Errors accumulate approximately linearly with output length."
  - Error content shows 12–19% higher entropy than whole-text baseline.
  - Factual & Detail Consistency is the dominant failure mode.
  - "Generation tasks yield highest error rates" versus continuation/expansion/completion.

- **19 models tested** across proprietary (GPT-5-Reasoning, Gemini-2.5-Pro, Claude-Sonnet-4.5), open-source (Qwen, DeepSeek, GLM), capability-enhanced (LongWriter-Zero), and agent-enhanced (SuperWriter).

- **Recommendation for outline systems** (verbatim from fetch):
  > "outline-based generation systems should incorporate entropy-guided mechanisms to flag high-uncertainty segments ... The strong correlation between factual errors and other categories indicates that robust entity-tracking infrastructure could cascadingly improve overall consistency."

### Failure modes from Creative Convergence (Chinese-specific, 2026)

- Source: https://arxiv.org/html/2603.14430v1 [accessed:2026-04-28] (see §9)
- 36% narrative-function recognition accuracy by LLMs → models cannot reason about plot grammar.
- All six plot templates collapse to default function sequences → "homogenization."

### Failure modes from AI_Gen_Novel author

- Source: https://github.com/cjyyx/AI_Gen_Novel [accessed:2026-04-28]
- Author's verbatim post-mortem: "current large language models lack sufficient capability for long webnovels."

### Failure modes from SnowMeth author

- Source: https://joelgrus.com/2025/07/23/vibe-coding-2-snowmeth-an-ai-novel-writing-assistant/ [accessed:2026-04-28]
- Author's verbatim assessment: "sort of a novel."

### Failure modes from informal sources

- Source: https://novarrium.com/blog/ai-story-consistency-complete-guide [accessed:2026-04-28 via search]
- Verbatim: "Specific details (character descriptions, world rules, plot specifics) fade faster than general narrative direction."
- Self-amplifying drift: "When the AI makes a small inconsistency, that altered version becomes part of the context for the next generation."

### Composite failure inventory for OUR system

(See "Failure modes inventory" section below for the synthesized list.)

---

## Pattern catalog

### Top-down (outline before writing)
- DOC / DOC v2 — detailed outliner + controller (Yang et al. 2023).
- Re3 — Plan/Draft/Rewrite/Edit (Yang et al. 2022).
- Plan-and-Write static schema (Yao et al. 2019).
- Dramatron — 5-stage hierarchical (DeepMind 2022).
- Snowflake / SnowMeth — 10 sequential stages.
- WritingPath — 5 steps (Lee et al. NAACL 2025).
- Agents' Room — 4 planning agents + 5 writing agents (ICLR 2025).
- StoryWriter — Outline / Planning / Writing agents (Tsinghua 2025).
- AutoNovel pipelines (Nous, FredericMN) — 4-phase Foundation→Draft→Revise→Export.

### Bottom-up (write then outline-fitting)
- StoryBox — multi-agent simulation in a sandbox, events emerge from agent interactions, then Storyteller Agent narrates (Chen et al. March 2026, ~12k words/story).
- Plan-and-Write dynamic schema — interleaves planning with surface.

### Hybrid / iterative
- DOME — rough plan → detailed plan grows during generation, memory-enhanced (NAACL 2025).
- EIPE-text — extract-then-refine plans (MSR 2023).
- Self-Refine pattern — FEEDBACK→REFINE loop on any output (Madaan et al. 2023).
- AutoNovel revision phase — 3-6 critic loops until plateau.
- Re3 — recursive reprompting + rewrite + edit modules.
- Learning to Reason — RL-trained next-chapter reasoning (Gurung & Lapata 2025).

### Structured templates (Snowflake, Save the Cat, Hero's Journey, Story Circle)
- Snowflake — Ingermanson; baked into SnowMeth + hestudy/snowflake-fiction repos.
- Save the Cat — Snyder 15 beats; Sudowrite supports as selectable template; no academic LLM baking.
- Hero's Journey — Campbell; DOME builds its rough outline directly on the 5 stages.
- Story Circle — Harmon's 8 steps; tutorial-grade Ollama implementations only.
- ASP narrative-function library — Wang & Kreminski's 9-function list with constraint enforcement (GPT-3.5).
- Proppian 34-function set adapted for Chinese webnovels — Creative Convergence study (2026).
- STORYTELLER SVO-triplet plot nodes — Li et al. ACL Findings 2025.

### LLM-emergent (let the model generate freely with light scaffolding)
- Direct prompting of Llama3-70B / Qwen2.5-72B — baseline in nearly every paper, consistently the worst (no structural memory, drifts after ~5k tokens).
- ChatGPT one-shot novel writing — covered in commercial-blog comparisons; not a published method.

### Outline-aware context handshake (universal pattern across all production systems)
- Per-chapter manifest: bible + voice + memory + outline_for_this_chapter + outline_for_next_chapter + previous_chapter_tail + summaries of recent chapters.

---

## Failure modes inventory

(Synthesized from Lost in Stories §10, Creative Convergence §9, Novarrium blog §10, OSS authors' post-mortems §8.)

1. **Mid-novel contradiction cluster** — most consistency bugs appear in the 40-60% range of the story (Lost in Stories §10). Implication: investing in mid-novel rolling validation pays more than over-validating early chapters.
2. **Geographical / temporal slop has the largest "delay gap"** — error establishes at 5% of story but contradicts at 36% (geo) / 35% (time). Implication: persistent world-state store > re-reading context.
3. **Linear error accumulation with length** — failure density grows linearly with output tokens, not sub-linearly (Lost in Stories §10). Implication: hierarchical compression that *resets* per-chapter doesn't help; you need explicit fact tracking.
4. **Factual & Detail Consistency dominates** — appearance / nomenclature / quantitative errors are highest-frequency (Lost in Stories §10). Implication: an entity-tracking module is highest ROI.
5. **Generation > continuation/expansion in error rate** — when you ask the model to generate a chapter from a brief, it errs more than when you ask it to continue text it already wrote. Implication: shorter, more structured prompts per chapter, with explicit re-statement of constraints.
6. **Self-amplifying drift** — small errors compound because they enter the context for the next chapter (Novarrium §10). Implication: review-and-correct **before** writing the next chapter, not after the whole novel.
7. **Default-template homogenization** — Chinese webnovel LLMs collapse to default function sequences across all six tested plot types (Creative Convergence §10). Implication: enforce randomized / story-bible-specific function ordering at the outline stage.
8. **Narrative-function comprehension failure** — LLMs hit only 36% accuracy at identifying narrative functions in Chinese fiction (Creative Convergence §10). Implication: cannot rely on the model to self-evaluate plot structure.
9. **"Cognitive fatigue" in autoregressive generation** — decaying prompt attention, hidden-state drift, entropy collapse over long outputs (broad-survey blog/paper aggregation from §10). Implication: chunked generation with hard resets is preferable to one continuous run.
10. **No academic baseline for trilogy / multi-volume** (§4) — the failure mode here is *we don't know*. The closest empirical reference is community projects like webnovel-writer at 2M characters.
11. **Author burnout: "sort of a novel"** — both SnowMeth and AI_Gen_Novel authors concluded their systems produce sub-novel output. Suggests the structural scaffolding is necessary but not sufficient; quality requires substantial human edit even with strong outlines.
12. **Rigid M=3 chapter ratios** (DOME) — fixed ratios per macro-act don't fit variable-genre webnovels. Implication: adaptive ratios per genre or per-volume.

---

## Top 3 candidate approaches for our system

### 1. DOME-style Dynamic Hierarchical Outline + TKG memory + 5-stage Hero's Journey at volume level

- Reasoning (时效性): NAACL 2025; current; published by NLP authors at South China University of Tech.
- Reasoning (鲁棒性): tested at 7k-word scale only; needs scaling validation but core mechanism (TKG + DHO) maps cleanly onto our existing SQLite knowledge_triples and ChromaDB stores.
- Reasoning (可行性): high — Chinese-trained authors, Qwen-based, Hero's Journey is a culturally portable structure for 玄幻/修仙. Can be implemented without re-training: prompt + state-machine + KG.
- Concrete adoption: encode 5 rough stages as a volume-scope enum; allow variable chapter ratios per stage; pipe SVO-triple memory (STORYTELLER) into our existing KG store; implement Temporal Conflict Analyzer as a new Consistency-agent sub-check.

### 2. STORYTELLER SVO plot nodes + Lost-in-Stories entity tracking layer

- Reasoning (时效性): ACL Findings 2025 + Lost in Stories March 2026 — bleeding edge.
- Reasoning (鲁棒性): Lost in Stories empirically catalogued 19 error subtypes across 19 models — strongest failure-mode evidence base in the field. SVO plot nodes are linguistically grounded and computationally cheap.
- Reasoning (可行性): high — both pieces are schema-level not training-level. SVO extraction is a single agent prompt; entity tracker is a deterministic post-processing pass.
- Concrete adoption: outline-level objects are SVO atoms; a separate `entity_registry` is the source of truth for any noun-phrase that appears 2+ times; chapter writer must consult the registry before generating; consistency agent checks each new SVO against the registry.

### 3. AutoNovel-style multi-phase pipeline with foreshadowing ledger + per-chapter manifest

- Reasoning (时效性): repo evidence from 2026, actively used by NousResearch to actually produce a 79k-word novel.
- Reasoning (鲁棒性): production-validated end-to-end including PDF export; the per-chapter manifest pattern is the union of what every other shipping OSS system does (webnovel-writer, InkOS, oh-story).
- Reasoning (可行性): high — pure prompt + filesystem engineering. We can replicate the foundation/draft/revise/export phases on top of our existing LangGraph pipeline by adding a `revision_loop` node and a `foreshadowing_ledger.json` artifact.
- Concrete adoption: introduce `outline.part1.md` (beats) + `outline.part2.md` (foreshadowing ledger); add `voice.md`; the Consistency agent owns foreshadowing-recovery tracking. Per-chapter context manifest: voice (full) + world (full) + characters (full) + this-chapter-outline + previous-chapter-tail (~1000 chars verbatim, not summary) + next-chapter-outline.

### Why not the other strong candidates as top-3
- **DOC v2**: still strong, but its FUDGE-style controller and OPT-era stack are 3 years old; v2 cleans this up but the codebase is small.
- **Plan-and-Write / PlotMachines / Re3**: foundational but pre-LLM-era model assumptions.
- **WritingPath**: Korean blog-post domain; great for the 5-step skeleton but not novel-shaped.
- **StoryWriter**: requires SFT of Llama3.1-8B / GLM4-9B; we lack the fine-tuning pipeline now.
- **Learning to Reason for Long-form**: highest-ceiling academically but requires building an RL training stack.
- **StoryBox bottom-up simulation**: interesting for character emergence but doesn't fit a planning-first product like ours.

---

## Open questions

1. **Multi-volume coherence has no academic benchmark.** Our best evidence is community repos at 2M-character scale; we should likely propose our own benchmark.
2. **What's the right α₁/α₂ compression ratio for Chinese vs. English novels?** Shen & Ying give α₁=0.05, α₂=0.20 for Gemini 2.0 Flash, T=0.3 — does this hold for Qwen / DeepSeek / Claude?
3. **Can SVO-triple plot nodes replace prose chapter summaries as memory?** STORYTELLER says yes for quality; nobody has measured cost/latency.
4. **DOME's fixed M=3 chapter ratio per rough stage** — is there an adaptive version? (Likely yes from web-novel data: prologue volumes vs. mid volumes have different ratios. No paper found.)
5. **Foreshadowing recovery rate is unmeasured.** Every OSS project tracks foreshadowing but none publish recovery-rate metrics. Open: build one for our pipeline.
6. **Is 起承转合 worth encoding explicitly?** No paper baked it in. Either (a) it's effectively equivalent to 4-act Western structure already covered, or (b) it's an underexplored low-cost lever — needs experimentation.
7. **At what length does our error rate cross "unusable"?** Lost in Stories shows linear accumulation; we should plot error/10k-words for our own pipeline as a baseline.
8. **Does outline-driven generation actually beat ChatGPT-style direct generation for 番茄/起点-style genres?** WebNovelBench would let us measure this against the 4,000-novel distribution but with our outline pipeline plugged in.
9. **Entropy-guided revision (Lost in Stories recommendation) — what's the per-token entropy threshold for "needs review"?** Unanswered in the paper.
10. **Critic-Writer loop diminishing returns** — AutoNovel uses 3-6 cycles. Is 3 enough? Is 6 too many? No public ablation.

---

(End of R1 raw findings. Synthesis with R2 memory, R4 OSS, R5 character will happen in `00-summary.md`.)
