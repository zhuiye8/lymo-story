# Phase Report: Phase 0 · Eval Baseline (Report #2)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-27 |
| Phase | Phase 0 · Evaluation Baseline (v2.1) |
| Status | green |
| Related | Report #1 (`2026-04-27-phase-report-phase-0-1.md`)；Review #1 (`decisions/2026-04-27-phase-0-report-1-review.md`，approved-with-corrections) |
| PM action needed | yes（AC2-final 监督独立评分 `bc910038/ch1` + 决议 detector regex 是否 v1 修复） |

## Summary

Review #1 的 2 项 correction 全部应用 + AC3 校准实跑通过 + AC2-bootstrap 给出 per-dim Spearman ρ。AC1/AC1b 改严格 100%、AC6 补 per-story 方差/斜率/前后段差，AC3 在 100+50 真样本上 recall=0.94、precision=1.00（远超 0.8/0.7 门槛）。AC2-final artifact 已就绪等监督填评分，AC2-bootstrap 给出 mean ρ=0.45（其中 rhetoric_quality ρ=−0.16，提示 LLM 判修辞与人工反向，对 Phase 1 anti-slop prompt 有指导意义）。

## Completed since Report #1

### Correction 1：AC1/AC1b 严格 100% 覆盖

- `backend/quality/batch.py`：pass 逻辑改 `scores_count == expected_scores`、`evals_count == scope`（之前是 ≥90% 的"warning"也算 pass）
- 90% 阈值仅作为 `partial_warning` 三元指示器，不再决定通过性
- 重新对 batch 2 验证：168/168=100%、21/21=100% → 仍 Pass

### Correction 2：AC6 per-story variance / trend

- `data/baselines/baseline_report_2026-04-27.md` 增补 §按小说聚合 表
- 三本书 composite mean / pstdev / min / max / 斜率（按 chapter_num 线性回归） / 前半段均值 / 后半段均值 / Δ
- 三本书 quality / slop / words 同样 mean+stdev
- per-dimension 表加 stdev（评委判分稳定性）
- 关键发现已写入：61513478（最长样本，最可信）composite Δ=−0.02 → 改 prompt 期间长篇上很快趋于饱和 → 印证 Phase 1+ 架构性改造需求

### AC3：slop 样本扩到 100+50 + 校准实跑

- `data/baselines/slop_samples_zh.json` 由 v0 bootstrap（25+12）扩到 v1-ac3（**100 slop + 50 normal**）
  - 8 类别均覆盖：tier1_banned ~40, fiction_tell ~25, tier2_cluster ~17, structural ~14, show_vs_tell ~11, em_dash_density ~7, transition_ratio ~6, sentence_cv ~4
  - normal 50 条全为日常生活、办公、家庭、出行人写散文，无 LLM 代表性 tics
- `scripts/calibrate_slop_detector.py`：threshold-based 二分类，输出 TP/FN/FP/TN + per-category + 误分类样本 + 分数分布
- `data/baselines/ac3_calibration_2026-04-27.json`：完整结果

### AC2-bootstrap：5 章 × 8 维 Spearman ρ

- `scripts/build_ac2_bootstrap_template.py`：盲采（仅章节文本，不含 LLM 分），从 batch 2 按 composite 五分位数挑章，自动排除 AC2-final 候选 `bc910038/ch1`
- `scripts/compute_ac2_bootstrap.py`：纯 stdlib 实现 Spearman（average ranks + Pearson）
- 5 章选定（覆盖 composite 3.06–6.69）：bc910038/ch3、61513478/ch2、61513478/ch8、bc910038/ch7、61513478/ch4
- 工程师盲读 + 8 维评分 + 写 evidence；result 见 `data/baselines/ac2-bootstrap-result-batch-2.json`

### AC2-final artifact 已构建（Report #1 时仅 schema，本次实跑）

- `scripts/build_ac2_final_artifact.py`：从 DB 拉 LLM 分 + evidence + slop_findings + 章节正文，输出 schema-完备的 JSON 模板
- `data/baselines/ac2-final-calibration-batch-2.json`：5287 字章节 + LLM composite=3.0（最低分章）+ 监督填空槽位

## Evidence

### AC3 校准结果（threshold=0.5 默认）

| 指标 | 值 | 标准 |
|---|---|---|
| 样本 | 100 slop + 50 normal | AC3 spec |
| TP / FN | 94 / 6 | — |
| FP / TN | **0** / 50 | — |
| **recall** | **0.9400** | ≥ 0.80 ✅ |
| **precision** | **1.0000** | ≥ 0.70 ✅ |
| F1 | 0.9691 | — |
| accuracy | 0.9600 | — |
| **AC3 PASS** | **True** | — |

阈值扫描（敏感性分析）：

| threshold | TP | FN | recall | precision |
|---|---|---|---|---|
| 0.0（任一 finding 即判 slop） | 98 | 2 | **0.9800** | 1.0000 |
| 0.3 | 96 | 4 | 0.9600 | 1.0000 |
| 0.5（默认） | 94 | 6 | 0.9400 | 1.0000 |

