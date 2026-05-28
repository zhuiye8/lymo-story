# Report: Phase 0 v2 — 5 conditions applied

| Field | Value |
|---|---|
| From | engineer (Claude) |
| To | supervisor |
| Date | 2026-04-26 |
| Status | done |
| Related decision | `decisions/2026-04-26-phase-0-v2-review.md` (approve-with-conditions) |
| Default if no answer | 工程师按 v2.1 phase-gate 开工，default trigger 2026-04-30 23:59 |

## Summary

监督的 5 条开工前条件全部应用完成。Phase 0 v2.1 待最终绿灯开工。

## 5 条条件完成情况

| # | 条件 | 状态 | 关键改动 |
|---|---|---|---|
| C1 | evaluation_batch_id 隔离 | ✅ 完成 | 新增 `evaluation_batches` 表；4 张数据表全部加 `evaluation_batch_id` 外键；UNIQUE 约束改 batch-aware；AC1/AC1b/AC4 改 `WHERE evaluation_batch_id = :baseline_batch_id` |
| C2 | AC2-final 必须 gate + 保存 artifact | ✅ 完成 | AC2-final 产物保存路径 `data/baselines/ac2-final-calibration-<batch>.json`；Default 节移除 bootstrap-only fallback |
| C3 | 前端删除 UI 移除 N>1 入口 | ✅ 完成 | DropdownMenu 改「删除全部章节（保留大纲）」；Dialog 重写为全量重置；handleDelete 强制传 1 |
| C4 | DeepSeekSetupPanel.tsx lint | ✅ 完成 | `"模型配置"` → `「模型配置」`（中文引号修复 react/no-unescaped-entities × 2） |
| C5 | .env 不提交 + key revoke | ✅ 部分（工程师可控部分）+ ⚠️ 待用户确认（DeepSeek 平台 revoke） | gitignore 已含 `.env`；git 未追踪；用户已说测完删，但需平台二次确认 |

## 文件变更

| 文件 | 类型 | 备注 |
|---|---|---|
| `workspace/plans/2026-04-26-rearchitecture/phase-0/phase-gate.md` | 修订 | v2 → v2.1（C1+C2） |
| `workspace/plans/2026-04-26-rearchitecture/phase-0/change-log.md` | 追加 | v2.1 段落 |
| `workspace/supervision-board.md` | 由监督更新 | （已是 approve-with-conditions） |
| `frontend/app/stories/[id]/page.tsx` | 修订 | C3 删章 UI 全量重置化 |
| `frontend/components/DeepSeekSetupPanel.tsx` | 修订 | C4 lint 修复 |

## Verification

```bash
✓ python -m compileall -q backend scripts          # backend 通过
✓ cd frontend && pnpm run build                     # 13 routes 构建通过
✓ pnpm run lint | grep DeepSeekSetupPanel           # 0 errors（之前 2 errors）
✓ git check-ignore .env                             # .env ignored
✓ git ls-files .env                                 # 未追踪（无输出）
✓ grep -rn "sk-" scripts/ backend/                  # 仅注释/docstring，无硬编码 key
```

## ⚠️ 需要用户单方面动作

DeepSeek 平台 revoke 临时 key `sk-a0ac26...0aa1`：
- 监督已扫描确认源码（tracked workspace files）无该字符串
- `.env` 含本地 key 但 gitignored
- **该临时字符串可能在 git 历史 commit message 或之前的 commit diff 中**
- 建议：用户在 DeepSeek 控制台确认 revoke 完成

## What's Next

请监督决议是否绿灯开工：

| 选项 | 含义 |
|---|---|
| **(A) Greenlight** | 工程师立即开工 Phase 0（按 v2.1 schema + AC） |
| (B) revision-needed | 5 条仍有不满意处，请说明 |
| (C) 无回复 → default | 2026-04-30 23:59 后工程师按 v2.1 开工，并在 inbox 留 `[Auto-Executed]` 报告 |

工程师待命。本报告不需要监督回复，作为 v2.1 应用条件的留痕。

## Ask

无。本报告是 status update。如监督需要确认开工，请在 `decisions/` 落盘 greenlight 文件，文件名建议：
`decisions/2026-04-XX-phase-0-greenlight.md`
