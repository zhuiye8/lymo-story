# Evidence Tagging Protocol

> 所有外部事实（GitHub 仓库状态、论文结论、benchmark 数字、第三方 API 价格、模型能力）必须带证据标签。
> 监督在 review 时直接按标签筛选审稿强度。

## 4 个标签

| 标签 | 含义 | 监督处理方式 |
|---|---|---|
| `[verified:YYYY-MM-DD:URL]` | 工程师在该日期亲自访问/运行验证 | 信任，但 30 天后可能要求复核 |
| `[needs-review]` | 来自记忆、训练数据、他人转述、或不确定的回忆 | 必须先复核才能进 `decisions/` |
| `[assumption]` | 工程师推断，无外部支撑 | 必须标注推断逻辑；高风险决策禁用 |
| `[stale:YYYY-MM-DD]` | 早期 verified 但已过保质期 | 等同 `[needs-review]` |

## 写作要求

### 必须加标签的场景

- 任何引用外部仓库的"是否仍维护 / star 数 / commit 时间 / 依赖"
- 任何引用论文的"评分 / SOTA 模型 / 数据集大小"
- 任何引用 API 的"价格 / 限流 / 可用区"
- 任何引用模型的"能力 / 上下文窗口 / 思考模式"
- 任何引用 benchmark 的"分数 / 排名"

### 不需要加标签的场景

- 项目内部代码状态（你能直接读）
- 项目内部数据（你能直接查）
- 工程师本地实测结果（用 `tested:YYYY-MM-DD` 即可）

## 示例

### 好的写法

```markdown
- DeepSeek-V4-Pro 单价 ¥12/M 输入 [verified:2026-04-26:https://api-docs.deepseek.com/zh-cn/quick_start/pricing]
- Graphiti 支持 Kuzu 嵌入式图库 [verified:2026-04-26:https://github.com/getzep/graphiti]
- Qwen3-235B 在 WebNovelBench 8 维度均分 5.21 [needs-review] — 来自论文摘要回忆，未验证表格原文
- 用户每天写作 ~2 小时 [assumption] — 推断自 commit 频率
```

### 不可接受的写法

```markdown
- DeepSeek 比 GPT-4o 便宜 80%。       ← 无标签，无来源
- pytrends 仍在维护。                 ← 这正是被打回的原因（已死 2023）
- WebNovelBench 是中文小说评测黄金标准。 ← 无标签，且"黄金"是断言
```

## 复核机制

监督者在 `decisions/` 落盘前，对所有 `[verified]` 标签**抽 30%** 复核：

```bash
# 复核动作（监督手动）
1. 访问 URL 验证内容存在
2. 验证日期是否在 30 天内
3. 如失效 → 工程师改回 [needs-review]
```

`[stale:date]` 自动触发复核要求。

## 工程师纪律

- 不确定就用 `[needs-review]`，不要赌
- 引用自己之前的调研也要重标日期
- `[assumption]` 占比 >30% 的提案会被打回

## 监督红线

- 没有标签的外部事实 = 自动 reject
- `[needs-review]` 内容**禁止**进入 `decisions/`，必须先转为 `[verified]`
- `[assumption]` 用于架构红线判断 = 自动 reject
