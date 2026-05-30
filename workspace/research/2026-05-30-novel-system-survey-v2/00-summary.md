# 中文小说生成系统调研 v2 — 总综合

> 调研批次：2026-05-30-novel-system-survey-v2
> 用户优先级锚定：**记忆(R2) = 角色(R5) = 大纲(R1) > 图谱(R3)**；其余为辅助/借鉴档
> 现有系统基线：六-agent（Director/World/Planner/Camera/Writer/Consistency）+ LangGraph + FastAPI + SQLite + ChromaDB + LiteLLM，纯 prompt 驱动，中文连载小说
> 所有 finding 均带 URL + [accessed:2026-05-30] + 时效性/鲁棒性/可行性三标签（详见各方向 v2 终稿）

---

## 1. 调研清单表（9 方向状态）

| 方向 | 主题 | 优先级档 | 状态 | 一句话结论 |
|------|------|---------|------|-----------|
| **R2** | 长期记忆 | **S（最高）** | ✅ 终稿 | 没有开箱即用的开源记忆系统（主流面向对话 agent）；把已验证机制组合进现有 LayeredMemory + KnowledgeGraph |
| **R5** | 角色扮演/一致性 | **S（最高）** | ✅ 终稿 | 角色一致性是谱系四档问题；纯 prompt 对对白区分度有**结构性上限**（RPNA 机理证明），①结构化角色卡+③知识边界检索性价比最高 |
| **R1** | 大纲/剧情结构 | **S（最高）** | ✅ 终稿 | 主架构 = DOME 双层动态大纲 + 时序四元组记忆；叠加 LongWriter 字数预算、相似度阈值触发反转、Propp-34 抗同质化 |
| **R10** | 结构化 LLM I/O | **A** | ✅ 终稿 | Phase 1 选 Instructor（`from_litellm` 零改造）、Phase 1.5 escape hatch 选 BAML；DeepSeek 无 json_schema → 约束解码对远端 API 无效，真问题是 robust parsing + reask |
| **R6** | Anti-slop/文笔质量 | **A** | ✅ 终稿 | 英文 anti-slop 生态成熟、中文几乎零开源词表；主路径 = 生成后检测（自建中文 slop 词表）→ 触发重写 → 异源去偏 Critic Room（严禁 DeepSeek 自评） |
| **R3** | 图谱管理 | **B** | ✅ 终稿 | 全量 KG + 图数据库 + GraphRAG 对本系统是**负 ROI**；只取退化形态——DOME 式按章号四元组事实表，SQLite 零新基础设施落地 |
| **R9** | 中文网文专属 | **B** | ✅ 终稿 | 选型 + 评测 + 题材模板三件事；最高 ROI = WebNovelBench 8 维 + EQ-Bench 三指标合成中文质量门禁，补强 consistency_check 不查文笔退化的缺口 |
| **R7** | Agent 编排框架决策 | **C（light）** | ✅ 终稿 | 维持 LangGraph 是对的且比 v1 更有把握；**固定 DAG 最优、不引入 supervisor/swarm 动态路由** |
| **R8** | 同类产品借鉴 | **C（light）** | ✅ 终稿 | 最高 ROI 在工程层：NovelAI Lorebook 注入机制 → L2、Novelcrafter Codex/Progressions → KnowledgeGraph；UI 层（Sudowrite）点到为止 |

**完成度：9/9 终稿全部写出。** 文件位于本目录 `r2-memory.md` / `r5-character.md` / `r1-outline.md` / `r4-open-source.md` / `r10-structured-io.md` / `r6-anti-slop.md` / `r3-graph.md` / `r9-chinese.md` / `r7-r8-light.md`。
（注：R4 开源项目调研并入清单作为移植源支撑 R1/R2/R5；上表 9 行对应 9 个终稿文件，R4 见第 2 节移植落地。）

---

## 2. 跨方向 5 大最高优先 finding

