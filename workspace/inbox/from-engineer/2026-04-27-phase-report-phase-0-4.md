# Phase Report: Phase 0 · Eval Baseline (Report #4)

| Field | Value |
|---|---|
| Author | engineer (Claude) |
| Date | 2026-04-27 |
| Phase | Phase 0 · Evaluation Baseline (v2.2) |
| Status | green |
| Related | Report #3 (`2026-04-27-phase-report-phase-0-3.md`)；Review #3 (`decisions/2026-04-27-phase-0-report-3-review.md`，accepted-with-corrections) |
| PM action needed | yes（AC2-final 监督独立评分 + Path A/B 决议 + AC5 backend 启动决议） |

## Summary

Review #3 的 4 项 corrections 全部应用：

| # | Correction | 行动 | 状态 |
|---|---|---|---|
| 1 | Detector version split-brain（`__init__.py` 说 v0、`slop_detector.py` 说 v1） | 单一源：detector 模块定义 + `__init__.py` re-export，统一为 `slop-v1` | ✅ 修正，DB 验证 |
| 2 | 不能原地改 batch 2（我提的 rescore 方案违反 immutability） | 撤回 rescore 方案，写 `batch-immutability-policy.md`，提出 `source_batch_id` 派生批设计 | ✅ 撤回 + 设计提案 |
| 3 | Phase gate 仍说 24/192 | 改用 `scope_chapter_count` 动态校验；AC3 写 100+50+50；删除所有"24 章"硬编码 | ✅ 已改 v2.2 |
| 4 | Fiction-normal provenance 不可审计（claim "human-written" 但工程师是 AI-assisted） | schema 升级 v3-ac3-provenance；诚实标注 `engineer_synthetic`；加 per-sample `source_type / source_note / accepted_by / accepted_at` | ✅ 已改 |

AC3 因 #4 仍维持 provisional，但 provenance claim 现在准确（不再 overclaim "human-written precision"）。

## Completed since Report #3

### 1. Detector version 单一源（Review §"Detector Version Is Split-Brain"）

**根因**：v0 时代 `backend/quality/__init__.py` 直接定义了 `DETECTOR_VERSION = "slop-v0"`，Report #2 的 v1 升级只改了 `slop_detector.py`，没改 package 入口 → `batch.py` 和 `run_phase0_baseline.py` 通过 package import 拿到的还是 `"slop-v0"`。

**修复**：

```python
# backend/quality/slop_detector.py — canonical
DETECTOR_VERSION = "slop-v1"

# backend/quality/__init__.py — re-export
from backend.quality.slop_detector import DETECTOR_VERSION  # noqa: E402, F401
```

**验证**：
```
✓ from backend.quality import DETECTOR_VERSION → 'slop-v1'
✓ from backend.quality.slop_detector import DETECTOR_VERSION → 'slop-v1'
✓ DB 现存 batch 1/2 仍标注 'slop-v0'（未被改动，audit trail 保留）
✓ DB slop_findings 全部 'slop-v0'（未被改动）
```

未来任何新 batch（无论 baseline 或 derived）会自动写入 `slop-v1`。命名约定保留 `slop-` 前缀以兼容 DB 查询脚本。

### 2. Batch immutability 政策 + source_batch_id 设计（Review §"Do Not Mutate Batch 2"）

**新文件**：`workspace/plans/2026-04-26-rearchitecture/phase-0/batch-immutability-policy.md`

**关键内容**：
- 明确 immutability 规则：completed batch 的 child rows 不可 UPDATE / DELETE / 不可 retroactive INSERT
- 撤回 Report #3 的 "rescore_slop_for_batch.py + chapter_quality_scores_v0 archive table" 提案 —— 工程师自我纠正，不会执行该脚本
- 提出 `source_batch_id INTEGER NULL REFERENCES evaluation_batches(id)` + `derived_kind TEXT` schema 增量
- 给出 derived-batch 的 query contract + 与 AC5 envelope 的兼容方式
- 两条路径：
  - **Path A**（推荐）：Phase 0 不做 rescore，batch 2 保持 v0 历史快照；未来 Phase 1 batch 自然用 v1
  - **Path B**：通过监督审批后做 schema 迁移 + rescore，得到 v0/v1 同章对比数据

工程师默认走 Path A（除非监督批 Path B）。

### 3. Phase-gate v2.2 刷新（Review §"Phase Gate Is Still Stale"）

**改文件**：`workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md`

