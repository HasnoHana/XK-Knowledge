# Tasks: Claude Code Skills 驱动的知识管理系统 MVP

**Input**: Design documents from `/specs/20260511-skills-ingest-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 本轮不生成独立 TDD/测试优先任务；仅保留实现所需的验证与验收任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立 skills-first MVP 的最小入口与文档骨架

- [x] T001 [Setup] 创建或整理 `skills/xk-ingest/SKILL.md` 的最小骨架，明确 `/xk-ingest` 是当前唯一 MVP 产品入口
- [x] T002 [P] [Setup] 整理 `src/claude_knowledge_mvp/prompts/ingest.md` 的正式 Prompt Pack 位置与加载约定
- [x] T003 [P] [Setup] 在 `src/claude_knowledge_mvp/helpers/` 下创建 `ingest_commit_helper.py` 占位文件，收口 helper 边界

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 完成所有用户故事共享的规则、上下文组装与提交流程边界

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [Foundation] 在 `skills/xk-ingest/SKILL.md` 中定义 skill 执行流：输入读取、上下文收集、Prompt 注入、Agent 调用、提交控制、结果反馈
- [x] T005 [P] [Foundation] 在 `src/claude_knowledge_mvp/domain/` 中整理 `RawDocument`、`SkillRuntimeContext`、`KnowledgeMutationSet`、`HelperCommitResult` 的结构契约与引用规则
- [x] T006 [P] [Foundation] 在 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中实现 helper 输入契约加载与基础校验入口，对齐 `specs/20260511-skills-ingest-mvp/contracts/xk-ingest-helper.contract.yaml`
- [x] T007 [Foundation] 在 `skills/xk-ingest/SKILL.md` 与仓库根目录下的 `CONSTITUTION.md` / `WIKI/<type>/LAWS.md` 之间建立固定读取约定，确保 skill 调用前能装配完整上下文
- [x] T008 [Foundation] 在 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中实现 staging、原子提交与失败回滚骨架，保证 page / index / link / log 不暴露部分成功状态

**Checkpoint**: Foundation ready - ingest user story can now begin

---

## Phase 3: User Story 1 - 通过 xk-ingest skill 将 Raw 落库为知识页 (Priority: P1) 🎯 MVP

**Goal**: 通过 Claude Code 原生 `/xk-ingest` skill 完成单份 Raw 的知识组织、统一 mutation set 生成与原子落库，使产物成为可供后续 query/check 消费的知识页

**Independent Test**: 在仓库根目录下的 `RAW/` 中准备一份已人工筛选的真实 Raw，通过 `/xk-ingest` 执行一次摄入；成功时同时生成 wiki 页面并更新 `INDEX.md`、`LINK.md`、`LOG/<date>.md`，且页面应体现按知识结构组织的内容重组，而不是沿 Raw 原文顺序压缩出的摘要页；若引用缺失、mutation set 不完整或落盘失败，则整体失败且无部分结果

- [x] T009 [US1] 在 `skills/xk-ingest/SKILL.md` 中实现 Raw 输入解析与准入检查，阻止未批准或不可读的 Raw 进入 ingest
- [x] T010 [US1] 在 `skills/xk-ingest/SKILL.md` 中实现 skill runtime context 组装：读取 Raw、仓库根目录下的 `CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md`、全局 `INDEX.md` / `LINK.md` 知识上下文与 ingest prompt
- [x] T011 [US1] 在 `skills/xk-ingest/SKILL.md` 中实现 Agent 调用路径，要求模型返回包含 `raw_chunks`、`wiki_page_draft`、`index_draft`、`link_draft`、`log_draft`、`completeness_report` 的统一 `KnowledgeMutationSet`，并在 Raw 证据约束下完成知识重组与页面组织，而不是按原文顺序压缩摘要
- [x] T012 [US1] 在 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中实现 schema 校验：拒绝缺少关键草稿、缺少合法 Raw 引用、`completeness_report` 为空，或虽然结构完整但本质上只是压缩摘要而未形成知识页的输出
- [x] T013 [P] [US1] 在 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中实现目标路径物化逻辑，解析 wiki 页面、`WIKI/INDEX.md`、`WIKI/LINK.md`、`LOG/<date>.md` 的写入位置
- [x] T014 [US1] 在 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中完成 page / index / link / log 的单次原子提交与回滚处理
- [x] T015 [US1] 在 `skills/xk-ingest/SKILL.md` 中接入 helper 提交结果，向用户输出知识摄入摘要而不是底层路径或 helper 内部细节
- [x] T016 [US1] 在 `skills/xk-ingest/SKILL.md` 与 `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` 中补全失败路径：Raw 不合法、Agent 输出漂移、引用非法、目标路径不可物化、任一写入失败时的拒绝与回滚
- [x] T017 [US1] 按 `specs/20260511-skills-ingest-mvp/quickstart.md` 手动跑通一次真实 ingest 演示，并记录需要修正的 skill 文案、Prompt 约束、知识页组织质量或 helper 提交细节

**Checkpoint**: User Story 1 完成后，skills-first MVP 应可独立演示

---

## Phase 4: User Story 2 - 通过 xk-query skill 基于索引和关联返回答案 (Priority: P2)

**Goal**: 保留 `xk-query` 的后续扩展位，基于 `index.md` / `link.md` 缩圈并返回带 Raw 引用链的答案

**Independent Test**: 在 US1 稳定后，对已覆盖主题发起 `xk-query`，返回答案、命中页面与至少一条 Raw 引用链

- [ ] T018 [US2] 在后续阶段于 `skills/xk-query/SKILL.md` 中实现 query skill 入口与问题输入协议
- [ ] T019 [US2] 在后续阶段实现基于 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 的候选页面缩圈与上下文扩展逻辑
- [ ] T020 [US2] 在后续阶段定义 `QueryAnswerDraft` 输出契约，并将引用链表达与结果展示接入 `xk-query`

**Checkpoint**: User Story 2 属于产品蓝图，当前不进入 MVP 实现

---

## Phase 5: User Story 3 - 通过 xk-check skill 核查单页引用一致性 (Priority: P3)

**Goal**: 保留 `xk-check` 的后续扩展位，对单页 wiki 执行引用一致性核查

**Independent Test**: 在 US1 稳定后，对包含缺引与过强结论的 wiki 页面执行 `xk-check`，输出结构化 finding

- [ ] T021 [US3] 在后续阶段于 `skills/xk-check/SKILL.md` 中实现单页检查入口与页面定位协议
- [ ] T022 [US3] 在后续阶段定义 `CheckFinding` 输出契约，区分 `missing_citation` 与 `overstated_claim`
- [ ] T023 [US3] 在后续阶段实现页面、Raw 证据与规则上下文的装配逻辑，并将核查结果反馈给用户

**Checkpoint**: User Story 3 属于产品蓝图，当前不进入 MVP 实现

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 收敛 MVP 文档、回归与后续扩展边界，不扩展新能力

- [ ] T024 [Polish] 对齐 `specs/20260511-skills-ingest-mvp/spec.md`、`plan.md`、`quickstart.md` 与实际 `/xk-ingest` 行为，确保 WIKI 始终被定义为知识页而不是 Raw 摘要，并修正文档偏差
- [ ] T025 [Polish] 清理旧的 CLI-first 表述或入口依赖，确保当前设计不再以 `cli.py` / `commands/*.py` 作为产品主接口
- [ ] T026 [Polish] 复核 `specs/20260511-skills-ingest-mvp/contracts/xk-ingest-helper.contract.yaml` 与 helper 实现的一致性，避免 skill/helper 契约漂移
- [ ] T027 [Polish] 明确记录 `xk-query` 与 `xk-check` 的后续扩展边界，确保本轮不误扩 scope

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user story work
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion，但本轮仅保留蓝图任务
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion，但本轮仅保留蓝图任务
- **Polish (Phase 6)**: Depends on desired implementation work being complete

### User Story Dependencies
- **User Story 1 (P1)**: 当前 MVP 唯一实现目标
- **User Story 2 (P2)**: 依赖 US1 产出的 wiki / index / link 结构
- **User Story 3 (P3)**: 依赖 US1 产出的 wiki 页面与 Raw 引用结构

### Within Each User Story
- 先完成 skill 输入与上下文装配
- 再完成 Agent 输出契约
- 然后完成 helper 校验与提交流程
- 最后完成端到端 walkthrough 与文案收口

### Parallel Opportunities
- Setup 阶段的 T002、T003 可并行
- Foundation 阶段的 T005、T006 可并行
- US1 阶段的 T012、T013 可并行，随后串行完成 T014-T017
- US2 / US3 当前仅作后续蓝图记录，不建议现在并行实现

---

## Parallel Example: User Story 1

```bash
Task: "在 skills/xk-ingest/SKILL.md 中实现 skill runtime context 组装"
Task: "在 src/claude_knowledge_mvp/helpers/ingest_commit_helper.py 中实现 schema 校验入口"
Task: "在 src/claude_knowledge_mvp/helpers/ingest_commit_helper.py 中实现目标路径物化逻辑"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **STOP and VALIDATE**：确认 `/xk-ingest` 能在 Claude Code 原生 skill 流程下完成成功落库与失败回滚
5. 若验证通过，本轮即可停止，不继续实现 US2 / US3

### Incremental Delivery
1. 先交付 `/xk-ingest` 作为唯一 MVP
2. 在 ingest 稳定后再考虑补 `xk-query`
3. 在 ingest 稳定后再考虑补 `xk-check`
4. 每个后续故事都必须继续遵守 skill orchestrator + thin helper 边界

---

## Notes
- 当前建议的**最小 MVP 范围就是 User Story 1**
- 当前 tasks.md 明确保留 `xk-query` / `xk-check` 的蓝图位，但不把它们纳入本轮实现范围
- helper 的职责被限制为 schema 校验、路径物化、原子提交与回滚，不得回退为知识判断层
- 若后续需要补独立自动化测试任务，可在不扩展产品范围的前提下单独追加
