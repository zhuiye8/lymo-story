# Phase 0 Submission Change Log

| Field | Value |
|---|---|
| Author | engineer |
| Date | 2026-04-26 |
| Triggered by | `decisions/2026-04-26-phase-0-review.md` (revision-needed) |
| Previous version | `phase-gate.md` v1 / `proposal.md` v1 (rejected) |
| Current version | v2（覆盖原文件） |

## 7 项 blocking findings 的处理

| # | Supervisor finding | 处理 | 文件位置 |
|---|---|---|---|
| 1 | WebNovelBench 维度命名错误 | **采纳 Option 2**：重命名为项目本地 **SEQR**（Story Engine Quality Rubric）v0；不再声称是 WebNovelBench | phase-gate §Artifact Schema / proposal §Design |
| 2 | HNES 公式来源错误（HNES 属 CreAgentive，WebNovelBench 用 PCA+ECDF） | **重写**：改为本地 **SEQR Composite Score**（8 维度等权均值 - slop_penalty）；明确不声称是 HNES | phase-gate / proposal |
| 3 | 缺章节级聚合表 | **新增** `chapter_quality_evaluations` 表（每章一行：composite + word_count + version + judge_run） | phase-gate §Artifact Schema |
| 4 | AC1 SQL 不是合法 SQLite | **修正**：改为 UNIQUE 约束 + 简单 COUNT(*) | phase-gate §AC1 |
| 5 | AC2 校准太弱 | **强化**：(a) 改为 per-dimension Spearman 报告；(b) 拆为 AC2-bootstrap（工程师自评，仅参考）+ AC2-final（监督独立校准 1 章作为 gate） | phase-gate §AC2 |
| 6 | 硬编码 API key | **已立即修复**：`scripts/test_deepseek_v4.py` 改为 `os.environ["DEEPSEEK_API_KEY"]`；用户已说明 key 已删；建议监督在合并前再确认 revoke | scripts/test_deepseek_v4.py |
| 7 | delete-from-chapter N>1 不安全 | **已立即修复**：N>1 时返回 400 + 详细说明；N=1 全量重置仍可用；安全 rewind 设为独立 feature（非 Phase 0 范围） | backend/api/stories.py |

## 4 项 Ask 决策的吸收

| Ask | Supervisor decision | v2 行动 |
|---|---|---|
| 整体 | revision-needed | 重交 v2 |
| Judge LLM | DeepSeek-V4-Pro non-thinking 仅用于首次 PoC，AC2 修订前不锁定 | 采纳：v2 phase-gate 注明"PoC only, not bound" |
| WebNovelBench review | 必须先修正，不允许并行 | 采纳：本次重写已基于亲查论文 [verified:2026-04-26] |
| AC2 human scoring | 工程师可 bootstrap，final gate 需要独立校准或显式降级 | 采纳：拆 AC2-bootstrap + AC2-final |

## 命名变化对照

| v1 | v2 | 理由 |
|---|---|---|
| WebNovelBench 8 dimensions | **SEQR v0** (Story Engine Quality Rubric) | 论文 8 维度命名错；改名后只对论文借鉴维度概念，不冒用 |
| HNES (Sq+Sl)/2 - slop | **SEQR Composite** = mean(8 dims) - slop_penalty | HNES 来源错；改名后只对内部纵向对比 |
| `chapter_quality_scores` only | + `chapter_quality_evaluations` | 缺聚合表；现在双表（明细 + 聚合） |
| AC1 `COUNT(DISTINCT a,b,c)` | UNIQUE 约束 + `COUNT(*)` | SQLite 语法 |
| AC2 single pass/fail | AC2-bootstrap (info) + AC2-final (gate) | 监督要求强化 |

## 为何选 Option 2（不照抄论文）

1. **CreAgentive HNES 需要 human eval**（Vd = 0.5×auto + 0.5×human），我们 Phase 0 没有 human eval 流水线
2. **WebNovelBench 是长篇 4000+ 部 PCA+ECDF 分布对齐**，不适合单章纵向跟踪
3. **目标错位**：我们要的是"Phase N vs Phase N-1 内部对比"，不是"和外部 leaderboard 对齐"
4. **维度仍可借鉴**：v2 SEQR 的 8 维度借鉴 WebNovelBench D1/D2/D4/D5/D8 + autonovel 反 slop 思路 + 中文网文实战需要
5. **未来可升级**：如 Phase 1+ 后想对齐外部 leaderboard，再加一份 WebNovelBench-strict 维度并行评分即可

## 未涵盖的原 Open Questions

v1 proposal 提的 2 个 Open Questions：
- 论文复核问题已闭环（本次已 verified）
- "基线建好后是否做 Phase 1.1 对照实验"保留到 v2

## 下一步

监督审 v2，落盘到新 `decisions/<date>-phase-0-v2-review.md`。如 approve 则工程师开工。

---

# v2 → v2.1（应用 5 条开工前条件）

| 日期 | 触发 |
|---|---|
| 2026-04-26 | `decisions/2026-04-26-phase-0-v2-review.md`（approve-with-conditions） |

## 5 条条件应用情况

