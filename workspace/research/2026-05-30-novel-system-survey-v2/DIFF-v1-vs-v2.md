# v1 ↔ v2 关键差异总表 + 幻觉剔除清单

> 调研批次：2026-05-30-novel-system-survey-v2
> 本文件汇总 9 个方向 v1→v2 的「新增 / 纠正 / 删除」三类关键差异，并在末尾汇总本次 workflow 自动剔除的全部幻觉。
> 通用变化（所有方向）：每条 finding 统一补 [accessed:2026-05-30] + 时效性/鲁棒性/可行性三标签 + 验真标记（check/orange/no-entry）；引入 2026-05 中文模型选型核查。

---

## 一、9 方向 v1↔v2 关键差异总表

### R2 — 长期记忆（S 档）
| 类型 | 内容 |
|------|------|
| **新增** | 对话型 vs 小说型记忆错配表；S/B/C 分档（按用户优先级）；S 档时效/鲁棒/可行标签；Mem0-vs-Zep benchmark 之争专节；"Rethinking Memory in AI 六操作自审"替换 CoALA；模型层指引绑定 per-agent registry；明确 no-Neo4j 边界；六个 open questions |
| **纠正** | DOME 会议→NAACL 2025 Long Papers；BEAM 从 no-source-found→已验证论文+repo；ConStory-Bench 元数据；WebNovelBench 八维逐字列出；A-MEM 降 B 档+reverify 标注 |
| **删除** | MemPalace 整节（名人系统、单源营销、第三方测试显示压缩掉准、发布后下调分数）；v1 非小说专属/博客来源章节（LangChain/LangGraph 记忆、LlamaIndex blocks、CoALA、DOC/Re3 细节、AgentMemoryBench、context-drift 博客源）；易腐的 star/commit 元数据简化为区间 |

### R5 — 角色扮演/一致性（S 档）
| 类型 | 内容 |
|------|------|
| **新增** | §0.3 接入 2026 中文模型实测选型（Kimi K2.6 文笔前/DeepSeek V4-Pro 知识强文笔少/Qwen3.6 开源利于本地 split-softmax）并串成选型决策链；WebNovelBench 八维并锁定 Distinctiveness of Character Dialogue + Consistency of Characterisation 两维作 rubric 直对 SEQR；新增已验真的 PersonaEval/PersonaGym/Persistent Personas/Moral RolePlay/Character-R1；每条 S 档补三标签 + 全表验真标记 |
| **纠正** | 2402.10962 标题（Persona Drift → **Instruction (In)Stability**，repo 名 persona_drift 是误记来源，论文本身存在）；v1 隐含的"必须 SFT"明确改写为"谱系四档"并用三条反向证据封死（PersonaEval=角色 SFT 数据反而有害 / 2402.10962=解码 training-free 可缓解 / Narrative Flattening=SFT 是扁平化病因），同时保留 v1 最强洞见（RPNA+Narrative Flattening 证纯 prompt 有结构上限）；RoleRAG 下调为论文存在但 repo 缺；一批 v1 2025-26 条目（Nautilus/RAIDEN-R1/SCORE/ConStory/LifeState/MRPrompt/CREFT/OpenCharacter/RoleLLM/ChatHaruhi/CharacterGLM 等）降级标 [v1-sourced，本轮未复验]；v1 偏英文工程细节（Character.AI MQA/KV、NeMo 变体）压成 B/C 档 |
| **删除** | PerRoleCognition（杜撰）；RPNA 的错误含义"角色扮演叙事分析"；2402.10962 的错误标题 |

