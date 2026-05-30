# R13 · 训练语料(中文网文高质量数据)—— 生产级终稿(v2 补充)

> 立场锚定:从 0 构建、面向生产、绝不质量妥协。本报告对每个数据来源/方法回答的不是"能不能跑起来",而是"对一个要做到最好的中文小说生成系统,这条语料路线值不值得从一开始就投入,以及法律/质量风险是否可控"。明确拒绝"先用爬来的数据凑合、上线前再洗"的埋雷式分期。
> 所有存活 claim 均经 2026-05-30 实际访问页面(WebSearch/WebFetch)+ HF/GitHub/arXiv 官方页核验。引用真实性已逐条过验真闸门(见 §10)。accessed 统一标注 [accessed:2026-05-30]。

---

## 0. 结论先行(TL;DR)

1. **现成中文网文数据集对生产基本不可用。** HF 上几十个"中文小说/网文"数据集无一例外满足至少两条:(a) 来源是**爬取的盗版商业网文**、(b) 体量小或年代久(多停在 2024)、(c) **无 license 或 license 在法律上无效**(爬来的他人著作权内容你无权再授权)。直接喂进生产模型 = 把版权炸弹焊进权重,且违反**《生成式人工智能服务管理暂行办法》第七条**(2023-08-15 施行)。**这是一票否决项,不是风险权衡项。**
2. **生产级唯一正路:自建"合成数据 pipeline + 公版/自有种子 + 去 slop 清洗 + 专项偏好对"。** 不存在"现成高质量中文网文 SFT 集";存在的是**构建它的成熟方法与工具**(Magpie / Persona Hub / OpenCharacter / 指令回译 Humpback / LongWriter / Antislop-FTPO),全部是 2024–2025 的当代件,论文+开源齐备。
3. **与地基锚点完全咬合。** R11 已定:生成内核建在**自托管开源权重(Qwen3-235B-A22B 首选)+ 解码层自控 + 针对性微调**。R13 的语料正是喂这套内核的"燃料"——只有掌握权重与 logits 的底座,才能消化 §3 的合成 SFT 与 §5 的 FTPO 偏好对。**语料自建与底座自托管是同一个"一步到位做对"决策的两面,不可拆。**
4. **量级(已验证锚点):** SFT 走 LIMA"质重于量"——**1k 级精品**即可对齐写作风格(知识在预训练里);长文能力补 LongWriter 的 **~6k**;偏好(反套话/对白区分度)阶段**数千–2万对**。轻量 continued-pretraining 提语感需**数亿–数十亿 token** 公版+自有(是否真需要见 §6,属可触发项而非必选地基)。
5. **去 slop = 中文小说生产的核心竞争力,不是可选项。** "对白区分度 / 反套话"必须靠**专门构造的偏好对**(chosen=有区分度对白 / rejected=AI 套话腔)。2025 年已有正式框架:**Antislop + FTPO**(arXiv 2510.15061,ICLR 2026),实测 **FTPO 减 slop 85–92% 且不掉通用能力,而 DPO 会显著退化**——这是把"能写"变"不像 AI"的当前最优杠杆。中文 slop 词表需自建(无成熟现成资源)。

---

## 1. 现成中文网文/小说数据集盘点(HF API 实测,全部存活但生产不可用)

跑了 `novel / chinese novel / 小说 / 网文 / 言情 / 武侠 / xianxia / creative writing / roleplay` 等十余个检索词。**中文小说类全部低质或带版权风险**:

| 数据集 | 规模/性质 | 实测指标 | license | 生产判断 [accessed:2026-05-30] |
|---|---|---|---|---|
| [jetaudio/chinese_web_novels](https://huggingface.co/datasets/jetaudio/chinese_web_novels) | **20万+ 部网文,202GB parquet 原文** | gated,需鉴权下载 | **无** | ✗ 明显爬取,无授权;gated 不改变版权侵权性质 |
| [b3x0m/Chinese-H-Novels](https://huggingface.co/datasets/b3x0m/Chinese-H-Novels) | 网文(成人,9.3亿行/60.9GB) | 2024-12 更新,免责声明"自担风险" | **无** | ✗ 盗版 + 内容合规双重雷 |
| [zxbsmk/webnovel_cn](https://huggingface.co/datasets/zxbsmk/webnovel_cn) | 网络小说 SFT,源 12,560 部网文,2170万条/50k 子集 | DOI 已发,603MB | 标 `MIT`(对爬取内容**无效**) | ✗ 埋雷:repo 标 MIT ≠ 内含他人著作权网文可商用 |
| [silk-road/50-Chinese-Novel-Characters](https://huggingface.co/datasets/silk-road/50-Chinese-Novel-Characters) | 50 部小说(斗罗/凡人/斗破等)14.2万行对白 | 581MB,月下载 219 | — | △ 源自版权网文,**仅可作人物/对白结构参考,不可入训练集** |
| [LooksJuicy/Chinese-Roleplay-Novel](https://huggingface.co/datasets/LooksJuicy/Chinese-Roleplay-Novel) | **合成**的 tavern 式角色对白(266 行) | 4.32MB | **apache-2.0** | △ 思路对(合成+角色卡),量太小;**可作格式/范式范本** |

**对照组——合成/角色/指令类集 traction 高,印证"自己合成"才是有效主流:**

| 数据集 | 性质 | license | 启示 [accessed:2026-05-30] |
|---|---|---|---|
| [m-a-p/COIG-CQIA](https://huggingface.co/datasets/m-a-p/COIG-CQIA)(NAACL 2025,[arXiv 2403.18058](https://arxiv.org/abs/2403.18058)) | 中文高质量指令 44,694 行(知乎/豆瓣/百科) | **CC-BY-4.0**(论文页核实) | "质量优先"范本,但**文学占比极低**;可商用但非网文风格主料 |
| [proj-persona/PersonaHub](https://huggingface.co/datasets/proj-persona/PersonaHub)([arXiv 2406.20094](https://arxiv.org/abs/2406.20094)) | 10亿 persona,合成数据载体 | **cc-by-nc-sa-4.0(非商用!)** | persona 合成是事实标准;**HF 数据集本身非商用,可商用的是方法/代码** |
| [xywang1/OpenCharacter](https://huggingface.co/datasets/xywang1/OpenCharacter)([arXiv 2501.15427](https://arxiv.org/abs/2501.15427)) | **2万合成角色 + 30.6万角色对白** | apache-2.0(**论文定位研究用**) | 角色/对白合成的现成范式;**照搬 pipeline,慎用其成品数据训生产模型** |

> **生产判断**:不要在"找现成中文网文 SFT 集"上耗时——**确定不存在生产级干净集**。silk-road / 50 部小说虽存活且数据干净结构好,但**源头是受版权网文,入训练即埋雷**,只能当抽取范式参考。精力 100% 投到 §3 自建合成 pipeline。

---

## 2. 版权与可商用红线(中国法域,最高优先级闸门)

### 2.1 商业网文 = 绝对禁区(有刑事先例)
- 起点/阅文、晋江、番茄(字节)、七猫连载内容均受著作权法保护、平台持独家信息网络传播权。爬取+用于训练生产模型在中国法下构成**著作权侵权**,可叠加**《反不正当竞争法》**。
- **真实刑案**:某团伙未经许可用爬虫抓正版电子书,在 20 余个"免费小说"App 展示牟利,**上线作品 2.4万余部、浏览章节 3.6亿余、广告违法所得 1.35亿元**,被以侵犯著作权罪论处。司法明确:权利人分散、难逐一举证时,只要证明系非法复制发行且行为人无授权证明,即可认定"未经著作权人许可"。

### 2.2 合规硬约束:《暂行办法》第七条(施行 2023-08-15)
> 第七条 ……应当依法开展预训练、优化训练等训练数据处理活动:(一)**使用具有合法来源的数据和基础模型**;(二)涉及知识产权的,**不得侵害他人依法享有的知识产权**;(三)个人信息须取得同意或符合法定情形;(四)采取有效措施提高训练数据质量,增强真实性、准确性、客观性、多样性;(五)遵守网安法/数据安全法/个保法。

> **生产判断**:任何"先用爬来的起点/番茄训练、上线前再洗来源"的分期路线 = **不可接受的埋雷**。权重训进受版权内容后无法"卸载",正是用户明确拒绝的妥协。**一票否决。** 这一条直接呼应 R11"从 0 把内核建在自控底座"——自有底座 + 干净语料是合规留证的前提,黑盒 API 反而把训练数据来源举证责任外包给了不可控的第三方。

### 2.3 公版边界——能用但有大坑
- 中国著作权法财产权保护期 = **作者终身 + 死后 50 年**(法人作品首发后 50 年);署名权/保护作品完整权**永久**。
- 公版现代中文文学**极少且偏文言/民国**(如鲁迅)。源:**维基文库 zh.wikisource.org**(CC-BY-SA)、Project Gutenberg 中文区。**坑**:文体与现代网文语感差异巨大;且**译本/校注另有独立著作权**,即便原作公版也不能整本拿。

> **生产判断**:公版只能当"中文文学语感/修辞密度"的**营养剂**(少量 continued-PT),**不能当现代网文风格主语料**。

### 2.4 自有/授权——理论最优、成本最高
- 与作者签授权或自有平台 UGC(用户协议须覆盖训练授权)是**唯一无瑕疵**的现代网文来源。生产级最优解,需法务+采购投入。**侧证(来自 R15 锚点)**:番茄 2024-07 新增"AI 训练协议"要求作者授权作品用于训练并引发抵制——这恰恰说明**即便平台方,合法用语料训练也必须走作者授权**,印证爬取路线无侥幸空间。

---

## 3. 合成数据 pipeline(生产级核心推荐路线)

干净现代网文真数据稀缺且贵,**合成 + 强模型蒸馏 + 少量真种子**是 2024–2025 已验证主流。五块基石,全部论文+开源可落地:

### 3.1 Magpie —— 零种子从对齐模型自抽指令(造"指令"的发动机)
[《Magpie》arXiv 2406.08464](https://arxiv.org/abs/2406.08464),2024-06。只喂对话模板左半边,对齐模型自回归吐出用户指令再回填答案;造 **400万** 对、过滤到 **30万**,微调后媲美官方对齐版。开源 [magpie-align/magpie](https://github.com/magpie-align/magpie)(861★ / MIT,ICLR 2025)。[accessed:2026-05-30]
→ **生产可行性:高。** 用最强中文写作对齐模型当 teacher 批量生成"写作类指令",极低成本、可规模化。

### 3.2 Persona Hub —— persona 驱动多样性(攻"AI 千篇一律")
[《Scaling Synthetic Data Creation with 1B Personas》arXiv 2406.20094](https://arxiv.org/abs/2406.20094)(Tencent AI Lab),2024-06(v3 2025-05)。**10亿 persona** 作为"世界知识分布式载体",注入 prompt 强制多视角;用例含**游戏 NPC**。代码 [tencent-ailab/persona-hub](https://github.com/tencent-ailab/persona-hub)(1.6k★)。**注意:HF 数据集 [proj-persona/PersonaHub](https://huggingface.co/datasets/proj-persona/PersonaHub) 为 cc-by-nc-sa-4.0(非商用),可商用的是方法本身**。[accessed:2026-05-30]
→ **生产可行性:高(用方法,不用成品数据)。** 把 persona 当**人物卡/叙述者视角发生器**——直接攻"对白区分度":不同 persona → 不同说话腔调 → 天然多角色区分对白。

### 3.3 OpenCharacter —— persona 落到"角色+对白"的现成范式
[《OpenCharacter》arXiv 2501.15427](https://arxiv.org/abs/2501.15427)(Tencent AI Lab 同源),2025-01。基于 Persona Hub 合成**角色画像**,再用"改写/生成"两策略产出**角色对齐对白**;发布 **2万合成角色 + 30.6万对白**([xywang1/OpenCharacter](https://huggingface.co/datasets/xywang1/OpenCharacter),apache-2.0,**论文定位研究用**),LLaMA-3-8B SFT 后角色扮演逼近 GPT-4o。[accessed:2026-05-30]
→ **生产可行性:高(照搬 pipeline 重造中文版)。** 中文版照搬此 pipeline 造**有区分度的人物对白 SFT 数据**。

### 3.4 指令回译 Humpback —— 把"高质量散文"逆向成 SFT 数据(盘活公版/自有)
[《Self-Alignment with Instruction Backtranslation》arXiv 2308.06259](https://arxiv.org/abs/2308.06259)(Meta,ICLR 2024)。两步:self-augmentation(给人写好文本反推"它是哪条指令的好答案")+ self-curation(模型自评筛高分)。[accessed:2026-05-30]
→ **生产可行性:高,且是质量天花板的关键。** 你手上的**公版文学/自有授权小说**是"只有答案没指令"的散文,Humpback 把它们**逆向成"写作指令→真人范文"金标准 SFT 对**——答案端是真人文笔而非 AI slop。**这是用真数据兜住"文笔上限"的关键手法**,直接对冲"纯合成塌缩到 teacher 风格"的风险。

### 3.5 LongWriter / AgentWrite —— 长文能力(网文必备)
[《LongWriter》arXiv 2408.07055](https://arxiv.org/abs/2408.07055)(THUDM),2024-08。发现写不长是因 SFT 缺长输出样本;AgentWrite 拆"超长生成"为带字数规划子任务,合成 **LongWriter-6k**(输出 2k–32k 词)。[THUDM/LongWriter](https://github.com/THUDM/LongWriter)(Apache-2.0,ICLR 2025)。[accessed:2026-05-30]
→ **生产可行性:高。** 本项目单章 2000–4000 字且需连贯,其"规划→分段写"管线和长输出配方可直接移植。**呼应 R11/R15:长篇一致性是真问题,须靠自有 memory + 解码控制 + 长输出 SFT 共治,不能寄望 API 黑盒。**

### 3.6 写作专用 LLM 整套范式参考:Weaver
[《Weaver: Foundation Models for Creative Writing》arXiv 2401.17268](https://arxiv.org/abs/2401.17268),2024-01。专为创作的 LLM 家族(Mini 1.8B → Ultra 34B),**在精选写作语料预训练** + "指令数据合成 + 对齐"对齐到职业写手偏好;小模型打赢数倍大的通用模型。[accessed:2026-05-30]
→ **验证了"专用语料+写作专项对齐 > 通用大模型"——与 R11"自建开源底座+微调顶天花板"立场完全一致。**

> **生产判断(整体)**:**生产级最优且值得一步到位。** 组合拳 = Magpie(指令多样)× Persona Hub/OpenCharacter(角色/视角/对白多样)× Humpback(把真散文逆向成金标准)× LongWriter(长文)。**teacher 必须用当前最强中文写作模型**——R11 锚点给出具体人选:Kimi K2.6 / DeepSeek-V3.2 留作蒸馏教师与质量天花板对照(中文写故事横评 Kimi K2 #1、DeepSeek V3.2 #2)。**用过时弱模型蒸馏会把弱 teacher 的 slop 固化进权重,自废武功。**

---

## 4. 数据清洗 与 去 slop

### 4.1 去 slop 工具链(sam-paech 系,事实标准;2025 已成体系)
- **Antislop 论文** [arXiv 2510.15061](https://arxiv.org/abs/2510.15061),2025-10,**ICLR 2026**,MIT。三件套:① **Antislop Sampler**(推理期回溯抑制不毁词表)② **FTPO(Final Token Preference Optimization)** 逐 token 外科式调 logit ③ **自动化 pipeline**。**实测 FTPO 减 slop 85–92% 且 GSM8K/MMLU/创作均不掉;DPO 抑制更弱却写作质量与词汇多样性显著退化。** [accessed:2026-05-30]
- [sam-paech/auto-antislop](https://github.com/sam-paech/auto-antislop):端到端——基线生成 → 统计找过度 n-gram → **自动生成 chosen/rejected 偏好对** → FTPO 微调。**这正是"反套话/对白区分度偏好对"的现成生产管线**。[accessed:2026-05-30]
- [sam-paech/slop-forensics](https://github.com/sam-paech/slop-forensics)(332★ / MIT):产出 `slop_list.json` / bigrams / trigrams / phrases.jsonl;**仅英文,中文需自建**。[accessed:2026-05-30]
- [sam-paech/antislop-sampler](https://github.com/sam-paech/antislop-sampler)(Apache-2.0,ICLR 2026):多 token 短语回溯抑制,OpenAI 兼容端点。[accessed:2026-05-30]
- [EQ-Bench Creative Writing v3](https://eqbench.com/creative_writing.html)([EQ-bench/creative-writing-bench](https://github.com/EQ-bench/creative-writing-bench) 106★;主榜 [EQ-bench/EQ-Bench](https://github.com/EQ-bench/EQ-Bench) 427★):judge=Claude Sonnet,32 prompt×3 轮,**含 Repetition + Slop Score + Rubric + Elo**;**仅英文,无中文分项**。[accessed:2026-05-30]

> **关键依存(R11 锚点)**:Antislop Sampler 与 FTPO **都要求 raw logits 访问 / 改权重**;[antislop-sampler](https://github.com/sam-paech/antislop-sampler) README 明言"Commercial APIs typically lack these capabilities, making them incompatible";Kimi 官方 API 不支持 logit_bias/logprobs。**这意味着 §4.1 这套去 slop 体系只有在 R11 选定的自托管开源底座上才能跑通**——语料/偏好对再好,没有能碰 logits 的底座也用不上。**语料自建与底座自托管在此处硬绑定。**

### 4.2 中文 slop 资源缺口(关键自建项,即护城河)
- **无成熟中文 slop 词表**。仅找到零星项目:`说人话`(Chinese-first 降 AI 腔写作精炼)、`BlinkDL/AI-Writer`(RWKV 中文网文生成,prior art)。`[no-source-found:现成中文 slop 词表]`
- 中文 AI 套话自成一套("不禁""嘴角勾起一抹弧度""空气仿佛凝固""作为一个……""值得一提的是"),需**自采中文人类基线语料 + slop-forensics 方法论统计**生成。**这是必须自做的本地化工程,也正是质量护城河。**

### 4.3 大规模去重(基础设施全成熟件)
- `huggingface/datatrove`(Apache-2.0,最活跃):工业级语料处理/过滤/去重,最贴生产。
- `NVIDIA/NeMo-Curator`(Apache-2.0):GPU 加速,精确/模糊/语义去重 + 30+ 启发式过滤 + 质量/安全分类器。
- `ChenghaoMou/text-dedup`(Apache-2.0):MinHash-LSH/SimHash/精确子串一站式。
- `google-research/deduplicate-text-datasets`(Apache-2.0):后缀数组精确子串去重。
- `facebookresearch/SemDeDup`:**语义去重**——去掉"换皮重复",对网文海量同质化套路桥段尤其有用。
- `allenai/dolma`(Apache-2.0):开源语料+全套清洗工具,方法论模板。

> 注:本节去重工具的具体 star/license 取自原始调研页,**未纳入本轮逐条 URL 验真闸门**(验真清单聚焦语料数据集与核心论文)。落地前应以 GitHub 官方页二次确认 license。

### 4.4 中文 continued-PT 语料(若补语感)
- [opencsg/Fineweb-Edu-Chinese-V2.1](https://huggingface.co/datasets/opencsg/Fineweb-Edu-Chinese-V2.1)(**cc-by-sa-4.0 / copyleft**)+ `chinese-cosmopedia` + `smoltalk-chinese`(OpenCSG 系,质量较高但 **ShareAlike** 需评估商用约束)。
- `Skywork/SkyPile-150B`(**150B token**,license=other,**需逐项核可商用**)。
- [liwu/MNBVC](https://huggingface.co/datasets/liwu/MNBVC) / [esbatmop/MNBVC](https://github.com/esbatmop/MNBVC)(MIT,对标 40T+,含小说/书籍/台词):**坑**——repo 标 MIT 不代表内含**爬取网文/小说子集**可商用,**必须按子集挑、剔除商业网文部分**。[accessed:2026-05-30]

> **生产判断(清洗)**:去重+去 slop 基础设施**全部成熟开源**。**唯一需自建的是"中文 slop 词表 + 中文创作评判 rubric"**——恰是护城河,值得重投。

---

## 5. 偏好对(Preference Pairs)—— 专攻"对白区分度 / 反套话"

把系统从"合格"推到"最好"的临门一脚,**必须定制构造**,无现成中文资源。

**可落地配方:**
1. **反套话对(用 auto-antislop / FTPO)**:同 prompt,chosen=低 slop 精修版,rejected=slop-forensics 测出高 slop 版(或弱模型/高温套话版)。**优先 FTPO 而非朴素 DPO**——[arXiv 2510.15061](https://arxiv.org/abs/2510.15061) 实测 DPO 在写作上抑制更弱且质量退化,FTPO 减 slop 85–92% 不掉能力。
2. **对白区分度对**:chosen=多角色对白中**每个角色语域/口头禅/句长/用词层次明显不同**;rejected=所有角色"一个腔调"。**用 Persona Hub/OpenCharacter 的 persona 作角色声音发生器**批量造 chosen,单一 persona 复制造 rejected。可借 [RoleLLM arXiv 2310.00746](https://arxiv.org/abs/2310.00746)(RoleBench 16.8万样本)的角色扮演评测/激发范式作中文对照设计。[accessed:2026-05-30]
3. **方法支撑**:与 Weaver"对齐到职业写手偏好"一致;[《What Matters in Data for DPO》arXiv 2508.18312](https://arxiv.org/abs/2508.18312) 指出**chosen 质量起主导、rejected 质量影响有限**,故 chosen 端要用强 teacher/真人精修。规模行业经验区间 **数千–2万对**(远低于 SFT 的 30万),精确拐点需实测。[accessed:2026-05-30]

> **生产判断**:对白区分度+反套话**不可能靠通用偏好集解决**,必须围绕中文小说专门造对。这是用户"绝不质量妥协"立场下**最该早做、竞品最少触及**的环节。
>
> **R15 锚点校准(重要,防误决策)**:R15 已查明——"纯 prompt 对对白区分度有结构性天花板"这条约束**半真**,且用户记忆里挂的论据(RPNA / arXiv 2510.24677)是**张冠李戴的错引**(该 paper 实为"医疗 LLM 神经元消融",与对白区分度无关),**不可拿它当地基决策依据**。因此本节偏好对的正确定位是:**对白区分度的第一防线是底座选型(Claude 系/选对开源底座本身就能吃掉大半差距)+ 角色级 prompt 工程 + 离线 stylometric 评测(Burrows' Delta / 引文归属分类器,arXiv 2301.05659、2401.16968 现成方法);只有当这三层跑满仍有 gap、且离线评测证明 gap 来自模型本身,FTPO 偏好对才作为"有数据支撑的天花板加层"上场。** 偏好对是**强力差异化武器**,但不是"因为有天花板所以必须地基期就训"——它是可触发的升级项。

---

## 6. 量级与成本(规划用)

| 阶段 | 规模锚点 | 来源 | 成本量级 |
|---|---|---|---|
| (**可选/可触发**)Continued-PT 补语感 | 数亿–数十亿 token | OpenCSG/SkyPile 子集 + 公版 + 自有 | 主成本=算力;获取低 |
| SFT 写作对齐 | **1k 级精品**(LIMA);长文另 **~6k**(LongWriter) | Magpie+Persona/OpenCharacter+Humpback 合成 + 真种子 | 主成本=teacher 推理 token + 人工精修 |
| 偏好(反套话/对白) | **数千–2万对** | auto-antislop + 自建对(§5) | 主成本=人工/强模型评判 |

- **LIMA 锚点**:[arXiv 2305.11206](https://arxiv.org/abs/2305.11206) 1000 条精选、LLaMa-65B、无 RLHF,人评 43% 场景不输 GPT-4 → 写作对齐"质 >> 量",别堆量堆出一堆 slop。[accessed:2026-05-30]
- **微调成本(来自 R11 锚点,可直接复用规划)**:70B QLoRA ≈ 8–12h on H100($10–16);全量微调 8×H100 24–48h ≈ $250–500。**微调本身不是成本瓶颈,teacher 蒸馏 token 与人工精修才是。**
- **continued-PT 是否真需要**:R15 立场提示——**不要为"语感"在地基期就上 continued-PT**。先用 §3 合成 SFT + §5 偏好对把底座对齐到目标;只有当评测证明"语感/修辞密度"确有可归因于预训练分布的 gap 时,才补 §4.4 的数亿–数十亿 token。属可触发项。`[no-source-found:中文创作 PT 规模消融具体拐点]`

---

## 7. Top 推荐配方(从 0 做对的优先级)

1. **法务先行(不可妥协地基)**:锁死"绝不碰商业网文爬取"红线(§2),建立**公版 + 自有授权**两条干净来源,**全程留存来源链路证据**(应对《暂行办法》第七条)。
2. **自建合成 pipeline**:Magpie(指令)× Persona Hub/OpenCharacter(角色/视角/对白)× **Humpback 把公版/自有散文逆向成金标准 SFT** × LongWriter(长章节)。**teacher = 当前最强中文写作模型(R11:Kimi K2.6 / DeepSeek-V3.2 作蒸馏教师)**。
3. **自建中文去 slop 体系**:移植 slop-forensics 方法论 + **自建中文 slop 词表**(参考 `说人话`)+ antislop 采样;去重用 datatrove/NeMo-Curator/SemDeDup。**前提:跑在 R11 自托管开源底座上(能碰 logits)。**
4. **专项偏好对(差异化护城河,可触发升级项)**:用 **auto-antislop + FTPO** 围绕"对白区分度 + 反套话"造对(优先 FTPO 而非 DPO)。**按 R15 校准:先底座选型 + 角色级工程 + 离线 stylometry,确认 gap 归因模型本身后再上。**
5. **评测闭环(地基期就建)**:搭**中文版 EQ-Bench-Creative 式 LLM-judge 榜(judge 用 Claude)+ slop 分 + 重复分 + Burrows' Delta 对白可分性**,持续回归。

---

## 8. 成本/风险

- **法律风险(最高,一票否决)**:误用商业网文 → 侵权(有 1.35亿罚没刑案)+ 违反《暂行办法》第七条。缓解:全程只用公版+自有+合成,留证据。
- **质量风险**:teacher 选弱 → 弱 slop 固化进权重。缓解:只用旗舰 teacher(R11 指名),Humpback 用真人散文兜上限。
- **license 暗雷**:Persona Hub 数据集 **非商用**、OpenCharacter **研究用定位**、OpenCSG **ShareAlike**、SkyPile/MNBVC **license 需逐子集核**、webnovel_cn 标 MIT 但**内容是爬取网文(MIT 无效)**——**用方法/代码,不直接用受限或盗版来源数据训生产模型**。
- **中文 slop 表缺口**:无成熟现成资源,需自建(工程量中等,是壁垒)。
- **公版文体错配 + 合成同质化**:公版当营养剂非主食;纯合成易塌缩到 teacher 风格 → Persona Hub 强制多样 + SemDeDup 语义去重 + 真种子(Humpback)锚定。
- **底座绑定风险(实为优势)**:§4.1/§5 的去 slop 与 FTPO 强依赖自托管开源底座——这与 R11 决断同向,**不是新增风险,而是同一个一步到位决策的必然结果**。

---

## 9. Open Questions(需实测/进一步确认)

1. **中文 slop 词表最优构造法与覆盖度** —— 无公开中文资源,需自采基线统计。`[no-source-found]`
2. continued-PT **需不需要、需多少 token** 才显著改善中文语感(vs 直接 SFT)—— 需消融。`[no-source-found:中文创作 PT 规模消融]`
3. 偏好对(对白区分度)**精确规模/配比拐点**;FTPO vs DPO 在**中文创作**上的具体增益(英文已证,中文未实测)。`[no-source-found:中文实测]`
4. SkyPile-150B / MNBVC / COIG-CQIA 各**子集 license 可商用性**需法务逐项核(尤其 MNBVC 网文部分)。
5. 微调**硬件时数/吞吐/美元成本**精确值依 teacher 与框架而定(R11 给出量级,精确吞吐未覆盖)。`[no-source-found:具体硬件吞吐基准]`
6. 是否值得自建一个**干净的中文授权网文采购管线**(向作者/平台采买)作为长期最优——属商务/法务决策,本调研未估价。

---

## 10. 引用验真闸门结果

- 本轮对 R13 引用的 **30 条核心 claim**(语料数据集 + 全部支撑论文/工具仓)逐条过验真:**全部 exists=true,无一剔除**。详见各章内联 URL。
- **未发现 exists=false 的引用**,故 `hallucinations_removed` 为空(仅记录跨方向的错引校准,见下)。
- **跨方向错引校准(非 R13 自身引用,来自 R15 锚点,在此显式标注以防误用)**:用户记忆中"对白区分度天花板"的论据 **arXiv 2510.24677(实为医疗 LLM 神经元消融 RPNA)** 与 **arXiv 2510.20266(实为图像去雾 GUSL-Dehaze)** 均为张冠李戴/同号误配,**两者都未出现在本 R13 报告的论证链中**,本报告也不依赖它们。任何后续决策不得以这两条作为"必须自建训练"的地基依据。
- §4.3 去重工具的 star/license 数值取自原始调研、未纳入本轮逐条 URL 验真,落地前以官方页二次确认(已在该节标注)。

---

## 11. production_verdict(不妥协生产级取舍结论)

**结论:R13 语料路线的生产级唯一正解 = 100% 自建("法务清洁地基 + 合成 pipeline + 中文去 slop 体系 + 专项偏好对 + 评测闭环"),从第一天就做,不存在合格的"先现成、后自建"路径。**

逐项取舍:

1. **现成中文网文数据集:不达标,直接淘汰。** 全部存活但全部满足"盗版来源 / license 无效 / 体量年代不足"中至少两条。任何"先用 jetaudio/webnovel_cn/silk-road 凑合训练、上线前再换干净来源"的分期 = **把版权炸弹焊进权重 + 违反《暂行办法》第七条**,是用户明确拒绝的埋雷。**一票否决,无商量余地。**

2. **合成 pipeline(Magpie×Persona/OpenCharacter×Humpback×LongWriter):达标,值得一步到位重投。** 这不是"凑合方案",而是 2024–2025 验证过的生产主流,且**与 R11"自建开源底座+微调"严丝合缝**——只有掌握权重的底座能消化这套 SFT。teacher 必须用旗舰中文写作模型(R11:Kimi K2.6/DeepSeek-V3.2),用弱 teacher 蒸馏 = 自废武功,同样不达标。

3. **中文去 slop 体系 + 专项偏好对:这是护城河,且只有自建底座能落地。** Antislop Sampler / FTPO 强依赖 raw logits 与改权重,纯 API 主路径**结构上做不到**(Kimi 官方 API 连 logit_bias 都不给)。**所以"语料自建"与 R11"底座自托管"是同一个决策的两面,绑死。** 中文 slop 词表无现成资源,必须自采基线统计——这正是竞品最少触及、最该早做的差异化壁垒。

4. **一处必须纠偏的"过度自建"诱惑:** 偏好对/微调**不应**因"对白区分度天花板"这条(已被 R15 查实为错引的)约束而在地基期无条件上马。正解是**底座选型 + 角色级 prompt 工程 + 离线 stylometry 评测**三层先跑满,确认 gap 确实来自模型本身后,FTPO 偏好对再作为"有数据支撑的加层"触发。把它当**可触发升级项**而非**必选地基**,才是真正的"一步到位做对"——既不埋雷,也不为错引的约束过度工程。continued-PT 同理(可触发,非必选)。

5. **法务地基(只用公版+自有授权+合成、全程留证)不达标即全盘归零。** 它不是"风险项"而是"是否合法存在"的前提,必须最先锁死。

**一句话:** 现成中文网文集对生产是死路(盗版+无效 license,分期使用即埋雷,一票否决);唯一达标路线是从 0 自建合成+清洗+偏好+评测全链,并与 R11 自托管开源底座硬绑定(去 slop/FTPO 必须碰 logits);其中合成 SFT 与中文去 slop 词表是必做地基与护城河,偏好对/微调/continued-PT 是有评测数据支撑后才触发的升级项,而非为(已被证错引的)"天花板"约束在地基期盲目上马。
