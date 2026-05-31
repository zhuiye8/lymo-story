# 狸梦小说 Lymo Story — 多智能体 AI 中文长篇小说生成系统

人类提供题材/思路，多个专用 AI Agent 通过 LangGraph 编排协作，自动完成世界构建、角色设计、大纲规划与逐章撰写——并在**事实一致性**、**角色情感连续性**、**伏笔埋坑/填坑**三条线上显式管理长程状态，配合确定性的反 AI 腔（anti-slop）质量闸。

> Brand: 狸梦小说 / Lymo Story｜作者：zhuiye（追夜）
> 这是 **Phase 1 重构版**（从 0 重建，不兼容旧数据）。设计文档见 `phase1/`。

## 系统架构

```
初始化（一次）：
  题材 → 立意 → 世界观(3步) → 角色设计(+对白指纹) → 大纲 → 组装落库
                                                   ↓ 初始 DOME 事实 + L0 身份记忆

逐章生成（循环）：
  载入上下文 → 推进细纲 → 分镜规划 → 召回记忆 → 写章(best-of-N)
                                                 ↓ 每个候选过质量闸
                                  [检测 slop → 字数矫正 → 局部改写 → 异源评委打分]
                                                 ↓ 取综合分最高
                              抽取记忆/事实/伏笔 → 落库(去重+冲突检测+伏笔回收)
```

### Agent 职责（backend/agents/phase1/）

| Agent | 职责 | 模型 |
|-------|------|------|
| Concept | 题材 → 立意（书名/题材/基调/金手指） | flash |
| WorldBuilder | 世界观（世界核心 → 势力 → 规则，分 3 步避免截断） | flash |
| CharacterDesigner | 角色名单 → 逐角色设计 + 对白指纹（voice profile） | flash |
| OutlinePlanner | 大纲骨架 → 分卷（粗纲） | flash |
| OutlineAdvance | 粗纲阶段 → 本章细纲节拍 | flash |
| ScenePlan | 节拍 → 分镜 + 每镜字数预算 + 章末钩子 | flash |
| SceneWriter | 分镜 → 中文正文 | **pro** |
| MemoryExtractor | 章节 → 事实四元组 + 状态 + 情感记忆 + 伏笔 + 摘要 | flash |
| Critic ×2 | 八维质量打分（异源去偏） | flash + **MiMo** |

## 长程一致性三件套

- **DOME 四元组**（`backend/memory/`）：只存**持久状态事实**，受控谓语词表（存活/境界/身份/阵营/能力/持有/关系）。单值谓语冲突检测捕捉"死人复活/境界倒退"式硬伤；事件归摘要，不污染事实库；写入去重 + invalidate-not-delete。
- **分层语义记忆 L0-L3**：L0 身份核心 + L1 情感关键记忆，双写 SQLite + ChromaDB（本地 Qwen3-Embedding 向量），按场景语境语义召回 + 情感权重召回，维系角色"记得什么、在意谁"。
- **伏笔闭环**：埋坑 → 按拖延章数催收给细纲师 → 兑现时标记回收。

## 质量闸（backend/quality/）

确定性 slop 检测（频次感知中文词表）→ 字数矫正 → 局部改写 → **异源评委房**（八维 WebNovelBench 评分，评委模型必须异于生成模型）→ best-of-N 取最优。

## 技术栈

- **后端**: Python 3.11 / FastAPI / LangGraph / LiteLLM / Instructor（结构化输出）
- **管理端**: Next.js 16 (TypeScript) / Tailwind 4 / Radix / ECharts — 建书、生成进度、章节阅读、质量/记忆/伏笔可视化、LLM 管理
- **阅读端**: Next.js 16（⚠️ 暂未对齐 Phase 1 接口）
- **存储**: SQLite（主库，含 bible/章节/四元组/状态/记忆/伏笔/质量）+ ChromaDB（记忆向量）
- **模型（硬约束，仅两家）**: DeepSeek API（主力，pro 写作 / flash 结构化与主评委）+ 小米 MiMo API（第二评委）
- **嵌入**: 本地 ollama + **Qwen3-Embedding-4B**（GPU，中文 SOTA；无 embedding API 依赖）
- **包管理**: 后端 pip（conda env "story"）/ 前端 pnpm