### R1 — 大纲/剧情结构（S 档）
| 类型 | 内容 |
|------|------|
| **新增** | §1.1 KG+文学理论（2508.03137，v1 完全缺失）带来"大纲相似度阈值触发反转"信号；LongWriter/AgentWrite（2408.07055）从顺带提及升为长输出一级方案；Propp-34（2603.14430）升格为"可计算叙事功能标签"抗同质化武器；oh-story 三层大纲升为最贴近实践参考；§6 模型选型建议；全文刷新 [accessed:2026-05-30] + 一手 GitHub API star/license/活跃度 |
| **纠正（最重要）** | ⚠️ **v1 §1 的 Expansion-Ratio 具体数值（R=0.01/α₁=0.05/α₂=0.20/Gemini2.0Flash/40 部中文小说）建议直接编码为默认值——经一手验真无法核实，v2 降级为不可核实并明确禁止当默认配置，只保留"存在最优压缩-扩展比"定性结论**；DOME 叙事框架澄清为英雄之旅+Freytag/Vogler+五段式（非单纯五幕）；DOME 页码/DOC v2 仓库/WebNovelBench 8 维权重数值降级待二次确认；WebNovelBench 作者名校准为 Liangtao Lin/Jun Zheng/Haidong Wang |
| **删除** | 4open.science 匿名数据集链接（403）；DOME 误报命名/页码细节；PerRoleCognition 杜撰。另：v1 大量未重验 C 档条目（Plan-and-Write/PlotMachines/LongStory/Agents'Room/StoryWriter/DSR/Self-Refine 等）未判为幻觉，仅降为"理念引用、未重新背书" |

### R4 — 开源项目调研（移植源，支撑 R1/R2/R5）
| 类型 | 内容 |
|------|------|
| **新增** | 整组 2026 新活跃项目（🥇 tyxben/AI_novel 首选移植源、MuMuAINovel 2520★、NovelForge、Novel-OS、libriscribe、gemini-writer、wfcz10086——v1 全无）；"四件套工程"共识框架（分层大纲+卷级强推 / 显式 ledger 跟踪伏笔债角色 / 上章结尾压缩防重复 / 机械+LLM-judge+读者模拟三层评估）；§3 基础事实核查整节（PerRoleCognition 预警 + 2026 中文大模型文笔实测 + per-agent 绑定建议）；"缺卷级层+缺显式 ledger 聚合层"两层架构缺口诊断；失败案例集中成独立节 |
| **纠正** | Ex3 论文 URL .832→**.494**（.832 实际指向 M4LE）；tyxben 定位澄清（对外 README 偏"小说转短视频"营销，移植前须 clone 确认内部文本生成组件）；issue 编号收敛（保留独立验真的 #112/#129/#135，标注 #120/#149/#150 未验真）；autonovel 字数口径统一为约 75k 字/23 章/5 轮 revision；WebNovelBench 八维再确认逐字正确 |
| **删除** | Ex3 错误 URL（唯一 exists=false）；预防性剔除 PerRoleCognition；v1 大量 2022-2024 纯学术 repo 编目（Re3/DOC/StoryWriter/Ex3-NovelWriter/BookWorld/IBSEN/CreAgentive/SillyTavern）降权压缩进 §5 学术血脉；SCORE/LongEval/HAMLET/SWAG 等未逐篇验真者显式降权 |

### R10 — 结构化 LLM I/O（A 档）
| 类型 | 内容 |
|------|------|
| **前提澄清** | v1 不是空骨架，而是 239 行成型调研；v1/v2 主结论一致（Phase1 选 Instructor、弃 Outlines/Guidance/PydanticAI、DSPy 记 backlog），分歧只在论据精度 |
| **新增** | §0 DeepSeek 硬约束（v1 完全没有这层）；JSONSchemaBench（2501.10868）作 Outlines 合规率量化反证；PromptPort（2601.06151）ROS/CSS 评估方法；落地排序表锚定用户优先级；§6 模型层事实核查（Kimi K2.6 双榜第一，Instructor provider-中立应对换模型） |
| **纠正** | (1) v1 说 Instructor 不内置 LiteLLM、要绕 from_openai+base_url → **纠正为有官方一等公民 `instructor.from_litellm(litellm.completion)`**；(2) 弃 Outlines/Guidance 理由从"要自托管/用不到 conditional branching"升级为更根本的"**约束解码对远端 API 无效**"；(3) issue 1069 与 7580 明确为 Closed as not planned，strict 从"可选保险"降级为"主路必须 Tools/MD_JSON+reask"；(4) PydanticAI v1.103.0→v1.104.0；(5) BAML"2-4× faster"标未验真不作硬依据，选 BAML 理由收敛到 SAP 鲁棒性+多语言 codegen |
| **删除** | DSPy 文档死链（exists=false 重定向页；该链不在 v1 Sources、来自 clean-room 稿，改由 dspy.ai/api/models/LM/ + GitHub README 佐证同一事实）。唯一幻觉，其余 30+ 条引用全 exists=true |

