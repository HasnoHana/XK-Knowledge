# Tasks: Claude Code 知识管理系统 MVP

**Input**: Design documents from `/specs/20260509-claude-knowledge-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 本次任务拆解不单独生成测试优先任务；仅保留最小 MVP 所需的实现与验收任务。若后续需要 TDD，再补充专门测试任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 初始化 `XK-Knowledge/` 项目骨架与最小运行环境

- [x] T001 [Setup] 创建 `XK-Knowledge/` 下的基础目录骨架：`RAW/`、`WIKI/`、`LOG/`、`.system/`、`src/claude_knowledge_mvp/`、`tests/`
- [x] T002 [Setup] 初始化 `XK-Knowledge/pyproject.toml` 与最小依赖，包含 Typer、Pydantic v2、PyYAML、pytest
- [x] T003 [P] [Setup] 创建 CLI 入口文件 `XK-Knowledge/src/claude_knowledge_mvp/cli.py` 并注册 `ingest`、`query`、`check` 三个子命令壳子
- [x] T004 [P] [Setup] 创建提示词目录与占位文件：`XK-Knowledge/src/claude_knowledge_mvp/prompts/ingest.md`、`query.md`、`check.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事共享的规则、存储和事务基础

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [Foundation] 创建唯一最高规则文件 `XK-Knowledge/CONSTITUTION.md`，写入最小全局规则：命名、引用、原子提交、人工筛选、MVP 边界
- [x] T006 [P] [Foundation] 创建类型级规则文件 `XK-Knowledge/WIKI/concept/LAWS.md`、`XK-Knowledge/WIKI/workflow/LAWS.md`、`XK-Knowledge/WIKI/cli/LAWS.md`
- [x] T007 [Foundation] 创建全局索引与关联文件 `XK-Knowledge/WIKI/INDEX.md`、`XK-Knowledge/WIKI/LINK.md`，并为三类知识创建各自的 `INDEX.md` / `LINK.md`
- [x] T008 [P] [Foundation] 在 `XK-Knowledge/src/claude_knowledge_mvp/domain/models.py` 中定义 `RawDocument`、`RawChunk`、`WikiPage`、`IndexEntry`、`LinkEntry`、`LogEntry`、`CheckFinding` 数据模型
- [x] T009 [P] [Foundation] 在 `XK-Knowledge/src/claude_knowledge_mvp/domain/schemas.py` 中定义 ingest/query/check 的输入输出 schema 与文件布局常量
- [x] T010 [Foundation] 实现文件系统适配层 `XK-Knowledge/src/claude_knowledge_mvp/adapters/markdown_store.py`，负责读写 `RAW/`、`WIKI/`、`LOG/` 和 `.system/`
- [x] T011 [Foundation] 实现事务服务 `XK-Knowledge/src/claude_knowledge_mvp/services/transaction_service.py`，支持 staging、提交与回滚，保证 `RAW / WIKI / LOG` 不暴露部分成功状态
- [x] T012 [Foundation] 实现 Claude Code 适配层 `XK-Knowledge/src/claude_knowledge_mvp/adapters/claude_code_runner.py`，统一封装 ingest/query/check 三类模型调用边界
- [x] T033 [Foundation] 在 `XK-Knowledge/src/claude_knowledge_mvp/prompts/ingest.md`、`query.md`、`check.md` 中补全正式 Prompt Pack，明确 AI Proxy 的输入上下文、Constitution/Laws 加载方式、输出 schema、完整性要求和失败条件
- [x] T034 [Foundation] 在 `XK-Knowledge/src/claude_knowledge_mvp/domain/models.py` 与 `domain/schemas.py` 中补充 `PromptPack`、`KnowledgeMutationSet`、`QueryAnswerDraft`、完整性报告等模型，支撑 AI Proxy 返回统一 mutation set

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Ingest 原始资料生成知识页 (Priority: P1) 🎯 MVP

**Goal**: 将一份已人工筛选的 Raw 文档经由 Claude Code 风格 AI Proxy 处理后落库为 wiki 页面，并同步更新全局/局部 Index、Link 与日志

**Independent Test**: 在 `XK-Knowledge/RAW/article/` 放入一份样例文档后执行 ingest；成功时可同时看到新 page、全局/局部 `INDEX.md`、全局/局部 `LINK.md` 和 `LOG/<date>.md` 更新；失败时不可看到部分更新结果；若 AI Proxy 输出不完整或引用非法，也必须失败

