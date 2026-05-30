# R5 — Character Consistency / Multi-Character Roleplay Techniques

Research sweep: 2026-04-28.
Scope: persona consistency, multi-character distinctness, character drift, knowledge boundaries, relationship tracking — with an eye toward long-form Chinese novel generation, multi-agent pipelines, and the SEQR `dialogue_distinct` weak dimension (ρ=−0.16).

Every claim in this document is backed by a WebSearch result or a WebFetch'd page accessed today.

---

## 1. State of the field (TL;DR)

The hot 2024-2026 character-consistency research has converged on roughly five families:

1. **Profile-driven SFT / DPO of role-playing LLMs** — Character-LLM, RoleLLM, OpenCharacter, CoSER, PsyMem, Pygmalion-3, Chinese CharacterGLM.
2. **Inference-time mechanisms to fight persona drift** — split-softmax attention reweighting (Li/Kenneth), CogDual "cognize-then-respond", role-aware reasoning (RIA + RSO).
3. **Retrieval and memory architectures** — RoleRAG (knowledge graph with cognitive-boundary rejection), PsyMem memory alignment, BookWorld dual-tier LTM/STM, SCORE state tracking.
4. **Benchmarks** — CharacterEval (Chinese), CharacterBench (bilingual, 11 dims), InCharacter (psychological interview), ConStory-Bench (5 dims × 19 subtypes), LifeState-Bench, RAIDEN benchmark, CoSER eval.
5. **Hobbyist / production patterns** — SillyTavern character cards + lorebooks, Character.AI's MQA + cross-layer KV-sharing + affective ranking.

Two findings recur across the literature and matter for our SEQR `dialogue_distinct` problem:

- **Post-training collapses stylistic variance.** "Narrative Flattening" (Stanford/Allen AI replication on OLMo 32B) shows SFT→DPO→RLVR each compress thematic, affective, and stylistic variation versus the base model. This is consistent with `dialogue_distinct` being a weak dim regardless of how clever our character prompts are. — `arxiv.org/abs/2605.27878`.
- **Role prompts don't create distinct cognition, only distinct surface style.** The RPNA study (medical LLMs) ablated role-sensitive neurons and found role prompts "primarily affect surface-level linguistic features, with no evidence of distinct reasoning pathways" — `arxiv.org/abs/2510.24677`. So "give each character its own system prompt" is structurally weaker than we hoped; the model wires them all into the same circuit and merely adjusts vocabulary on top.

These two findings together are the strongest evidence base for our SEQR weak `dialogue_distinct` correlation — see §"Top 3 candidates" and §"Open questions".

---

## 2. Individual findings

### Character-LLM (Shao, Gu et al., EMNLP 2023, still foundational)

- Source: https://arxiv.org/abs/2310.10158 [accessed:2026-04-28]
- Type: paper
- Org: Fudan + ByteDance (choosewhatulike repo)
- Date: 2023-10-16 (still the most-cited Character-LLM SFT paper)
- Maturity: prototype with open weights and data
- Key idea (verbatim quote from search result):
  > "editing profiles as experiences of a certain character and training models to be personal simulacra with these experiences"
- Concrete mechanism:
  - Constructs character profile → expands to "experience" episodes → trains separate Character-LLM per character on the synthesized episodes.
  - One trained agent per character (e.g. Beethoven, Cleopatra). At inference, the trained model just is the character.
- Strengths: doesn't rely on persona prompt drift; character is in the weights.
- Limitations: one model per character; impossible to scale to a novel's 30+ characters; no mechanism for multi-character interaction in one model.
- Applicability: low for our case — we need many characters in a single inference path, not one fine-tune per character.
  - adoption cost: rewrite
  - Chinese readiness: paper used English exemplars; method is language-agnostic but no Chinese release.

---

### RoleLLM (Wang et al., ACL 2024 Findings)

- Source: https://arxiv.org/abs/2310.00746 ; https://aclanthology.org/2024.findings-acl.878/ [accessed:2026-04-28]
- Type: paper
- Org: Renmin / academic collab
- Date: ACL Findings 2024 (final 2024-06)
- Maturity: prototype; produces RoleLLaMA (EN) and RoleGLM (ZH)
- Key idea (verbatim):
  > "Role Profile Construction for 100 roles; Context-Based Instruction Generation (Context-Instruct) for role-specific knowledge extraction; Role Prompting using GPT (RoleGPT) for speaking style imitation; and Role-Conditioned Instruction Tuning (RoCIT)"
- Mechanism:
  - 95 English + 5 Chinese roles selected from 916 EN + 24 ZH scripts.
  - Context-Instruct extracts role-specific QA pairs from the script context.
  - RoleGPT prompts GPT-4 to produce speaking-style imitation data.
  - RoCIT fine-tunes open models on RoleBench (168,093 samples).
- Strengths: produces an open Chinese role-playing LLM (RoleGLM) we could fine-tune from.
- Limitations: small Chinese subset (5 roles); single-character orientation; old base models (LLaMA-2 era).
- Applicability: medium — useful as a *data construction template* for our scene→role-aware SFT, not as a model directly.
  - adoption cost: medium (data pipeline reuse)
  - Chinese readiness: yes, ZH split exists.

---

### CoSER (Wang et al., ICML 2025)

- Source: https://arxiv.org/abs/2502.09082 ; https://icml.cc/virtual/2025/poster/46115 [accessed:2026-04-28]
- Type: paper + open weights (CoSER-8B / CoSER-70B)
- Org: Xintao Wang group
- Date: 2025-02 paper; ICML 2025 poster
- Maturity: production-ready open weights on LLaMA-3.1
- Key idea (verbatim):
  > "given-circumstance acting for training and evaluating role-playing LLMs, where LLMs sequentially portray multiple characters in book scenes"
- Mechanism:
  - 17,966 characters extracted from 771 renowned books → authentic dialogues + internal thoughts + character experiences.
  - "Given-Circumstance Acting" — train the model to play all characters in a scene sequentially, conditioned on the scene's actual circumstances.
  - Released CoSER-8B and CoSER-70B on LLaMA-3.1.
- Strengths: SOTA on InCharacter (75.80%) and LifeChoice (93.47%); matches/exceeds GPT-4o.
- Limitations: heavily English-literature centric (771 "renowned books" = mostly western canon); doesn't directly model continuous emotional state or per-character KB.
- Applicability: HIGH — its "play multiple characters sequentially in one scene" objective is exactly our use case.
  - adoption cost: medium (use as ZH-translated SFT data + as inference baseline; LLaMA-3.1 weights are pluggable)
  - Chinese readiness: not ZH-native; would need data translation or Chinese analog construction.

---

### PsyMem (Cheng et al., 2025)

- Source: https://arxiv.org/abs/2505.12814 ; https://arxiv.org/html/2505.12814v2 [accessed:2026-04-28]
- Type: paper + Qwen2.5-7B fine-tune (PsyMem-Qwen)
- Date: 2025-05
- Maturity: open weights
- Key idea (verbatim):
  > "supplements textual descriptions with 26 psychological indicators to detail model character … implements memory alignment training, explicitly training the model to align character's response with memory"
- Mechanism (the 26 indicators are the only paper I found that operationalizes them this densely):
  - Big Five (5) + Schwartz values (10) + Zimbardo social/leadership (6) + Thomas-Kilmann conflict (5) = 26 quantitative attributes per character (1-5 scales).
  - Two-stage training: (1) baseline attribute training, (2) memory-augmented SFT where retrieved memory is up-weighted (α=20 loss weight).
  - Memory pipeline uses Nano-GraphRAG; deliberately injects irrelevant retrievals as noise to teach the model to trust retrievals.
  - Dataset: 539 novels post-June 2024, 5,414 characters, 38,962 dialogues, 536,636 utterances — all third-person narration.
