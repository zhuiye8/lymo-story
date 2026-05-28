# Proposed Additions（已审阅）

工程师建议合并到 skill 主体的文件与机制。监督结论见 `workspace/decisions/2026-04-26-skill-additions.md`。

| ID | 文件 | 合并目标位置 | 状态 |
|---|---|---|---|
| P0-A | `references/evidence-tagging.md` | 同名位置 | accepted and merged |
| P0-B | `templates/question.v2.md` | 替换 `templates/question.md` | accepted and merged |
| P1-A | `references/standing-decisions.md` | 同名位置 + 创建 `decisions/standing/` 目录 | accepted and merged |
| P1-B | `templates/phase-gate.md` | 同名位置 | accepted and merged |
| P2-B | `references/engineer-side.md` | 同名位置；同时在 SKILL.md 末尾加引用 | accepted and merged |
| P2-A | 拆分通用 PM skill + 小说特化 skill | 暂不执行 | deferred |
| P3 | inbox 自动状态机 | 暂不执行 | deferred |

## 执行结果

- 已更新 `workspace/skill-draft/novel-rearchitecture-supervisor/SKILL.md`。
- 已更新 `workspace/templates/question.md`，要求必须写默认动作。
- 已新增 `workspace/templates/phase-gate.md`。
- 已新增 skill 内部 references 与 templates。
- 已新增 `workspace/decisions/standing/`。
- 暂不拆分 skill，等至少跑完一个完整阶段后再复盘。
- 暂不做 inbox 自动状态机，等消息量证明需要后再加。

## 上下文

详见 `inbox/from-engineer/2026-04-26-question-skill-improvements.md`。
