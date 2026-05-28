# Question: <topic>

| Field | Value |
|---|---|
| From | <PM/engineer> |
| To | <PM/engineer> |
| Date | <YYYY-MM-DD> |
| Status | open / answered / closed |
| Needed by | <date> |
| **Default if no answer** | **<必填：默认动作 + 触发时间>** |

> **Default 字段缺失或为空 = 该 question 自动 reject，提问方需重写**。
> 这条强制规则避免任何一方因等待而停摆。

## Question

<一句话问题。如有多个相关问题，拆成多个文件。>

## Context

<必要上下文，不超过 10 行。>

## Options

| Option | Tradeoff | Evidence |
|---|---|---|
| A | <tradeoff> | <[verified] / [needs-review] / [assumption] 链接> |
| B | <tradeoff> | <evidence> |

## Recommendation

<提问方推荐 + 理由 1-3 行。>

## Default Behavior（如无回复）

> 提问方承诺：如未在 `Needed by` 之前收到回复，将按此默认动作执行，事后用 `inbox/from-engineer/` 通知结果。

```text
默认动作：<具体做什么>
触发时间：<收到截止日期 +N 天后>
回滚成本：<low / medium / high>
事后追溯：<是否需要事后补审批>
```

## Examples

### 好的 Default 写法

```text
默认动作：按 Option A 执行（用 DeepSeek-V4-Pro 关思考做评委）
触发时间：2026-04-30 23:59 之后
回滚成本：low（仅评委 LLM 配置可改）
事后追溯：否（成本 <¥10）
```

### 不可接受的 Default 写法

```text
等待 PM 回复       ← reject，没有 default 即没有 default
默认 reject        ← reject，提问方要给出可执行的默认值
按情况判断          ← reject，必须明确动作
```