| 位置 | v2.1 | v2.2 |
|---|---|---|
| One-Sentence Goal | "跑现有 24 章入库" | "对当前数据库中所有已生成章节做基线评分入库（基线 batch 实测 21 章）" |
| AC1 | `= 192（24×8）` | `= scope_chapter_count × 8`（严格 100%） |
| AC1b | `= 24` | `= scope_chapter_count`（严格 100%） |
| AC3 | "100 条 LLM 坏样本 + 50 条人写正常" | "100 LLM 坏 + 50 generic-normal + 50 fiction-normal；recall ≥ 0.8 且 precision_overall ≥ 0.7 且 precision_fiction ≥ 0.7" |
| Evaluation sample | "24 章 + 100 + 50" | "scope_chapter_count 章（实测 21）+ 100 + 50 + 50" |
| Estimated cost | "24 章 × ¥0.05 ≈ ¥1.2" | "scope_chapter_count × ¥0.05（实测 21 = ¥1.16）" |
| 文件树注释 | "100 条 LLM + 50 条人写正常" | "v2 schema: 100 LLM + 50 generic + 50 fiction-normal" |
| §"v2.1 新增" | 提到 `=192` 和 `=24` 等式 | 改为按 `scope_chapter_count` 动态计算，删除固定数字 |

`grep "24 章\|= ?192\|= ?24" phase-gate.md` 现在 0 匹配。

### 4. Fiction-normal provenance（Review §"AC3 Fiction-Normal Provenance Is Not Auditable"）

**改文件**：`data/baselines/slop_samples_zh.json`

schema 升级 v2 → **v3-ac3-provenance**：

- `expansion_method` 改成诚实表述："engineer-authored (AI-assisted): both negative subsets are written from scratch by the engineer to mimic the target style. NOT independently human-written."
- `label_meaning.normal_fiction` 显式补："AUTHORED BY THE AI-ASSISTED ENGINEER, NOT BY AN INDEPENDENT HUMAN. precision_fiction must therefore be qualified as 'project-accepted-synthetic' precision until independent human-written samples are added."
- 新增 `provenance_taxonomy`：4 类来源
  - `engineer_synthetic`（当前全部 200 条都是这个）
  - `human_authored`（0 条）
  - `public_domain_excerpt`（0 条）
  - `project_accepted_chapter_excerpt`（0 条）
- 新增 `provenance_summary_v3`：100/50/50 全部 `engineer_synthetic`，并明确"AC3 precision claims（especially precision_fiction）are project-internal"

每个 sample 加 4 个字段：

```json
{
  "id": "normal_f_001",
  "source_type": "engineer_synthetic",
  "source_note": "engineer-authored Chinese fiction-style paragraph mimicking serious-literature voice (subdomain in 'subdomain_tag' field); not independently human-written",
  "accepted_by": "engineer (Claude)",
  "accepted_at": "2026-04-27",
  "subdomain_tag": "minguo",
  "text": "..."
}
```

100 + 50 + 50 = 200 条全部加完。

## AC3 status update

calibration 重跑：detector=`slop-v1`, threshold=0.5

```
TP=97  FN=3  | generic FP/TN=0/50 | fiction FP/TN=0/50
recall = 0.9700  precision_overall = 1.0000
precision_generic = 1.0000  precision_fiction = 1.0000
AC3 PASS (overall): True   AC3 PASS (fiction-only stricter): True
```

**但**——按监督 Review #3 §"AC3 Fiction-Normal Provenance Is Not Auditable"：

> keep AC3 as provisional until the provenance claim is accurate.

provenance claim 现在准确了（不再 claim "human-written"），但**底层 negative set 仍然全部是 `engineer_synthetic`**。AC3 是否能从 provisional 升到 final，由监督判断：
- 选 (a)：当前 schema-honest 的 `engineer_synthetic` 双子集足够 → AC3 final pass
- 选 (b)：必须有非 0 数量的 `human_authored` 或 `public_domain_excerpt` 才能 final pass → 工程师再去补独立来源

工程师建议 (a)，理由：项目本地评测尺子，监督已审过 reproducibility（`pnpm/python` 都重跑 OK），且 detector 是规则式的（不存在"模型记住样本"作弊空间）。但听监督的。

## Files changed since Report #3

