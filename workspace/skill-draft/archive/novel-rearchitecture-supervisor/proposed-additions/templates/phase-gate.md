# Phase Gate: <phase name>

> 每个 Phase 启动前必须填完此文件，监督批准后才能开工。
> 缺任何一项 = 自动 reject，工程师补全后重交。

| Field | Value |
|---|---|
| Phase | Phase X · <name> |
| Author | engineer |
| Date | <YYYY-MM-DD> |
| Estimated duration | <weeks> |
| Cost ceiling | <CNY> |
| Decision needed | yes / no |
| Status | draft / pending-review / approved / blocked / done |

## 1. One-Sentence Goal

<最多 25 字。例："建立中文小说 8 维度评测基线，跑现有 3 本对照"。>

## 2. Non-Goals

- <明确不在本 Phase 范围内的事>
- <避免范围膨胀>

## 3. Artifact Schema

<本 Phase 产出的核心数据结构 / API / 文件。代码 schema 用 TypeScript / SQL / Pydantic 表达。>

```python
# 例：
class ChapterQualityScore(BaseModel):
    chapter_id: str
    dimension: Literal["fluency","vocab","plot","character",...]
    score: float                # 0-10
    judge_model: str
    evidence: str
    judged_at: datetime
```

## 4. Acceptance Criteria

每条必须含：**评测样本** + **样本量** + **指标** + **及格阈值** + **失败阈值**。

| # | 标准 | 评测方式 | 及格阈值 | 失败阈值（触发回滚） |
|---|---|---|---|---|
| AC1 | <例：所有现有章节有评分入库> | SQL 查询 `SELECT COUNT` | 100% | <50% |
| AC2 | <例：slop_score 中文化召回率> | 100 条人工标注样本 | ≥80% | <60% |
| AC3 | ... | ... | ... | ... |

> 不允许写"提升 X%"而无样本量、评委模型、校准方法。

## 5. Evaluation Method

| 项 | 说明 |
|---|---|
| 评委 LLM | <model + thinking mode> |
| 评测样本 | <来自哪里 + 多少条> |
| 人工校准 | <是 / 否；如是：抽样 N 条对照> |
| 自动指标 | <列表> |
| 评测频率 | <每提交一次 / 每天 / Phase 末一次> |
| 单次评测成本 | <¥X / 章> |

## 6. Cost Bound

| 类目 | 预估成本 | 上限 | 报警阈值 |
|---|---|---|---|
| LLM 调用（开发期） | <¥X> | <¥Y> | 80% Y |
| LLM 调用（评测） | ... | ... | ... |
| 外部 API | ... | ... | ... |
| 工程师时间 | <weeks> | <weeks+1> | 超时 1 周报警 |

## 7. Rollback / Exit Condition

| 触发条件 | 回滚动作 |
|---|---|
| AC 失败阈值触发 | <具体动作；例：保留旧 KG，删除 Graphiti 集成代码> |
| 成本超 100% | <暂停，重新评估> |
| 用户体验恶化 | <立即回退到上一个 git tag> |
| 监督要求中止 | <按 inbox 指令执行> |

**Git tag 策略**：每个 Phase 开始前 `git tag pre-phase-N`，结束前 `git tag post-phase-N`。

## 8. Dependencies

| 依赖 | 类型 | 状态 | Evidence |
|---|---|---|---|
| Phase 0 evaluation baseline | upstream phase | <done / in-progress> | <链接> |
| Graphiti+Kuzu | external library | <verified / needs-review> | <[verified:date:URL]> |
| ... | ... | ... | ... |

## 9. Standing Decisions Touched

> 列出本 Phase 涉及的已生效决议；如挑战其中任何一条，必须显式说明。

- arch-001 (editorial office): <一致 / 挑战：<理由>>
- process-001 (evaluation first): <一致>
- ...

## 10. Ask

<监督需要做什么。例："请在 2026-05-01 前 approve / reject"。>

## Default if no review

<如未在 deadline 前收到回复的默认行为。引用 question.v2.md 的 default 机制。>