### R6 — Anti-slop/文笔质量（A 档）
| 类型 | 内容 |
|------|------|
| **新增** | ICLR 2026 多源确认（poster+OpenReview）；EQ-Bench Slop Score 精确加权（60% words/25% not-x-but-y/15% trigrams）；4 篇 LLM-judge 去偏 paper-grade 支撑（2604.23178/2406.07791/2604.22891/2411.15594）把"Critic Room 去偏"从口头建议升级为有文献依据；中文商业竞品（星月写作反翻译腔、腾讯朱雀 AI 检测对抗基线）；LitBench（2507.00769）reward model 长期备选；auto-antislop 用户增量 ban 接口；autonovel 三文件 URL 全验真 + 12 类 anti-pattern 完整列出 |
| **纠正** | DeepSeek 约束更精确（支持 logprobs 但文档未列 logit_bias + sglang#8734 MTP bug，结论不变论据更扎实）；Antislop code 链接归位（Sampler 实现是 antislop-sampler 而非 v1 误标的 auto-antislop）；判官与生成模型**必须异源分离**；EQ-Bench"98.6%"数字不再断言 |
| **删除** | 无 exists=false 幻觉（27 条全真）；降级移出 5 个弱引用（Ozigi 博客 / Awesome-LLM-judge / lyc8503 / EnsemJudge / emergentmind）；弱化 v1"可发表/中文社区影响力"的未证实战略表述 |

### R3 — 图谱管理（B 档）
> ⚠️ **总综合者更正**：v2 子调研稿声称"v1 目录无 r3-graph、整方向净新增"，但**经核对 v1 目录确实存在 `r3-graph.md`（2026-04-28，含 F1-F5：Graphiti/Zep、MS GraphRAG、LightRAG、DOME 四元组、EvolvTrip/CREFT，Verdict=不引入独立图谱组件、嵌入 R2 记忆系统、DOME 四元组作 knowledge_triples 依据）**。故 R3 **不是**净新增方向，而是大幅深化。v1↔v2 真实差异如下。

| 类型 | 内容 |
|------|------|
| **新增（相对 v1 的深化）** | v1 仅 5 条 finding 卡片、Verdict 是"图谱能力嵌入 R2 记忆系统（MemoryOS/Graphiti/Mem0 之一）"；v2 首次给出**分场景 ROI 结论**（全局检索/局部注入/事实记账三分）+ **GraphRAG 怀疑论证据链**（2506.05690 GraphRAG-Bench 对 generation 掉点 + 2506.06331 增益偏差修正 + 2502.11371）+ 六候选逐条工程评级 + EnigmaToM(2503.03340)/局部 KG 转折(2508.03137)/可控性用户研究(2505.24803)。v1 已有的 Graphiti「不引 Neo4j、只借 bi-temporal」判断 v2 延续并强化 |
| **纠正/深化** | 把 DOME(2412.13575) 从 v1 r1-outline 的"动态大纲"角度重定位为与 R3 知识三元组直接对标的 MEM 四元组（章号 index）；关键更正"**DOME 扁平四元组在官方 repo 实际存 Neo4j——逻辑视图不等于必须图数据库，可用 SQLite 复现**"（v1 r3 已说 DOME 四元组作 knowledge_triples 依据，但未点破 repo 存 Neo4j 这层）；回填 v1 三个 open question（R2 章号缺失→章号四元组+Graphiti 有效区间；R5 belief/desire 随章演化→EvolvTrip 4 谓词归 R5；R1 转折自动生成→局部 KG 目标-障碍建模） |
| **删除** | 无幻觉 URL 可删（23 条全 exists=true）；2502.11371 逐条数字降级为二手待核（非删除）。**另：子调研稿"v1 无 r3"的前提本身是误判，已由总综合者更正（见上方警示框）** |