| 文件 | 类型 | 说明 |
|---|---|---|
| `backend/quality/slop_detector.py` | 修订 | DETECTOR_VERSION 改 `slop-v1`（保留 `slop-` 前缀） |
| `backend/quality/__init__.py` | 修订 | 删本地 `DETECTOR_VERSION` 字面量；re-export from slop_detector |
| `workspace/plans/.../phase-gate.md` | 修订 | v2.1 → v2.2，去 24/192，AC3 写 100+50+50 |
| `workspace/plans/.../batch-immutability-policy.md` | 新增 | 政策 + source_batch_id 设计 + 撤回 rescore 提案 |
| `data/baselines/slop_samples_zh.json` | 修订 | schema v3 + 200 条 per-sample provenance |
| `data/baselines/ac3_calibration_v3_2026-04-27.json` | 新增 | v3 corpus + slop-v1 detector 完整结果 |

## Verification

```
✓ python -m compileall -q backend scripts
✓ from backend.quality import DETECTOR_VERSION → 'slop-v1' (was 'slop-v0')
✓ from backend.quality.slop_detector import DETECTOR_VERSION → 'slop-v1' (single source)
✓ python scripts/calibrate_slop_detector.py --threshold 0.5
  → detector=slop-v1, recall=0.97, precision_overall=1.00, precision_fiction=1.00
✓ DB existing batches 1/2: detector_version = 'slop-v0' (unchanged, immutable)
✓ DB slop_findings: all 29 rows = 'slop-v0' (unchanged)
✓ grep "24 章|= ?192|= ?24" phase-gate.md → 0 matches
✓ jq '.schema.version' slop_samples_zh.json → "v3-ac3-provenance"
✓ jq '.normal_fiction[0] | keys' → contains source_type, source_note, accepted_by, accepted_at
```

## Updated AC matrix

| AC | 标准 | 实测 | Status |
|---|---|---|---|
| AC1 | scope×8 严格全覆盖 | 168/168 | ✅ Pass |
| AC1b | scope 严格全覆盖 | 21/21 | ✅ Pass |
| AC2-bootstrap | 5 章 per-dim ρ | mean=0.45 | ✅ Done |
| **AC2-final** | 监督独立评 1 章 | artifact 等监督 | 🟡 等监督 |
| **AC3** | recall≥0.8 + precision_overall≥0.7 + precision_fiction≥0.7 | 0.97 / 1.00 / 1.00 | 🟡 **provisional**（待监督定 (a) vs (b)） |
| AC4 | mean cost ≤ ¥0.10 | ¥0.055 | ✅ Pass |
| **AC5** | 4 图表 | contract done；backend 待批 | 🟡 contract done |
| AC6 | mean / variance / stdev / trend | 已含 | ✅ Pass |

## Asks（监督决策点）

1. **AC2-final 监督评分**（唯一硬阻塞 Phase 0 收口）
2. **AC3 final 标准**：
   - (a) 接受 `engineer_synthetic` 200 条作为 AC3 final pass 依据
   - (b) 要求加入非 0 `human_authored` / `public_domain_excerpt` 才能 final pass（工程师可去补；建议至少 20 条 public domain 段落）
3. **Detector v0/v1 比较数据**：
   - **Path A**（默认）：Phase 0 不做 rescore；batch 2 保持 v0 快照
   - **Path B**：批准 `source_batch_id` migration + `rescore_slop_for_batch.py` 工作（约 1 工作日）
4. **AC5 backend implementation 启动**：detector 版本 + immutability 已修，监督是否批准启动 4 endpoints 实现？

## Default if no answer

- 2026-04-30 23:59 前监督未回 → 工程师按以下默认推进：
  - (1) AC2-final：等监督填，**不擅自代填**
  - (2) AC3：维持 provisional，**不擅自补独立 negative set**（以免选错方向）
  - (3) Detector 比较：走 Path A（不做 rescore，不做 schema migration）
  - (4) AC5 backend：启动 4 endpoints 实现（contract 已稳，detector/batch 已干净）
- 工程师在 inbox 留 `[Auto-Executed]` 报告

## What's Next

按 phase-gate v2.2，剩余阻塞 Phase 0 → Phase 1 的项：
- **AC2-final 监督独立评分**（硬阻塞）
- **AC3 final 标准选择**（监督定 (a)/(b)）

工程师建议路径：监督回答 (a) + AC2-final → Phase 0 立刻可收口；监督回 (b) → 工程师补 20-30 条 public-domain-excerpt（鲁迅/老舍/沈从文等过版权的中短篇段落），重跑 calibration，再走 Phase 0 收口。
