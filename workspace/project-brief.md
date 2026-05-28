# Project Brief: Story Engine Rearchitecture

本文件只记录当前项目的特定背景和审查原则。通用沟通规范放在 `skill-draft/pm-engineer-collaboration/`，不要把本文件内容写进通用 skill。

## 项目目标

重构 Story Engine，使它从“多 Agent 流水生成章节”转向“AI 小说编辑部”：

- 先有故事契约和评测基线，再谈生成质量提升。
- 用场景卡控制叙事焦点，再让写手生成正文。
- 用 Context Compiler 给写手最小必要上下文。
- 用 Critic / Revision Loop 在正文发布前主动修订。
- 世界模拟只提供候选事件、压力和约束，不直接决定正文。

## 当前长期决议

- `decisions/standing/arch-001-editorial-office.md`
- `decisions/standing/process-001-evaluation-first.md`

## 当前监督红线

- 不允许把重构重新做成“更多 Agent 的流水线”。
- 不允许 Writer 直接读取全量历史和全量设定。
- 不允许世界模拟直接决定正文，只能输出候选事件和约束。
- 不允许没有评测基线就声称质量提升。
- 不允许未经复核的外部仓库结论进入 `decisions/`。
- 不允许阶段计划没有退出条件和回滚方案。

## 下一步

工程师应提交 `Phase 0 Evaluation Baseline` 的 1-2 周执行计划，同时使用：

- `templates/phase-gate.md`
- `templates/proposal.md`

计划必须明确评测样本、自动指标、人工校准、评委模型、成本上限，以及失败退出方案。
