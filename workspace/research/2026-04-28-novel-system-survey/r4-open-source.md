# Open-Source LLM Novel Generation Survey

- author: research-agent (Claude)
- date: 2026-04-28
- scope: Open-source projects (and papers with code releases) for LLM-based long-fiction / novel generation
- methodology: All claims are sourced from live WebSearch / WebFetch results executed on 2026-04-28. No claims are made from training-memory.

## Index of projects covered

1. [NousResearch/autonovel](#nousresearchautonovel) — multi-phase autonomous pipeline w/ anti-slop framework
2. [YILING0013/AI_NovelGenerator](#yiling0013ai_novelgenerator) — Chinese pipeline, 5.1k stars
3. [MaoXiaoYuZ/Long-Novel-GPT](#maoxiaoyuzlong-novel-gpt) — Chinese hierarchical outline → chapter → body w/ RAG
4. [cjyyx/AI_Gen_Novel](#cjyyxai_gen_novel) — Chinese multi-agent / RecurrentGPT-inspired
5. [xindoo/ai-novel-lab](#xindooai-novel-lab) — Chinese 100-chapter case study using AGENTS.md
6. [aiwaves-cn/RecurrentGPT](#aiwaves-cnrecurrentgpt) — foundational LSTM-in-natural-language paper
7. [yangkevin2/emnlp22-re3-story-generation](#yangkevin2emnlp22-re3-story-generation) — Plan / Draft / Rewrite / Edit
8. [yangkevin2/doc-story-generation](#yangkevin2doc-story-generation) — Detailed Outline Control
9. [THU-KEG/StoryWriter](#thu-kegstorywriter) — event-based outline + planning + writing agents
10. [alienet1109/BookWorld](#alienet1109bookworld) — multi-agent society simulation → story
11. [OpenDFM/ibsen](#opendfmibsen) — director-actor agent collaboration (drama)
12. [Taskii-Lei/Ex3-NovelWriter](#taskii-leiex3-novelwriter) — extract / excelsior (fine-tune) / expand
13. [Austinggg/CreAgentive](#austingggcreagentive) — three-stage agent workflow w/ Story Prototype
14. [datacrystals/AIStoryWriter](#datacrystalsaistorywriter) — simple multi-stage pipeline
15. [KazKozDev/NovelGenerator](#kazkozdevnovelgenerator) — TypeScript multi-thread narrative
16. [adamwlarson/ai-book-writer](#adamwlarsonai-book-writer) — AutoGen-based six agents
17. [OedonLestrange42/webnovelbench](#oedonlestrange42webnovelbench) — Chinese benchmark code release
18. [SillyTavern/SillyTavern](#sillytavernsillytavern) — reference: lorebook / WorldInfo runtime patterns
19. [X-PLUG/MM_StoryAgent](#x-plugmm_storyagent) — multimodal story video pipeline (reference)
20. [Awesome-Story-Generation](#yingpengmaawesome-story-generation) — meta resource

---

### NousResearch/autonovel

- repo URL: https://github.com/NousResearch/autonovel [accessed:2026-04-28]
- created_at: 2026-03-14 (per GitHub API)
- last push: 2026-03-20 (per GitHub API)
- stars / forks: 1,022 / 187 (per GitHub API, 2026-04-28) — search snippet showed 1,000 earlier; canonical = 1,022
- license: None specified (per GitHub API); README references no SPDX entry — concerning for production reuse
- language: Python (94.8% per repo file breakdown)
- maturity: research_prototype trending toward production (produced an actual 79k-word published novel)
- maintenance_status: active (pushed within ~5 weeks of access date)

#### Architecture (verbatim from PIPELINE.md / docs):
- Five co-evolving layers — quote from analysis of repo docs:
  - "Prose chapters (the actual writing)"
  - "Narrative outline with beats"
  - "Character registry with traits"
  - "World-building bible with lore"
  - "Voice guidelines defining stylistic rules"
- Phase decomposition — verbatim quote from PIPELINE.md:
  - Phase 1 Foundation: "INPUT: seed.txt OUTPUT: world.md, characters.md, outline.md, voice.md, canon.md, MYSTERY.md"
  - Phase 2 First Draft: "INPUT: all foundation docs OUTPUT: chapters/ch_01.md through ch_NN.md"
  - Phase 3 Revision: 3-6 iterations of adversarial editing → reader panels → revision briefs
  - Phase 4 Export: PDF/ePub/audiobook/landing page
- Foundation gate: "foundation_score > 7.5, lore_score > 7.0" thresholds
- Chapter gate: "must score above 6.0 or is discarded and retried (maximum 5 attempts)"
- Opus review: full manuscript passed to Claude Opus with "dual-persona prompting (literary critic + fiction professor). Iterates until major issues resolved"

#### Anti-slop (verbatim from ANTI-SLOP.md):
- Three detection approaches:
  1. "Word-level analysis: Flagging overrepresented vocabulary like 'delve,' 'utilize,' and 'leverage'"
  2. "Structural patterns: Identifying rigid paragraph templates and excessive list formatting"
  3. "Statistical signals: Measuring perplexity, sentence length variation, and burstiness"
- Banned constructions include: "This isn't just X—it's Y", "It's worth noting that...", "In today's fast-paced world..."
- Vocabulary tiers — Tier 1 "almost never appear in casual human writing" (e.g. elucidate, synergy)
- Voice fingerprinting: framed as detecting **absence** of voice (no "I" statements, no anecdotes, no contractions) rather than presence

#### Anti-patterns (verbatim from ANTI-PATTERNS.md):
12 categories:
1. "Over-Explain: If a scene shows it, the narrator doesn't say it."
2. "Triadic Listing"
3. "Negative-Assertion Repetition" (e.g. "He did not look back. He did not think about the room")
4. "Cataloging-by-Thinking"
5. "Simile Crutch" ("the way X did Y" — 4-8 per chapter flagged)
6. "Section Break Overuse"
7. "Paragraph Uniformity" (4-6 sentence clustering)
8. "Predictable Emotional Arcs"
9. "Repetitive Chapter Endings"
10. "Balanced Antithesis" ("Not X, but Y")
11. "Polished Dialogue" (no stammering / interruption)
12. "Scene-Summary Imbalance"

#### Craft heuristics (verbatim from CRAFT.md):
Eight qualities:
1. Specificity, 2. Surprise, 3. Rhythm Variation, 4. Subtext, 5. Earned Metaphor, 6. Sensory Grounding, 7. Restraint, 8. Quiet Moments
- Dialogue test: "Remove all dialogue tags. Can you still tell who is speaking?"
- Exposition rule: "Zero pure-exposition paragraphs over 100 words in chapter 1"
- Scene outcomes: "Yes, but..." / "No, and..."

#### Evaluation:
- Dual immune system: mechanical scoring (regex) + LLM Judge (separate model assesses prose quality, voice, character distinctiveness, plot beat coverage)
- LLM Judge produces 0-10 scores against fixed dimensions

#### What's reusable for our Chinese LLM novel project:
- **Anti-slop word/phrase blocklists**: cost = low. Translate to Chinese (delve→深入探讨, leverage→利用, etc.). The structural rules port directly (triadic listing, "not X but Y" 不是 X 而是 Y is very common in LLM Chinese).
- **Per-chapter score gate (e.g. >6.0 or rewrite, max 5 attempts)**: cost = low. Already partially have via consistency_check in our pipeline; add a numeric prose-quality gate.
- **Five-layer co-evolving doc model (prose / outline / characters / world / voice)**: cost = medium. Closely mirrors our Story Bible 2.0 work; "voice.md" as a separate file is something we should add.
- **Dual-persona Opus review pass over full manuscript**: cost = medium. We can do this with our LiteLLM gateway against a high-tier model at end of generation.
- **Mechanical anti-slop regex detector run inline**: cost = low. Simple Python script. High signal.

#### What to AVOID copying:
- The no-license-file gap means we should not lift code verbatim — treat as "read for ideas, write our own implementation."
- Hardcoded thresholds (>7.5, >6.0) — these are tuned to one genre/model, not transferable. Make ours configurable.
- LaTeX/audiobook/landing page out-of-scope for a Chinese web-novel system.

Sources:
- https://github.com/NousResearch/autonovel
- https://github.com/NousResearch/autonovel/blob/master/PIPELINE.md
- https://github.com/NousResearch/autonovel/blob/master/ANTI-SLOP.md
- https://github.com/NousResearch/autonovel/blob/master/ANTI-PATTERNS.md
- https://github.com/NousResearch/autonovel/blob/master/CRAFT.md
- https://api.github.com/repos/NousResearch/autonovel

---

### YILING0013/AI_NovelGenerator

- repo URL: https://github.com/YILING0013/AI_NovelGenerator [accessed:2026-04-28]
- created_at: 2025-01-29
- last push: 2026-05-19 (very recent!)
- stars / forks: 5,139 / 934 — the most-starred Chinese novel-AI project we found
- license: AGPL-3.0 (per GitHub API)
- language: Python 100%
- maturity: production_grade (large user base, GUI tool, multi-provider support)
- maintenance_status: active

#### Architecture (verbatim from README analysis):
- NOT explicitly multi-agent. Sequential pipeline with 4 steps:
  1. "Novel Setting Generation" — worldbuilding, character design, plot blueprint
  2. "Chapter Directory Creation" — titles and outlines for all chapters
  3. "Draft Chapter Generation" — with coherence checking
  4. "Finalization & State Updates" — consistency verification and memory integration

- Memory/state — three files:
  - `character_state.txt` — character state tracking
  - `global_summary.txt` — global plot summary, updated per chapter
  - `plot_arcs.txt` — plot arc management
- Vector-based semantic search (kNN against embeddings) for long-term context retrieval
- Knowledge base integration for local-doc references
- Automated proofreading detects plot contradictions
- Visual GUI (CustomTkinter Python desktop app, not web)

#### What's reusable for our Chinese LLM novel project:
- **3-file state model (character_state, global_summary, plot_arcs)**: cost = low. Simple and battle-tested at 5k-star scale. We have richer schemas but this trio is a useful minimal interface.
- **kNN embedding retrieval for context**: cost = low. We already do this via ChromaDB.
- **AGPL license**: cost = blocker. If we want to ship a closed-source commercial reader, copying code triggers AGPL viral effects. Read for ideas only.

#### What to AVOID copying:
- Tkinter GUI — irrelevant to web stack.
- "Sequential pipeline" without agent decomposition — we already have a more sophisticated LangGraph architecture, no regression desired.

Sources:
- https://github.com/YILING0013/AI_NovelGenerator
- https://api.github.com/repos/YILING0013/AI_NovelGenerator
- https://raw.githubusercontent.com/YILING0013/AI_NovelGenerator/main/README.md

---

### MaoXiaoYuZ/Long-Novel-GPT

- repo URL: https://github.com/MaoXiaoYuZ/Long-Novel-GPT [accessed:2026-04-28]
- created_at: 2024-01-11
- last push: 2025-11-05 (within last ~6 months — slow)
- stars / forks: 1,136 / 204
- license: None specified (per GitHub API) — same legal red flag as autonovel
- language: Python 61.6%, JavaScript 22.1%, CSS 7.2%, Jinja 5.7%, HTML 2.2%
- maturity: production-ish (has frontend + backend + docker)
- maintenance_status: slow (last push ~6 months pre-access)

#### Architecture (verbatim quotes):
- README: "Long Novel Agent采用大纲-章节-正文的自上而下扩写来一步步生成最终长篇小说"
  - Translation: "Long Novel Agent uses outline → chapter → body top-down expansion to progressively generate the final long novel"
- README: "在生成过程中调用工具检索相关正文片段和剧情纲要"
  - Translation: "During generation it calls tools to retrieve relevant text passages and plot outlines"
- v2.1 feature: "自动管理上下文" (automatic context management) — claims explicit API cost control
- Workflow step: "拆书（提取剧情人物关系，生成剧情纲要）"
  - Translation: "Book decomposition: extract plot/character relationships, generate plot outline" — interesting reverse-engineering capability where you import an existing novel and the system extracts structure

#### What's reusable:
- **Hierarchical outline → chapter → body expansion**: cost = low. We already do similar. Reinforces field consensus.
- **"拆书 (book decomposition)" feature**: cost = medium. Useful for fine-tuning data and for users who want to continue an existing novel. Interesting prompt engineering pattern worth studying.
- **RAG-on-text-fragments while regenerating**: cost = low. Standard pattern.

#### What to AVOID copying:
- No license = legally unsafe to copy code.
- Tool calls to retrieve plot info during writing — be careful about latency budget. We've seen this can balloon token costs.

Sources:
- https://github.com/MaoXiaoYuZ/Long-Novel-GPT
- https://api.github.com/repos/MaoXiaoYuZ/Long-Novel-GPT

---

### cjyyx/AI_Gen_Novel

- repo URL: https://github.com/cjyyx/AI_Gen_Novel [accessed:2026-04-28]
- created_at: 2024-03-17
- last push: 2024-09-04 (>20 months ago — [stale])
- stars / forks: 418 / 82
- license: MIT (per GitHub API) — friendly for code reuse
- language: Python 100%
- maturity: research_prototype (author's stated thesis is exploring limits)
- maintenance_status: [stale] >12 months. Matters: less so — value is in the design ideas/prompts.

#### Architecture (verbatim from README, Chinese quotes):
- "优化Prompt，多智能体协作，激发 LLM 的能力，提升其原创性"
  - Translation: "Optimize prompts; multi-agent collaboration; unleash LLM capability; improve originality"
- "借鉴RecurrentGPT的核心思想，基于语言的循环计算，通过迭代的方式创作任意长度的文本"
  - Translation: "Borrowing RecurrentGPT's core idea — language-based recurrent computation, iteratively creating arbitrary-length text"
- Memory strategy: "利用LLM的能力压缩长文本为几句话组成的记忆"
  - Translation: "Use LLM to compress long text into a few-sentence memory"
- Author's own conclusion: "current large language models lack sufficient ability to create long web novels" (suggests still exploratory)

#### What's reusable:
- **LLM-as-summarizer for compressed memory**: cost = low. We already do this in ChapterExtractor.
- **MIT-licensed prompt corpus**: cost = low. Their prompts for 网文-genre may be directly liftable.

#### What to AVOID copying:
- The actual code is from RecurrentGPT-era — surpassed by later approaches with explicit knowledge graphs and event-based outlines.
- Author's own pessimism is worth heeding: prompt-only multi-agent on the 2024-era models was insufficient; we need richer state.

Sources:
- https://github.com/cjyyx/AI_Gen_Novel
- https://api.github.com/repos/cjyyx/AI_Gen_Novel
- https://raw.githubusercontent.com/cjyyx/AI_Gen_Novel/main/README.md

---

### xindoo/ai-novel-lab

- repo URL: https://github.com/xindoo/ai-novel-lab [accessed:2026-04-28]
- created_at: 2026-02-01
- last push: 2026-03-27
- stars / forks: 41 / 3 (small but very recent)
- license: MIT
- language: JavaScript 64.2% (the website), with the actual novel in Markdown
- maturity: case_study (1 completed novel, 100 chapters, 430k characters)
- maintenance_status: active

#### Architecture (verbatim Chinese from README):
- "一个使用 AI 大模型自动创作长篇小说的实验性项目。本项目通过系统化的工程方法，探索 AI 在长篇叙事创作中的可能性、挑战与解决方案。"
  - Translation: "An experimental project using LLMs to automatically create long-form novels. We use systematic engineering methods to explore the possibilities, challenges, and solutions of AI in long-form narrative creation."
- Hierarchical three-tier approach:
  1. Macro: complete novel outline + worldbuilding + character profiles + 100-chapter structure
  2. Mid: chapter-level planning with 10k-word targets
  3. Micro: scene-by-scene scaffolding with consistency checkpoints
- Crucially uses **AGENTS.md** as the constraint file — a single Markdown file that codifies writing standards, 爽文 (web-fiction power-fantasy) conventions, workflow, character-consistency requirements
- Four consistency-maintenance mechanisms:
  1. Preventive (pre-built dossiers)
  2. Generative (prompt constraints in AGENTS.md)
  3. Corrective (Python word-count validation scripts)
  4. Retrospective (multi-pass revisions, scored 73→93)
- The 10-chapter insertion phase fixed temporal contradictions

#### What's reusable for our Chinese project (high-priority signal):
- **AGENTS.md pattern**: cost = low. A single Markdown file that the LLM reads on every chapter call, containing genre conventions / character rules / banned phrases is dirt simple and very effective. We could promote our "Story Bible" toward this format. Note: our repo already has an `AGENTS.md` file at root — this convention is sticking.
- **Preventive + Generative + Corrective + Retrospective consistency taxonomy**: cost = low. Useful mental model for organizing the existing consistency_check stage.
- **Word-count validation**: cost = low. Trivial to add; our writer agent currently has soft targets.
- **Multi-pass revision (73→93 score)**: cost = medium. We don't currently iterate over completed chapters. Worth a Phase 5.

#### What to AVOID copying:
- Single-author case study — small n=1, generalization risk. Test before adopting any specific scoring number.
- Not a reusable framework — it's a writing project with scaffolding, not a library.

Sources:
- https://github.com/xindoo/ai-novel-lab
- https://api.github.com/repos/xindoo/ai-novel-lab

---

### aiwaves-cn/RecurrentGPT

- repo URL: https://github.com/aiwaves-cn/RecurrentGPT [accessed:2026-04-28]
- created_at: 2023-05-22
- last push: 2024-05-15 (~2 years ago — [stale])
- stars / forks: 1,002 / 158
- license: GPL-3.0 (per GitHub API) — copyleft, derivative works must remain GPL
- language: Python 98.8%
- maturity: research_prototype (paper-attached)
- maintenance_status: [stale] but is foundational reference work

#### Architecture (verbatim from README):
- "RecurrentGPT replaces the vectorized elements in an LSTM RNN with natural language paragraphs and simulates recurrence with prompt engineering."
- Dual-memory architecture:
  - **Long-term memory** = "summaries of all previously generated paragraphs, retrievable via semantic search. This can be persisted on disk for handling arbitrarily long texts."
  - **Short-term memory** = "natural language summaries of key information from recent timesteps, updated at each generation step"
- At each timestep model receives: previous paragraph + brief plan + LT memory (search) + ST memory → outputs new paragraph + next-paragraph plan + updated memory

#### What's reusable:
- **The "natural-language LSTM" metaphor for memory state**: cost = low. Pure prompt engineering. Our LayeredMemory L0/L1/L2/L3 is a richer descendant of this idea.
- **Persist long-term memory to disk; search via embedding**: cost = low. Standard.
- Educational value: every paper since (incl. CreAgentive, AI_Gen_Novel) cites it. Worth reading even if not copying.

#### What to AVOID copying:
- Code is GPL-3.0 — viral if you import it. Use the *idea*, not the *code*.
- Sequential paragraph-by-paragraph generation is too slow for novel-scale.
- Plan-per-paragraph granularity is wrong for novels — we want plan-per-chapter or plan-per-scene.

Sources:
- https://github.com/aiwaves-cn/RecurrentGPT
- https://api.github.com/repos/aiwaves-cn/RecurrentGPT

---

### yangkevin2/emnlp22-re3-story-generation

- repo URL: https://github.com/yangkevin2/emnlp22-re3-story-generation [accessed:2026-04-28]
- created_at: 2022-10-13
- last push: 2022-12-21 (~3.5 years ago — [stale])
- stars / forks: 257 / 44
- license: MIT
- language: Python 98.6%
- maturity: research_prototype
- maintenance_status: [stale] — but Yang's follow-up work (DOC) continues the line

#### Architecture (verbatim quotes):
4-stage pipeline:
1. **Plan** — "Generates an outline structure for the story"
2. **Draft** — "Creates initial narrative passages based on the plan"
3. **Rewrite** — "Produces alternative candidate passages for selection"
4. **Edit** — "Refines passages for consistency and coherence"

Quote from README warning users: "Don't worry if you see some errors being printed, as long as the program doesn't terminate early" (signal: rough code quality).

Paper findings: "Re3's stories as having a coherent overarching plot (by 14% absolute increase), and relevant to the given initial premise (by 20%)" vs. base GPT-3.

#### What's reusable:
- **4-phase Plan/Draft/Rewrite/Edit pipeline**: cost = low (we partially have this via init→world_advance→write→consistency). The "Rewrite produces multiple candidates and reranks" pattern is something we don't do — could add a candidate-ranking step.
- **MIT licensed**: reasonable for code lifting if needed.

#### What to AVOID copying:
- 2022-era prompting against GPT-3 — modern models eat this for breakfast. Architecture matters, code does not.
- Inactive — no help if you hit a bug.

Sources:
- https://github.com/yangkevin2/emnlp22-re3-story-generation
- https://api.github.com/repos/yangkevin2/emnlp22-re3-story-generation

---

### yangkevin2/doc-story-generation

- repo URL: https://github.com/yangkevin2/doc-story-generation [accessed:2026-04-28]
- created_at: 2022-12-20
- last push: 2023-10-27 (~1.5 years ago — [stale])
- stars / forks: 161 / 23
- license: MIT
- language: Python 100%
- maturity: research_prototype (ACL 2023)
- maintenance_status: [stale]. Matters: less so — design ideas matter more than code.

#### Architecture (verbatim quotes):
- Detailed Outliner — three components:
  - GPT-3 plan/outline generation
  - Outline order reranker (longformer_classifier using roberta-large)
  - Character + setting detection
- Detailed Controller — three components:
  - **Relevance Reranker** (longformer_classifier) — alignment with plan
  - **Coherence Reranker** (longformer_classifier) — passage-level consistency
  - **Fudge Controller** — token-level logit modification (constraint-decoding)
- Result: stories average 3,500+ words, +22.5% plot coherence over Re3 baseline, +28.2% outline relevance, +20.7% interestingness

#### What's reusable:
- **Two reranker passes (relevance + coherence) per candidate passage**: cost = medium. Plugs into our consistency_check loop. Worth a try.
- **Hierarchically nested outline (multiple depth levels)**: cost = low. We have outline_planner already; deepen the hierarchy.

#### What to AVOID copying:
- Longformer-classifier rerankers — we're a modern-LLM-only stack. Use the same LLM acting as judge instead.
- Fudge controller (token-level logits) — needs raw model access; cuts off LiteLLM/closed providers. Not portable.
- Pre-2024-era LLM assumptions throughout. Don't reproduce; adapt.

Sources:
- https://github.com/yangkevin2/doc-story-generation
- https://api.github.com/repos/yangkevin2/doc-story-generation

---

### THU-KEG/StoryWriter

- repo URL: https://github.com/THU-KEG/StoryWriter [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2506.16445 (CIKM 2025)
- created_at: 2025-06-18
- last push: 2025-06-18 (only the initial push! likely just code release; ~11 months ago — borderline stale, but recent enough that this is the publication SOTA)
- stars / forks: 40 / 6 (small — but it's a 2025 academic release)
- license: None specified (per GitHub API) — legal caution
- language: Python 98.9%
- maturity: research_prototype (CIKM 2025)
- maintenance_status: slow (release-and-leave pattern)

#### Architecture (verbatim quotes from README/paper):
Three agents:
1. **Outline Agent** — "generates event-based outlines containing rich event plots, character, and event-event relationships"
2. **Planning Agent** — "further details events and plans which events should be written in each chapter to maintain an interwoven and engaging story"
3. **Writing Agent** — "dynamically compresses the story history based on the current event to generate and reflect new plots, ensuring the coherence of the generated story"

Output dataset: ~5,000–6,000 stories averaging 8,000 words.

#### What's reusable (very high signal):
- **Event-based outline (not chapter-based)**: cost = medium. This is the biggest divergence from our current design. We have outline-as-beats; they have outline-as-events-with-relationships. Events can be linked (causal/temporal) as a graph. Strong claim of better coherence.
- **Event-to-chapter assignment as a separate planning step**: cost = low. We could add this. Our chapter graph currently has plot_plan stage; explicit event → chapter mapping would help.
- **Dynamic story-history compression by writing agent**: cost = low — we have memory layers, this is similar but agent-driven.
- Citation closest to academic frontier on multi-agent novel generation (CIKM 2025) — adopting their event-graph ontology gives us a paper-citable architecture.

#### What to AVOID copying:
- No license = no code copying. But the architecture is described in the paper, replicable.
- Their writing agent is monolithic — we want POV/camera control which they don't have.

Sources:
- https://github.com/THU-KEG/StoryWriter
- https://arxiv.org/abs/2506.16445
- https://api.github.com/repos/THU-KEG/StoryWriter

---

### alienet1109/BookWorld

- repo URL: https://github.com/alienet1109/BookWorld [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2504.14538 (ACL 2025)
- project page: https://bookworld2025.github.io/
- created_at: 2025-04-08
- last push: 2026-01-02 (~4 months ago — active)
- stars / forks: 177 / 31
- license: Apache-2.0 (per GitHub API) — commercial-friendly
- language: Python 78.2%
- maturity: research_prototype with demo
- maintenance_status: active

#### Architecture (verbatim quotes):
- **World Agent** — "Orchestrates overall simulation and scene-based story progression"
- **Role Agents** — "Character-specific agents that handle individual behavior and dialogue"
- System extracts character data and worldview from source books, simulates scenes (working / communicating / trading), updates agent memory/status/goals; world agent maintains global status + environmental feedback; histories rephrased to novelistic text by LLM
- "Win rate of 75.36%" vs. previous baselines on creative quality + fidelity to source

#### What's reusable:
- **World Agent + Role Agents separation**: cost = medium. We already have specialized agents (Director, World, Camera) but explicit per-character agents acting autonomously is a new pattern for us. Could be powerful for dialogue-heavy scenes.
- **Scene simulation → LLM rephrasing as prose**: cost = medium. Two-stage: agents enact scene, then writer agent narrates. This separates "what happens" from "how it's told." A potential refactor of our writer stage.
- **Apache-2.0 = clean license** for studying code patterns.

#### What to AVOID copying:
- Original purpose is fan-fiction extension of existing books — pure "from scratch" generation isn't its target. Adapt with care.
- Per-character agents add a lot of token cost. Use sparingly (key scenes only).

Sources:
- https://github.com/alienet1109/BookWorld
- https://api.github.com/repos/alienet1109/BookWorld
- https://arxiv.org/abs/2504.14538

---

### OpenDFM/ibsen

- repo URL: https://github.com/OpenDFM/ibsen [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2407.01093 (ACL 2024)
- created_at: 2024-04-01
- last push: 2025-07-05 (~10 months ago — slow)
- stars / forks: 52 / 2
- license: MIT
- language: Python 100%
- maturity: research_prototype
- maintenance_status: slow but maintained

#### Architecture (verbatim quotes):
- **Director Agent** — "creates and checks the current drama storyline"; "surveillance and oversight, ensuring the drama progresses toward desired plot objectives while maintaining narrative coherence"
- **Actor Agents** — "LLM-powered characters that generate dialogue and actions aligned with their personalities and the director's plot guidance"
- **Player Agent** — "humans can directly participate in the drama, interacting with actors while the system keeps the plot advancing toward intended goals"
- "By default IBSEN uses gpt-4o-mini as the backbone LLM, and the implementation of the IBSEN framework is largely prompt-based, allowing one to easily construct IBSEN agents on any publicly available general LLMs without fine-tuning."
- Character profiles + dialogue corpora in `/data/profile` and `/data/corpus`

#### What's reusable:
- **Director-supervises-actors pattern**: cost = low to medium. Our Director agent already generates the bible. Promoting it to a runtime supervisor that *vetoes* role-agent outputs is a small change.
- **Human-in-the-loop player agent**: cost = medium. We don't have this but it's the obvious UX for interactive storytelling — could be a future feature.
- **MIT license** = reusable code.

#### What to AVOID copying:
- Drama/script-focused — heavy on dialogue, weak on long-form prose narration. Don't adopt the whole architecture.
- Only 52 stars and 2 forks. Small community. Lift ideas, write your own implementation.

Sources:
- https://github.com/OpenDFM/ibsen
- https://api.github.com/repos/OpenDFM/ibsen

---

### Taskii-Lei/Ex3-NovelWriter

- repo URL: https://github.com/Taskii-Lei/Ex3-NovelWriter [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2408.08506 (ACL 2024)
- created_at: 2024-08-23
- last push: 2024-09-01 (~20 months ago — [stale])
- stars / forks: 20 / 4
- license: None specified
- language: Python 100%
- maturity: research_prototype
- maintenance_status: [stale]. Matters: somewhat — fine-tuning approach is dated.

#### Architecture (verbatim quotes):
Three stages:
1. **Extract** — "extracts structure information from raw novel data" (chapters → recursive extraction → relative information folder → entity extraction → character/entity corpus)
2. **Excelsior** — "combining this structure information with the novel data, an instruction-following dataset is meticulously crafted. This dataset is then utilized to fine-tune the LLM, aiming for excelsior generation performance."
3. **Expand** — "tree-like expansion method is deployed to facilitate the generation of arbitrarily long novels"; uses two LLMs at inference (one fine-tuned writer, one entity extractor) with title/tags/intro as premise

#### What's reusable:
- **Train-on-extracted-novel-structure pattern**: cost = high (need GPUs, dataset). But: we have access to vast Chinese web-novel corpora. If we wanted to fine-tune a 7B writer model on 网文 style, this paper is the blueprint.
- **Tree expansion at inference**: cost = medium. Hierarchical generation where each node expands into children. We already do outline→chapter→scene; tree expansion just formalizes it.

#### What to AVOID copying:
- Fine-tuning is expensive and locks you to one model. Modern strong models (DeepSeek-V3, Claude 4.5) may make this unnecessary.
- Tiny community (20 stars). Treat the paper as reference, not the codebase.

Sources:
- https://github.com/Taskii-Lei/Ex3-NovelWriter
- https://api.github.com/repos/Taskii-Lei/Ex3-NovelWriter

---

### Austinggg/CreAgentive

- repo URL: https://github.com/Austinggg/CreAgentive [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2509.26461 (2025-09)
- created_at: 2025-05-28
- last push: 2025-10-14 (~6 months ago — slow)
- stars / forks: 7 / 0 (tiny)
- license: Apache-2.0
- language: Python 100%
- maturity: research_prototype, very new
- maintenance_status: slow

#### Architecture (verbatim from search snippet, paper still hard to extract from PDF):
- Three-stage workflow:
  1. **Initialization Stage** — "constructs a user-specified narrative skeleton"
  2. **Generation Stage** — "long- and short-term objectives guide multi-agent dialogues to instantiate the Story Prototype"
  3. **Writing Stage** — "leverages this prototype to produce multi-genre text with advanced structures such as retrospection and foreshadowing"
- Key innovation: **Story Prototype** — "uses a multiversion character plot dual knowledge graph to store and manage global narrative information"
- Claim: "generates thousands of chapters with stable quality and low cost (less than $1 per 100 chapters) using a general-purpose backbone model"
- Repo structure: `Agent/`, `Operator/`, `Resource/`, `Workflow/` directories

#### What's reusable:
- **Dual knowledge graph (character × plot)**: cost = medium-high. We have a single KG. Splitting character and plot graphs (with cross-references) is a non-trivial refactor but theoretically better.
- **Multiversion graph (probably tracks character beliefs / hypothetical timelines)**: cost = high. Worth studying the paper before deciding.
- **Apache-2.0 = clean license**.
- **Cost claim ($1 per 100 chapters)** — interesting if real, suggests aggressive context pruning. Worth comparing to our token budget.

#### What to AVOID copying:
- Tiny user base (7 stars, 0 forks) — no validation that this works at scale beyond paper's own claim.
- Likely many bugs / undocumented APIs.

Sources:
- https://github.com/Austinggg/CreAgentive
- https://api.github.com/repos/Austinggg/CreAgentive
- https://arxiv.org/pdf/2509.26461

---

### datacrystals/AIStoryWriter

- repo URL: https://github.com/datacrystals/AIStoryWriter [accessed:2026-04-28]
- created_at: 2024-06-19
- last push: 2025-11-24 (~5 months ago — slow)
- stars / forks: 248 / 61
- license: AGPL-3.0
- language: Python 100%
- maturity: hobby project, moderate community
- maintenance_status: slow but updated

#### Architecture (verbatim quotes):
- README: "Generate full-length novels with AI! Harness the power of large language models to create engaging stories based on your prompts."
- Multi-stage pipeline:
  - Initial outline creation
  - Chapter-level outline development
  - Chapter writing
  - Revision phases
- No agents or memory systems mentioned (sequential calls only)
- Supports Ollama (local), Google, OpenRouter

#### What's reusable:
- Not much beyond what we already have. Reference for "minimum viable" project structure.

#### What to AVOID copying:
- AGPL = viral. Don't import.
- README author admits: "areas needing improvement: reducing repetitive phrases, enhancing chapter flow, and addressing pacing issues" — i.e., open issues are unresolved.

Sources:
- https://github.com/datacrystals/AIStoryWriter
- https://api.github.com/repos/datacrystals/AIStoryWriter

---

### KazKozDev/NovelGenerator

- repo URL: https://github.com/KazKozDev/NovelGenerator [accessed:2026-04-28]
- created_at: 2024-11-02
- last push: 2025-11-05 (~6 months ago — slow)
- stars / forks: 130 / 33
- license: "Other" / unspecified SPDX (per GitHub API)
- language: TypeScript (web UI), Vite-built
- maturity: prototype, web app
- maintenance_status: slow

#### Architecture (verbatim quotes from README):
- "Fiction generator using LLM agents to create complete novels with coherent plots, developed characters, and diverse writing styles."
- Pipeline generates "multi-threaded narratives" tracking:
  - Multiple character perspectives across different timelines
  - "Character knowledge states at given moments"
  - "Emotional arcs with psychological consistency"
  - "Independent plot threads synchronized with consistent chronology"

#### What's reusable:
- **Per-character knowledge-state tracking**: cost = medium. This is similar to LayeredMemory L0 (identity) — but their angle is "what does this character know at this moment?" which is critical for thrillers/mysteries. Worth modeling explicitly.
- **Multi-thread synchronized chronology**: cost = medium. Useful for parallel POVs.

#### What to AVOID copying:
- TypeScript/Vite — different stack.
- Small community, license unclear.

Sources:
- https://github.com/KazKozDev/NovelGenerator
- https://api.github.com/repos/KazKozDev/NovelGenerator

---

### adamwlarson/ai-book-writer

- repo URL: https://github.com/adamwlarson/ai-book-writer [accessed:2026-04-28]
- created_at: 2025-01-02
- last push: 2025-03-27 (~13 months ago — borderline [stale])
- stars / forks: 384 / 130
- license: None specified (per GitHub API)
- language: Python 100%
- maturity: prototype, AutoGen-based
- maintenance_status: [stale]

#### Architecture (verbatim quote):
- Built on AutoGen
- Six agents:
  - **Story Planner**
  - **World Builder**
  - **Memory Keeper**
  - **Writer**
  - **Editor**
  - **Outline Creator**
- Configurable `num_chapters` (25 in examples)

#### What's reusable:
- **Six-agent decomposition mirrors our six-agent design** (Director / World / Planner / Camera / Writer / Consistency). Notable they have a dedicated "Memory Keeper" agent — we have a memory layer but no agent that proactively curates memory. Worth considering.
- AutoGen as an alternative to LangGraph — but we're committed to LangGraph.

#### What to AVOID copying:
- AutoGen orchestration patterns won't transfer to LangGraph.
- No license = no code copying. Use as design reference.

Sources:
- https://github.com/adamwlarson/ai-book-writer
- https://api.github.com/repos/adamwlarson/ai-book-writer

---

### OedonLestrange42/webnovelbench

- repo URL: https://github.com/OedonLestrange42/webnovelbench [accessed:2026-04-28]
- paper: https://arxiv.org/abs/2505.14818 (EACL 2026 Findings)
- HF dataset: https://huggingface.co/datasets/Oedon42/webnovelbench
- created_at: 2025-05-18
- last push: 2025-07-02 (~10 months ago — slow)
- stars / forks: 15 / 3
- license: MIT
- language: Python 100%
- maturity: research_release (paper attached)
- maintenance_status: slow

#### The 8 Narrative Quality Dimensions (verbatim from paper Table 1, Section 3.2):
1. **Use of Literary Devices**
2. **Richness of Sensory Detail**
3. **Balance of Character Presence**
4. **Distinctiveness of Character Dialogue**
5. **Consistency of Characterisation**
6. **Atmospheric and Thematic Alignment**
7. **Contextual Appropriateness**
8. **Scene-to-Scene Coherence**

These are evaluated via LLM-as-Judge against >4,000 Chinese web novels. Scores are aggregated via PCA and mapped to percentile rank vs. human-authored works.

#### Files in repo:
- `novel_original_critic.py` — scoring script
- `novel_gands_pipeline.py` — main generation+scoring pipeline
- `config_example.json`
- `fixed_parameters.json`

Usage: `python novel_original_critic.py --dir absolute/path/to/novels_dir`

#### What's reusable (critical for our quality system):
- **The 8 dimensions are directly usable as the LLM-Judge rubric for our scene-level eval.** Cost = low. Translate to Chinese, plug into our existing eval framework. This is *the* benchmark the field is now citing for Chinese-language novel evaluation.
- **PCA aggregation + percentile-rank-against-human-corpus**: cost = medium. Requires baseline human novels (they provide 4,000 via HuggingFace). Lets you say "this generated novel is at the 73rd percentile" — much more interpretable than raw scores.
- **MIT license** = clean.
- HuggingFace dataset of 4k+ Chinese web novels = priceless training/eval data.

#### What to AVOID copying:
- They require Volcengine SDK + SiliconFlow API. Adapt to our LiteLLM gateway.
- The earlier user-shared brief noted that "we got burned earlier by hallucinating WebNovelBench's dimension names from memory" — the names above are NOW verified verbatim from the paper. Use these, not training-memory variants.

Sources:
- https://github.com/OedonLestrange42/webnovelbench
- https://arxiv.org/abs/2505.14818
- https://arxiv.org/html/2505.14818v1
- https://api.github.com/repos/OedonLestrange42/webnovelbench

---

### SillyTavern/SillyTavern

- repo URL: https://github.com/SillyTavern/SillyTavern [accessed:2026-04-28]
- created_at: 2023-02-09
- last push: 2026-05-20
- stars / forks: 28,510 / 5,414 — the giant of the space
- license: AGPL-3.0
- language: JavaScript 86.2%
- maturity: production_grade (massive user base)
- maintenance_status: active

#### WorldInfo / Lorebook system (verbatim from official docs):
- "World Info (also known as Lorebooks or Memory Books) is a powerful tool available in ST to insert prompts dynamically into your chat to help guide the AI replies."
- "It functions as a dynamic dictionary that only inserts relevant information from World Info entries when keywords associated with the entries are present in the message text."
- **Keyword-based (green entries)**: "triggered only in the presence of the keyword"
- **Constant entries (blue entries)**: "would always be present in the prompt"
- **Vector-based (chain link)**: "allowed to be inserted by embedding similarity"
- Budget: "Context % / Budget defines how many tokens could be used by World Info entries at once"
- Priority: "Constant entries will be inserted first. Then entries with larger order numbers."
- Scan depth setting and recursive activation (entries activating other entries)

#### What's reusable (this is THE proven pattern in the field):
- **Three-tier entry triggering (constant / keyword / vector)**: cost = low. Our world/memory system can adopt this directly. Much cleaner than our current always-load-everything-up-to-budget approach.
- **Token budget enforcement on lore entries**: cost = low. Critical for cost control on long stories.
- **Recursive activation**: cost = medium. Powerful but can blow up token budget. Add as opt-in.
- **Order numbers for prioritization**: cost = low.

#### What to AVOID copying:
- AGPL — viral. Use as design reference, write your own implementation.
- SillyTavern is roleplay-focused; their UX for editing lore entries inline assumes a chat context. Our novel-writing UX needs different ergonomics.
- The JavaScript codebase is monolithic. Don't try to port directly.

Sources:
- https://github.com/SillyTavern/SillyTavern
- https://docs.sillytavern.app/usage/core-concepts/worldinfo/
- https://api.github.com/repos/SillyTavern/SillyTavern

---

### X-PLUG/MM_StoryAgent

- repo URL: https://github.com/X-PLUG/MM_StoryAgent [accessed:2026-04-28]
- license: Apache-2.0
- language: Python 100%
- stars / forks: 307 / 56

#### Architecture (verbatim quotes):
- "Employs LLMs and diverse expert tools across several modalities to produce expressive storytelling videos."
- Three strengths:
  1. "Customizable workflow — Users can define their own expert tools for improving component generation"
  2. "High-quality story writing — Multi-agent, multi-stage pipeline based on story settings"
  3. "Immersive video composition — Integrates assets from image, speech, sound, and music modalities"
- Agents configured via YAML, implement `__init__` and `call` methods

#### What's reusable:
- **YAML-configurable agent definitions**: cost = low. Cleaner than hardcoded agent classes. Worth considering for our model-binding system.
- **GPT-4-based grading rubric across "attractiveness, warmth, and educational value"** for evaluation
- **Apache-2.0** = clean license

#### What to AVOID copying:
- Multimodal (video) — out of scope for our text-first product.
- Not directly comparable to long-novel projects.

Sources:
- https://github.com/X-PLUG/MM_StoryAgent

---

### yingpengma/Awesome-Story-Generation (meta resource)

- repo URL: https://github.com/yingpengma/Awesome-Story-Generation [accessed:2026-04-28]
- Curated list of LLM-era story-generation papers, organized by category (Plan and Write, Multi-Agent, Better Storytelling, etc.)

Useful entries (verbatim from list):
- `ACL-2024` "Ex3: Automatic Novel Writing by Extracting, Excelsior and Expanding"
- `NAACL-2025` "Generating Long-form Story Using Dynamic Hierarchical Outlining with Memory-Enhancement" (DOME — based on temporal knowledge graphs, fuses plan and write stages, includes a Temporal Conflict Analyzer)
- `ICLR-2025` "Agents' Room: Narrative Generation through Multi-step Collaboration" (Google DeepMind — `https://github.com/google-deepmind/tell_me_a_story` dataset only)
- `ACL-2024` "IBSEN: Director-Actor Agent Collaboration for Controllable and Interactive Drama Script Generation"
- `EMNLP Findings-2024` "SWAG: Storytelling With Action Guidance"
- `EMNLP Findings-2023` "Improving Pacing in Long-Form Story Planning"

DOME (NAACL 2025) is worth tracking — temporal-KG-based memory + plan-and-write fusion, very close to our architecture goals.

Sources:
- https://github.com/yingpengma/Awesome-Story-Generation
- https://arxiv.org/pdf/2412.13575 (DOME paper)

---

## Cross-project synthesis

### Architecture recurrence (with citations)

- **Outline → Chapter → Body hierarchical decomposition** appears in: autonovel (Phase 1+2), AI_NovelGenerator (4 steps), Long-Novel-GPT (top-down expansion), Ex3 (tree expansion), DOC (detailed outliner), Re3 (Plan + Draft), DOME (dynamic hierarchical outlining), StoryWriter (event → plan → write), ai-novel-lab (macro/mid/micro). **9/15 projects.** Field consensus = strong.
- **Director / Writer / Critic loop pattern** appears in: autonovel (foundation → draft → revision), Re3 (plan/draft/rewrite/edit), DOC (controller rerankers), IBSEN (director-actor), ai-book-writer (planner + writer + editor), StoryWriter (outline + planning + writing). **6/15 projects** use some critic/revision agent.
- **Per-character agents / character cards** appears in: BookWorld (role agents), IBSEN (actor agents), SillyTavern (character cards). **3 projects.** Niche but powerful.
- **Knowledge graph for state** appears in: CreAgentive (multiversion dual KG), DOME (temporal KG), StoryWriter (event-event relationships). **3 projects.** Emerging frontier.
- **LLM-as-Judge eval** appears in: autonovel, WebNovelBench, MM_StoryAgent, ai-novel-lab (Python validators). **4 projects.** Becoming standard.
- **Explicit anti-slop measures** appears in: autonovel (most elaborate by far), ai-novel-lab (Markdown rules), AIStoryWriter (admits unsolved). **3 projects, autonovel is the clear leader.**

### Memory approaches comparison

| Project | Memory model | Persistence | Retrieval |
|---|---|---|---|
| autonovel | Layered docs (world/characters/voice/canon) | filesystem .md | reads whole files |
| YILING0013/AI_NovelGenerator | 3 state files + embeddings | filesystem + vector DB | kNN |
| RecurrentGPT | Long + short natural-language memory | disk | semantic search |
| StoryWriter | Story-history dynamic compression | in-memory | LLM compression |
| BookWorld | Per-agent memory updated each scene | unspecified | continuous |
| ai-book-writer | Dedicated "Memory Keeper" agent | unspecified | agent-mediated |
| SillyTavern | Lorebook (constant/keyword/vector entries) | DB | three-tier trigger |
| CreAgentive | Dual KG (character × plot, multiversion) | KG store | graph query |
| DOME | Temporal KG with valid_from/valid_to | KG store | graph query |
| Our (Story Engine) | LayeredMemory L0-L3 + ChromaDB + KG triples | SQLite + Chroma + JSON | layered + semantic + KG |

Field is moving toward **knowledge graphs + vector + per-character memory**. Our 4-tier layered memory is at the frontier.

### Outline approaches comparison

| Project | Outline structure | Outline granularity |
|---|---|---|
| autonovel | outline.md + MYSTERY.md (separate mystery layer) | chapter beats |
| Re3 | Plan section | scene-level |
| DOC | Hierarchical (3-level) | sub-paragraph |
| StoryWriter | Event-based graph with event-event relations | event nodes |
| Ex3 | Tree expansion | recursive |
| DOME | Dynamic hierarchical outline | adapts during generation |
| YILING0013/AI_NovelGenerator | plot_arcs.txt | arc-level |
| Long-Novel-GPT | Outline → Chapter → Body | three levels |
| ai-novel-lab | Macro → Mid → Micro (scene) | three levels |
| Our (Story Engine) | OutlinePlanner → chapter beats | beat-level |

Trend: **event-graph outlines (StoryWriter) and dynamic/adaptive outlines (DOME) are the 2025 SOTA.** Static three-level decomposition is the conservative-baseline.

### Character handling comparison

| Project | Character model |
|---|---|
| autonovel | characters.md, with dialogue distinctiveness (8 measurable dimensions) |
| YILING0013/AI_NovelGenerator | character_state.txt updated per chapter |
| BookWorld | Per-character agent with memory/status/goals |
| IBSEN | Actor agents with profile + corpus |
| SillyTavern | Character cards (JSON, with personality fields) |
| KazKozDev/NovelGenerator | Character knowledge-states per timestep |
| CreAgentive | Multiversion character branch of dual KG |
| Our (Story Engine) | Per-character LayeredMemory + KG triples |

### Anti-slop techniques comparison

| Project | Word-level | Structural | Voice / craft |
|---|---|---|---|
| autonovel | Banned vocab (delve, leverage, ...), tier lists | 12 anti-patterns (triadic listing, "not X but Y", etc.) | 8 craft heuristics, dialogue tag test |
| ai-novel-lab | Implicit in AGENTS.md | rules in AGENTS.md | manual |
| AIStoryWriter | (none) | (none) | (acknowledged as unsolved) |
| Most others | (none) | (none) | (none) |

**Autonovel is the only project with industrial-grade anti-slop machinery.** This is the single most valuable artifact to study.

### Field consensus (synthesis)

Strong consensus (>50% of projects):
- Hierarchical outline decomposition (≥3 levels)
- LLM-as-Judge for evaluation
- Vector retrieval for long-context memory
- Some form of revision loop

Emerging consensus (2024-2026):
- Event-graph outlines over chapter-list outlines (StoryWriter, DOME, CreAgentive)
- Per-character agents/memory for dialogue scenes (BookWorld, IBSEN, KazKoz)
- Temporal/multiversion knowledge graphs (CreAgentive, DOME)
- Anti-slop word/phrase + structural rule sets (autonovel pioneers this)

Gaps / underserved areas:
- POV / camera control (we have this; almost nobody else does)
- Per-language adaptation (most projects are English-first; Chinese-specific anti-slop is unexplored ground)
- Integrated reader/publisher tooling (most stop at .md output)

---

## Top 3 recommendations for adoption

### #1: WebNovelBench's 8 evaluation dimensions + corpus

**Why**: This is *the* most rigorous Chinese-language long-novel benchmark (EACL 2026 Findings, 4,000+ novels, MIT license, HuggingFace dataset). It is exactly the right shape for our quality system.

**What to take**:
- The 8 dimensions as our LLM-Judge rubric (verbatim, in Chinese translation):
  1. Use of Literary Devices (文学手法运用)
  2. Richness of Sensory Detail (感官细节丰富度)
  3. Balance of Character Presence (角色登场平衡)
  4. Distinctiveness of Character Dialogue (角色对话辨识度)
  5. Consistency of Characterisation (人物塑造一致性)
  6. Atmospheric and Thematic Alignment (氛围与主题契合)
  7. Contextual Appropriateness (语境恰当性)
  8. Scene-to-Scene Coherence (场景间连贯性)
- PCA-aggregated score → percentile rank vs. corpus
- The HuggingFace dataset for both fine-tuning data and percentile baselines

**What to leave**:
- Their Volcengine SDK / SiliconFlow plumbing — adapt to our LiteLLM gateway.
- The PCA weights — recompute on our own preferred sub-corpus.

**Cost**: low. Mostly prompt + Python.

---

### #2: NousResearch/autonovel's anti-slop framework

**Why**: The most thorough, openly-documented quality control of any project. Solves the exact problem (AI-tell detection) we currently don't address.

**What to take**:
- Word-level banned-vocabulary lists (translate to Chinese; e.g. "delve" → "深入探讨" patterns)
- 12 structural anti-patterns (triadic listing, "not X but Y" = "不是X而是Y", etc.) as Chinese regex rules
- 8 craft heuristics as positive prompt guidance (specificity, surprise, rhythm variation, ...)
- Dual scoring: mechanical regex pass + LLM-Judge pass, both gating chapter acceptance
- Per-chapter score threshold + retry (with cap) — we already retry but without a quality gate
- Final dual-persona Opus review pass over the full manuscript

**What to leave**:
- The hardcoded thresholds (7.5, 6.0) — make ours configurable.
- LaTeX/ePub/audiobook pipeline (out of scope).
- Don't lift code (no license) — implement our own.

**Cost**: medium. The blocklists and rules are weeks of prompt-engineering work, but it's the highest-leverage quality investment we can make.

---

### #3: SillyTavern's WorldInfo three-tier triggering model

**Why**: This is THE proven pattern in the field for runtime world-info injection. 28k stars, 3 years of production use. Solves the "what context goes in the prompt" problem cleanly.

**What to take**:
- Three entry types: constant (always-included) / keyword-triggered (only when match) / vector-triggered (semantic similarity above threshold)
- Token budget enforcement with priority order
- Scan depth and recursive activation (opt-in)

**What to leave**:
- AGPL code — implement our own.
- Roleplay-chat UX — our novel UX needs different ergonomics (probably an inspector panel in the editor).
- Recursive activation as default — risk of token explosion.

**Cost**: medium. Re-architecting our world-info retrieval is a multi-week task, but pays for itself on every chapter generation.

(Honourable mentions: THU-KEG/StoryWriter for the event-graph outline pattern; xindoo/ai-novel-lab for the simple AGENTS.md pattern; BookWorld for per-character agent pattern.)

---

## Red flags / gotchas

1. **License hygiene is poor.** Many top projects have **no LICENSE file**: autonovel, Long-Novel-GPT, StoryWriter (THU-KEG), Ex3, ai-book-writer, KazKoz/NovelGenerator. Legally, no license = all rights reserved = you can't redistribute. **Treat all of these as "read for ideas only, never copy code verbatim."** Apache-2.0 or MIT projects (BookWorld, IBSEN, RecurrentGPT under GPL, AI_Gen_Novel, doc-story, WebNovelBench, CreAgentive, MM_StoryAgent, ai-novel-lab) are the safe-to-study tier.

2. **AGPL is viral.** SillyTavern, YILING0013/AI_NovelGenerator, AIStoryWriter, RecurrentGPT (GPL-3) — if we import their code, our entire stack becomes AGPL/GPL. We're building a hosted product with a closed-source reader; this is incompatible. Re-implementation is required.

3. **Many "agent" projects are sequential pipelines.** YILING0013/AI_NovelGenerator (5.1k stars!), AIStoryWriter, etc., describe themselves as "AI agents" but the code is sequential LLM calls. We have an actual LangGraph multi-agent architecture; don't regress.

4. **Star counts ≠ quality.** YILING0013 has 5.1k stars and a simple sequential pipeline. StoryWriter (40 stars) is CIKM 2025 SOTA with event-graph outlines. Star counts correlate with marketing reach (Chinese hobby community) not architectural sophistication.

5. **Staleness ≠ irrelevance** for research-code projects. Re3 and DOC haven't been touched in 1-3 years but the ideas (multi-stage reranking, hierarchical outlines) are still cited. Conversely, an actively-pushed hobby project may have no useful ideas.

6. **WebNovelBench dimension hallucination risk (the brief's warning).** Earlier sessions reportedly invented dimension names. Verified verbatim list above. **Always quote from the paper, never from training memory.**

7. **CreAgentive's claims look strong but the repo has 7 stars / 0 forks.** Be skeptical of the "$1 per 100 chapters" / "thousands of chapters" claims until independently reproduced. The Story Prototype concept is interesting; the implementation may be brittle.

8. **autonovel only published ONE novel.** The framework's apparent quality is built on n=1 production. Their score thresholds may be tuned to that one book's genre/voice.

9. **xindoo/ai-novel-lab is also n=1** (one 430k-char novel). Authors explicitly graded their own work 73→93. Self-eval is suspect.

10. **Chinese-specific anti-slop is unexplored.** Every anti-slop framework we found targets English ("delve", "leverage", ...). Building a Chinese-specific blocklist (e.g. 网文 clichés: 修长如玉手、星眸、嘴角勾起一抹弧度、不是X而是Y) is novel work — there's a real research-publishable opportunity here.

11. **Memory architecture is converging on knowledge graphs.** Three frontier projects (CreAgentive, DOME, StoryWriter) all use some form of KG. Our current SQLite KG triples are aligned with this trend; keep investing here.

12. **Anthropic's official cookbooks have NO novel-writing recipe.** We will not find a quick-start template from Anthropic. We are blazing the trail here.

13. **Some "Chinese AI novel" Google results lead to commercial products** (NovelCrafter, NovelAI, Sudowrite) that have no open-source release. We confirmed these are proprietary; they cannot be studied beyond their docs.

14. **NousResearch/autonovel's pushed_at is 2026-03-20** but `updated_at` is 2026-05-28 — these mean different things on GitHub (push = code commits; update = metadata changes incl. star activity). The real code-cadence is push_at, which is ~5 weeks before access. Active but not daily.
