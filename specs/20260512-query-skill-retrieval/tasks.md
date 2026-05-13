# Tasks: 20260512-query-skill-retrieval

**Input**: Design documents from `/specs/20260512-query-skill-retrieval/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 当前不单独生成测试任务；MVP 先以 quickstart 人工验证为准。

## Format: `[ID] [Story] Description`
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: 确认最小实现落点。

- [ ] T001 [Setup] 核对 `specs/20260512-query-skill-retrieval/` 下的设计文档与 `src/claude_knowledge_mvp/runtime/ingest.py` 的可复用模式
- [ ] T002 [Setup] 确认 query 只新增 `src/claude_knowledge_mvp/runtime/query.py`、`src/claude_knowledge_mvp/prompts/query.md`，以及可选 `.claude/commands/xk-query.md`

---

## Phase 2: Foundational

**Purpose**: 建立 query MVP 的公共基础能力。

- [ ] T003 [Foundational] 在 `src/claude_knowledge_mvp/runtime/query.py` 中建立 query runtime 骨架：接收问题、装配执行流程、调用 Agent
- [ ] T004 [Foundational] 在 `src/claude_knowledge_mvp/prompts/query.md` 中建立 query prompt pack，固化 skill-first、只读、证据绑定和最小输出约束
- [ ] T005 [Foundational] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 的读取入口，并约束为一跳扩展

**Checkpoint**: MVP foundation ready.

---

## Phase 3: User Story 1 - 在对话中直接触发知识查询 (Priority: P1) 🎯 MVP

**Goal**: 用户直接在对话中提问即可触发 query，并拿到答案、引用内容和 Raw chunk。

**Independent Test**: 在已有相关 wiki 页时，直接提问可得到答案、引用内容和 Raw chunk；无须先输入 `/xk-query`。

- [ ] T006 [US1] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现自然语言问题输入到 query runtime 的主路径
- [ ] T007 [US1] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现把相关 index/link/wiki 页面上下文提供给 Agent 的流程
- [ ] T008 [US1] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现最小结果整理：输出答案、引用内容、Raw chunk 与限制说明
- [ ] T009 [US1] 在 `src/claude_knowledge_mvp/prompts/query.md` 中补全“证据不足 / 问题模糊 / 不得伪造知识库结论”的回答约束

**Checkpoint**: User Story 1 delivers the MVP query path.

---

## Phase 4: User Story 2 - 基于索引缩圈并按 link 扩一跳上下文 (Priority: P2)

**Goal**: query 基于 Index 缩圈，再基于 Link 做一跳扩展，由 Agent 在相关知识上下文内回答。

**Independent Test**: 对依赖关联页面的问题，结果能体现 `INDEX.md` 命中与 `LINK.md` 一跳扩展带来的上下文补充。

- [ ] T010 [US2] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现 `INDEX.md` 命中策略，输出主页面候选集合
- [ ] T011 [US2] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现基于 `LINK.md` 的一跳扩展规则，禁止多跳扩散
- [ ] T012 [US2] 在 `src/claude_knowledge_mvp/runtime/query.py` 中实现无命中、link 缺失、冲突证据时的降级语义

**Checkpoint**: User Story 2 adds bounded retrieval.

---

## Phase 5: User Story 3 - 通过薄命令别名显式进入同一查询流程 (Priority: P3)

**Goal**: `/xk-query` 作为可选薄别名进入同一 query runtime，而不是形成第二套实现。

**Independent Test**: 对同一主题分别使用自然语言和 `/xk-query`，结果在答案内容与引用边界上保持一致。

- [ ] T013 [US3] 新增 `.claude/commands/xk-query.md`，定义可选薄别名入口并避免暴露底层实现细节
- [ ] T014 [US3] 在 `.claude/commands/xk-query.md` 中约束 `/xk-query` 仅包装问题输入并委托到统一 query runtime
- [ ] T015 [US3] 在 `src/claude_knowledge_mvp/runtime/query.py` 中补充显式入口路径，确保与 skill-first 共享同一行为

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish

**Purpose**: 收口实现边界和文档一致性。

- [ ] T016 [Polish] 对照 `specs/20260512-query-skill-retrieval/contracts/query-entrypoints.md` 检查实现，确认未重新引入 `query_output_schema` 或额外中间模型
- [ ] T017 [Polish] 对照 `specs/20260512-query-skill-retrieval/quickstart.md` 手工验证自然语言触发、无命中、link 扩展、`/xk-query` 对照场景
- [ ] T018 [Polish] 更新相关设计文档中的实现状态说明，确保 `spec.md`、`plan.md`、`quickstart.md` 与真实代码路径一致

---

## Dependencies & Execution Order

- Setup → Foundational → US1 → US2 → US3 → Polish
- **US1 (P1)** 是建议 MVP scope
- **US2 (P2)** 在 US1 基础上增加结构化检索价值
- **US3 (P3)** 仅为可选显式入口，不应阻塞 US1/US2

## Implementation Strategy

### MVP First
1. 完成 Setup
2. 完成 Foundational
3. 完成 US1
4. 按 quickstart 做人工验证

### Incremental Delivery
1. 先交付 US1 的直接查询路径
2. 再补 US2 的 index/link 一跳扩展
3. 最后决定是否需要 US3 的 `/xk-query` 薄别名

## Notes
- Suggested MVP scope: **User Story 1 only**
- 所有任务都应保持 query 为只读能力，不得引入写路径、commit 语义或独立 schema 约束