按用户优先级（记忆=角色=大纲）排序，每条标注涉及方向、可落地动作、关键约束。

### Finding 1 ⭐ 纯 prompt 对「角色对白区分度」有结构性上限——这是 SEQR 弱维的机理级解释
**方向：R5（主）× R2 × R3**
- **证据**：RPNA 神经元消融研究（arXiv:2510.24677）证明角色 prompt 只改表层措辞、不改底层推理通路——所有角色接到**同一回路**。这直接解释了项目 SEQR `dialogue_distinct` 弱维（rho = −0.16）。Narrative Flattening 进一步证明：基座越 post-trained 越扁平，SFT 是扁平化病因之一。
- **落地动作**：短期用 ①结构化角色卡 + 硬约束 prompt + ③RoleRAG/TimeChara 知识边界护栏（复用 KnowledgeGraph 的 `valid_from`/`valid_to`）把上限内的空间吃满；评测用 CharacterEval（中文底座，repo 已核实）+ 去标签说话人识别（PersonaEval 思路）。
- **关键约束/决议点**：**要真正突破对白区分度上限，必须三选一——换扁平化更轻的基座 / 解码期干预（split-softmax，需开源模型）/ SFT。** 三条都要求脱离"纯远端 API + 纯 prompt"，是重大架构决策，留给用户拍板（见 §5）。

### Finding 2 ⭐ 把"按章号四元组事实表"作为记忆与图谱的共同地基（抄思想、不引框架）
**方向：R2 × R3 × R1（三方向交汇）**
- **证据**：DOME（NAACL 2025 Long，2412.13575）的 `<主体,谓词,客体,章号>` 四元组 + `valid_from`/`valid_to` 有效区间，消融证据显示其对长程一致性是**刚需**（冲突率 0.56% → 4.52% 当去掉它；在 Qwen 上验证、中文现成）。Graphiti 的 bi-temporal「invalidate-not-delete」机制可借（只借机制，不引 Neo4j）。
- **落地动作**：升级现有 `knowledge_triples` 表，每条加**章号 index**；事实失效用有效区间标记而非物理删除；在现有 SQLite 上即可实现，**零新基础设施**。回填了 v1 三个 open question（R2 章号缺失/无法回溯、R5 belief 随章演化、R1 转折自动生成）。
- **关键约束**：**不要图数据库、不要全量 GraphRAG**（R3 验证为负 ROI）；DOME 官方 repo 虽存 Neo4j，但那只是逻辑视图、不等于必须图数据库。图数据库只在将来做 reader 端全书问答时才考虑（届时选 LightRAG/LazyGraphRAG，不选原版 GraphRAG）。

### Finding 3 ⭐ 大纲主架构 = DOME 双层动态大纲 + 三处增量
**方向：R1（主）× R2**
- **证据**：演进链 Re3(2022) → DOC(2023) → DOME(2025) → KG+文学理论(2508.03137, 2025-08) 已确认。
- **落地动作（主架构 + 三增量）**：
  1. 主架构：DOME 双层动态大纲 + 时序四元组记忆（与 Finding 2 共用地基）；
  2. 长输出地基：LongWriter/AgentWrite（2408.07055）的「字数预算 plan → 逐段填充」升为一级方案；
  3. 低成本防平淡：2508.03137 的「大纲相似度阈值触发反转」信号；
  4. 抗同质化武器：Propp-34（2603.14430）中文叙事功能标签。
- **工程参考**：oh-story-claudecode（全书→卷纲→细纲→章节，1.7k★ 极活跃）是最贴近的中文实践参考。
- **关键约束**：⚠️ **v1 给出的 Expansion-Ratio 具体数值（R=0.01/α₁=0.05/α₂=0.20）经一手验真无法核实，v2 已降级、明确禁止当默认配置**，只保留"存在最优压缩-扩展比"的定性结论。

