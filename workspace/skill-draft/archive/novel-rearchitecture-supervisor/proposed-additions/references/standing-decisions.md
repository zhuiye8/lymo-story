# Standing Decisions（已生效不再争论的决议库）

## 目的

避免重复 review 同一件事。已批复的决议沉淀为 standing decisions，新提案如**不挑战** standing decisions，可以快速通过。

## 目录约定

```
decisions/
├── standing/                   # 已生效、长期有效的决议
│   ├── arch-001-editorial-office.md
│   ├── arch-002-evaluation-first.md
│   └── ...
├── 2026-04-XX-<topic>.md       # 普通决议
```

## Standing Decision 文件格式

```markdown
# Standing Decision <ID>: <topic>

| Field | Value |
|---|---|
| ID | arch-001 / process-001 / tech-001 |
| Approved | <YYYY-MM-DD> by <PM> |
| Source proposal | <path> |
| Status | active / superseded by <new-id> |
| Revisit trigger | <什么条件下可重新审议> |

## Decision

<一句话决议>

## Rationale

<3-5 行，简明扼要>

## Constraints on Future Proposals

<新提案在哪些情况下违反此决议时必须显式说明>
```

## 示例

### `decisions/standing/arch-001-editorial-office.md`

```markdown
# Standing Decision arch-001: 目标架构是 AI 编辑部

| Field | Value |
|---|---|
| ID | arch-001 |
| Approved | 2026-04-XX by <PM> |
| Source proposal | plans/2026-04-26-rearchitecture/ |
| Status | active |
| Revisit trigger | 12 周内出现 ≥3 个独立 Phase 失败 |

## Decision

系统架构目标是 AI 编辑部（Story Contract / Scene Card / Context Compiler / Critic Room / Revision Loop），不再是多 Agent 流水线。

## Rationale

蓝图已诊断流水线范式无法解决质量问题。调研 4 个项目证明编辑部模式可行。

## Constraints on Future Proposals

任何新提案如建议"加 Agent 解决问题"必须显式回答：
1. 该 Agent 替代了哪个编辑部模块，还是新增了哪个模块？
2. 是否引入了 Critic 或 Revision 闭环？
3. 是否绕过了 Context Compiler？
```

### `decisions/standing/process-001-evaluation-first.md`

```markdown
# Standing Decision process-001: 评测先行

| Field | Value |
|---|---|
| ID | process-001 |
| Approved | 2026-04-XX |
| Status | active |
| Revisit trigger | 评测公约失效或基线无法计算 |

## Decision

任何质量改进 claim 必须先有 baseline + 样本量 + 评委模型 + 校准方法。

## Constraints on Future Proposals

- 不允许写"提升 X%"而无样本量
- 不允许新评测维度未做人工对照
- 不允许跳过 Phase 0 的提案
```

## 工程师纪律

- 提交新 proposal 前，**先扫一遍 `decisions/standing/`**，避免重复劳动
- 如新提案与某条 standing decision 冲突，必须在 proposal 头部加 `Challenges Standing: arch-001` 字段
- 监督看到 `Challenges Standing` = 高强度 review；否则 = 快速通过

## 监督纪律

- 已批复的决议**主动落入 `standing/`**，不要散落在日期目录里
- 当某条 standing decision 被 supersede，原文件状态改 `superseded by <new-id>`，不删除
- 每季度 review 一次 standing decisions 是否仍 valid