### R9 — 中文网文专属（B 档）
> ⚠️ **总综合者更正**：v2 子调研稿声称"v1 文件不存在（Read file-not-found + Glob 均 No files found）"，但**经核对 v1 目录确实存在 `r9-chinese.md`（2026-04-28，含 F1-F4：中文模型文笔对比、网文题材分布、Creative Convergence 34 功能、阅文妙笔产品实践，Verdict=DeepSeek 非必然默认 / Kimi K2.6·GLM-5.1 文笔更强 / 34 功能进 outline）**。故 R9 **并非** clean-room 净新增，v1 已有实质 findings 且主结论与 v2 一致。子调研稿应是未能定位到 v1 文件（疑似路径或编码问题）而误判。v1↔v2 真实差异如下。

| 类型 | 内容 |
|------|------|
| **前提更正** | v1 文件**存在**（非"file-not-found"）。v1 已正确得出 Kimi K2.6/GLM 文笔更强、DeepSeek 非必然默认、Creative Convergence 34 功能进 outline——v2 主结论与之**一致**，v2 在其上补验真、补评测门禁、补许可风险 |
| **新增** | §6 角色认知交叉指针（声明 PerRoleCognition 杜撰 + 转介 RPNA/RoleRAG/Character-LLM 给 R5/R3）；每条候选补三标签 + Top 候选表加备注列；Open Q6 升级为"数据可商用性双风险"；新增 Open Q7（中文创意写作缺可复核单一榜单）；"借方法不借资产"提醒贯穿全文；把质量门禁（WebNovelBench 8 维 + EQ-Bench 三指标合成 consistency_check）写到可落地深度（v1 未涉评测门禁） |
| **纠正** | 选型证据链重建（删 EVY/Mayne 后 Writer 选型结论 Kimi K2.6/Qwen3 大杯不变但改用可复核榜单 + 基础事实核查）；WebNovelBench 元数据补正（作者署名 Leon Lin vs Liangtao Lin 同一人、数据集许可 CC-BY-NC-SA-4.0 非商用）；8 维逐字核验标注"已核验"；34 功能数据可得性从"匿名 repo 可取"纠正为"链接失效、只能采框架/自标"（v1 r9 已注"配套数据 repo 已失效"，v2 与之吻合并补 4open.science 403 实证）；**"v1 文件不存在"前提误判已更正（见上方警示框）** |
| **删除** | 4 处幻觉/不实链接：acl26-ED4E 数据 repo（403）、EVY 聚合分数整段（页面存在但未以中文模型分数为榜单项）、Andrew Mayne 404 博文、Weaver 404 HTML（替换为 ar5iv 镜像）；PerRoleCognition 显式声明不引用 |

### R7+R8 — 编排框架决策 + 同类产品借鉴（C 档 light）
| 类型 | 内容 |
|------|------|
| **新增** | R7 候选从 4 家扩到 5 家（加 OpenAI/Claude SDK 及绑单厂商否决理由）；**新增整节 A6「supervisor vs swarm」并得出「固定 DAG 最优、不引入动态路由」的反向 confirm（v2 最重要增量，v1 无此维度）**；R8 从两个泛泛 UX 印象升级为可执行工程规格——补齐 NovelAI Lorebook 完整注入机制（Search Range/Insertion Order/Position/Token Budget/Always On/Cascading/Key-Relative）下沉到 L2，补 Progressions↔时序三元组镜像对应；来源可信度分级；模型选型轻量锚定 |
| **纠正** | AutoGen 从 v1"⭐⭐⭐⭐推荐、可在 LangGraph 节点内嵌"据官方 README 降级为"**维护模式、官方劝退、排除**"（v1 内嵌 AutoGen 建议已不成立）；NovelAI 从 v1"二次元不重叠几乎弃用"纠正为"**本方向最高价值工程借鉴来源**（Lorebook 与题材无关）"；量化 benchmark 数字降可信度；Sudowrite Muse 改以官方文档为准 |
| **删除** | Sudowrite Muse 404 博客 URL；错配的 MAF URL（指向 AutoGen，纠正为 github.com/microsoft/agent-framework）；错配的 AFlow URL（指向 MetaGPT，纠正为 FoundationAgents/AFlow）；v1 全部未验证的零散对比博客（pooya.blog/openagents.org/meta-intelligence.tech/nerdynav.com/novarrium.com/sidekickwriter.com）与 SidekickWriter 条目；v1 量化 benchmark 精确数字（LangGraph 62%/CrewAI 54%/AutoGen 58%/60% faster debugging，来源未验真已弃用为论据） |

