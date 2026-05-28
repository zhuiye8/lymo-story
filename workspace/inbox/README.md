# Inbox

本目录用于短消息、问题、阶段汇报和风险预警。重大决策必须转入 `../decisions/`。

## 目录

- `from-pm/`：PM/监督发给工程师的问题、指令、修改要求。
- `from-engineer/`：工程师发给 PM/监督的阶段汇报、风险预警、决策请求。

## 消息要求

- 一条消息只解决一个主题。
- 开头必须写 `Status` 和 `Ask`。
- 如果需要 PM/监督动作，必须写明截止时间和默认处理方式。
- 证据用链接，不在消息里堆长文。

## 命名

```text
YYYY-MM-DD-<type>-<topic>.md
```

示例：

- `2026-04-27-question-phase-0-scope.md`
- `2026-04-27-report-phase-0.md`
- `2026-04-27-risk-graphiti-poc.md`

## 推荐模板

- 问题：`../templates/question.md`
- 阶段汇报：`../templates/phase-report.md`
- 监督 review：`../templates/review-request.md`

