# R9 · 中文网文专属 layer

| Field | Value |
|---|---|
| Topic | 中文 LLM 在网文生成上的对比；中文 platform 的题材分布；中文专属 narratology；阅文妙笔等产品级实践 |
| Author | engineer (Claude) |
| Researched | 2026-04-28（WebSearch + WebFetch only） |
| Verdict | **DeepSeek 不一定是 Phase 1 默认 model**；**Kimi K2.6 / GLM-5.1 中文文笔更强**；中文 narratology（Creative Convergence 的 34 narrative functions）应进 outline 设计 |

> 用户优先级声明：等通用模式（R1/R2/R4/R5）清楚后再叠中文 layer。本 doc 给"中文专属"的具体差异点。

## Findings

### F1 · Top-5 中文 LLM（2026-04 排名）

| Model | 中文文笔 | 代码 | 价格 | 长上下文 | 推理 |
|---|---|---|---|---|---|
| DeepSeek V4+/V4-Pro | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 极便宜 | 128k | ⭐⭐⭐⭐ |
| Qwen 3.6 / Qwen3-Max | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 极便宜 | 128k+ | ⭐⭐⭐⭐ |
| **Kimi K2.6** | **⭐⭐⭐⭐⭐** | ⭐⭐⭐ | 便宜 | **200k+** | ⭐⭐⭐⭐ |
| MiniMax M2.7 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 便宜 | 128k | ⭐⭐⭐ |
| **GLM-5.1** (智谱) | **⭐⭐⭐⭐⭐** | ⭐⭐⭐⭐ | 便宜 | 128k | ⭐⭐⭐⭐ |