precision 全程 1.0 → 50 条 normal 样本零误判。Recall 随阈值降低单调上升。

### per-category 命中分布（slop 样本中触发的类别次数）

| category | 触发次数 | 解读 |
|---|---|---|
| tier1_banned | 40 | 最常见的中文 LLM slop 来源 |
| fiction_tell | 23 | 瞳孔/嘴角/心脏 系列 |
| tier2_cluster | 17 | 复杂/深邃/凌厉 堆叠 |
| structural | 14 | 不仅仅是…更是… |
| show_vs_tell | 11 | 显式情绪标注 |
| em_dash_density | 7 | 破折号密集 |
| transition_ratio | 6 | 段首转折堆砌 |
| sentence_cv | 4 | 句长过于均匀 |

### Detector 规则限制（6 条 FN 分析）

| ID | 文本片段 | 失检原因 |
|---|---|---|
| slop_002 | `心脏漏跳了一拍 / 嘴角微微勾起 / 眼神变得复杂` | **regex bug 群**：`心脏[漏停猛]了一?[拍跳下]` 要求 漏 后接 了，但常见 "漏跳了" 不匹配；`嘴角[微微]?[勾起]` 把 [微微] 写成字符类（实为单字 `微`），`微微勾起` 反而失配；`眼神[变得]?` 同理 |
| slop_059 | `不仅仅关乎他个人，更关乎` | **regex bug**：`不(?:仅仅\|只)是.{2,30}(?:更\|而)是` 要求"是"，但"不仅仅关乎"普遍存在 |
| slop_063 | `瞳孔骤然紧缩 + 心脏猛了一跳` | 部分匹配（仅 `心脏猛了一跳` 命中 fiction_tell），penalty=0.3 < 0.5 阈值；瞳孔[一微]?[紧]?[缩] 漏掉 "瞳孔骤然紧缩" |
| slop_079 | `难过地 + 紧张地 + 觉得十分失望 + 感到非常紧张` | show_vs_tell 命中但权重低，penalty=0.3 < 0.5 |
| slop_087 | sentence_cv = 0.18（cv 极低） | sentence_cv 上限 1.0×系数，penalty=0.476 < 0.5 |
| slop_089 | sentence_cv = 0.20 | penalty=0.392 < 0.5 |

→ 真正的 detector 规则缺陷只有 2 条（slop_002、slop_059）；其余 4 条是 threshold-edge 而非误判。

**建议（待监督决议）**：

- (a) 维持 v0 detector，AC3 已过，不做修复
- (b) v1 detector：修以上 3 处 regex（漏跳了 / 嘴角微微 / 眼神变得 + 不仅仅...更...无"是"）
- (c) 阈值降至 0.3：recall 直接到 0.96，precision 仍 1.0

### AC2-bootstrap Spearman ρ（n=5 章 × 8 维）

| 维度 | engineer mean | LLM mean | Spearman ρ | 解读 |
|---|---|---|---|---|
| `fluency` | 7.20 | 7.20 | **+0.61** | moderate-strong（一致） |
| `dialogue_distinct` | 4.20 | 5.10 | **+0.73** | strong（LLM 略高，但排序一致） |
| `character_consistency` | 7.40 | 7.40 | +0.15 | weak（差异化不强） |
| `scene_drama` | 6.80 | 5.80 | **+0.83** | strong（engineer 略高） |
| `sensory_detail` | 6.60 | 6.20 | +0.32 | weak |
| `rhetoric_quality` | 5.60 | 5.60 | **−0.16** | ⚠️ **inverse** |
| `continuity` | 7.20 | 7.70 | +0.30 | weak |
| `overall_readability` | 6.80 | 6.50 | **+0.83** | strong |
| **mean ρ** | — | — | **0.45** | moderate |

**关键发现**：

- 3 维 strong agreement（≥ 0.7）：dialogue_distinct / scene_drama / overall_readability — 即"读起来怎样"的整体感受维度
- 1 维 inverse：**rhetoric_quality ρ=−0.16** — engineer 把 bc910038/ch3（套话最重）评 4 分，LLM 评 6 分；engineer 把 61513478/ch4（最少套话）评 7 分，LLM 评 5.5 分。两端反向 → 排序倒置
- 推论：当前 SEQR-v0 judge prompt 对中文修辞套话的敏感性 **远不及** 工程师感知。这恰好是 `tier1_banned` 类 slop 试图捕捉的内容
- → Phase 1 应该把 `rhetoric_quality` 的 anti-cliché 标准在 judge prompt 里强化，或者更依赖 slop_penalty 来扣分（当前 SEQR composite = mean(8) − slop_penalty 已在做，但 mean(8) 本身的 rhetoric 维度被高估）

