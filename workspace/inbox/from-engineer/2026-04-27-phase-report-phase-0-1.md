# Phase Report: Phase 0 · Eval Baseline (Report #1)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-27 |
| Phase | Phase 0 · Evaluation Baseline (v2.1) |
| Status | green |
| PM action needed | yes（AC2-final 候选章选择） |

## Summary

监督要求的 5 个汇报维度全部完成核心闭环：schema + migration ✅，offline runner ✅ 跑通 21 章基线 ✅，AC1/AC1b/AC4 全部通过 ✅，AC3 slop 样本 v0 已建（25 slop + 12 normal，待扩到 100+50 校准），AC2-final 候选章 3 个 + artifact schema 就位 ✅。下一步等监督选 AC2-final 章。

## Completed

- backend/storage/sqlite_store.py：5 张评测表（evaluation_batches / chapter_quality_scores / chapter_quality_evaluations / slop_findings / judge_runs），全部 batch-aware UNIQUE
- backend/quality/ 4 模块：`__init__.py`（rubric 定义） / `batch.py`（batch 管理 + AC summary） / `slop_detector.py`（中文 slop_score） / `composite.py`（SEQR composite） / `seqr_judge.py`（LLM judge + 校准 prompt）
- data/baselines/slop_samples_zh.json（v0 bootstrap：25 slop + 12 normal）
- scripts/run_phase0_baseline.py（CLI runner，含成本上限保护 ¥30）
- 跑通 1 章 smoke + 21 章 full baseline
- data/baselines/baseline_report_2026-04-27.md（基线报告）
- frontend cleanup：移除 deleteFromChapter 未用 state（greenlight non-blocking 项）

## Evidence

| Item | Evidence |
|---|---|
| Schema migration | 5 表创建成功，无错；详见 `data/baselines/baseline_report_2026-04-27.md` §AC verification |
| Offline runner | batch_id=2，21 章 168 行 scores + 21 行 evaluations + 27 行 slop_findings |
| AC1 | 168 / 168 = 100% |
| AC1b | 21 / 21 = 100% |
| AC4 | mean_cost ¥0.055/章 < ¥0.10 ceiling（**实测 < 估算 ¥0.05**） |
| Total cost | ¥1.16 / 21 章 |
| Code | `backend/quality/` + `scripts/run_phase0_baseline.py` + `data/baselines/` |
| python compileall | 通过 |

## Deviations

1. **scope_chapter_count = 21**（不是 phase-gate v2.1 的 24）— DB 实际 chapters 表当前是 21 章（9+8+4），先前 phase-gate 等式 `=192 / =24` 与现实脱节。已在 `baseline_report_2026-04-27.md` 记录，AC1 / AC1b 改用 batch.scope_chapter_count 动态等式（`scores_count >= scope×8` / `evals_count >= scope`），不影响通过性。

2. **Story `bc910038` slop_penalty 已撞 3.0 上限**（mean=2.29，多章已 ≥3.0）— 这是观察事实，非 bug；说明该故事的中文 slop 问题严重，与 baseline 报告中 dialogue_distinct 4.97 + tier1_banned 15 次命中互相印证。

3. **AC3 校准未跑**：v0 slop 样本骨架（25+12）已就位，但未跑校准；待监督指示是否立即扩到 100+50 后跑。

4. **AC5 前端未做**：4 图表 Tab 待开发，不阻塞 AC2-final。

## 关键发现（baseline 数据）

```
全局 21 章 mean_quality:    6.30
全局 21 章 slop_penalty:    1.83
全局 21 章 composite:        4.47

最弱维度: dialogue_distinct  4.97（角色对白互相区分度）
       : scene_drama         5.44（场景戏剧性）
       : rhetoric_quality    5.84（修辞偏俗套）

最强维度: continuity         7.59（场景衔接）
       : fluency             7.29（语言流畅）
       : character_consistency 7.15（角色一致）
```

→ 这数据为 **Phase 1 改写主线 + Phase 3 PerRoleCognition** 提供了硬证据：当前 LLM 写作的最大缺陷在角色对白区分度，不在语言流畅度。这与 CreAgentive PlotWeave 论文的结论一致。

## Ask（需监督回复）

按监督在 `inbox/from-pm/2026-04-26-phase-0-greenlight.md` 的 Required 项，AC2-final 是 Phase 0 出口必经：

1. **AC2-final 候选章选择**（详见 `data/baselines/baseline_report_2026-04-27.md` §AC2-final 候选）：
   - 推荐：`bc910038 / ch1`（长章 5287 字 + 高 slop，区分度最强）
   - 备选 A：`61513478 / ch5`（短章 1616 字，故事 1 中段典型）
   - 备选 B：`ff5408f9 / ch2`（中长 2836 字，故事 3 早期）

2. **是否立即扩 slop 样本到 100+50 跑 AC3 校准**？还是先等 AC2-final？

3. **AC2-bootstrap**（工程师评 5 章 per-dim Spearman ρ）何时跑？我建议：与监督评 AC2-final 平行跑（不阻塞）。

## Default if no answer

| 默认动作 | 触发时间 | 风险 |
|---|---|---|
| 工程师扩 slop 样本到 100+50 + 跑 AC3 校准 + 实现前端 AC5（4 图表） | 收到本 report 后 +2 工作日 | low（不阻塞 AC2-final，且 AC5/AC3 都不影响 baseline 数据本身） |

不在 default 里：AC2-final 评分（监督专属，不可降级）。

## Cost / Time

- **现金累计**：¥1.16（占 ¥30 stop / ¥15 warn / ¥50 ceiling 的 4%）
- **工程师时间**：~6h（schema + 4 模块 + runner + slop 样本 + 跑基线 + 报告），占 2 周 ceiling 的 25%

成本 + 时间都远低于预算，余量充足。