### Finding 4 ⭐ 把 WebNovelBench 8 维 + EQ-Bench 三指标合成"中文章节质量门禁"
**方向：R9 × R6 × R5（评测层枢纽）**
- **证据**：现有 `consistency_check` 只查一致性、**不查文笔退化**——这是质量层最大缺口。WebNovelBench 8 维量表（2505.14818，人设一致性权重最高 0.1377，已逐字核验）+ EQ-Bench 的 slop/repetition/degradation 三指标可补强。
- **8 维（已核实）**：Use of Literary Devices / Richness of Sensory Detail / Balance of Character Presence / Distinctiveness of Character Dialogue / Consistency of Characterisation / Atmospheric and Thematic Alignment / Contextual Appropriateness / Scene-to-Scene Coherence。其中 `Distinctiveness of Character Dialogue` + `Consistency of Characterisation` 两维直对 SEQR `dialogue_distinct`，锁定为 R5 rubric。
- **落地动作**：全 training-free，可直接进 CI；评测集建议复用项目 SEQR 基线，自建中文小说连续性测试集。
- **关键约束/许可**：⚠️ **WebNovelBench 数据集 CC-BY-NC-SA 非商用、Creative Convergence 配套数据 repo 已失效**——两者均"借方法不借资产"，词表/数据必须本土自建。

### Finding 5 ⭐ 结构化输出选 Instructor（不选约束解码），且判官必须与生成模型异源
**方向：R10 × R6（工程护栏）**
- **证据（R10）**：DeepSeek 无 final-message `json_schema`（官方文档 + LiteLLM issue 7580 双证，closed not planned），beta strict 工具调用有未修 bug（issue 1069，closed not planned）→ **约束解码路线（Outlines/Guidance）对远端 API 无效**。真问题是 robust parsing + reask，正是 Instructor 强项，可经官方 `instructor.from_litellm(litellm.completion)` **零改造** patch 现有 LiteLLM gateway/Router，且与 LangGraph 完全正交。
- **证据（R6）**：自偏好偏置研究 + 文笔实测表明，**Critic Room 判官须用与生成模型异源的高文笔模型（Kimi K2.6/Claude，Qwen 本地备选），严禁 DeepSeek 自评**。
- **落地动作**：按用户优先级，Director（Bible→大纲）、Planner（beats）、ChapterExtractor（记忆+角色）优先包 Instructor；Writer 保持 `_call_text()` 不动。DeepSeek 支持 logprobs 但文档未列 logit_bias → Sampler/FTPO 本地 logits 回溯路线不可行，R6 主路径为"生成后检测 + 重写"。

---

## 3. Phase 1 推荐架构草图

> 原则：**抄思想、不引框架**；零新基础设施优先；记忆/角色/大纲先行，图谱退化为事实表，质量层补门禁。