| # | 监督条件 | 处理 | 验证位置 |
|---|---|---|---|
| C1 | 加 `evaluation_batch_id` 到 schema + AC1/AC1b 按 batch 过滤 | 新增 `evaluation_batches` 表（共 5 张）；4 张数据表都加 `evaluation_batch_id` 外键；UNIQUE 约束改 batch-aware；AC1/AC1b/AC4 改 `WHERE evaluation_batch_id = :baseline_batch_id` | phase-gate.md v2.1 §Artifact Schema / §AC1 §AC1b §AC4 |
| C2 | AC2-final 必须 gate + 保存 calibration artifact，不可降级 | AC2-final 行新增产物路径 `data/baselines/ac2-final-calibration-<batch>.json`（含 chapter_id / rubric / human_scores / llm_scores / supervisor_conclusion）；Default 节明确"不可 bootstrap-only fallback" | phase-gate.md v2.1 §AC2-final + §Default |
| C3 | 前端删除 UI 不再提供 N>1 入口 | (1) DropdownMenu 文案改为「删除全部章节（保留大纲）」；(2) onClick 强制 `setDeleteFromChapter(1)`；(3) Dialog 整体重写为全量重置模式，移除 number input；(4) `handleDeleteChaptersFrom` 强制 `await deleteChaptersFrom(storyId, 1)` | `frontend/app/stories/[id]/page.tsx` |
| C4 | 修 `DeepSeekSetupPanel.tsx` lint 错 | `react/no-unescaped-entities` × 2：正文中 ASCII 双引号 `"模型配置"` 改为中文引号 `「模型配置」` | `pnpm run lint` 不再报本文件 |
| C5 | 确认 key revoke + `.env` 不提交 | `.gitignore` 第 10 行已含 `.env`；`git ls-files .env` 返回空；用户已说临时 key 测完删除——**仍需用户在 DeepSeek 平台二次确认 revoke**（key 字符串已在 git 历史） | gitignore 检查 + git 状态 |

## 验证

```bash
✓ python -m compileall -q backend scripts          # backend 通过
✓ pnpm run build                                    # 13 routes 构建通过
✓ pnpm run lint                                     # DeepSeekSetupPanel 0 errors
✓ git check-ignore .env                             # .env ignored
✓ git ls-files .env                                 # 未追踪
```

## 仍需用户单方面确认

⚠️ **DeepSeek 平台 revoke 临时 key `sk-a0ac26...0aa1`**：用户之前说"测完即删"，监督扫描确认源码已无该字符串，但**该字符串可能仍在 git 历史中**（看 commit 时是否包含过该值）。建议：
1. 在 DeepSeek 控制台确认该 key 已 revoke
2. 如确实在 git 历史中且仓库未推送 → `git filter-branch` 或 BFG 清理
3. 如已推送 → 仅靠 revoke 即可（不再可用）

## 状态

5 条条件 100% 应用，工程师待开工指令。

---

## v2.2 — 2026-04-27（Report #4 review）

| 类别 | 改动 |
|---|---|
| 标题/header | v2.1 → v2.2，修订日期 2026-04-27 |
| Scope | 删除"24 章 / 192 分"硬编码，全部改用 `scope_chapter_count` 动态校验 |
| AC1 / AC1b | 标准改 `= scope × 8` 和 `= scope`（严格 100%），90% 仅作 partial_warning |
| AC3 | sample 升级 100 + 50 generic + 50 fiction；标准加 `precision_fiction ≥ 0.7`（in-domain stress） |
| AC6 | 报告必须含 `mean / variance / stdev / trend`，不可 stdev 与 variance 混用 |
| Detector | DETECTOR_VERSION 单一源（`slop_detector.py` canonical，`__init__.py` re-export），统一为 `slop-v1` |
| Schema | `sqlite_store.py` 删除 `detector_version DEFAULT 'slop-v0'` 字面量，强制 caller 显式传 |
| proposal.md | 标 superseded，禁止再驱动开工 |

参见：
- `decisions/2026-04-27-phase-0-report-2-review.md`（AC6 + AC3 跨域）
- `decisions/2026-04-27-phase-0-report-3-review.md`（detector split-brain + batch immutability + provenance）
- `decisions/2026-04-27-phase-0-report-4-review.md`（schema default + proposal stale + AC3 final standard）

---

## v2.3 — 2026-04-27（Report #6 review）

| 类别 | 改动 |
|---|---|
| 标题/header | v2.2 → v2.3 |
| AC3 sample 描述 | "100 LLM 坏 + 50 generic-normal + 50 fiction-normal" → "100 slop + 50 generic-normal + 50 project-accepted fiction-normal（engineer_synthetic）+ 21 public_domain_excerpt（wikisource source-verifiable）" |
| AC3 标准 | 增加 `precision_pd_excerpt ≥ 0.7`（独立非合成 stress 必须独立达标）；删除"human-written"表述（除非真补独立人写样本） |
| AC5 readiness | heatmap 按 chapter_quality_evaluations 推导 expected chapters，每章必须全 8 dim；distribution 同时要求 evaluations_complete 和 scores_complete |
| Evaluation sample 描述 | 同步至 v5 corpus 三子集 |
| Scripts 文件清单 | slop_samples_zh.json 注释升 v5 |

参见：
- `decisions/2026-04-27-phase-0-report-5-review.md`（trend delta 算法 / AC5 readiness 1.0）
- `decisions/2026-04-27-phase-0-report-6-review.md`（heatmap 漏整章 / distribution 仅 evals 不够 / AC3 wording）
