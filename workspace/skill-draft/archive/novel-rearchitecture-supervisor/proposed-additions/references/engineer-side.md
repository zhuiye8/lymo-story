# Engineer-Side Operating Manual

> SKILL.md 写给监督者，本文写给工程师。
> 工程师按本文工作 = 减少格式打回、加快监督响应。

## 1. 选对消息类型

| 我现在要做的事 | 用什么 | 放在哪 |
|---|---|---|
| 启动一个新 Phase | `phase-gate.md` | `plans/<phase>/phase-gate.md` |
| 改架构、加大模块、引入大依赖 | `proposal.md` | `plans/<date>-<topic>/` |
| 问监督一个具体问题 | `question.md`（v2，强制 default） | `inbox/from-engineer/` |
| Phase 末汇报进度 | `phase-report.md` | `inbox/from-engineer/` |
| 24h 内必须监督介入的风险 | `question.md` 标 `Status: urgent` | `inbox/from-engineer/` |
| 请监督审一个具体产物 | `review-request.md` | `inbox/from-engineer/` |
| 通知"我要按 default 执行了" | `question.md` 后续追加 `[Auto-Executed]` 段 | 同 question 文件 |

## 2. 标证据是工程师的硬纪律

每写一条外部事实必须带 `[verified:date:URL]` / `[needs-review]` / `[assumption]` / `[stale:date]`。
详见 `references/evidence-tagging.md`。

**最容易出错的场景**：
- ❌ "DeepSeek V4 比 V3 便宜很多"
- ✅ "DeepSeek V4-Flash 输入 ¥1/M，V3 输入 ¥2/M [verified:2026-04-26:https://api-docs.deepseek.com/zh-cn/quick_start/pricing]"

- ❌ "Graphiti 是主流图数据库 SDK"
- ✅ "Graphiti 是 Zep 团队开源的 temporal KG 库 [verified:2026-04-26:https://github.com/getzep/graphiti]"

## 3. 每个 question 必须有 Default

不允许"等监督回复"。必须写：

```text
Default if no answer：<具体动作> + 触发时间 + 回滚成本
```

**这不是为了甩锅，是为了让你不被卡住**。监督也希望你这么做。

## 4. 一个文件一个主题

不要把"询问决策 1 + 报告进度 + 提风险"塞同一个文件。
监督一次只 review 一个主题，混着写 = 你被打回。

## 5. 写之前先扫 standing decisions

每次启动 proposal 前：

```bash
ls decisions/standing/
```

如果你的提案与某条 standing decision 冲突，必须在 proposal 头部加：

```markdown
| Challenges Standing | arch-001（理由：<一句话>）|
```

否则监督看到与 standing 冲突 = 直接 reject。

## 6. 写短

| 文档类型 | 字数上限 |
|---|---|
| `question.md` | 500 字（不含 Evidence 链接） |
| `phase-report.md` | 1000 字 |
| `proposal.md` | 2000 字（详细设计另开附件） |
| `phase-gate.md` | 1500 字 |
| `review-request.md` | 300 字 |

超字 = 监督有权要求重写。

## 7. 默认决策执行流程

如果到了 default 触发时间监督还没回：

1. 在原 question.md 末尾追加：

```markdown
---

## [Auto-Executed] <YYYY-MM-DD HH:MM>

按 Default 执行：<具体动作>。
等待事后批准。

执行结果：<链接到 phase-report 或 commit>
```

2. 同时新建 `inbox/from-engineer/<date>-report-auto-executed-<topic>.md` 通知监督
3. 监督事后可补 reject，但代价由监督承担

## 8. Phase 末必须做的 4 件事

完成一个 Phase 时：

1. `git tag post-phase-N`
2. 提交 `phase-report.md` 到 `inbox/from-engineer/`
3. 把本 Phase 关联的临时 decisions 整理为 standing decision 候选（监督批准后入 `decisions/standing/`）
4. 跑评测基线对比并附在 phase-report 的 Evidence 段

## 9. 不要做的事

- ❌ 直接编辑监督已批准的文件（用版本号副本：`-v2.md`）
- ❌ 在对话中拍板大决议（必须落盘到 `decisions/`）
- ❌ 把 5 个问题塞 1 个 question 文件
- ❌ 引用未带证据标签的外部信息
- ❌ 假设"上次说过了" — 监督每次 review 都按文件审
- ❌ 写"提升 X%" 不带样本量

## 10. 心法

**监督的稀缺资源是注意力，不是 review 时间**。
你的工作是把信息压缩到监督能 60 秒做决定。

写完任何文档前问自己：

> 监督花 60 秒读完，能不能给出 approve / reject / revision-needed？
> 如果不能，重写。
