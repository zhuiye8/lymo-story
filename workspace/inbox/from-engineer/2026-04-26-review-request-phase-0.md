# Review Request: Phase 0 Evaluation Baseline

| Field | Value |
|---|---|
| Requester | engineer (Claude) |
| Date | 2026-04-26 |
| Artifact | `plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` + `proposal.md` |
| Review type | architecture + quality + risk |
| Needed by | 2026-04-29 23:59（default 触发时间） |

## What Changed

- 新建 `plans/2026-04-26-rearchitecture/phase-0/` 目录
- 提交 `phase-gate.md`（契约层 8 件套：goal / non-goals / artifact schema / AC / evaluation / cost / rollback / dependencies / standing decisions）
- 提交 `proposal.md`（详细设计：3 个核心组件 + workflow + risks + open questions）
- 已更新 `supervision-board.md` Phase 0 状态为 pending-review

## What To Review

按优先级（监督若时间紧只看前 3）：

1. **Acceptance Criteria 是否够硬**（phase-gate AC1-AC6） — 特别 AC2（Spearman ρ ≥ 0.6）和 AC3（slop recall ≥ 0.8）的阈值是否合理
2. **Evidence tag 是否充分** — 重点是 `[needs-review]` 项（WebNovelBench 8 维度 / HNES 公式）是否允许并行开工，还是必须先复核
3. **Default action 是否真的低风险可逆** — 评委 LLM 选 DeepSeek-V4-Pro 关思考、AC2 工程师自评、与开发并行复核论文，这 3 个默认是否符合"低风险可逆"
4. Cost ceiling 是否合理（¥50 现金 + 2 周时间）
5. Non-Goals 是否漏掉应排除的范围
6. 是否触动 standing decisions（我标的是均一致，请复核）

## What Not To Review

- 不必现在 review WebNovelBench 论文表格细节（开工后工程师持续复核，差异立即在 inbox 报告）
- 不必现在审 Phase 1+ 的设计（属下一份 phase-gate）
- 不必审中文 slop 词典具体词条（属 implementation 细节，有 AC3 校准兜底）

## Evidence

| Claim | Evidence |
|---|---|
| 评委 LLM 已可用 | scripts/test_deepseek_v4.py 端到端测试 [verified:2026-04-26] |
| autonovel slop_score 函数可抄 | https://github.com/NousResearch/autonovel/blob/master/evaluate.py [verified:2026-04-26] |
| 现有 24 章数据完整 | data/story.db 实测 [verified:2026-04-26] |
| WebNovelBench 8 维度 | docs/rearchitecture_blueprint.md §4.10 + 工程师调研 [needs-review] |
| HNES 公式 | docs/rearchitecture_blueprint.md + 调研 [needs-review] |

## Specific Ask

请监督在 `decisions/2026-04-XX-phase-0-approval.md` 落盘：

1. **整体决议**：approve / approve-with-conditions / revision-needed / reject / blocked-pending-evidence
2. **4 项决策回复**（见 phase-gate.md Ask 节）：
   - 评委 LLM 选 A / B / C / D
   - WebNovelBench 论文复核：先 / 并行
   - AC2 人工评分：A / B / C
3. 如有补充约束（cost ceiling / 时间 / AC 阈值），请明列

如未在 2026-04-29 23:59 前回复，工程师按 phase-gate「Default If No Review」节执行，并在 inbox 留 `[Auto-Executed]` 报告。
