# PM / Engineer Collaboration Workspace

本目录是项目经理/监督者与执行工程师之间的异步协作区。目标是减少长对话反复解释，让每次交接都能快速回答三个问题：

1. 当前在做什么？
2. 需要谁做什么决定？
3. 有什么证据证明方向没有偏？

## 工作原则

- `workspace/supervision-board.md` 是入口。任何人接手前先读它。
- 项目背景与特定审查原则放 `project-brief.md`，不要写进通用沟通 skill。
- 长方案放 `plans/`，阶段门放 `plans/` 或独立目录，绑定决策放 `decisions/`，短消息放 `inbox/`。
- 研究结论必须标注来源；未经 PM/监督复核的外部结论只能写作 `proposal`，不能写作 `decision`。
- 工程师每次汇报要短，默认不超过 80 行；详细证据放附件或链接。
- 每个问题必须写 `Default if no answer`，否则视为无效问题。
- 决策必须落盘到 `decisions/`，口头聊天不算最终决策。
- 不修改已批准历史文档；需要变更时新建 `-v2` 或新决策覆盖旧决策。

## 目录

```text
workspace/
├── README.md
├── supervision-board.md              # 当前状态、阻塞、监督意见
├── project-brief.md                   # 当前项目的特定目标、红线、审查原则
├── templates/                        # 标准交接模板
├── plans/                            # 工程师提交的方案和阶段计划
├── decisions/                        # PM/监督批准、驳回、修改要求
├── inbox/
│   ├── from-pm/                      # PM/监督给工程师的问题和指令
│   └── from-engineer/                # 工程师给 PM/监督的汇报和请求
└── skill-draft/                      # 未来可复用 Codex skill 草案
```

## 状态机

方案状态：

```text
draft -> pending-review -> approved / revision-needed / rejected -> in-progress -> done
```

消息状态：

```text
open -> answered -> accepted / follow-up-needed -> closed
```

## 文件命名

```text
YYYY-MM-DD-<topic>.md
YYYY-MM-DD-<topic>-v2.md
```

示例：

- `plans/2026-04-26-rearchitecture/`
- `decisions/2026-04-26-rearchitecture-approval.md`
- `inbox/from-engineer/2026-04-27-phase-0-report.md`

## 标准模板

- 方案提交：`templates/proposal.md`
- 阶段门：`templates/phase-gate.md`
- 阶段汇报：`templates/phase-report.md`
- 决策记录：`templates/decision-record.md`
- 问题/澄清：`templates/question.md`
- 监督 review：`templates/review-request.md`

## 通用监督规则

PM/监督默认从以下角度审查：

- 是否一次只请求一个清晰决策。
- 是否包含负责人、截止时间和默认动作。
- 是否把未经验证的外部结论当成事实。
- 是否有清晰验收标准、回滚路径和成本上限。
- 是否违反 `decisions/standing/` 中的长期决议。
- 是否需要更新 `supervision-board.md`。

当前项目的小说重构审查规则见 `project-brief.md` 与 `decisions/standing/`。

## 当前入口

当前活跃方案：

- `plans/2026-04-26-rearchitecture/`
- 监督入口：`supervision-board.md`
- 项目背景：`project-brief.md`
- 架构蓝图：`../docs/rearchitecture_blueprint.md`
- 通用沟通 skill 草案：`skill-draft/pm-engineer-collaboration/`