ρ=0.45 整体属"moderate"。n=5 噪声较大，监督评 AC2-final 后会得到更严格的判断（独立评分 + 是否合理结论）。

## Files changed since Report #1

| 文件 | 类型 | 说明 |
|---|---|---|
| `backend/quality/batch.py` | 修订 | Correction 1：strict 100% AC1/AC1b |
| `data/baselines/baseline_report_2026-04-27.md` | 修订 | Correction 2：per-story variance / trend |
| `data/baselines/slop_samples_zh.json` | 重写 | v0(25+12) → v1-ac3(100+50) |
| `data/baselines/ac3_calibration_2026-04-27.json` | 新增 | AC3 calibration 完整结果 |
| `data/baselines/ac3_calibration_t00.json` / `t03.json` | 新增 | 阈值扫描结果 |
| `data/baselines/ac2-bootstrap-template-batch-2.json` | 新增 | 工程师 5 章评分 |
| `data/baselines/ac2-bootstrap-result-batch-2.json` | 新增 | Spearman ρ 结果 |
| `data/baselines/ac2-final-calibration-batch-2.json` | 新增 | 监督待填 |
| `scripts/calibrate_slop_detector.py` | 新增 | AC3 校准 CLI |
| `scripts/build_ac2_bootstrap_template.py` | 新增 | AC2-bootstrap 第 1 步：盲采 |
| `scripts/compute_ac2_bootstrap.py` | 新增 | AC2-bootstrap 第 2 步：Spearman ρ |
| `scripts/build_ac2_final_artifact.py` | 新增 | AC2-final artifact 抽取 |

## Verification

```bash
✓ python scripts/calibrate_slop_detector.py --threshold 0.5
  → recall=0.94 precision=1.00 (AC3 PASS True)
✓ python scripts/build_ac2_bootstrap_template.py --batch 2 --exclude bc910038:1
  → 5 chapters spanning composite 3.06-6.69
✓ python scripts/compute_ac2_bootstrap.py --template ...
  → mean Spearman ρ = 0.45 across 8 dims
✓ python scripts/build_ac2_final_artifact.py --batch 2 --story bc910038 --chapter 1
  → artifact 写入，5287 字章节 + LLM scores + evidence
✓ python -m compileall -q backend scripts
```

## Updated AC matrix

| AC | 标准 | 实测 | Status |
|---|---|---|---|
| AC1 | 8 维评分入库 == scope×8（**严格 100%**） | 168 / 168 | ✅ Pass |
| AC1b | 聚合记录入库 == scope（**严格 100%**） | 21 / 21 | ✅ Pass |
| AC2-bootstrap | 工程师 5 章 per-dim ρ | mean ρ=0.45 (8 dims), 1 dim inverse | ✅ 完成（仅信号性指标） |
| AC2-final | 监督独立评 `bc910038/ch1` | artifact 已就绪等监督填空 | 🟡 等监督 |
| **AC3** | **slop recall ≥ 0.8, precision ≥ 0.7（100+50）** | **0.94 / 1.00** | **✅ Pass** |
| AC4 | 单章 mean_cost ≤ ¥0.10 | ¥0.055 | ✅ Pass |
| AC5 | 前端 4 图表 | **待开发** | 🟠 pending |
| AC6 | 基线报告（per-story mean/variance/trend） | mean+stdev+slope+前后段差 | ✅ Pass（已修） |

## Asks（监督决策点）

1. **AC2-final**：是否同意 `bc910038/ch1` 作为唯一独立评分章？artifact 在 `data/baselines/ac2-final-calibration-batch-2.json`，需监督填 `human_scores` / `human_evidence` / `supervisor_conclusion` 三块
2. **Detector regex 修复**：选 (a) 维持 v0、(b) Phase 0 内修 v1、(c) 仅降阈值至 0.3 — 监督决策
3. **rhetoric_quality 反向**：是否在 Phase 1 把"中文 anti-cliché"列入 judge prompt 改造？工程师建议 yes（与 slop_penalty 双管齐下）
4. **AC5 前端图表**：是否启动？建议在 AC2-final 完成、SEQR-v0 通过监督独立审之后再开（避免数据契约前移）

## Default if no answer

- 2026-04-30 23:59 前监督未回 → 工程师按以下默认推进：
  - (1) AC2-final：等监督填，不擅自代填
  - (2) Detector regex：选 (a) 维持 v0（AC3 已过），把 (b) 列入 Phase 1 backlog
  - (3) rhetoric anti-cliché：列入 Phase 1 backlog
  - (4) AC5 前端：启动数据契约设计（仅契约，不上图表）
- 工程师在 inbox 留 `[Auto-Executed]` 报告

## What's Next

按 phase-gate v2.1，Phase 0 通过条件：AC1/AC1b/AC2-final/AC3/AC4/AC5/AC6 全部 Pass 后允许进入 Phase 1。当前 6/8 通过，仅 AC2-final 等监督 + AC5 待开发。