---

## 二、本次 workflow 自动剔除的幻觉清单（汇总）

### A. 全网杜撰术语（最严重，跨方向防串扰）
| 幻觉 | 性质 | 涉及方向 | 处置 |
|------|------|---------|------|
| **PerRoleCognition** | **杜撰**——arXiv / Google Scholar / 全网均无任何学术发表（三项基础事实核查确认） | R1/R2/R3/R4/R5/R6/R9 全部登记防串扰 | 全方向禁用。真实近邻替代：RPNA（arXiv:2510.24677）/ RoleRAG（2505.18541）/ Character-LLM（2310.10158） |

### B. exists=false 的伪造/死链 URL（逐条验真为假）
| 幻觉 URL / 内容 | 方向 | 验真结果 | 处置 |
|----------------|------|---------|------|
| `anonymous.4open.science/r/acl26-ED4E/`（Propp-34 / Creative Convergence 匿名数据集） | R1、R9 | HTTP 403 + 全网无索引 | 剔除；论文本体（arXiv 2603.14430）为真保留，功能定义改从 PDF 正文取，配套数据标注"不可得、只采框架" |
| `aclanthology.org/2024.acl-long.832/`（Ex3 论文地址） | R4 | exists=false，该 URL 实指向另一篇论文 M4LE | 替换为正确地址 `aclanthology.org/2024.acl-long.494/`（ACL 2024, pp.9125-9146） |
| `dspy.ai/learn/programming/language_models/`（DSPy 文档） | R10 | exists=false，无实质内容的重定向页（跳到 /getting-started/installation/） | 剔除死链；"DSPy 走 LiteLLM"事实保留，改由 dspy.ai/api/models/LM/ + GitHub README 佐证。（注：该链不在 v1 Sources，来自 clean-room 稿） |
| `evy.so/compare/best-llms-for-writing/` 及其全部中文模型聚合分数 | R9 | exists=false（页面存在但未以"中文模型分数"作榜单项，所引数值无法复核） | 整段删除；选型证据改用 WebNovelBench + EQ-Bench v3 + 基础事实核查重建 |
| `andrewmayne.com/2025/07/14/...kimi-k2...creative-writing...`（Kimi 实测博文） | R9 | HTTP 404 | 删除背书；Kimi K2.6 优势改由基础事实核查多源中文实测支撑 |
| `arxiv.org/html/2401.17268v1`（Weaver 全文 HTML） | R9 | HTTP 404（非标准 arXiv HTML 路径） | 替换为 ar5iv 镜像 `ar5iv.labs.arxiv.org/html/2401.17268` + arXiv 摘要 |
| `sudowrite.com/blog/sudowrite-muse-...`（Sudowrite Muse 博客） | R7/R8 | HTTP 404（产品真实、slug 不存在） | 删除 URL，改引官方 docs Muse 页 |
| "Microsoft Agent Framework (MAF) 仓库 = github.com/microsoft/autogen" | R7/R8 | exists=false（该 URL 指向 AutoGen 而非 MAF） | 纠正为 `github.com/microsoft/agent-framework`，标注本轮未验证成熟度 |
| "AFlow 仓库 = github.com/FoundationAgents/MetaGPT" | R7/R8 | exists=false（该 URL 是 MetaGPT，仅示例中提及 AFlow） | 纠正为独立仓库 `github.com/FoundationAgents/AFlow`；AFlow ICLR 2025 paper 本身真实 |