- Reported strengths:
  - Character Fidelity 82.64% (avg) vs base Qwen2.5; beats CoSER-70B (82.28%) and GPT-4o (80.86%) despite being 7B.
  - Memory alignment 91.80% — large jump because the SFT specifically rewards memory grounding.
- Limitations: requires constructing 26 psych vectors per character (heavy authoring/profiling cost); novel-source not specified as ZH.
- Applicability: HIGH — closest existing system to our scene-level generation. The psych-indicator schema directly maps onto our Story Bible character cards.
  - adoption cost: low-medium (we can adapt prompts/indicators without retraining; medium if we want the memory-alignment SFT).
  - Chinese readiness: paper says novels include "diverse genres"; not explicit ZH but Qwen-base means ZH-friendly out of the box.

---

### CogDual (2025)

- Source: https://arxiv.org/abs/2507.17147 [accessed:2026-04-28]
- Type: paper
- Date: 2025-07
- Maturity: prototype
- Key idea (verbatim):
  > "cognize-then-respond" with "both external awareness of situations and internal self-awareness"
- Mechanism:
  - Reinforcement learning (GRPO-style) with two general rewards: "implicit rule-based" — open-domain text-quality rewards.
  - The model generates an internal cognition trace ("What is the situation? What does my character know? What do I want?") before producing the response.
- Strengths: cross-benchmark gen on CoSER bench, Cross-MR, LifeChoice.
- Limitations: open-domain reward is fuzzy; doesn't address inter-character distinctness directly.
- Applicability: medium — the "cognize-then-respond" trace can be implemented as a prompted pre-step in our Writer agent without retraining.
  - adoption cost: low (prompt-level)
  - Chinese readiness: language-agnostic.

---

### Role-Aware Reasoning / RIA + RSO ("Thinking in Character", 2025)

- Source: https://arxiv.org/pdf/2506.01748 [accessed:2026-04-28]
- Type: paper
- Date: 2025-06
- Maturity: prototype
- Key idea (verbatim from search result summary):
  > "Role-Aware Reasoning (RAR) is designed to imbue LLMs with the capacity for deep thinking that aligns with character settings. RAR addresses challenges like 'attention diversion' and 'style drift' through RIA (Role Identity Activation) and RSO (Role Style Optimization)"
- Mechanism (from search summary, full PDF text not extractable):
  - RIA activates "key role traits like emotions and motivations" before generation.
  - RSO "guides the model to generate reasoning traces in suitable styles depending on context."
- Strengths: explicit names for the two failure modes (attention diversion, style drift) match our `dialogue_distinct` problem.
- Limitations: full mechanism details require the actual PDF text which our fetcher couldn't decode; treat with caution.
- Applicability: medium-high — vocabulary and decomposition look directly useful for designing our character agent prompts.
  - adoption cost: low (prompt-level pattern)
  - Chinese readiness: language-agnostic.

---

### RAIDEN-R1 (Wang et al., 2025)

- Source: https://arxiv.org/abs/2505.10218 ; https://arxiv.org/html/2505.10218v1 [accessed:2026-04-28]
- Type: paper
- Date: 2025-05
- Maturity: prototype + benchmark
- Key idea (verbatim):
  > "Verifiable Role-Awareness Reward (VRAR) … singular and multi-term mining strategies to generate quantifiable rewards by assessing role-specific keys"
- Mechanism:
  - Single-Term Validation (STV): WH-question keywords cross-verified against multiple LLM-derived references (GPT-4, Claude, Baichuan); binary reward on presence.
  - Multi-Term Dynamic Parsing (MTDP): expand keywords via QwQ-32B, generate Python validator functions, require >70% consistency between LLM judgment and code execution.
  - Cold-start SFT on compressed DeepSeek-R1 reasoning + style adaptation with bracketed internal monologue.
  - RAIDEN benchmark scores: 14B-GRPO model — Script-Based Knowledge 88.04%, Conversation Memory 88.65%.
- Strengths: verifiable rewards = reproducible signal without depending on subjective LLM-as-judge.
- Limitations: WH-keyword based reward biases toward factual recall, not dialogue style.
- Applicability: medium — the "Role-Cognition Boundary" metric in RAIDEN benchmark is a clean evaluation target for us.
  - adoption cost: medium (would adopt the benchmark + reward design, not retrain)
  - Chinese readiness: bench is bilingual-friendly.

---

### Persona-Aware Contrastive Learning (PCL, 2025)

- Source: https://arxiv.org/abs/2503.17662 [accessed:2026-04-28]
- Type: paper
- Date: 2025-03
- Key idea (verbatim):
  > "Role Chain Method … encourages models to self-question based on the role characteristics and dialogue context to adjust personality consistency"
- Mechanism: iterative contrastive learning between role-aware vs role-blind responses; RLHF-style annotation-free signal.
- Reported strengths: PCL-trained models beat vanilla LLMs on CharEval + GPT-4 + human eval.
- Limitations: contrastive pair construction is the load-bearing step; quality depends on it.
- Applicability: medium — Role Chain self-questioning is implementable as a prompt step.
  - adoption cost: low (prompt) or high (training)
  - Chinese readiness: language-agnostic.

---

### OpenCharacter (Wang et al., 2025)

- Source: https://arxiv.org/abs/2501.15427 ; https://arxiv.org/html/2501.15427v1 [accessed:2026-04-28]
- Type: paper + open data + LLaMA-3 8B weights
- Date: 2025-01
- Maturity: production-ready
- Key idea: 20,000 synthetic characters → 306,000 instruction-response pairs → SFT LLaMA-3 8B → approaches GPT-4o on PersonaGym.
- Mechanism:
  - **R variant (Rewriting):** transform existing instruction-tune responses to character style while preserving original task knowledge.
  - **G variant (Generation):** generate fresh character-aligned responses.
- Strengths: published data + weights; 20k characters is a huge population.
- Limitations: characters are GPT-4o synthesized → carry GPT-4o's style bias; English-centric.
- Applicability: medium — useful as data construction template.
  - adoption cost: medium (re-run pipeline in Chinese with our characters)
  - Chinese readiness: not native, but pipeline portable.

---

### CharacterEval (Tu et al., ACL 2024) — the canonical Chinese benchmark

- Source: https://aclanthology.org/2024.acl-long.638/ ; https://arxiv.org/abs/2401.01275 [accessed:2026-04-28]
- Type: benchmark paper
- Date: 2024-01 (ACL 2024)
- Maturity: production benchmark — 1,785 multi-turn dialogues, 23,020 examples, 77 ZH characters from novels/scripts.
- Key idea (verbatim from our fetch):
  > "multifaceted evaluation approach, encompassing thirteen targeted metrics on four dimensions"
- The 4 dimensions × 13 metrics:
  1. **Conversational Ability** (3): fluency, coherency, consistency
  2. **Character Consistency** (5): split into knowledge (exposure, accuracy, hallucination) + persona (behavior consistency, utterance consistency)
  3. **Role-playing Attractiveness** (4): human-likeness, communication skills, expression diversity, empathy
  4. **Personality Back-Testing** (1): MBTI accuracy
- CharacterRM: Baichuan2-13B-base trained on human annotations; reportedly higher correlation with humans than GPT-4 as judge.
- Findings: BC-Character-Turbo > MiniMax > InternLM-20B; "GPT-4's effectiveness diminishes in Chinese role-playing conversations" due to EN training bias.
- Applicability: HIGH — this is *the* benchmark to measure our system on for Chinese.
  - adoption cost: low (test-time)
  - Chinese readiness: native.

---

### CharacterBench (Zhou et al., AAAI 2025)

- Source: https://arxiv.org/abs/2412.11912 ; https://arxiv.org/html/2412.11912v1 [accessed:2026-04-28]
- Type: bilingual benchmark
- Date: 2024-12
- Maturity: production benchmark — 22,859 human-annotated samples, 3,956 characters across 25 sub-categories.
- The 11 dimensions across 6 aspects (verbatim from our fetch):
  1. **Memory**: Memory Consistency
  2. **Knowledge**: Fact Accuracy, Boundary Consistency
  3. **Persona**: Attribute Consistency, Behavior Consistency
  4. **Emotion**: Emotional Self-regulation, Empathetic Responsiveness
  5. **Morality**: Morality Stability, Morality Robustness
  6. **Believability**: Human-likeness, Engagement