## 环境要求

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html)、Node.js ≥ 18、pnpm
- 一块 GPU（用于本地嵌入模型；嵌入模型很小，~3GB 显存足够）
- [ollama](https://ollama.com)（本地嵌入服务）
- DeepSeek API Key（必需）；MiMo API（可选，第二评委）

## 快速开始

### 1. Python 环境 + 依赖

```bash
conda create -n story python=3.11 -y && conda activate story
cd C:\Files\work\story
pip install -e ".[dev]"
```

### 2. 配置 `.env`（根目录）

```bash
cp .env.example .env
```
```env
# DeepSeek 主力（必需）
STORY_LITELLM_MODEL=deepseek/deepseek-chat
STORY_LITELLM_API_KEY=sk-your-deepseek-key
STORY_LITELLM_API_BASE=https://api.deepseek.com

# 第二评委 MiMo（可选；关闭则单评委降级）
STORY_MIMO_ENABLED=true
STORY_MIMO_API_KEY=sk-...
STORY_MIMO_API_BASE=http://<proxy>/v1

# 语义记忆嵌入（本地 ollama + Qwen3）
STORY_EMBED_PROVIDER=ollama
STORY_EMBED_MODEL=qwen3-embedding:4b
```

### 3. 拉取嵌入模型（一次）

```bash
ollama pull qwen3-embedding:4b   # 2.5GB；ollama 在 Windows 开机自启
```

### 4. 播种模型配置到 DB（一次 / 改 .env 模型后重跑）

```bash
python scripts/seed_phase1_models.py
```

### 5. 启动后端（从根目录）

```bash
conda activate story
uvicorn backend.main:app --reload --port 8000
```
验证：http://localhost:8000/api/health → `{"status":"ok"}`

### 6. 启动管理端

```bash
cd frontend && pnpm install && pnpm dev   # http://localhost:3000
```

## 使用流程

1. 管理端首页「新建故事」，填题材（如"落魄程序员觉醒代码编辑器系统，能改写现实源码"）+ 题材类型 + 目标章数
2. 系统后台跑初始化管线，生成立意/世界观/角色/大纲（状态变为 `bible_ready`）
3. 在故事仪表盘点击「生成第 N 章」，观察生成管线逐阶段进度
4. 章节阅读器查看正文；质量页看八维雷达/趋势/热力；记忆页看 L0/L1 分层记忆；伏笔页看埋坑/填坑
5. （阅读端发布流程待 Phase 1 对齐）

## 项目结构

```
story/
├── backend/
│   ├── main.py / config.py / deps.py
│   ├── agents/phase1/           # init_agents.py + chapter_agents.py（结构化走 _call_structured）
│   ├── prompts/phase1/          # 中文提示词（含 anti-slop 负向指令）
│   ├── graph/
│   │   ├── phase1_init.py        # 初始化图（5 节点）
│   │   ├── phase1_chapter.py     # 章节图（7 节点，best-of-N）
│   │   └── phase1_quality_gate.py# 检测-改写-评分闸
│   ├── memory/
│   │   ├── knowledge_quads.py    # DOME 四元组
│   │   ├── predicates.py         # 受控谓语词表 + 归一 + 兼容判断
│   │   └── layered_memory.py     # L0-L3 分层语义记忆（SQLite + ChromaDB）
│   ├── quality/                 # slop_lexicon_zh / slop_detector / rubric / critic_room / rewrite
│   ├── storage/                 # sqlite_store.py（主库）/ vector_store.py（ChromaDB，嵌入可配置）
│   ├── llm/                     # client.py（LiteLLM+Instructor）/ model_registry / logger / providers
│   ├── models/                  # phase1.py（bible）/ phase1_chapter.py（章节管线 schema）
│   └── api/                     # phase1_stories.py / quality_admin.py / llm_admin.py / public.py
├── frontend/                    # 管理端 Next.js 16（Phase 1 重建）
│   └── app/stories/[id]/{,chapters,characters,outline,quality,memory,foreshadowing}
├── reader/                      # 阅读端 Next.js 16（⚠️ 待 Phase 1 对齐）
├── scripts/                     # seed_phase1_models.py / stress_10ch.py（压测）
├── phase1/                      # 架构与实现计划文档
├── data/                        # 运行时数据（gitignored：SQLite + ChromaDB）
├── pyproject.toml / .env.example / CLAUDE.md
```

## API 端点（Phase 1）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/stories | 创建故事（后台初始化） |
| GET | /api/stories | 列出故事 |
| GET | /api/stories/{id} | 故事详情（含 bible） |
| GET | /api/stories/{id}/progress | 生成进度（阶段级） + 状态 + 章数 |
| GET | /api/stories/{id}/characters | 角色（含 voice profile） |
| GET | /api/stories/{id}/outline | 粗纲阶段 |
| POST | /api/stories/{id}/generate | 生成下一章 |
| GET | /api/stories/{id}/chapters[/{n}] | 章节列表 / 正文 |
| GET | /api/stories/{id}/foreshadowing | 伏笔（埋/收/待回收） |
| GET | /api/stories/{id}/memories | 分层记忆（L0/L1，按角色） |
| GET | /api/admin/quality/story/{id}/{trend,by-dimension,heatmap,distribution} | 质量图表 |
| GET/POST/PUT/DELETE | /api/admin/{models,bindings,logs,usage} | LLM 管理 |
| GET | /api/public/books[/{id}[/chapters/{n}]] | 阅读端公开接口 |

## 开发路线

- [x] **Phase 1 重构** — 从 0 重建，API-only（DeepSeek + MiMo），无质量妥协
  - [x] 初始化/章节双管线（LangGraph）+ best-of-N + 质量闸
  - [x] DOME 四元组事实一致性（冲突检测根因修复）
  - [x] 分层语义记忆 L0-L3（Qwen3-Embedding 中文向量）
  - [x] 伏笔埋坑/填坑闭环
  - [x] 异源评委房（DeepSeek + MiMo，八维 WebNovelBench）+ anti-slop
  - [x] 管理端 UI（建书/进度/阅读/质量/记忆/伏笔）
- [ ] 阅读端 reader 对齐 Phase 1 + 发布流程
- [ ] 长篇产出体验打磨（best-of-N 调优、critic 提示词迭代）
```
