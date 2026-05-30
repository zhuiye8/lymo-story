# Novel System Survey · Pre-Phase-1 Research

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Started | 2026-04-28 |
| Purpose | 为 Phase 1 重构提供"先调研后设计"的实证基础。不兼容 Phase 0 旧数据，全部从零设计。 |
| Status | in-progress |
| Audit goal | 每条 finding 必须有 source URL + accessed-date + 关键引文，可被监督独立 reproduce |

## Scope（用户 2026-04-28 确认）

按 user-stated 优先级：**记忆 = 角色 = 大纲 > 图谱**；P0 = P1 同等深度；R4（开源项目）放最前作为 R1/R2/R5 的实战参考。

## 调研清单

| Tier | 编号 | 方向 | 状态 | 文件 |
|---|---|---|---|---|
| S | R4 | 现有开源小说生成项目 | ✅ done | [r4-open-source.md](r4-open-source.md) |
| S | R1 | 大纲 / 剧情结构生成 | ✅ done | [r1-outline.md](r1-outline.md) |
| S | R2 | 长程记忆系统 | ✅ done | [r2-memory.md](r2-memory.md) |
| S | R5 | 角色扮演 / 角色一致性 | ✅ done | [r5-character.md](r5-character.md) |
| A | R10 | Structured LLM I/O | ✅ done | [r10-structured-io.md](r10-structured-io.md) |
| A | R6 | Anti-slop / 文笔质量 | ✅ done | [r6-anti-slop.md](r6-anti-slop.md) |
| B | R3 | 图谱管理 | ✅ done | [r3-graph.md](r3-graph.md) |
| B | R9 | 中文网文专属 | ✅ done | [r9-chinese.md](r9-chinese.md) |
| C | R7 | Agent 编排（confirm） | ✅ done | [r7-r8-light.md](r7-r8-light.md) |
| C | R8 | 商业工具（脚注） | ✅ done | [r7-r8-light.md](r7-r8-light.md) |

## 调研约束（自我约束）

1. **不凭训练记忆**：任何 claim 必须有 URL + accessed-date。如果只能凭记忆，必须标 `[memory:unverified]` 并说明无法找到 source 的原因。
2. **时效性**：每个 repo/paper 标 `last_commit` 或 `published` 日期；超过 18 个月没动的标 `[stale]`。
3. **鲁棒性**：区分 toy demo / research prototype / production-grade；星数、issue 活跃度、test coverage 都要看。
4. **可行性**：每条都问"我们能不能抄？要重写多少？" —— 给一个 `adoption_cost: low/medium/high/rewrite` 标签。
5. **结构化输出**：每个方向独立一份 md 文件；内有 finding list + 综合判断。

## 文件清单

- `00-summary.md`（本文件）：执行综合 + 推荐架构草图（待 R1-R5 完成后回填）
- `r1-outline.md`：大纲生成（sub-agent 写）
- `r2-memory.md`：长程记忆（sub-agent 写）
- `r4-open-source.md`：开源项目深扒（sub-agent 写）
- `r5-character.md`：角色一致性（sub-agent 写）
- `r10-structured-io.md`：DSPy/Outlines/Instructor（engineer 写）
- `r6-anti-slop.md`：anti-slop（待）
- `r3-graph.md`：图谱（待）
- `r9-chinese.md`：中文专属（待）
- `r7-r8-light.md`：编排 + 商业（待）

## Verification protocol

每个 sub-agent 报告回来后，engineer 抽样 spot-verify：随机挑 3 条 finding，用 WebFetch 重新拉源 URL，确认引文/数据吻合。Spot-verify 结果 append 到本文件 §"Verification log"。

## Verification log

### 2026-04-28 spot-verify batch 1（R4/R1/R2/R5 sub-agent claims）

| 待验 claim | 来源 agent | engineer 独立 verify 路径 | 结果 |
|---|---|---|---|
| "PerRoleCognition" 是工程师之前瞎编的名字（不在任何 paper 里） | R5 | WebSearch `"PerRoleCognition" LLM character roleplay` 2026-04-28 | ✅ **CONFIRMED hallucinated**。0 result 含字面字符串，只返回 Character-LLM/CoSER 等真实相关 paper。 |
| MemGPT 改名为 Letta；Letta 是 framework，MemGPT 现指 design pattern | R2 | WebFetch `https://github.com/letta-ai/letta` 2026-04-28 | ✅ **CONFIRMED**。README 顶部明写 "Letta (formerly MemGPT)"；v0.16.8（2026-05-14 发布）；23k stars；Apache-2.0。 |
| WebNovelBench 8 维度（verbatim 列出，修正之前的 hallucination） | R1+R4 | WebFetch `https://arxiv.org/html/2505.14818v1` 表 1 | ✅ **CONFIRMED verbatim**。D1 Use of Literary Devices / D2 Richness of Sensory Detail / D3 Balance of Character Presence / D4 Distinctiveness of Character Dialogue / D5 Consistency of Characterisation / D6 Atmospheric and Thematic Alignment / D7 Contextual Appropriateness / D8 Scene-to-Scene Coherence。 |
| DOME 用四元组 `<subject, action, object, chapter_index>` 存 TKG；outline 用 rough(5)→detailed(M=3) | R1+R2 | WebFetch `https://arxiv.org/html/2412.13575v1` | ✅ **CONFIRMED verbatim**。"TKG is stored by quadruples in the form of <subject, action, object, index>" + "the hierarchical outline H={R,D}" + Joseph Campbell hero's journey 5 阶段。 |