- Dense (manifest naturally) vs sparse (need targeted queries) dimensions split.
- Top model: Claude-3-Opus (3.82-3.88 normalized to 5pt).
- CharacterJudge (Qwen2-7B-Chat) reaches 68% correlation with human scores.
- Applicability: HIGH — bilingual; "Boundary Consistency" maps directly to our character knowledge isolation problem; "Attribute Consistency" maps to dialogue distinctness.
  - adoption cost: low (test-time)
  - Chinese readiness: bilingual.

---

### InCharacter (Wang et al., ACL 2024)

- Source: https://arxiv.org/abs/2310.17976 ; https://incharacter.github.io/ ; https://github.com/Neph0s/InCharacter [accessed:2026-04-28]
- Type: paper + benchmark
- Date: 2023-10 (final ACL 2024)
- Key idea: assess RPA personality fidelity by *interviewing* the agent with psychological scales (BFI, 16P, DTDD, BSRI, ECR-R, CABIN, GSE, LMS, EIS, WLEIS).
- Mechanism: two-phase — interview the RPA to elicit behavioral patterns, then assess via Option Conversion (OC) or Expert Rating (ER).
- Reported strength: SOTA RPAs match target characters at 78.9% avg accuracy across these scales.
- Applicability: medium — interesting as an *out-of-band* evaluation; not a runtime mechanism.
  - adoption cost: low (eval pipeline)
  - Chinese readiness: scales need translation, MBTI 16P exists in ZH.

---

### BookWorld (Ran, Wang et al., ACL 2025) — Fudan multi-agent novel sim

- Source: https://arxiv.org/abs/2504.14538 ; https://bookworld2025.github.io/ ; https://github.com/alienet1109/BookWorld [accessed:2026-04-28]
- Type: paper + open repo
- Date: 2025-04 (ACL 2025)
- Maturity: prototype with demo
- Key idea (verbatim from our fetch):
  > "extracts character data and background knowledge from source books, and constructs a multi-agent system using these data, comprising role agents for the characters and a world agent for simulation control"
- Mechanism (our fetch returned good detail):
  - **Role Agents** — per-character LLM agents with static attrs (gender/age/personality) and dynamic attrs (goals/states/memories). Dual-tier memory: STM stores recent events; LTM stores abstracted summaries.
  - **World Agent** — environmental orchestrator. Generates "conflict-rich events" and environmental responses; controls 9,912 worldview settings.
  - Prompts contain: action history, character profile, world description, current goals, status, accessible characters. Output is JSON with action_type, target, visibility, and a "literary narrative statement containing thoughts, speech, and actions."
- Reported result: 75.36% win rate vs direct LLM + vs HoLLMwood.
- Applicability: VERY HIGH — closest published architectural twin to our pipeline. Static/dynamic attribute split + STM/LTM + visibility filtering = a clean reference design.
  - adoption cost: low-medium (architecture portable; we already have World agent and Camera agent)
  - Chinese readiness: paper is Fudan, source code available — Chinese-first likely.

---

### SCORE (2025)

- Source: https://arxiv.org/abs/2503.23512 ; https://arxiv.org/html/2503.23512v1 [accessed:2026-04-28]
- Type: paper
- Date: 2025-03
- Maturity: prototype
- Key idea (verbatim from our fetch):
  > "integrates dynamic state tracking to monitor characters via symbolic logic, context-aware summarization with hierarchical episode summaries, and hybrid retrieval methods"
- Mechanism (well-detailed in our fetch):
  - Symbolic state per item/character: `S_i(t) ∈ {active, lost, destroyed}` modeled as Markov chain with destroyed/lost as absorbing states.
  - Hierarchical episode summaries — per-episode tracking of character actions A_c(t), item interactions I_i(t), emotional states.
  - Hybrid retrieval: FAISS + OpenAI embeddings for semantic + TF-IDF for keyword + sentiment filter σ(e).
- Strengths: explicit symbolic state guards against "dead character resurrects" failure.
- Limitations: graph construction details are conceptual in the paper.
- Applicability: HIGH — the absorbing-state Markov idea is a direct match for our knowledge_graph valid_from/valid_to design.
  - adoption cost: low (small additions to our state tracker)
  - Chinese readiness: language-agnostic.

---

### CREFT (2025) — multi-agent character relation extraction

- Source: https://arxiv.org/pdf/2505.24553 [accessed:2026-04-28]
- Type: paper
- Date: 2025-05
- Mechanism: sequential multi-agent LLM pipeline — Identification → Relation Detection → Refinement agents — produces subject-predicate-object triples from narrative text.
- Applicability: medium — relevant to seed our knowledge_triples table from existing fiction; not directly for generation.
  - adoption cost: medium
  - Chinese readiness: pipeline language-agnostic.

---

### Constella (CHI / ACM TOCHI 2025) — HCI tool for character creation

- Source: https://arxiv.org/abs/2507.05820 ; https://dl.acm.org/doi/10.1145/3796234 [accessed:2026-04-28]
- Type: HCI paper + tool
- Date: 2025-07
- Key idea: "constellation" — characters gain meaning by inter-relation. Three features: FRIENDS DISCOVERY (suggest related characters), JOURNALS (parallel inner mindscapes for several characters), COMMENTS (relationships as inter-character responses).
- Mechanism: LLM calls orchestrated in parallel + thread-sequenced patterns; each character has its own panel-agent.
- Applicability: medium — UX inspiration for our admin dashboard; the COMMENTS pattern (each character reacts to events from their own POV) is potentially powerful for testing dialogue distinctness during authoring.
  - adoption cost: medium (UI work)
  - Chinese readiness: language-agnostic.

---

### Lost in Stories / ConStory-Bench (2025-2026)

- Source: https://arxiv.org/abs/2603.05890 ; https://arxiv.org/html/2603.05890v1 [accessed:2026-04-28]
- Type: benchmark paper
- Date: 2026-03 (huggingface paper page exists)
- Key idea: 2,000 prompts × 4 narrative tasks (generation/continuation/expansion/completion), 8k-10k word target outputs, 5-dim × 19-subtype error taxonomy.
- Full 5×19 taxonomy (from our fetch):
  1. **Timeline & Plot Logic (6)**: absolute time contradictions, duration contradictions, simultaneity contradictions, causeless effects, causal logic violations, abandoned plot elements
  2. **Characterization (4)**: memory contradictions, knowledge contradictions, skill fluctuations, forgotten abilities
  3. **World-building & Setting (3)**: core rules violations, social norms violations, geographical contradictions
  4. **Factual & Detail Consistency (3)**: appearance mismatches, nomenclature confusions, quantitative mismatches
  5. **Narrative & Style (3)**: perspective confusions, tone inconsistencies, style shifts
- Models tested: GPT-5-Reasoning, Gemini-2.5-Pro, Claude-Sonnet-4.5, Grok-4, Qwen3, DeepSeek-V3.2, GLM-4.6, LongWriter-Zero, SuperWriter, DOME.
- Key finding: "Characterization errors show notably lower prevalence" than other categories; primary failure modes are memory & knowledge contradictions; errors cluster in mid-narrative, in high-entropy segments.
- Applicability: HIGH — the 4-subtype Characterization taxonomy is exactly the failure mode catalog we need for QA.
  - adoption cost: low (taxonomy adoption)
  - Chinese readiness: paper covers multilingual models incl. Qwen3/DeepSeek/GLM.

---

### Measuring & Controlling Persona Drift (Li/Kenneth et al., 2024)

