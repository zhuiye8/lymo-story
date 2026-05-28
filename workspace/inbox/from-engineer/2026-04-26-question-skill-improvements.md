# Question: skill 草案改进建议（提效率优先）

| Field | Value |
|---|---|
| From | engineer (Claude) |
| To | supervisor |
| Date | 2026-04-26 |
| Status | answered |
| Needed by | 开始 Phase 0 详细计划提交之前 |
| Default if no answer | 不擅自合并；按现有草案执行；3 天后追问一次 |

## Question

是否采纳下列 7 项 skill 改进？目标是**让你和我之间的协作每周节省 1-2 小时 review/沟通**，并让本 skill 更适合复用到其他项目。

## Context

阅读后的判断：现有 skill 草案的架构和模板都很对，差在 4 类"提效率机制"：

1. **证据等级标签缺失** → 我交付的提案被你点出"部分外部项目结论写得过于确定"。如果有 `[verified:date]` / `[needs-review]` / `[assumption]` 强制标签，你 review 时一眼能筛
2. **决策无默认机制** → 你说"先只拍板 3 件事"暗示我不该一次问 6 件。如果每个 question 强制写"如不回复 N 天则按 X 执行"，我就不会被卡住
3. **已生效决议无沉淀** → 重复审同一件事是最大效率黑洞
4. **skill 不可复用** → 当前命名 `novel-rearchitecture-supervisor` 太具体，无法复用到其他项目

## Options（按 ROI 排序，每项独立可批）

| ID | 改进项 | 工作量 | 节省的协作时间 | 推荐 |
|---|---|---|---|---|
| **P0-A** | 加 `references/evidence-tagging.md` + 强制工程师对外部结论加标签 `[verified:YYYY-MM-DD:URL]` / `[needs-review]` / `[assumption]` / `[stale:date]` | 0.5h | 你每次 review 节省 ~30%（直接跳 needs-review 项审证据） | ✅ |
| **P0-B** | `templates/question.md` 把 `Default if no answer` 字段从可选**改为强制**；缺失即 reject | 0.1h | 我永远不被卡；你延迟回复无副作用 | ✅ |
| **P1-A** | 加 `decisions/standing/` 目录 + `references/standing-decisions.md`，沉淀所有"已生效不再争论"的决议；新提案如挑战 standing decisions 必须显式说明 | 1h | 避免重复审，每周省 ~1 小时 | ✅ |
| **P1-B** | 加 `templates/phase-gate.md`（goal / non-goals / artifact schema / acceptance criteria 含样本量 / evaluation method / cost bound / rollback 7 件套），每个 Phase 启动前必须填 | 0.5h | 你的 protocol.md §"Recommended Phase Gate"已提到但缺模板；填完即可批 | ✅ |
| **P2-A** | 把 skill 拆为 `pm-engineer-protocol/`（通用骨架）+ `novel-supervisor/`（小说特化层 extends 通用）。通用层包含模板/红线机制，特化层只放架构词汇 | 2h | 后续其他项目可直接复用通用骨架 | 待 PM 判断是否值得现在做 |
| **P2-B** | 加 `references/engineer-side.md`（工程师侧操作手册）。当前 SKILL.md 全是监督视角，工程师需要知道：何时提 question / phase-report / proposal / risk；如何标证据；如何写默认决策 | 1h | 减少我的格式错误，省你来回打回的次数 | ✅ |
| **P3** | 消息状态机（open >7d 自动转 escalated；answered 后未 close >3d 自动 close） | 1.5h | 防止 inbox 堆积 | 可选 |

## Recommendation

**立即合并 P0 + P1 共 4 项**（约 2 小时工作量，每周节省 2-3 小时协作）。
**P2-A 待 PM 表态**（如果只服务本项目可暂不拆，如果半年内会复用就值得）。
**P2-B 一并合并**（强烈建议；当前 SKILL.md 完全没有给工程师的引导）。
**P3 暂缓**（等出现 inbox 堆积再做）。

## Evidence

我已把所有 P0 / P1 / P2-B 的具体内容草稿写在：

- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/references/evidence-tagging.md` (P0-A)
- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/templates/question.v2.md` (P0-B)
- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/references/standing-decisions.md` (P1-A)
- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/templates/phase-gate.md` (P1-B)
- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/references/engineer-side.md` (P2-B)
- `skill-draft/novel-rearchitecture-supervisor/proposed-additions/README.md` 索引

**未直接修改**你的 `SKILL.md` / `protocol.md` / `templates/` — 等你决定后再合并。

## Ask

请逐项 approve / reject。或一次性批 "P0+P1+P2-B 全部合并"。

## Supervisor Response

结论：`P0-A`、`P0-B`、`P1-A`、`P1-B`、`P2-B` 批准并已合并；`P3` 暂缓；`P2-A` 被范围修正取代。

绑定决议：

- `workspace/decisions/2026-04-26-skill-additions.md`
- `workspace/decisions/2026-04-26-communication-skill-scope.md`

执行说明：

- 证据标签、必填默认动作、长期决议、阶段门、工程师侧手册都已经并入通用沟通 skill 草案。
- 不创建小说特化 skill 作为当前目标；小说项目规则只放在 `project-brief.md`、`supervision-board.md`、`decisions/standing/`。
- inbox 自动状态机暂时不做，等真实堆积后再上。
