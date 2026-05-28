# 01 · 项目现状与重构必要性

## 1.1 项目现在是什么样

### 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.12 / FastAPI / LangGraph / SQLite + ChromaDB |
| 前端 | Next.js 16 / React 19 / Tailwind v4 / shadcn-style 自建组件 |
| 阅读端 | 独立 Next.js 16 应用 `reader/` |
| LLM 接入 | LiteLLM（统一接入 DeepSeek / 通义 / OpenAI / Anthropic） |
| 总代码量 | ~14000 行（不含 node_modules / 测试数据） |

### 核心 Pipeline（蓝图诊断的"流水线"）

```
[Init Graph · 8 节点]
concept → world_build → character_design → outline_plan
→ assemble_bible → extract_characters → init_world → init_world_book

[Chapter Graph · 13 节点]
load_context → world_advance → plot_plan → camera_decide
→ build_context → load_memories → scene_split → write_scenes
→ assemble_chapter → consistency_check → save_chapter / save_with_warning
→ extract_memories
```

### 现有 Agent 清单（17 个，按蓝图归类）

| 类别 | Agent | 当前职责 |
|------|-------|---------|
| 设定生成 | concept / world_builder / character_designer / outline_planner / outline_parser | 一次性生成 StoryBible V2 |
| 章节生成 | world / planner / camera / scene_splitter / scene_writer / scene_consistency / consistency / titler / character_arc | 流水线推进 |
| 辅助 | extractor / character_reviewer | 章末抽取记忆 + 更新角色状态 |

### 已有"半成熟"机制

下面这些是**已完成的工作**，重构时**不必从零造**，但可能需要改造：

1. **记忆版本化**：`chapter_versions.is_live` + `source_version_id` 全链路
2. **三层记忆**：`LayeredMemory` + `ContextBuilder`（L1 全局 / L2 摘要 / L3 检索）
3. **WorldBook 关键词触发注入**（已有 schema 但字段简陋，仅 5 字段）
4. **场景级生成**：每章 2-5 scene，独立写作 + 独立校验
5. **scene → chapter 反馈链**：`scene_consistency` 失败 feedback 传给 retry，`chapter_consistency` 失败也传给 scene retry（最近修复）
6. **任务取消机制**：`TaskRegistry` + `/control/cancel`
7. **DeepSeek 适配器**：thinking/fast 模式可配置 + 一键分层绑定 16 个 agent
8. **可视化前端**：8 个独立深度页（角色 / 世界 / 3D 宇宙 / 数据洞察 / 管线 / 版本树）

### 测试数据

- `data/story.db`：3 本测试小说（共 24 章），有完整记忆/triple/版本数据
- `data/story.db.bak_20260415_205247`：迁移前备份

## 1.2 为什么必须重构（蓝图诊断 + 实测验证）

### 蓝图给的"症状 → 根因"映射

| 症状 | 根因 | 缺失能力 |
|------|------|---------|
| 上下文一长就偏离 | Writer 直接面对过多历史和设定，缺少场景级上下文编译 | Context Compiler（已有雏形但不够） |
| 写得太流水 | 只有事件推进，没有场景戏剧结构 | Scene Dramaturgy（SceneCard 字段还很简单） |
| 不像人写的小说 | 缺少文风指纹、反 AI 味检测和重写循环 | Voice Bible + Style Critic + Revision Loop（**完全缺失**） |
| 没有聚焦效果 | 世界事件和章节焦点没有分权 | Narrative Director（当前 camera 是"客观摄像头"） |
| 长篇越写越散 | 没有读者承诺、分卷目标和伏笔账本强约束 | Story Contract + Foreshadow Ledger（**完全缺失**） |
| 一致性只能事后补救 | Consistency 是末端检查，不是贯穿式约束 | Canon & Memory Kernel（KG 太弱） |

### 实测验证（用户反馈 + 我的代码 review）

**用户原话**：
> "现在写出的小说效果太差了，我打算重构了"
> "上下文一长就偏离" / "字数不受控制" / "不像人写的"

**我的代码 review 发现的核心结构性问题**：

1. **Writer 职责过重**：当前 `scene_writer.py` prompt 同时承担「理解世界 + 判断一致性 + 发明冲突 + 决定 POV + 控制伏笔 + 写正文 + 自审」7 种任务（蓝图 §2.2 反对的反模式）

2. **没有"评审-修订"闭环**：
   - 当前 `scene_consistency` 失败 → 重写整个 scene（粗暴）
   - 没有"诊断 → 局部修订 brief → 定向重写"
   - 没有多候选 / pairwise 选择
   - autonovel 已证明这套闭环必需

3. **没有客观质量基线**：所有 LLM 调优都基于"我感觉这次更好"，无法证伪。这是导致**"调了三个月还是差"**的元问题。

4. **记忆系统的对象错位**：
   - 当前 `KnowledgeGraph` 是手写 `(subject, predicate, object, valid_from)` 四元组，但**没有 conflict detection**（DOME 论文证明加上后冲突率下降 8 倍）
   - `LayeredMemory` 实际上只在 query 时做关键词搜索，**没有"角色视角认知"**（A 知道但 B 不知道）

5. **Camera Agent 是"客观跟拍"而非"叙事选择"**：
   - 当前 `camera_decide_node` 输出 visible_events / hidden_events，本质是"摄像头看到什么"
   - 蓝图明确指出（§4.4）这是错的，应该是"叙事导演决定本章看什么"

6. **Init pipeline 一次定生死**：
   - 大纲生成后基本不再迭代（最近加了 regenerate-outline 是补丁）
   - 没有"读者承诺"的硬约束在每个 critic 中引用
   - 没有伏笔账本，伏笔种下后无追踪

## 1.3 重构必要性的最终判断

**结论：必须重构**。但有两个重要修正：

### 修正 1：不是"6 个 agent 不够聪明"，而是"系统范式不对"

不能再加 agent 解决问题。继续叠加 agent 只会让流水线更长更脆弱。
必须从「单链推进」转向「多内核协作 + 编辑部闭环」。

### 修正 2：不是"全部推倒重来"，是"基线驱动渐进改造"

理由：
- 现有 14000 行代码里有大量**正确的部分**（LangGraph 编排 / 版本化 / 前端组件库 / DeepSeek 适配器 / TaskRegistry 等）
- 推倒重来会损失 **2 个月的有效工程积累**
- 真正缺的是「评测基线 + 编辑闭环 + Per-Role Cognition + 强 KG」
- 这些都可以**渐进叠加**到现有 LangGraph 上

### 重构能否成功的元判断

**最大风险不是技术，而是无法证伪**。如果重构后还是凭"感觉变好了"判断，三个月后我们会回到原点。

→ **Phase 0 评测基线必须是第一步，且必须独立可用**。
→ 不能等所有 Phase 做完才看结果，每个 Phase 都要在基线上证明 +X% 改进。