### C. 标题/命名/数值不实（论文存在，细节错——按纠正而非删除处理）
| 幻觉内容 | 方向 | 性质 | 处置 |
|---------|------|------|------|
| 2402.10962 错误标题"Measuring and Controlling **Persona Drift** in Language Model Dialogs" | R5 | exists=false（标题不符）；真实标题为"Measuring and Controlling **Instruction (In)Stability** in Language Model Dialogs"（Kenneth Li 等，repo 名 persona_drift 是误记来源） | 论文存在，纠正标题而非删除 |
| RPNA 的错误含义"角色扮演叙事分析（role-play narrative analysis）" | R5 | 查无此义 | 删除该错误含义；RPNA 仅保留真实所指（RP-Neuron-Activated 神经元消融评测，arXiv:2510.24677） |
| DOME 在 aclanthology.org/2025.naacl-long.63/ 的"标题字面为 DOME"命名匹配 + 未确认的"pp.1352-1391"精确页码 | R1 | 验真误报（URL 与论文本身真实，经复核保留） | 保留 URL，剔除"命名匹配"与"精确页码"两处不实细节 |
| v1 Expansion-Ratio 具体数值 R=0.01/α₁=0.05/α₂=0.20/Gemini2.0Flash/40 部中文小说 | R1 | 一手验真无法核实 | 降级为不可核实，**明确禁止当默认配置**，只保留"存在最优压缩-扩展比"定性结论 |
| EQ-Bench"与人类 preference 相关性 98.6%" | R6 | v1 via snippet，本轮未复现 | 不再断言，改述可核对的去偏协议本身 |
| v1 量化 benchmark（LangGraph 62%/CrewAI 54%/AutoGen 58% 完成率、60% faster debugging） | R7/R8 | 来源未经本轮验真 | 弃用为论据，改用官方 README 能力描述 + 打折标注的第三方排名 |

### D. 降级移出主线的弱引用（非证伪，仅"未复现为核心证据"而降权）
- **R6**：Ozigi 产品博客（banned-lexicon-validator）/ Awesome-LLM-as-a-judge / lyc8503 LLM-classifier + EnsemJudge（2603.27949，属"检测人写 vs 机写"正交方向）/ emergentmind FTPO 二手词条——共 5 个弱引用移出主线，由验真通过的论文/官方文档取代。
- **R5**：MemPalace 整节（celebrity 系统，单源营销）——R2 删除，R5 不涉。
- **R2**：v1 非小说专属/博客来源章节（LangChain/LangGraph 记忆、LlamaIndex blocks、CoALA、AgentMemoryBench、context-drift 博客）整体移出。
- **R1**：Plan-and-Write/PlotMachines/LongStory/Agents'Room/StoryWriter/DSR/Self-Refine 等 C 档条目降为"理念引用、未重新背书"（区别于确证删除）。
- **R4**：Re3/DOC/StoryWriter/Ex3-NovelWriter/BookWorld/IBSEN/CreAgentive/SillyTavern 等 2022-2024 纯学术 repo 降权压缩进 §5 学术血脉。
- **R7/R8**：pooya.blog / openagents.org / meta-intelligence.tech / nerdynav.com / novarrium.com / sidekickwriter.com 及 SidekickWriter 条目——不在验真白名单、对 C 档结论无 load-bearing，不再引用。

---

### 幻觉拦截统计
- **全网杜撰术语**：1 个（PerRoleCognition）——跨 7 方向预防性登记。
- **exists=false 伪造/死链 URL**：9 条（含 4open.science、Ex3 .832、DSPy 死链、EVY、Andrew Mayne、Weaver HTML、Sudowrite Muse、MAF→AutoGen 错配、AFlow→MetaGPT 错配）。
- **标题/命名/数值不实**：6 处（2402.10962 标题、RPNA 错误含义、DOME 命名+页码、Expansion-Ratio 数值、EQ-Bench 98.6%、编排 benchmark 数字）。
- **降级弱引用**：6 方向共约 25+ 条（非证伪，降权处理）。
- **逐条验真全真的方向**：R3（23 条全 exists=true）、R6（27 条全 exists=true）——无伪造 URL 需删。

*完整逐条证据见各方向终稿的 hallucinations_removed 段与 Sources 段。*