- [x] T013 [US1] 实现 Raw 文档加载与 chunk 切分逻辑于 `XK-Knowledge/src/claude_knowledge_mvp/services/ingest_service.py`，生成稳定 `chunk_id`
- [x] T014 [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/ingest_service.py` 中实现基于 `CONSTITUTION.md` + `WIKI/<type>/LAWS.md` 的最小类型判定与 page 生成编排
- [x] T015 [P] [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/index_service.py` 中实现全局与局部 `INDEX.md` 的构建/更新逻辑
- [x] T016 [P] [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/link_service.py` 中实现全局与局部 `LINK.md` 的构建/更新逻辑，支持 `related`、`depends_on`、`superseded_by`
- [x] T017 [P] [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/log_service.py` 中实现 `LOG/<date>.md` 的追加写入逻辑
- [x] T018 [US1] 将 `ingest_service.py` 与 `transaction_service.py` 集成，保证 page、INDEX、LINK、LOG 以单次提交方式写入
- [x] T019 [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/commands/ingest.py` 中实现 `ingest` 命令，接入 `claude_code_runner.py`、存储服务与事务服务
- [x] T020 [US1] 补充最小错误路径：Raw 未通过人工筛选、无可引用 chunk、任一目标文件写入失败时的失败返回与回滚处理
- [x] T035 [US1] 重写 `XK-Knowledge/src/claude_knowledge_mvp/adapters/claude_code_runner.py` 的 ingest 路径，使其经由 Claude Code 风格 AI Proxy 和 `prompts/ingest.md` 执行，而不是用启发式规则推断 `wiki_type`、章节和关系
- [x] T036 [US1] 重构 `XK-Knowledge/src/claude_knowledge_mvp/services/ingest_service.py`：由 AI Proxy 完成 Raw chunk 划分、知识提炼、完整性检查、wiki 页面草稿以及 `index/link/log` 修正草稿生成；工程层仅负责上下文装配、结构化校验、稳定 ID 赋值和原子提交
- [x] T037 [US1] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/ingest_service.py` 与 `domain/schemas.py` 中增加完整性拒绝路径：当 AI Proxy 仅覆盖 Raw 局部内容、缺少合法引用集或 mutation set 不完整时，必须失败并回滚
- [x] T038 [US1] 调整 `XK-Knowledge/src/claude_knowledge_mvp/services/index_service.py`、`link_service.py`、`log_service.py` 的接口，使其接收 AI Proxy 返回的 mutation draft 进行物化，而不是自行推断核心知识变更

**Checkpoint**: User Story 1 完成后，最小 MVP 落库链路应可独立演示

---

## Phase 4: User Story 2 - Query 基于索引和关联返回答案 (Priority: P2)

**Goal**: 基于全局/局部 Index 和 Link 缩小上下文，再经由 Claude Code 风格 AI Proxy 返回答案与 Raw 引用链

**Independent Test**: 在 US1 已生成至少一篇 wiki 页后执行 query；返回答案、命中的 wiki 页面和至少一条 Raw chunk 引用链；未命中时返回明确提示

- [ ] T021 [US2] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/query_service.py` 中实现基于 `WIKI/INDEX.md` 的候选页面检索逻辑，并产出供 `prompts/query.md` 使用的上下文包
- [ ] T022 [US2] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/query_service.py` 中实现基于全局/局部 `LINK.md` 的一跳关联扩展逻辑，并将扩展上下文交给 AI Proxy 而不是直接拼接答案
- [ ] T023 [US2] 在 `XK-Knowledge/src/claude_knowledge_mvp/adapters/claude_code_runner.py` 中实现 query Prompt Pack 调用，返回结构化答案与 Raw chunk 引用链
- [ ] T024 [US2] 在 `XK-Knowledge/src/claude_knowledge_mvp/commands/query.py` 中实现 `query` 命令，并处理无命中与多候选返回

**Checkpoint**: User Story 2 完成后，知识库应具备最小可消费价值

---

## Phase 5: User Story 3 - Check 单页引用一致性核查 (Priority: P3)

**Goal**: 对单页 wiki 执行由 AI Proxy 主导的引用一致性检查，识别无来源陈述和过强结论

**Independent Test**: 对一篇包含正确引用、缺失引用和过强措辞的 wiki 页面执行 check；输出至少两类 finding：`missing_citation` 与 `overstated_claim`

- [ ] T025 [US3] 在 `XK-Knowledge/src/claude_knowledge_mvp/services/check_service.py` 中实现单页加载、对应 Raw chunk 读取与 check Prompt Pack 上下文装配逻辑
- [ ] T026 [US3] 在 `XK-Knowledge/src/claude_knowledge_mvp/adapters/claude_code_runner.py` 中实现 check Prompt Pack 调用，生成 `missing_citation` 与 `overstated_claim` finding
- [ ] T027 [US3] 在 `XK-Knowledge/src/claude_knowledge_mvp/commands/check.py` 中实现 `check` 命令，并输出结构化结果而不是直接改写页面

**Checkpoint**: 所有用户故事完成后，系统应能完整跑通 ingest → query → check 闭环

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 收敛最小 MVP 所需的文档与验证，不扩展新能力

- [ ] T028 [Polish] 对照 `specs/20260509-claude-knowledge-mvp/quickstart.md` 手动验证一次完整演示流程，并修正文档中的实际命令或路径偏差
- [ ] T029 [Polish] 清理 `XK-Knowledge/src/claude_knowledge_mvp/` 中不再需要的启发式占位逻辑，确保未引入 plan 之外的额外能力
- [ ] T030 [Polish] 运行最小回归检查，确认 AI Proxy 驱动的 ingest 原子提交、query 引用链与单页 check 三条主路径均可工作
- [x] T031 [Polish] 在 Claude Code 配置最小入口层，新增 `/xk-ingest`、`/xk-query`、`/xk-check` slash skill/command，并保持底层复用 `XK-Knowledge` 本地 CLI
- [x] T032 [Polish] 为 Claude Code 入口层补充最小 wrapper/参数转发实现，避免向用户暴露 `PYTHONPATH`、绝对路径拼接或 MCP 前置配置
- [ ] T039 [Polish] 为 `XK-Knowledge/src/claude_knowledge_mvp/prompts/` 下的 Prompt Pack 增加版本标识与最小回归校验，确保运行时加载的是正式 prompt 而非占位内容

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion because query 需要已有 wiki 数据可读
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion because check 需要已有 wiki 页面与 Raw 引用
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: 第一优先级，也是建议 MVP 停止点
- **User Story 2 (P2)**: 依赖 US1 产出的 wiki/索引/关联结构
- **User Story 3 (P3)**: 依赖 US1 产出的 wiki 页面与引用结构，但不依赖 US2

### Within Each User Story

- Prompt Pack 与模型输出契约先完成
- AI Proxy 输出物化晚于上下文装配与结构校验
- 命令入口晚于对应 service / runner
- 先完成 P1，再决定是否继续 P2 / P3，避免过分扩展

### Parallel Opportunities

- Setup 阶段的 T003、T004 可并行
- Foundational 阶段的 T033、T034 可并行
- US1 阶段的 T035、T038 可并行，随后串行完成 T036、T037
- US2 内部以串行为主，避免在 `query_service.py` 中产生同文件冲突
- US3 内部以串行为主，避免在 `check_service.py` 中产生同文件冲突

---

## Parallel Example: User Story 1

```bash
Task: "在 XK-Knowledge/src/claude_knowledge_mvp/prompts/ingest.md 中编写正式 ingest Prompt Pack"
Task: "在 XK-Knowledge/src/claude_knowledge_mvp/domain/models.py 和 domain/schemas.py 中补充 KnowledgeMutationSet 与完整性报告模型"
Task: "在 XK-Knowledge/src/claude_knowledge_mvp/adapters/claude_code_runner.py 中接入 Claude Code 风格 AI Proxy 的 ingest 调用"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **STOP and VALIDATE**：手动验证 ingest 是否经由 AI Proxy 在 Prompt Pack 引导下原子写入 page、全局/局部索引、全局/局部关联和日志
5. 若仅需要最小 MVP，到此可以先停止，不继续扩展 US2 / US3

### Incremental Delivery

1. Setup + Foundational 完成后，先交付 US1 作为最小 MVP
2. 在 US1 稳定后再增加 US2（Query）
3. 在 US1 稳定后可独立增加 US3（Check）
4. 每个故事都必须在自己的 checkpoint 被独立验证

---

## Notes

- 本任务拆解严格按当前 plan 执行，不额外扩展类型系统、向量检索、Web UI 或多用户能力
- `[P]` 只用于不同文件、无直接依赖的任务
- 当前建议的**最小 MVP 范围就是 User Story 1**
- 已完成的 T013-T020 反映此前实现历史；根据本轮澄清新增的 T033-T039 用于把系统从启发式工程流纠偏为 Prompt Pack 驱动的 AI 主导流程
- 若后续要补自动化测试或 TDD，请在此 tasks.md 基础上单独追加，不要在本轮实现中扩 scope