- Source: https://arxiv.org/abs/2402.10962 ; https://arxiv.org/html/2402.10962v1 ; https://github.com/likenneth/persona_drift [accessed:2026-04-28]
- Type: paper + open code
- Date: 2024-02
- Maturity: prototype with public code
- Key idea (from our fetch):
  > the agent LM gradually stops following its persona; baseline persona adherence drops from ~0.8 at round 1 to ~0.4 by round 8
- Mechanism:
  - Two-LM dialog (sA, sB); at each round replace user turn with a probe pB; score with deterministic persona function fB(·) ∈ [0,1].
  - **Split-softmax (SS) intervention** — training-free; reweights attention with `attn_sys *= π_k(t)/π(t)` and `attn_other *= (1-π_k(t))/(1-π(t))`; hyperparam k ∈ [0,1].
- Reported numbers: tested on LLaMA2-chat-70B; persona drift starts within 8 rounds.
- Applicability: HIGH for inference-time mitigation — split-softmax is implementable in our generation step without retraining if we control the inference stack; less so if we're stuck behind a closed API.
  - adoption cost: medium (requires modifying attention compute — feasible only with self-hosted open weights)
  - Chinese readiness: language-agnostic.

---

### Examining Identity Drift in LLM Agent Conversations (2024)

- Source: https://arxiv.org/abs/2412.00804 [accessed:2026-04-28]
- Type: paper
- Date: 2024-12
- Key findings:
  1. Larger models drift *more*, not less.
  2. Persona prompt assignment alone does NOT prevent identity drift.
  3. Model family differences are smaller than parameter-scale effects.
