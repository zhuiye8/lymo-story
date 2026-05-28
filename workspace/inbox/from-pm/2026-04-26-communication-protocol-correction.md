# Direction: communication protocol skill scope

| Field | Value |
|---|---|
| From | PM / supervisor |
| To | engineer |
| Date | 2026-04-26 |
| Status | open |
| Needed by | before next Phase 0 submission |
| Default if no answer | Use `skill-draft/pm-engineer-collaboration/` and current `workspace/templates/`; do not use the archived novel-specific skill draft. |

## Direction

The reusable skill is a generic PM/engineer communication protocol. It is not a Story Engine or novel-writing supervisor skill.

## Core Principle

This is the point that must not drift:

我们现在讨论和沉淀的是一套高效率的 PM / 监督者 / 工程师异步沟通规范。它的目标是让不同项目都能复用这套协作方式，包括看板、阶段门、问题默认动作、证据标签、决策记录、长期决议和汇报模板。

Story Engine 只是这套沟通规范的第一个使用场景，不是通用 skill 的主题。小说重构、AI 小说编辑部、评测基线、世界模拟等内容都属于当前项目的项目规则，只能放在 `project-brief.md`、`supervision-board.md`、`decisions/standing/` 或具体方案里，不能写进通用沟通 skill 的核心说明。

## Context

The Story Engine rewrite remains the current project, but its architecture principles belong in project-local files:

- `project-brief.md`
- `supervision-board.md`
- `decisions/standing/`

The reusable communication protocol belongs in:

- `skill-draft/pm-engineer-collaboration/`

The previous `novel-rearchitecture-supervisor` draft is archived and should not be used as the active skill.

## Required Behavior Going Forward

- Use the workspace templates for Phase 0 submissions.
- Keep project-specific arguments out of the generic skill.
- Add evidence tags for external claims.
- Include `Default if no answer` on every question.
- Update `supervision-board.md` when the active next action changes.
- If a future improvement is only useful for Story Engine, put it in project-local files. If it improves PM/engineer communication across projects, put it in the generic skill.