**Conclusion**: 4/4 抽样通过，4 个 sub-agent 报告的 finding 可信度高。继续 R10 / R6 / R3 / R9 / R7+R8。

---

# 综合 finding（cross-direction synthesis）

## A. 五条最高优先级 finding（按可行性 × 影响力排）

1. **DOME 四元组 `<subject, action, object, chapter_index>` 与我们 Phase 0 `knowledge_triples` 几乎完全匹配**（R1+R2+R3 spot-verified）
   - 我们 zero-cost 升级到 SOTA 学术 schema
   - 还可顺手加 outline 层（rough 5 hero's-journey + detailed M=3 per stage）

2. **Phase 0 dialogue_distinct ρ=−0.16 真凶找到**（R5）
   - **RPNA 论文（arxiv 2510.24677）**：神经元 ablation 证明 prompt 只改 surface style，不改 cognitive process
   - **Narrative Flattening 论文**：post-training 反而 collapse 风格方差
   - **结论**：单纯改 prompt 治不了；要 SFT-level 干预（**FTPO 或 LoRA tuned model**），Phase 1 用 prompt 缓解，Phase 3+ 上 FTPO

3. **MemoryOS（中文原生，EMNLP 2025 Oral）+ Mem0 + Graphiti embedded 是 R2 三件套** —— 三选一不如三协同
   - MemoryOS = primary architecture（STM/MTM/LPM 与我们 LayeredMemory 同构）
   - Mem0 = 多信号检索层（ADD-only single-pass，**94.8% LongMemEval / 91.6% LoCoMo**）
   - Graphiti embedded（Kuzu）= 双时态 world state（**Apache-2.0 + 26.7k stars**）

4. **DeepSeek V4-Pro 在中文文笔评分上未必最强**（R9）
   - GLM-5.1 / Kimi K2.6 在中文语言 5⭐；DeepSeek 在代码 5⭐
   - **Phase 1 应做 model A/B 矩阵实测**（DeepSeek vs Kimi vs GLM × 题材 × SEQR）

5. **Antislop ICLR 2026（Paech 等）= anti-slop 决定性 SOTA**
   - 我们 Phase 0 slop_detector v0/v1 → autonovel port → 已对齐 ANTISLOP 的 Sampler 思路
   - Sampler / FTPO 需要自托管 LLM（DeepSeek API 不行）
   - 但**slop-forensics 中文化** 是 Phase 1 可立即开工的窗口（1 工作日）

## B. 工程师的 5 个"事实确认"

| 之前的 claim / 假设 | 调研结果 | 行动 |
|---|---|---|
| "PerRoleCognition" 是已发表技术 | **❌ 完全瞎编**（R5 + WebSearch double-verified）| 从 Phase 1 plan 删除该词；改用 RoleRAG (boundary-aware retrieval) 或 PsyMem |
| WebNovelBench 8 维度 = 我们曾误写的 fluency/vocab/plot/character/dialogue/theme/innovation/overall | **❌**；真正 8 维度已 verbatim 验证 | SEQR Phase 1 重命名对齐 WebNovelBench |
| MemGPT 是 active 项目 | **改名 Letta**（2024-09），现 v0.16.8 Apache-2.0 23k stars | 引用名称统一为 Letta |
| autonovel 可直接 fork 用 | **无 LICENSE 文件** + 6+ 顶星 OSS 同样问题 | 已 Phase 0 自己 port；继续这条路 |
| DeepSeek 是 Chinese-novel 最强 | **代码强 / 文笔仅 ⭐⭐⭐⭐**；Kimi 和 GLM 是 ⭐⭐⭐⭐⭐ | Phase 1 做 model A/B 矩阵 |

## C. Phase 1 推荐架构（基于 R1-R10 综合）

> 这是基于全部调研的**初稿草图**；具体 schema 在 Phase 1 proposal 详化。