来源：[NextFuture LLM 对比](https://nextfuture.io.vn/blog/2026-chinese-llm-stack-qwen-deepseek-minimax-kimi-glm-compared) [accessed:2026-04-28]、[TokenMix Q2 2026 update](https://tokenmix.ai/blog/best-chinese-ai-models-2026-comparison-guide) [accessed:2026-04-28]

**关键 verbatim 评价**（[global-apis.com](https://global-apis.com/blog/deepseek-vs-qwen-vs-kimi-vs-glm-2026) [accessed:2026-04-28]）：
> "For Chinese language tasks, both GLM and Kimi excel with 5-star ratings, while for code generation, DeepSeek leads with a 5-star rating."

**对我们的可行性**：
- ⚠️ **重大发现**：Phase 0 baseline 用的是 DeepSeek V4-Pro，但 DeepSeek 在**中文文笔**评分**低于 Kimi 和 GLM**
- ✅ 价格优势：Phase 0 单章 ¥0.055 主要靠 DeepSeek 便宜
- 🟡 **Phase 1 应做 A/B**：同一章用 Kimi K2.6 / GLM-5.1 / DeepSeek V4-Pro 各跑一次，让 SEQR rubric 打分 + 人审
- 价格补偿可能：Kimi 200k context 可以减少多次调用次数

### F2 · 阅文妙笔（中国 #1 网文厂的工具）

| Field | Value |
|---|---|
| 工具名 | 阅文妙笔 / 作家助手妙笔版 |
| Source | [aigc.cn/sites/12902](https://www.aigc.cn/sites/12902.html) [accessed:2026-04-28] + [news.dayoo.com (阅文部署 DeepSeek)](https://news.dayoo.com/gzrbrmt/202502/15/170636_54787434.htm) [accessed:2026-04-28] |
| 状态 | 已上线（2023-07 首发，2026-02 集成 DeepSeek-R1） |
| 工厂背景 | **国内第一个网文大模型**（首发 2023-07） |

**核心功能 4 件套**（verbatim from aigc.cn）：
- 世界观设定
- 角色设定
- 情景描写
- 战斗描写

**DeepSeek-R1 集成 升级**（verbatim from news.dayoo.com）：
> "DeepSeek-R1大模型对国内网文进行AI辅助润色，帮助作家启发思路、提升文笔，尤其擅长战斗描写及对话补足。"

**关键设计哲学**（verbatim）：
> "AIGC不会取代作家，它是创作的金手指，而主角永远是作家"

**对我们的可行性**：
- ✅ **重要参考**：阅文是中国最大网文公司，他们的产品方向就是 4 件套 + 润色辅助
- ⚠️ 不开源（"作家助手" 是闭源 SaaS），只能看产品形态
- ✅ **方向验证**：四件套 = 世界 / 角色 / 场景 / 战斗 = 我们 Phase 0 Director / Camera / Writer agent 的对应 → 说明业内 agent 拆分思路收敛
- adoption cost: N/A（不开源）；学习 cost: high（看他们的 user feedback 趋势）

### F3 · Creative Convergence or Imitation（arxiv 2603.14430，2026-03）

| Field | Value |
|---|---|
| Paper | [arxiv.org/abs/2603.14430](https://arxiv.org/abs/2603.14430) [accessed:2026-04-28] |
| Authors | Yuanchi Ma 等 8 人（affiliations 在 abstract page 不可见） |
| Date | 2026-03 |

**核心 claim**（verbatim from abstract）：
> "LLM-generated texts exhibit structurally homogenized stories, frequently following repetitive arrangements and combinations of plot events along with stereotypical resolutions. The root cause is that models are unable to correctly comprehend the meanings of narrative functions and instead adhere to rigid narrative generation paradigms."

**核心贡献**：
- 扩 Propp narratology（俄国民间故事 31 functions）→ **34 modern web-narrative functions for Chinese web fiction**
- 构建 human-annotated corpus 分析 LLM-generated 文本的 narrative structure

**verbatim 34 narrative function 列表 — 未在 abstract 中**：
- ⚠️ 需要下载 full PDF 才能看 34 个 function 名字
- 已 search snippet 提到包含 **金手指** / **打脸** 等中文 web 网文专属功能（per R1 agent finding，需 verify）

**对我们的可行性**：
- ✅ **Outline 设计的关键武器**：把 34 functions 列表加进 OutlinePlanner 的 prompt，让 LLM 必须 explicitly tag 每个 beat 是哪个 function
- ✅ 中文 native：直接覆盖网文真实结构
- adoption cost: **low-medium**（需要先拉 34 个 function 列表，再做 prompt engineering）

### F4 · 平台题材分布（市场情报）

来源：[zhihu.com/p/1936374238455001232 (平台对比)](https://zhuanlan.zhihu.com/p/1936374238455001232) [accessed:2026-04-28]、[艾媒网 2025 IP 排行](https://www.iimedia.cn/c1088/106462.html) [accessed:2026-04-28]

#### 番茄小说

- 用户：Z 世代 + 一线 + 中西部二三线
- 头部作品案例：《十日终焉》8000 万+ 读者
- 男频热门：**系统 / 穿越 / 无敌**
- 女频热门：**甜宠 / 穿越 / 双洁**
- 子题材趋势：游戏现实主义

#### 七猫小说

- 用户：受众偏大，Z 世代 + 新锐白领 + 小镇青年
- 男频热门：**系统流 / 赘婿 / 战神**
- 女频热门：**逆袭 / 萌宝 / 虐恋**
- 风格：传统新媒体风

#### 起点读书

- 用户：95 后为主力
- 题材偏好：**现实 / 科幻 / 宏观历史 / 西方魔幻 / 克苏鲁混合**
- 头部作品风格：《诡秘之主》—— 跨文化融合
- 95 后占现实题材阅读 49%、科幻 62%

**对我们的可行性**：
- ✅ **MVP 选题策略**：男频系统流（番茄/七猫共同热门）是数据上最安全的起步
- ⚠️ DeepSeek/Kimi/GLM 在不同题材上未必同样擅长（古风可能 GLM 更好，科幻可能 DeepSeek 更好）—— Phase 1 应做题材 × Model 矩阵 benchmark

### F5 · WebNovelBench（spot-verified earlier）

| Field | Value |
|---|---|
| Paper | [arxiv.org/abs/2505.14818](https://arxiv.org/abs/2505.14818) |
| Venue | EACL 2026 Findings（确认录用） |
| Dataset | 4,000+ Chinese web novels |
| 8 维度 | 已 verbatim spot-verified in 00-summary.md |

**对我们的可行性**：
- ✅ **直接采纳作为 evaluation gold standard**：8 维度 + HF dataset MIT license
- 已经在 SEQR 里部分对齐了（dialogue_distinct / character_consistency / scene_drama / sensory_detail / rhetoric_quality 都有对应）
- Phase 1 应让 SEQR 维度名 **完全对齐** WebNovelBench 命名，方便论文引用

## Recommendation

### Phase 1 立即

1. **Model A/B 矩阵**：同 3 章 × {DeepSeek V4-Pro, Kimi K2.6, GLM-5.1} × {古风男频系统流, 现代都市}
   - 用 SEQR rubric 自动评 + 工程师抽样人评
   - 输出：每题材 × 每 model 的成本-质量曲线
   - 估时：~1 工作日（含 LLM 调用 cost ¥10-30）

2. **34 narrative functions 抓取**
   - 下 arxiv 2603.14430 full PDF（用 urllib 或 curl）
   - 提取 34 个 function 列表
   - 写入 `data/baselines/chinese_web_narrative_functions_v1.json`
   - 在 OutlinePlanner prompt 里加 function tagging 要求

3. **SEQR 维度命名对齐 WebNovelBench**
   - 当前 SEQR 8 维度 ≠ WebNovelBench 8 维度名字（虽然语义类似）
   - 重命名以方便后续学术引用 + 跨工程 comparison

### Phase 2

4. **阅文妙笔产品形态学习**
   - 抓阅文作家助手的 UI 截图（公开渠道）+ user feedback
   - 学习他们的"灵感 / 润色 / 描写 4 件套"如何在 UI 上呈现
   - 我们 admin UI 可以借鉴

5. **中文 slop 词库扩展**（与 R6 联动）
   - 从 WebNovelBench 数据集里 4000 本人写网文抽统计，对比 DeepSeek 输出的高频词，找 model-specific slop
   - 工具：slop-forensics 中文化（R6 已规划）

### Phase 3+

6. **题材专家化**
   - 不同题材各训一个 prompt template（古风 vs 都市 vs 科幻）
   - 题材分类器自动选 template

## 时效性 / 鲁棒性 / 可行性

| 信息 | 时效性 | 鲁棒性 | 可行性 |
|---|---|---|---|
| Top-5 中文 LLM 排名 | 2026-04 | ⭐⭐⭐⭐（多源 corroboration） | ⭐⭐⭐⭐⭐ |
| 平台题材分布 | 2025-2026 | ⭐⭐⭐（行业报告，非学术） | ⭐⭐⭐⭐ |
| 34 narrative functions | 2026-03 paper | ⭐⭐⭐⭐⭐（学术） | ⭐⭐⭐⭐（需 fetch full paper） |
| 阅文妙笔 | 2023 首发 + 2026 R1 集成 | ⭐⭐⭐⭐（产品级） | ⭐⭐（不开源） |
| WebNovelBench | EACL 2026 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐（已 spot-verified） |

## Open questions

- DeepSeek V4-Pro vs Kimi K2.6 vs GLM-5.1 在我们 SEQR 上的实测对比未做。可能 Phase 1 改 Kimi 收益最大。
- Creative Convergence 的 34 functions 全列表需 fetch full PDF；金手指 / 打脸 等中文专属 trope 需 verify
- 阅文妙笔的内部架构（不开源）：能否从公开技术博客/工程师面试逆向推测？
- 网文平台对 AIGC 内容的政策（番茄 / 七猫 / 起点 是否接受 AI 生成稿件？）—— Phase 4 上线前必查

## Sources

- [nextfuture.io.vn/blog/2026-chinese-llm-stack-qwen-deepseek-minimax-kimi-glm-compared](https://nextfuture.io.vn/blog/2026-chinese-llm-stack-qwen-deepseek-minimax-kimi-glm-compared) [accessed:2026-04-28]
- [tokenmix.ai/blog/best-chinese-ai-models-2026-comparison-guide](https://tokenmix.ai/blog/best-chinese-ai-models-2026-comparison-guide) [accessed:2026-04-28]
- [global-apis.com/blog/deepseek-vs-qwen-vs-kimi-vs-glm-2026](https://global-apis.com/blog/deepseek-vs-qwen-vs-kimi-vs-glm-2026) [accessed:2026-04-28]
- [benchlm.ai/best/chinese-models](https://benchlm.ai/best/chinese-models) [via search snippet, accessed:2026-04-28]
- [arxiv.org/abs/2603.14430 (Creative Convergence)](https://arxiv.org/abs/2603.14430) [accessed:2026-04-28]
- [aigc.cn/sites/12902 (阅文妙笔)](https://www.aigc.cn/sites/12902.html) [accessed:2026-04-28]
- [news.dayoo.com/.../170636_54787434 (阅文部署 DeepSeek)](https://news.dayoo.com/gzrbrmt/202502/15/170636_54787434.htm) [accessed:2026-04-28]
- [stcn.com/.../1515811 (作家助手三大功能升级)](https://www.stcn.com/article/detail/1515811.html) [via search snippet, accessed:2026-04-28]
- [zhuanlan.zhihu.com/p/1936374238455001232 (平台对比)](https://zhuanlan.zhihu.com/p/1936374238455001232) [accessed:2026-04-28]
- [iimedia.cn/c1088/106462 (2025 中国 网文 IP 排行)](https://www.iimedia.cn/c1088/106462.html) [accessed:2026-04-28]
- [cssn.cn/.../t20260420_5981165 (2025 中国 网络文学发展研究报告)](https://www.cssn.cn/skgz/bwyc/202604/t20260420_5981165.shtml) [via search snippet, accessed:2026-04-28]
- [arxiv.org/abs/2505.14818 (WebNovelBench, spot-verified)](https://arxiv.org/abs/2505.14818) [accessed:2026-04-28]
