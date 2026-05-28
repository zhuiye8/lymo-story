# Review Request: Phase 0 v2 Resubmission

| Field | Value |
|---|---|
| Requester | engineer (Claude) |
| Date | 2026-04-26 |
| Artifact | `plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` v2 + `proposal.md` v2 + `change-log.md` |
| Review type | architecture + quality + risk |
| Needed by | 2026-04-30 23:59（default 触发时间） |
| Supersedes | `2026-04-26-review-request-phase-0.md`（v1 已被 revision-needed） |

## What Changed (vs v1)

7 项 blocking findings 全部处理（详见 `change-log.md`）：

1. **重命名 rubric → SEQR v0**（Story Engine Quality Rubric）；不再冒用 WebNovelBench / HNES 论文名
2. **公式重写**：`SEQR_composite = mean(8 dims) - slop_penalty`；不再写 HNES
3. **新增聚合表** `chapter_quality_evaluations`（每章 1 行）
4. **修复 AC1 SQL**：UNIQUE 约束 + `COUNT(*)`，移除非 SQLite 的 `COUNT(DISTINCT a,b,c)`
5. **AC2 拆为两层**：bootstrap（工程师 5 章 per-dim ρ，info-only）+ final（监督评 1 章，gate）
6. **API key 已修复**：`scripts/test_deepseek_v4.py` 改为 `os.environ["DEEPSEEK_API_KEY"]`
7. **delete-from-chapter N>1 已禁用**：返回 400 + 详细说明；Phase 0 范围内不实现 safe rewind

## What To Review (按优先级)

1. **重命名是否被接受**：Option 2（项目本地 SEQR v0）是否符合监督预期？还是要求 Option 1（实现论文真维度+权重）？
2. **AC2-final 由监督评 1 章** 是否被接受？或选 (a) Qwen3-235B 当金标准 / (b) 工程师评+显式标 bootstrap-only 不做 final gate
3. **聚合表 schema** `chapter_quality_evaluations` 字段是否完整（composite/mean_quality/slop_penalty/word_count/rubric_version）
4. **AC1 SQL** 改用 UNIQUE + COUNT(*) 是否被接受
5. **Slop 中文词典 v0** 标 `[assumption]`，校准用 AC3 兜底；监督是否接受这一不确定性
6. v2 是否漏掉 v1 review 中的任何 finding

## What Not To Review

- 不必再 review WebNovelBench 论文表格细节（已 verified + 选择 Option 2 不直接照搬）
- 不必现在审 Phase 1+ 的设计（属下一份 phase-gate）
- 不必审 SEQR 维度是否"完美"（v0 + 等权，AC2-final 通过即可；优化留 v0.1）

## Evidence (v2 已升级)

| Claim | Evidence | Status |
|---|---|---|
| WebNovelBench 8 真维度 | https://arxiv.org/html/2505.14818 | [verified:2026-04-26] |
| WebNovelBench 用 PCA+ECDF | 同上 | [verified:2026-04-26] |
| HNES 属 CreAgentive | https://arxiv.org/html/2509.26461 | [verified:2026-04-26] |
| autonovel slop_score | https://github.com/NousResearch/autonovel/blob/master/evaluate.py | [verified:2026-04-26] |
| API key 已从源码移除 | scripts/test_deepseek_v4.py 改为 env var | [verified:2026-04-26] |
| delete-from-chapter N>1 已禁用 | backend/api/stories.py 返回 400 | [verified:2026-04-26] |

## Specific Ask

请监督在 `decisions/2026-04-XX-phase-0-v2-review.md` 落盘：

1. **整体 v2 决议**：approve / approve-with-conditions / revision-needed / reject
2. **5 项决策回复**（见 phase-gate.md v2 Ask 节）
3. 如有补充约束（cost / 时间 / AC 阈值），明列

如未在 2026-04-30 23:59 前回复，工程师按 phase-gate v2「Default If No Review」节执行（SEQR v0 命名 / 工程师 bootstrap-only / DeepSeek-V4-Pro 关思考 PoC / delete N>1 维持禁用），并在 inbox 留 `[Auto-Executed]` 报告。

## Side Note (向用户)

API key 风险：监督发现 `scripts/test_deepseek_v4.py` 含硬编码 key `sk-a0ac26...`（用户测试用的临时 key）。
- 工程师已**立即**改为环境变量
- 用户已说明该 key 测完即删，但**强烈建议在 DeepSeek 平台再次确认 revoke**（因为该字符串已在 git 历史中）
- 如确认 revoke，可考虑用 `git filter-branch` 或 BFG Repo-Cleaner 清理历史；如未推送，本地 amend 即可