```
┌─ Outline Layer ─────────────────────────────────────────────────┐
│  ConceptAgent  →  WorldBuilder  →  CharacterDesigner            │
│                ↓                                                  │
│   OutlinePlanner with DOME hierarchy + 34 中文 narrative func    │
│   (rough 5 stages [Joseph Campbell] + detailed M=3 per stage)   │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─ Generation Loop (LangGraph) ───────────────────────────────────┐
│  load_context → world_advance → plot_plan → camera_decide       │
│         ↓                                                         │
│  load_memories (MemoryOS STM/MTM/LPM)                            │
│         ↓                                                         │
│  write_chapter (Instructor-wrapped DeepSeek/Kimi/GLM)            │
│         ↓                                                         │
│  consistency_check + anti-slop pass (detector v1.1 +             │
│      prompt-level negative instructions)                         │
│         ↓ (pass)              ↓ (fail)                            │
│  extract_memories             retry up to 3                      │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─ Storage ───────────────────────────────────────────────────────┐
│  SQLite (story_bible, chapters, knowledge_triples=DOME 4-tuple) │
│  ChromaDB (semantic memory)                                      │
│  +「Codex」UI 组织（Novelcrafter pattern）                       │
└─────────────────────────────────────────────────────────────────┘
```

**关键架构决定**：

| 决定 | 来源 | 备注 |
|---|---|---|
| **保留 LangGraph** | R7 | 监督已批；2026 仍最佳（62% 复杂任务） |
| **Instructor 替换手写 JSON** | R10 | 零 agent 层改动 |
| **Init pipeline 拆成 4 agent**（Concept/WorldBuilder/CharacterDesigner/OutlinePlanner） | R4（与已有 plan `reactive-wandering-floyd.md` 一致）+ R1 + 阅文妙笔 4 件套 | 之前已在 plan 模式提过 |
| **OutlinePlanner 采用 DOME 双层 + 34 中文 func tagging** | R1 + R9 | 34 functions 待 follow-up fetch |
| **knowledge_triples 升级到 DOME quadruple** | R3 | 改 valid_from → chapter_index |
| **MemoryOS 替换我们当前 LayeredMemory** | R2 | EMNLP 2025 Oral，中文 native |
| **Model A/B 矩阵**（DeepSeek vs Kimi vs GLM × 题材） | R9 | 不预设 DeepSeek 最优 |
| **slop_detector v1.1 frequency-aware + slop-forensics 中文化** | R6 | Phase 0 backlog 兑现 |
| **prompt 层 anti-slop 负指令** | R6 | Two-Layer Validator 模式 |
| **FTPO / Antislop Sampler 列 Phase 3+ backlog** | R6 | 需自托管 LLM |
| **CREFT 反向抽取 + EvolvTrip ToM 列 Phase 2+ backlog** | R3 + R5 | 角色心理嵌套 |

## D. Open questions（监督决策点）

1. **Phase 1 vs Phase 0 数据兼容性**：用户已说"不兼容旧数据，全部从 0 开始" — 是不是要 archive `data/story.db` 为 `data/story.db.archive_pre_phase_1_<date>`，新建 empty DB？
2. **Phase 1 model 选型**：A/B 矩阵跑出来谁赢就用谁，还是先固定 Kimi K2.6 作为 default（中文 ⭐⭐⭐⭐⭐ + 200k context）？
3. **34 narrative functions 拉取**：需要 PDF 解析工具（如 pypdf）抽 arxiv 2603.14430 的 Appendix；要不要工程师做这步？
4. **Phase 1 proposal 时机**：等 AC2-final 完成 + Phase 0 收口报告再提，还是现在就提 Phase 1 proposal 让监督评？
5. **Phase 1 范围裁剪**：本调研画了大蓝图（Init 拆分 + DOME + MemoryOS + Instructor + slop v1.1 + anti-slop prompt + model A/B + Codex UI），单个 Phase 1 做不完。建议**Phase 1 切成 Phase 1A / 1B / 1C**？

## E. Verification log（已 spot-verified 4/4 batch 1）

见上文。

## F. 后续 actions for engineer（待用户决议）

| # | Action | 触发条件 | 估时 |
|---|---|---|---|
| 1 | 整理 Phase 1 proposal 草案，把本 summary 的 §C 架构 + §D open questions 写成正式提案 | 用户/监督批准方向 | 2-4 hr |
| 2 | PDF 解析提取 arxiv 2603.14430 的 34 narrative functions 列表 | 用户同意 | 1 hr |
| 3 | Model A/B 矩阵脚本（5 章 × 3 model × 2 题材 = 30 chapter generations，SEQR 评分） | 用户同意 + 预算 ¥30-50 | 0.5 d |
| 4 | slop-forensics 中文化（jieba 替换 NLTK） | 用户同意 | 1 d |
| 5 | MemoryOS / Mem0 / Graphiti embedded 单元 PoC（不动 storage 主线，单独 demo） | Phase 1 立项后 | 1-2 d 每个 |