```
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 1 增量（叠加在现有六-agent + LangGraph 固定 DAG 之上）              │
└─────────────────────────────────────────────────────────────────────┘

【编排层】 R7 → 维持 LangGraph 固定 DAG，不引入 supervisor/swarm 动态路由
          （durable execution / checkpoint / HITL / 循环图 正好命中章节重试循环）

【结构化 I/O 层】 R10 → instructor.from_litellm() patch 现有 LiteLLM gateway
          ├─ Director  (Bible→大纲)      ┐
          ├─ Planner   (beats)           ├─ 优先包 Instructor（喂养 S 档）
          └─ ChapterExtractor (记忆+角色)  ┘
          └─ Writer 保持 _call_text() 纯文本不动
          主路径：Tools/MD_JSON + Pydantic 校验 + reask 自愈（strict 不可作保险）

【记忆 + 图谱共同地基】 R2 × R3 → SQLite 内升级，零新基础设施
          knowledge_triples 表 → 加章号 index：<主体,谓词,客体,章号>
                              → 加 valid_from / valid_to 有效区间（invalidate-not-delete）
          LayeredMemory L0-L3 保留 → 叠加 Generative Agents 公式
                              (recency=章节距离, importance=保护伏笔, relevance)
          ✗ 不引图数据库 / 不引全量 GraphRAG（负 ROI）

【角色一致性层】 R5 → ①结构化角色卡 + ③知识边界检索（training-free 先行）
          复用 KnowledgeGraph valid_from/valid_to 做 RoleRAG/TimeChara 护栏
          评测：CharacterEval(中文) + 去标签说话人识别 + persona 自洽三指标
          ⚠ 突破对白区分度上限需换基座/解码干预/SFT —— 留 Phase 2 决议

【大纲层】 R1 → DOME 双层动态大纲 + 时序四元组（与记忆地基共用）
          + LongWriter 字数预算 plan→逐段填充
          + 相似度阈值触发反转（防平淡）
          + Propp-34 中文叙事功能标签（抗同质化）
          ✗ 禁用 v1 未核实的 Expansion-Ratio 数值作默认配置

【质量门禁层】 R6 × R9 → 补强 consistency_check（当前只查一致性、不查文笔退化）
          中文 slop 词表（自建，移植 autonovel evaluate.py）+ 正则 → 触发重写
          → 异源去偏 Critic Room（Kimi K2.6/Claude 判官，严禁 DeepSeek 自评）
          rubric = autonovel 四维 ∪ WebNovelBench 八维，全 training-free 进 CI

【模型绑定层】 → per-agent 模型绑定（复用现有 ModelRegistry）
          Writer 首选 Kimi K2.6（中文创意写作双榜第一）/ Qwen3 大杯
          推理/结构类 → DeepSeek V4-Pro（性价比 + 知识强，文笔弱）
          Critic 判官 → 必须异源高文笔模型（Kimi/Claude）
          换模型时 R10 约束 + R6 判官选型需重核

【移植源】 R4 → 🥇 tyxben/AI_novel（MIT、同栈、原生中文）逐组件移植：
          LedgerStore / PrevTailSummarizer / StyleBible / MilestoneTracker
          🥈 NousResearch/autonovel（只读方法论 ANTI-SLOP/CRAFT/PIPELINE）
          架构缺口诊断：现六-agent 缺「卷级层」+「显式 ledger 聚合层」两块

【借鉴规格】 R8 → NovelAI Lorebook（关键词命中+Insertion Order+Token Budget）→ L2 注入
          Novelcrafter Codex（自动别名链接+RAG 注入+Progressions 时序覆盖）→ KnowledgeGraph
```

**Phase 1 优先级落地顺序（按用户锚定）：**
1. **记忆地基**（R2×R3 四元组 + 章号 + 有效区间，SQLite 内）——同时服务记忆/角色/大纲三个 S 档；
2. **结构化 I/O**（R10 Instructor patch）——Director/Planner/ChapterExtractor 喂养 S 档；
3. **大纲主架构**（R1 DOME 双层 + LongWriter）；
4. **角色护栏**（R5 角色卡 + 知识边界检索，training-free）；
5. **质量门禁**（R6×R9 中文 slop 检测 + 异源 Critic Room）。

**Phase 1.5 / Phase 2 决议项**：结构化输出 escape hatch（BAML）；角色对白区分度突破（换基座/解码干预/SFT，需开源模型）；reader 端全书问答（届时才上 LightRAG）。

---

## 4. 三项基础核查结论