- Tested across 9 LLMs.
- Applicability: high as a *cautionary* finding — confirms that pure prompt-side persona engineering will not solve our problem for the largest models.
  - adoption cost: NA (it's a warning, not a method)
  - Chinese readiness: language-agnostic finding.

---

### Nautilus Compass (2026, persona drift detection in production)

- Source: https://arxiv.org/abs/2605.09863v1 ; https://arxiv.org/html/2605.09863 [accessed:2026-04-28]
- Type: paper (very recent)
- Maturity: production-tested on real Claude Code sessions
- Key mechanism:
  - Black-box; works only on prompt text.
  - Cosine similarity between user prompt embeddings (BGE-m3) and behavioral anchor texts.
  - Weighted top-k mean aggregation as the drift signal.
- Reported numbers: ROC AUC 0.83 for drift detection; reproduction cost $3.50 (14× cheaper than GPT-4o alternatives).
- Applicability: medium-high for drift *monitoring* (not prevention); our Consistency agent could embed a Nautilus-style anchor check on each chapter draft.
  - adoption cost: low (BGE-m3 inference + one cosine sim per chapter)
  - Chinese readiness: BGE-m3 is bilingual/multilingual native.

---

### Dissecting Role Cognition in Medical LLMs via Neuronal Ablation (RPNA, 2025)

- Source: https://arxiv.org/abs/2510.24677 ; https://arxiv.org/html/2510.24677 [accessed:2026-04-28]
- Type: paper
- Date: 2025-10
- Key idea (verbatim from our search):
  > "role prompts do not significantly enhance the medical reasoning abilities of LLMs. Instead, they primarily affect surface-level linguistic features, with no evidence of distinct reasoning pathways or cognitive differentiation across clinical roles."
- Mechanism (verbatim from our fetch):
  - Identify role-sensitive neurons by activation deltas across layers; select top K layers (typically 4); ablate top 5% neurons per layer.
  - Compare with random-neuron ablation control.
  - Datasets: MedQA, MedMCQA, MMLU-Med.
- Implications quote: "Organizations implementing role-based AI systems—customer service, legal analysis, educational tutoring—should question whether prompts create genuine behavioral differentiation or superficial linguistic variation."
- Applicability: HIGHEST as a *theoretical bound*. This is the strongest evidence we have for why simple "give each character a system prompt" approach will plateau, and it directly explains the SEQR `dialogue_distinct` ρ=−0.16 finding.
  - adoption cost: NA (it's a warning)
  - Chinese readiness: medical domain only, but the architectural conclusion generalizes.

---

### Narrative Flattening (2026)

- Source: https://arxiv.org/abs/2605.27878 [accessed:2026-04-28]
- Type: paper
- Date: 2026 (preprint)
- Key idea (verbatim from our fetch):
  > "post-training compresses dynamic variation … thematic transitions become more uniform, high-intensity emotions give way to neutrality, and stylistic diversity across stories shrinks"
- Mechanism: matched story-continuation evaluation across 4 OLMo 32B checkpoints (Base, SFT, DPO, RLVR) on StoryStar / TMAS / The New Yorker.
- Finding: compression is monotone in training stage. Biggest gap to professional literary fiction.
- Implication: even with perfect prompts, the *base instruction-tuned model itself* is biased toward flatter character voices. This combines with RPNA to explain `dialogue_distinct` weakness *structurally*.
- Applicability: HIGH as a strategic finding — argues for either base-model selection (less post-trained = more diverse) or our own SFT on diverse style data.
  - adoption cost: NA (it's a warning)
  - Chinese readiness: finding is model-family-general.

---

### RoleRAG (2025)

- Source: https://arxiv.org/abs/2505.18541 ; https://arxiv.org/html/2505.18541v1 [accessed:2026-04-28]
- Type: paper
- Date: 2025-05
- Key idea (from our fetch):
  > "efficient semantic entity normalization algorithm" + "boundary-aware retriever" that "rejects out-of-scope questions that exceed the character's cognitive boundaries"
- Mechanism:
  - Entity disambiguation merges 'Anakin Skywalker' and 'Darth Vader' to one canonical entity, reducing LLM calls by `|N|/k`.
  - Three retrieval modes: out-of-scope rejection, specific entity retrieval, general 1-hop neighborhood.
- Reported strengths: across Harry Potter, RoleBench-zh, Character-LLM datasets — outperforms baselines on knowledge exposure + hallucination + unknown rejection.
- Limitations (authors' own): multi-turn consistency still open.
- Applicability: HIGH for per-character knowledge boundary enforcement.
  - adoption cost: low-medium (entity normalization is reusable across our existing kg_triples schema; boundary-aware retrieval is a small layer on top of our memory L3)
  - Chinese readiness: explicitly tested on RoleBench-zh.

---

### Memory-Driven Role-Playing / MREval / MRPrompt (2026)

- Source: https://arxiv.org/abs/2603.19313 ; https://arxiv.org/html/2603.19313 [accessed:2026-04-28]
- Type: paper
- Date: 2026 (preprint)
- Key idea (from our fetch):
  - Decompose role-playing into 4 sequential memory abilities: Memory-Anchoring, Memory-Selecting, Memory-Bounding, Memory-Enacting.
  - MRPrompt = Narrative Schema (hierarchical persona with cue-addressable keys) + Magic-If Protocol (Stanislavski-inspired LTM/STM control).
  - MRBench: 200 EN + 200 ZH instances.
- Reported strengths: smaller models (Qwen3-8B + MRPrompt) on par with closed-source giants.
- Applicability: HIGH — operationally close to our LayeredMemory L0-L3.
  - adoption cost: low (prompt-level patterns)
  - Chinese readiness: explicit ZH split.

---

### Pygmalion-3 (open-weights roleplay LLM)

- Source: https://huggingface.co/PygmalionAI/Pygmalion-3-12B [accessed:2026-04-28]
- Type: model card
- Maturity: production open weights, Apache-2.0
- Mechanism: LoRA rank-32 over Mistral-Nemo-Base-2407; trained on PIPPA + creative writing + RP forum data; ChatML format with "Enter roleplay mode."
- Applicability: medium — Chinese support inherited from Nemo (decent ZH but not native); useful as a *roleplay baseline* model for our admin's per-agent binding system.
  - adoption cost: low (drop-in via vLLM / Ollama)
  - Chinese readiness: medium (Nemo handles ZH but not specialized).

---

### Mistral NeMo roleplay variants (community)

- Source: https://mistral.ai/news/mistral-nemo ; https://huggingface.co/ArliAI/Mistral-Nemo-12B-RPMax-v1.1 ; https://openrouter.ai/nothingiisreal/mn-celeste-12b [accessed:2026-04-28]
- Type: open model variants
- Notable models: ArliAI RPMax v1.1/v1.2, MN-12B-Lyra-v1 (Sao10K), MN-12B-Celeste, Mahou-1.5, Pantheon-RP.
- Base: Mistral Nemo 12B, 128k context, Apache-2.0.
- Applicability: medium — same as Pygmalion-3; useful for ensemble / per-agent binding.
  - adoption cost: low
  - Chinese readiness: medium.

---

### SillyTavern Character Cards V2 + Lorebook

- Source: https://github.com/malfoyslastname/character-card-spec-v2 ; https://docs.sillytavern.app/usage/core-concepts/personas/ ; https://docs.sillytavern.app/usage/core-concepts/worldinfo/ [accessed:2026-04-28]
- Type: spec + docs
- Maturity: production hobbyist
- Spec V2 fields (from our fetch):
  - Standard: `name`, `description`, `personality`, `scenario`, `first_mes`, `mes_example`
  - V2 additions: `spec` ("chara_card_v2"), `spec_version`, `creator_notes`, `system_prompt`, `post_history_instructions`, `alternate_greetings`, `character_book`, `tags`, `creator`, `character_version`, `extensions`
  - `character_book`: embedded lorebook with `entries`, `scan_depth`, `token_budget`, `recursive_scanning`
  - Lorebook entry: `keys`, `content`, `case_sensitive`, `priority`, `position`
- Practical pattern (verbatim from our search):
  > "Character Card handles core personality and summary (800-1200 tokens) while Lorebook contains details, world info, and behaviors (fires when needed), resulting in more tokens for conversation and richer context when relevant."
- Applicability: HIGH as a *data schema* reference. Our Story Bible character cards should adopt V2 field structure for interop, and our knowledge_triples can power a lorebook-like keyword-triggered retrieval.
  - adoption cost: low (schema mapping)
  - Chinese readiness: yes — many existing ZH character cards in the SillyTavern ecosystem.

---

### Character.AI's production architecture

- Source: https://blog.character.ai/optimizing-ai-inference-at-character-ai-2/ ; https://blog.character.ai/news/research/ ; https://arxiv.org/html/2409.15012v1 (MixAttention) [accessed:2026-04-28]
- Type: engineering blog + cited paper
- Maturity: production, ~20k QPS, ~20% of Google Search volume
- Mechanism (verbatim aggregation of our fetches):
  - **Multi-Query Attention (MQA)** in *all* layers → 8× KV cache reduction vs GQA.
  - **Cross-layer KV sharing** across neighboring attention layers → another 2-3×.
  - **Hybrid attention horizons** — 1024-token local windows interleaved with global attention (only 1 of 6 layers global). O(L²) → O(L) for most layers.
  - **Native int8 training** — avoids quantization-train mismatch.
  - **Affective ranking classifier** ranks candidate replies for emotional appropriateness after primary generation.
  - **Session-level memory buffer** + April 2026 "Smarter Memory" feature (newer post not technical-detailed).
- Honest limitation in our search result: "system architecture combines refined prompt engineering, session-level memory buffers, and preference modeling … but it lacks persistent identity modules and end-to-end multimodal integration."
- Their in-house model: **Kaiju** (Nov 2025 blog post).
- Applicability for us: 
  - Inference optimizations: HIGH relevance for cost — but we're not at scale where this matters.
  - The *architectural pattern* (separate affective ranking pass after generation) maps perfectly onto our Consistency agent gating.
  - adoption cost: low for pattern, high for inference engineering.
  - Chinese readiness: their architecture is language-agnostic.

---

### "Talk Less, Call Right" (CPDC 2025) — Rule-Based Role Prompting (RRP)

- Source: https://arxiv.org/abs/2509.00482 ; https://arxiv.org/html/2509.00482v1 [accessed:2026-04-28]
- Type: paper (challenge submission)
- Date: 2025-09
- Key contribution: **CSC (Character-card / Scene-Contract)** prompt structure separating "Voice" (NPC speech) from "Action" (legal function calls). Plus HEF (Hard-Enforced Function Calling).
- Numbers:
  - Basic role prompting: 0.523
  - Improved manual prompting: 0.533
  - Automatic prompt optimization (APO): 0.538
  - **Rule-Based Role Prompting (RRP): 0.571** — best.
- Applicability: medium-high — RRP's CSC pattern (Voice / Action split + scene contract) is directly transplantable to our Writer agent prompt schema.
  - adoption cost: low (prompt-level)
  - Chinese readiness: language-agnostic.

---

### "Beyond Profile" / CharacterBot (Lu Xun, ACL 2025 Findings)

- Source: https://arxiv.org/abs/2502.12988 [accessed:2026-04-28]
- Type: paper
- Date: 2025-02
- Key idea: simulate not just biographic facts but *thought patterns* of a writer (uses Lu Xun's 17 essay collections).
- Mechanism: pre-training on linguistic patterns + fine-tuning on multiple-choice QA, generative QA, style transfer. **CharLoRA** = general-style expert + task-specific experts.
- Applicability: medium — interesting model-of-a-writer approach but specialized; the CharLoRA pattern is reusable to layer per-character LoRA adapters atop a base.
  - adoption cost: medium (per-character LoRA training)
  - Chinese readiness: native ZH (Lu Xun).

---

### Too Good to be Bad: LLMs failing at villains (2025)

- Source: https://arxiv.org/abs/2511.04962 [accessed:2026-04-28]
- Type: paper
- Date: 2025-11
- Key finding: "LLM role-playing fidelity declines with decreasing character morality, especially for manipulative traits, as a fundamental tension exists between the prosocial objectives of safety alignment and the task of authentically simulating selfish, manipulative, or malicious characters."
- Applicability: HIGH as a failure-mode warning. For Chinese fiction with antagonists, expect the model to break character toward moralizing — needs explicit countermeasures.
  - adoption cost: NA (it's a warning)
  - Chinese readiness: alignment effect is model-family-general.

---

### LifeState-Bench (2025)

- Source: https://arxiv.org/pdf/2503.23514 [accessed:2026-04-28]
- Type: benchmark
- Date: 2025-03
- Key idea: assess lifelong learning in role-playing LLMs via Hamlet + synthetic-script datasets; tests self-awareness, episodic memory retrieval, relationship tracking, given access only to current 2 dialogue turns.
- Finding: non-parametric (retrieval) methods beat parametric for stateful learning; all models suffer catastrophic forgetting at scale.
- Applicability: medium — directly evaluates the long-conversation property our pipeline cares about.
  - adoption cost: low (eval)
  - Chinese readiness: Hamlet is EN; would need ZH bench construction.

---

### Multi-party speaker-aware contrastive learning (SA-LLM, 2025)

- Source: https://arxiv.org/abs/2503.08842 [accessed:2026-04-28]
- Type: paper
- Mechanism: speaker-attributed input encoding + contrastive learning objective — "implicitly learn[s] contextual coherence and speaker roles without explicit relation annotations."
- Evaluated on Ubuntu IRC + Movie Dialogues.
- Applicability: medium — applies more to multi-party chat than novel scenes, but the speaker-attributed encoding could be reused.
  - Chinese readiness: language-agnostic.

---

### CharacterGLM (Zhou et al., EMNLP 2024)

- Source: https://aclanthology.org/2024.emnlp-industry.107/ (referenced in our search) [accessed:2026-04-28]
- Type: model paper
- Key idea: LLM specifically designed for customized social characters in Chinese contexts; integrates social behaviors + character profiles; uses public historical figure data for fine-tuning.
- Applicability: HIGH for ZH — explicitly Chinese-first; pair with ChatHaruhi for data.
  - adoption cost: medium (model selection)
  - Chinese readiness: native.

---

### ChatHaruhi (Li, Leng et al., 2023-2024)

- Source: https://arxiv.org/abs/2308.09597 ; https://github.com/LC1332/Chat-Haruhi-Suzumiya [accessed:2026-04-28]
- Type: dataset + model
- Key idea: control LMs via improved prompt + memories extracted from scripts; 32 ZH/EN characters, 54k simulated dialogues; **Haruhi-MBTI** = first practical RP benchmark.
- Applicability: high — established ZH-RP ecosystem to draw character data from.
  - adoption cost: low (data reuse)
  - Chinese readiness: native.

---

### MIMIC — Multi-party Dialogue Augmentation via Speaker Stylistic Transfer (EACL 2026)

- Source: https://aclanthology.org/2026.findings-eacl.141.pdf [accessed:2026-04-28]
- Type: paper
- Mechanism: rephrase utterances via speaker stylistic transfer while preserving discourse coherence. MASK metric identifies speakers for replacement; MIRROR picks substitute speakers with similar prior discourse interactions.
- Applicability: medium — could be repurposed to *augment* training data by re-styling dialogue across our character roster.
  - adoption cost: medium (data pipeline)
  - Chinese readiness: language-agnostic technique.

---

## 3. "PerRoleCognition" verdict

**Verdict: "PerRoleCognition" is NOT a real published technique. The name appears to be hallucinated.**

Searches performed:
- `"PerRoleCognition" LLM character roleplay` — returns *no* PerRoleCognition match; only Character-LLM, RoleLLM, CoSER appear.
- `"PerRoleCognition" arxiv` — returns unrelated neuroscience/cognition papers (PMC perception articles, biorxiv neural-network papers).
- `"Per Role Cognition" LLM persona` — returns PersonaLLM workshop, PCL, etc., none containing the literal phrase.
- `"PerRoleCognition" OR "PerRoleAgent" OR "Per-Role-Cognition"` — zero matches for any of the three exact strings.
- `"Role-Cognition Boundary" OR "per role cognition" character LLM` — closest single real match is the RAIDEN-R1 benchmark's "Role-Cognition Boundary" *metric*, and the RPNA paper "Dissecting Role Cognition in Medical LLMs" (arxiv 2510.24677). Neither uses "PerRoleCognition".

What likely happened: the term is plausibly a misremembering or fabrication that blends three real concepts:
- "**Role Cognition**" — used in RPNA paper (arxiv 2510.24677, *Dissecting Role Cognition in Medical LLMs via Neuronal Ablation*) and as the RAIDEN-R1 benchmark metric **Role-Cognition Boundary**.
- "**Per-character**" / "**per-role**" — common prefix in our own design discussions and in CharacterBench's "Boundary Consistency" dimension.
- "**Cognition**" — RPNA's central theme.

So if a prior conversation introduced "PerRoleCognition" as a real technique, that was a hallucination. The *real* line of work that matches what the name implies is the RPNA / RAIDEN-R1 "Role-Cognition Boundary" research — that's worth citing instead. The closest existing system that operationalizes per-role cognition boundaries is **RoleRAG** (2505.18541) with its boundary-aware retriever that explicitly rejects out-of-scope queries.

Recommended replacement vocabulary:
- For "the model maintains separate cognition per character" → use **Role Cognition** (cite RPNA, RAIDEN-R1).
- For "the character refuses to discuss things outside their knowledge" → use **Cognitive Boundary** (cite RoleRAG; CharacterBench Boundary Consistency).
- For "each character thinks differently" → there is no published mechanism that achieves this in one model. RPNA explicitly *disproves* the hypothesis that role prompts induce distinct reasoning paths.

---

## 4. Pattern catalog

### Pattern A — Single-character cards (SillyTavern style)
- **Schema**: V2 card with `description`, `personality`, `scenario`, `first_mes`, `system_prompt`, plus a per-card embedded `character_book` (lorebook).
- **Inference**: keyword-triggered lorebook entries inject into prompt when scan_depth matches recent messages.
- **Strengths**: extremely simple, deployable today; massive ZH community content.
- **Weaknesses**: per-conversation, not designed for multi-character scenes; manual authoring; RPNA shows the prompt alone doesn't change cognition.
- **Refs**: SillyTavern V2 spec, lorebook docs.

### Pattern B — Multi-character knowledge graphs
- **Schema**: entity-disambiguated subject-predicate-object triples with temporal `valid_from`/`valid_to` (like our `knowledge_triples`); boundary-aware retrieval distinguishes "in-scope for character X" vs "out-of-scope, reject."
- **Inference**: per-character query → entity disambiguation → boundary check (reject if out-of-scope) → 1-hop neighborhood retrieval.
- **Strengths**: enforces what character X knows vs Y; reduces hallucination.
- **Weaknesses**: KG construction cost; multi-turn consistency still an open problem (RoleRAG authors admit).
- **Refs**: RoleRAG (2505.18541); SCORE symbolic state (2503.23512); CREFT triple extraction (2505.24553).

### Pattern C — Per-character LLM instance / fine-tune
- **Schema**: each character gets its own model (Character-LLM) or LoRA adapter (CharLoRA).
- **Inference**: route message to character's model.
- **Strengths**: character is in the weights — highest fidelity possible.
- **Weaknesses**: doesn't scale to a 30-char novel; multi-character scenes need orchestration; SFT cost per character.
- **Refs**: Character-LLM (2310.10158); CharacterBot CharLoRA (2502.12988).

### Pattern D — In-context persona prompts (the default)
- **Schema**: system prompt template + character description + recent context.
- **Variants**: basic role prompting, manual-crafted, APO, **rule-based (RRP/CSC)**.
- **Strengths**: zero training cost; instant per-character switch.
- **Weaknesses**: RPNA shows it only changes surface style; "Examining Identity Drift" shows persona prompts don't prevent drift in long conversations; drift starts within 8 turns.
- **Refs**: Talk Less Call Right CSC pattern (2509.00482); RPNA disproof (2510.24677); Identity Drift study (2412.00804); Split-softmax mitigation (2402.10962).

### Pattern E — Emotional weight / relationship matrix
- **Schema**: N×N attitude/affection matrix between characters; per-character emotional state vector (mood, intensity, target).
- **Inference**: matrix conditions tone of dialogue; updates after each scene via extractor agent.
- **Strengths**: maps directly to our LayeredMemory L0 identity + character_memories; gives dialogue *direction* (warm to A, hostile to B).
- **Weaknesses**: matrix grows O(N²); update consistency depends on extractor quality.
- **Refs**: BookWorld dynamic attributes (2504.14538); PsyMem 26 indicators (2505.12814); Emotional RAG (referenced in search); SCORE emotional continuity dimension.

### Pattern F — Drift detection + correction loop
- **Schema**: external monitor (Nautilus Compass style) or in-loop critic checks chapter/turn against persona anchor; fails → retry or flag.
- **Inference**: BGE-m3 embedding cosine against anchor texts; weighted top-k mean as drift score.
- **Strengths**: catches drift our generation already produced; works on black-box models.
- **Weaknesses**: post-hoc, not preventive.
- **Refs**: Nautilus Compass (2605.09863); split-softmax for prevention (2402.10962); our existing Consistency agent fits this pattern.

### Pattern G — Cognize-then-respond / Role-Aware Reasoning
- **Schema**: model emits explicit internal-cognition block before dialogue (situation? what do I know? what do I want?), then produces utterance.
- **Strengths**: forces grounding before generation; matches Stanislavski / Magic-If acting theory.
- **Weaknesses**: token cost; trace may itself drift.
- **Refs**: CogDual (2507.17147); Role-Aware Reasoning RIA+RSO (2506.01748); MRPrompt's Magic-If Protocol (2603.19313).

---

## 5. Comparison: dialogue distinctness mechanisms

| Mechanism | Where it lives | Distinctness signal | Training? | Cost per turn | Maturity | ZH ready | Our verdict |
|-----------|---------------|---------------------|-----------|---------------|----------|----------|-------------|
| Bare persona prompt | system prompt | vocabulary tweak only | none | none | production hobbyist | yes | weakest — RPNA shows it's surface only |
| Character card V2 + lorebook | system prompt + retrieval | keyword-triggered context | none | small | production hobbyist | yes | better than bare prompt, schema worth adopting |
| Rule-Based Role Prompting (CSC) | structured prompt with Voice/Action split | enforced structure | none | small | competition-tested | language-agnostic | quick win; integrate into Writer agent |
| Cognize-then-respond (CogDual/RAR/MRPrompt) | inline reasoning block | per-utterance grounding pre-step | optional SFT | medium (~2x tokens) | research prototype | yes (MRPrompt has ZH) | strong; cheap to prototype |
| Per-character fine-tune (Character-LLM, CharLoRA) | model weights | weight-level character bias | per-character SFT | low | research / single-char | partly | infeasible at 30-char scale |
| Multi-character SFT on book scenes (CoSER, PsyMem) | base model weights | model learns to play multiple chars in scenes | one-shot SFT | low | production-ready open weights | partly | strongest published path; needs ZH data |
| Speaker-attributed encoding (SA-LLM) | input encoding | speaker token embedding influences attn | SFT | low | research | language-agnostic | secondary aid |
| Split-softmax attention reweighting | inference-time attn manipulation | up-weights persona tokens | none | low (compute) | research with code | yes | requires open-weight inference stack |
| KG / boundary-aware retrieval (RoleRAG) | retrieval layer | character knowledge confined | none | medium (KG) | research, ZH-tested | yes | strong for knowledge boundaries; weak for style |
| Drift detection (Nautilus Compass) | post-hoc monitor | embedding sim to anchor | none | very low | production | yes (BGE-m3) | great for QA, not for prevention |
| Emotional/relationship matrix (BookWorld) | state tracker | tone conditioned on N×N matrix | none | low | research with code | yes | natural fit for our LayeredMemory |
| Affective ranking second pass (Character.AI) | post-generation candidate ranking | classifier scores K candidates | classifier train | medium (K-way sampling) | production | language-agnostic | feasible as Consistency agent extension |

---

## 6. Top 3 candidate approaches for our project

The SEQR `dialogue_distinct` weak dim (ρ=−0.16) is a *structural* problem (RPNA + Narrative Flattening), not just a prompt problem. So our top 3 mix prompt-level quick wins with deeper architectural moves.

### Candidate 1 — BookWorld-style role agents + per-character KG + boundary-aware retrieval

Combine **BookWorld's role-agent / world-agent architecture** with **RoleRAG's entity-disambiguated boundary-aware retrieval** and **SCORE's symbolic state Markov tracking**.

- **时效性 (timeliness)**: All three are 2025 papers; BookWorld is ACL 2025; RoleRAG is published; SCORE is 2025. Maximally current research line.
- **鲁棒性 (robustness)**: BookWorld already validates the dual-tier memory pattern; RoleRAG adds explicit out-of-scope rejection; SCORE prevents impossible state transitions (e.g. dead character reappears). Three independent papers triangulating on the same architectural idea = robust signal.
- **可行性 (feasibility)**: Our pipeline already has 6 agents, character_memories, knowledge_triples, ChromaDB. The deltas:
  - Add entity disambiguation pass on knowledge_triples (~1 day).
  - Add boundary-check before retrieval (~2 days; one extra LLM call per query).
  - Add valid_from/valid_to absorbing-state validation in our knowledge graph (already have the schema).
  - Wrap Writer agent into a role-agent prompt with BookWorld's JSON output schema (action_type, target, visibility, narrative).
- **Risk**: Won't directly fix dialogue distinctness — that's Candidate 2's job. This fixes knowledge consistency and per-character cognitive boundaries.

### Candidate 2 — CSC structured prompt + Cognize-then-respond + PsyMem-style 26-vector personas (prompt-only first, SFT later)

Adopt **Talk-Less-Call-Right's CSC (Character-card / Scene-Contract)** schema combined with **MRPrompt's Magic-If protocol** and **PsyMem's 26 psychological indicators** as character attributes — first as pure prompt engineering, then optionally as SFT.

- **时效性**: CSC = Sep 2025; MRPrompt = 2026 preprint; PsyMem = May 2025. All current.
- **鲁棒性**: CSC is *measurably* better than APO (0.571 vs 0.538) in a controlled challenge. MRPrompt's 4 memory abilities (anchor, select, bound, enact) give an explicit pre-generation checklist. PsyMem's 26-vector personas are dense enough to break ties between similar characters — which is exactly what `dialogue_distinct` measures. Combined: enforces structural difference between characters at the prompt level.
- **可行性**: All prompt-level. We can ship in days:
  - Extend our Bible character schema to include the 26 PsyMem indicators (or a subset: Big Five 5 + Schwartz 10 + 3-5 Zimbardo dims = 18-20).
  - Restructure Writer agent prompt: explicit Voice / Action split (CSC), pre-generation Magic-If retrieval ("anchor → select → bound → enact"), psychological-vector dropoff per character.
  - Test on CharacterEval & CharacterBench dimensions.
- **Risk**: RPNA still says prompts only do surface change. Will get us mid-range improvement, not radical fix.

### Candidate 3 — SFT on CoSER-style "given-circumstance acting" with ZH-translated data + measure via CharacterEval, drift-detect via Nautilus-style embedding anchors

Take the **CoSER given-circumstance-acting training objective** (LLMs sequentially portray multiple characters in a scene), translate or generate ZH data analog, fine-tune our base model (Qwen or DeepSeek) with the **PsyMem two-stage memory-alignment objective**. Evaluate against CharacterEval (ZH native) + CharacterBench (bilingual). Add Nautilus-style BGE-m3 anchor drift detection in our Consistency agent.

- **时效性**: CoSER = ICML 2025; PsyMem = May 2025; CharacterEval is the established ZH bench. All current.
- **鲁棒性**: This is the deepest fix because it changes the *weights*, not just the prompts. PsyMem-Qwen at 7B beats GPT-4o + Claude-3.5 on character fidelity — proving that targeted SFT on the right objective is more powerful than scale. Narrative Flattening warns us our base instruction-tuned model is structurally flat; this is the way out.
- **可行性**: Highest cost.
  - Data: ~5k-50k ZH character dialogue scenes; we may need to translate CoSER's 17,966 chars or extract from ChatHaruhi + ZH web fiction.
  - Compute: 7B Qwen2.5 LoRA SFT is days on a single A100.
  - Evaluation infrastructure: CharacterEval is run-ready.
  - This is a 4-8 week investment vs Candidate 1 and 2's 1-2 weeks.
- **Risk**: ZH data construction; potential safety alignment loss if not careful (cf "Too Good to be Bad" — we may need to retain a controlled morality mechanism for antagonist characters).

**Recommended order:** ship Candidate 2 first (1-2 weeks, addresses `dialogue_distinct` at prompt level), Candidate 1 second (knowledge & boundary architecture, parallel implementation), Candidate 3 third as a major investment if results plateau.

---

## 7. Failure-mode catalog (when character consistency breaks)

Empirical failure modes documented in the papers above:

1. **Persona drift over conversation turns** — LLaMA2-chat-70B drops from ~0.8 persona adherence at turn 1 to ~0.4 at turn 8 (Li/Kenneth 2024). Larger models drift *more*, not less (Identity Drift study).
2. **Memory contradictions** — most common Characterization error per ConStory-Bench. Includes "knowledge contradictions", "skill fluctuations", "forgotten abilities."
3. **Cognitive boundary violation** — character knows something they shouldn't (no per-character knowledge isolation); RoleRAG specifically targets this.
4. **Helpful-assistant voice leakage** — "助手音" is documented as "the #1 enemy of RP-LLMs" — moralizing, breaking character to refuse (Chinese RP-LLM analysis CSDN post; "Too Good to be Bad" arxiv 2511.04962).
5. **Villain alignment collapse** — LLMs fail to authentically portray malicious characters because safety training overrides character ("Too Good to be Bad").
6. **Style flattening** — after post-training, models converge to a narrow default style (Narrative Flattening 2605.27878). Affects `dialogue_distinct`.
7. **Mid-narrative error concentration** — errors cluster mid-text and at high-entropy segments (ConStory-Bench).
8. **Character resurrection / state violation** — items/characters in absorbing states (dead, destroyed) spontaneously return; SCORE flags this.
9. **Cross-character knowledge bleed** — char X demonstrates knowledge only char Y has; CharacterBench's "Boundary Consistency" metric.
10. **Attention diversion** — when characters share screen time, attention is split across personas; Role-Aware Reasoning RIA targets this.
11. **Surface style without distinct cognition** — RPNA neuronal ablation shows prompt-induced personas use the same reasoning circuit. This is the structural cap on prompt-only methods.

---

## 8. Open questions

1. **Does explicit Mandarin-Chinese stylistic differentiation (formality 等级, 古文 vs 白话, dialect markers) survive base-model post-training flattening?** Narrative Flattening was demonstrated on English (OLMo). We have no published ZH replication. This directly affects our `dialogue_distinct` weak dim.

2. **Is there a Chinese equivalent of CoSER / PsyMem datasets we can build on without translating English-canon characters?** ChatHaruhi (32 chars) + CharacterEval (77 chars) + CharacterGLM data is the closest, but none reach CoSER's 17,966 char scale.

3. **Can split-softmax (Li 2024) be approximated via prompt-only attention bias hints (e.g. attention sink tokens, "remember you are X" inserts)?** No paper we found tests this in a prompt-only setting. Worth a controlled ablation.

4. **For our SEQR ρ=−0.16 `dialogue_distinct`, is the limiting factor the model or our evaluation?** The CharacterBench paper notes "Attribute Consistency" and "Behavior Consistency" are sparse dimensions that require targeted queries. Our metric may not even be measuring distinctness on the right cue distribution.

5. **Does the PsyMem two-stage SFT objective transfer cleanly to Chinese?** PsyMem uses Qwen2.5-7B-Instruct as base (ZH-friendly), and includes "diverse genres" novels — but the paper doesn't isolate ZH performance. Worth replicating.

6. **What's the right "scene-contract" granularity for novel-length output?** Talk-Less-Call-Right is for tool-using agents with short turns. Adapting CSC to chapter-length output requires defining what "Voice" and "Action" mean at scene granularity. No published work yet.

7. **How does affective ranking (Character.AI) interact with per-character distinctness?** A second-pass classifier ranks candidate replies for emotional appropriateness. For multi-character novels we'd need K candidates per speaking turn — expensive. Is there a single-pass approximation?

8. **For Chinese antagonist characters, does safety-alignment morality leakage manifest as different lexical fingerprints we can detect?** ("Too Good to be Bad" only studied English models.) If yes, this is a measurable QA signal.

9. **Can we measure dialogue distinctness with a "bootstrap distinctiveness" metric per character pair?** The "From stage to page" paper (arxiv 2301.05659) proposed language-independent bootstrap measures of distinctiveness in fictional speech. We couldn't decode the PDF in this sweep; worth a follow-up read. URL: https://arxiv.org/pdf/2301.05659.

10. **Is RPNA's neuronal-ablation finding (prompts don't change cognition) negated by methods like Character-LLM that actually fine-tune?** No paper yet runs RPNA-style ablation on a Character-LLM-trained model to verify it forms distinct circuits. This is the cleanest experiment to settle "training vs prompting" for character cognition.

---

## Sources index (all URLs accessed 2026-04-28)

Foundational / Surveys:
- https://arxiv.org/abs/2310.10158 — Character-LLM
- https://arxiv.org/abs/2310.00746 — RoleLLM
- https://github.com/Neph0s/awesome-llm-role-playing-with-persona — curated survey list

Methods (training-time):
- https://arxiv.org/abs/2502.09082 — CoSER
- https://arxiv.org/abs/2505.12814 — PsyMem
- https://arxiv.org/abs/2501.15427 — OpenCharacter
- https://arxiv.org/abs/2503.17662 — PCL (Persona-Aware Contrastive Learning)
- https://arxiv.org/abs/2505.10218 — RAIDEN-R1
- https://arxiv.org/abs/2507.17147 — CogDual
- https://arxiv.org/pdf/2506.01748 — RIA+RSO Role-Aware Reasoning
- https://arxiv.org/abs/2502.12988 — CharacterBot (Lu Xun, CharLoRA)
- https://huggingface.co/PygmalionAI/Pygmalion-3-12B — Pygmalion-3
- https://mistral.ai/news/mistral-nemo — Mistral NeMo base

Inference-time / drift:
- https://arxiv.org/abs/2402.10962 + https://github.com/likenneth/persona_drift — Split-softmax
- https://arxiv.org/abs/2412.00804 — Identity Drift study
- https://arxiv.org/abs/2605.09863v1 — Nautilus Compass drift detection
- https://arxiv.org/abs/2510.24677 — RPNA (neuronal ablation, key disproof of prompt-induced cognition)
- https://arxiv.org/abs/2605.27878 — Narrative Flattening (post-training compression)

Retrieval / memory / KG:
- https://arxiv.org/abs/2505.18541 — RoleRAG (boundary-aware retrieval)
- https://arxiv.org/abs/2603.19313 — MREval/MRPrompt
- https://arxiv.org/abs/2503.23512 — SCORE
- https://arxiv.org/pdf/2505.24553 — CREFT

Multi-agent / story:
- https://arxiv.org/abs/2504.14538 + https://bookworld2025.github.io/ — BookWorld
- https://arxiv.org/abs/2507.05820 — Constella

Benchmarks:
- https://arxiv.org/abs/2401.01275 + https://aclanthology.org/2024.acl-long.638/ — CharacterEval (ZH)
- https://arxiv.org/abs/2412.11912 — CharacterBench (bilingual, 11 dims)
- https://arxiv.org/abs/2310.17976 + https://incharacter.github.io/ — InCharacter
- https://arxiv.org/pdf/2503.23514 — LifeState-Bench
- https://arxiv.org/abs/2603.05890 — ConStory-Bench (5×19 taxonomy)

Prompt engineering:
- https://arxiv.org/abs/2509.00482 — Talk Less Call Right / RRP / CSC
- https://github.com/malfoyslastname/character-card-spec-v2 — SillyTavern V2
- https://docs.sillytavern.app/usage/core-concepts/personas/ — Personas
- https://docs.sillytavern.app/usage/core-concepts/worldinfo/ — World Info / Lorebook

Production architecture:
- https://blog.character.ai/optimizing-ai-inference-at-character-ai-2/ — Character.AI inference
- https://blog.character.ai/news/research/ — research blog index
- https://arxiv.org/html/2409.15012v1 — MixAttention

Chinese-specific:
- https://github.com/LC1332/Chat-Haruhi-Suzumiya + https://arxiv.org/abs/2308.09597 — ChatHaruhi
- CharacterGLM (referenced in our search, EMNLP 2024)

Multi-party dialogue distinctness:
- https://arxiv.org/abs/2503.08842 — SA-LLM (speaker-attributed contrastive)
- https://aclanthology.org/2026.findings-eacl.141.pdf — MIMIC stylistic transfer
- https://arxiv.org/pdf/2301.05659 — bootstrap distinctiveness measures

Failure modes:
- https://arxiv.org/abs/2511.04962 — "Too Good to be Bad" (villain failure)