| 核查项 | 结论 | 处置 |
|--------|------|------|
| **PerRoleCognition** | **杜撰**。arXiv / Google Scholar / 全网均无此发表文献。 | 全方向**禁用**。遇到即视为幻觉。真实近邻：**RPNA**（arXiv:2510.24677，神经元消融）/ **RoleRAG**（2505.18541，图引导检索增强）/ **Character-LLM**（2310.10158，EMNLP 2023 可训练角色 agent）。R5/R3 改引这三项。 |
| **WebNovelBench 8 维** | **已逐字核实**（arXiv:2505.14818 Table 1）。 | 8 维 = Use of Literary Devices / Richness of Sensory Detail / Balance of Character Presence / Distinctiveness of Character Dialogue / Consistency of Characterisation / Atmospheric and Thematic Alignment / Contextual Appropriateness / Scene-to-Scene Coherence。锁定为 R5/R6/R9 共用 rubric。⚠ 数据集 **CC-BY-NC-SA 非商用**，借方法不借资产。 |
| **2026 中文模型实测** | Kimi K2.6 中文创意写作**双榜第一**（超 GPT-5）。 | **Writer 首选 Kimi K2.6**（2M 上下文、文笔领先，但最贵 ¥3-3.5/百万 Token）；**性价比选 DeepSeek V4**（$0.25/百万 Token，知识强文笔弱）；**开源本地选 Qwen3.6-Plus**（Apache 2.0，C-Eval 93%）；GLM-5.1 编程强但创意非强项、上下文仅 128K。**判官（Critic）必须异源**——与生成模型不同源的高文笔模型。 |

---

## 5. 全局 open questions / 待用户决议点

### 重大架构决议（需用户拍板）
1. **是否为"角色对白区分度"引入开源模型 / 解码干预 / SFT？**
   纯远端 API + 纯 prompt 有 RPNA 证明的结构性上限（直接拖累 SEQR `dialogue_distinct` rho=−0.16）。突破三选一：① 换扁平化更轻的基座；② split-softmax 解码期干预（需自托管开源模型）；③ 角色 SFT（但 Narrative Flattening 警示 SFT 本身可能加剧扁平化，且 PersonaEval 显示角色 SFT 数据反而有害）。**这是 Phase 2 最大开放问题。**

2. **数据可商用性双风险。**
   WebNovelBench 数据集 CC-BY-NC-SA 非商用；Creative Convergence 配套数据 repo 已失效。若系统将来商业化，评测/词表/题材模板**必须本土自建**，不能直接用其数据资产。

3. **模型绑定策略与成本。**
   Kimi K2.6 文笔最好但最贵（约 DeepSeek 的 12-14 倍）。是否对 Writer 用 Kimi、对结构/推理用 DeepSeek、对 Critic 用第三方异源模型做精细分工？换模型时 R10 的结构化约束与 R6 的判官异源性都需重新核验。

### 工程开放问题
4. **Pydantic schema 是否按 `story_bible` 动态生成？**（R10）当前 Instructor 的输出 schema 是否需要随每部小说的设定动态构造。
5. **现六-agent 架构补"卷级层"与"显式 ledger 聚合层"的具体形态？**（R4）诊断出这两块缺失，但落地形态（新增 agent / 新增 graph 节点 / 纯存储层）待定。
6. **中文创意写作缺可复核的单一权威榜单。**（R9）建议建立自有门禁小样实测（Kimi K2.6 vs Qwen3）作内部基准。
7. **中文 slop 词表的人类网文语料基线如何采集？**（R6）slop-forensics 中文化 + jieba + 人类网文语料基线的具体语料来源与去偏方法待定。

### 待二次确认的引用（非幻觉，仅降级标注）
- R2：A-MEM 降为 B-tier 待 reverify。
- R1：DOME 精确页码、DOC v2 仓库、WebNovelBench 8 维权重数值 待二次确认（论文本体、8 维名称已确认）。
- R3：2502.11371 逐条数字（NQ −13.4% 等）为二手转述，标 `[no-source-found]` 待 PDF 复核。
- R5：RoleRAG 论文存在但 repo 缺（no-source-found）；一批 v1 2025-26 条目（Nautilus/RAIDEN-R1/SCORE 等）标 `[v1-sourced，本轮未复验]`——是"未复核"而非"被判假"。
- R4：SCORE/LongEval/HAMLET/SWAG 本轮未逐篇验真，引用前二次确认。

---

*本总结由 v2 workflow 自动综合。各方向完整证据链、URL、三标签评级见同目录对应终稿文件。v1↔v2 完整差异见 `DIFF-v1-vs-v2.md`。*
