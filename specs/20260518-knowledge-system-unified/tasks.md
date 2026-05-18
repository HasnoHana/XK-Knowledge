# Tasks: 20260518-knowledge-system-unified

**Input**: Design documents from `/specs/20260518-knowledge-system-unified/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md
**Tests**: 本轮以收紧系统风格与一致性为主，不新增独立 TDD 任务；保留必要的 quickstart 验证与现有测试文件收口任务。
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 明确本轮只做系统一致性收紧，不扩展新能力面。

- [ ] T001 [Setup] 对齐 `specs/20260518-knowledge-system-unified/spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`，确认本轮范围仅为统一边界、统一结果面、统一命令口径
- [ ] T002 [P] [Setup] 盘点并锁定本轮改动文件：`.claude/commands/xk-ingest.md`、`.claude/commands/xk-check.md`、`.claude/commands/xk-query.md`、`src/claude_knowledge_mvp/domain/models.py`、`src/claude_knowledge_mvp/runtime/{ingest,query,query_cli,check,check_cli}.py`、`src/claude_knowledge_mvp/prompts/{ingest/query/check}`、`tests/{conftest.py,unit/}`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共享的一致性基础。

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [Foundation] 在 `src/claude_knowledge_mvp/domain/models.py` 中补齐共享结果模型，统一 query / check 的 citation、answer、report、evidence limit 结构
- [ ] T004 [P] [Foundation] 在 `tests/conftest.py` 中建立统一 repo fixture，减少 ingest/query/check 各自维护不同最小仓库形态的问题
- [ ] T005 [Foundation] 统一 `src/claude_knowledge_mvp/prompts/paths.py` 与 runtime 引用约定，确保 query CLI、check CLI、prompt 目录命名与现有路径一致

**Checkpoint**: 三条主路径已有共享模型、共享测试夹具、共享路径约定

---

## Phase 3: User Story 1 - 已经可以把 Raw 落成可消费的知识页 (Priority: P1) 🎯 MVP

**Goal**: 在不改变 ingest 能力边界的前提下，让 ingest 与系统其余部分在命令口径、错误语义和单向调用边界上保持一致。

**Independent Test**: 执行 `/xk-ingest RAW/article/example.md` 时，用户看到的仍是直接命令体验、结构化成功/失败结果，以及明确的 Claude Code → 本地脚本 单向边界。

- [ ] T006 [US1] 收紧 `.claude/commands/xk-ingest.md` 的措辞，使其与统一契约一致：当前会话负责 AI 推理，本地 runtime/helper 只负责 prepare / parse / validate / commit / rollback
- [ ] T007 [US1] 收紧 `src/claude_knowledge_mvp/runtime/ingest.py` 的桥接错误语义和结果字段命名，使其与系统一致性契约中的 ingest result surface 对齐
- [ ] T008 [US1] 收紧 `src/claude_knowledge_mvp/prompts/ingest/prompt.md` 的证据边界措辞，统一与 query/check 的 evidence limit 语言
- [ ] T009 [US1] 收口 `src/claude_knowledge_mvp/runtime/ingest_cli.py` 的本地调试入口文案，明确它是 debug/runtime tooling 而不是主要用户产品形态
- [ ] T010 [US1] 用 `specs/20260518-knowledge-system-unified/quickstart.md` 的 ingest 场景手工核对命令主路径与失败路径描述是否仍成立

**Checkpoint**: ingest 保持原有功能，但表达、错误语义和 orchestration boundary 已与全系统统一

---

## Phase 4: User Story 2 - 已经可以基于现有知识进行查询和审计 (Priority: P1)

**Goal**: 统一 query 和 check 的结果面、命令面和证据语义，让“可消费 + 可审计”读起来像同一个系统。

**Independent Test**: 对已有 wiki 页面执行 query 与 `/xk-check` 时，二者都显式暴露 evidence limits，且 query 返回统一 citations 结构、check 返回统一 report 结构。

- [ ] T011 [US2] 新增或规范化 `.claude/commands/xk-query.md`，把它定义为 query 的薄命令别名，但不改变 query 的 skill-first 产品定位
- [ ] T012 [US2] 在 `src/claude_knowledge_mvp/runtime/query.py` 中统一 query 输出结构，至少固定 `answer`、`citations`、`evidence_limits`，去掉与系统契约不一致的顶层字段
- [ ] T013 [P] [US2] 新增 `src/claude_knowledge_mvp/runtime/query_cli.py`，让 query 也拥有与 ingest/check 对齐的本地 runtime 入口，但不在内部调用 Claude
- [ ] T014 [US2] 收紧 `src/claude_knowledge_mvp/prompts/query/prompt.md`、`src/claude_knowledge_mvp/prompts/check/phase1.md`、`src/claude_knowledge_mvp/prompts/check/phase2.md` 的证据边界与输出契约措辞
- [ ] T015 [US2] 收紧 `src/claude_knowledge_mvp/runtime/check.py` 与 `src/claude_knowledge_mvp/runtime/check_cli.py` 的结果面和报告结构，保证 `status`、`phase1_findings`、`phase2_findings`、`evidence_limits`、`report_markdown` 始终显式存在

**Checkpoint**: query 与 check 的结果面、命令面和 prompt 语言已经统一成同一种系统风格

---

## Phase 5: User Story 3 - 下一阶段要把三个能力收敛成更稳定的统一系统 (Priority: P2)

**Goal**: 把 ingest / query / check 三条路径真正收口成统一系统，而不是三个各自成立的局部实现。

**Independent Test**: 从 `Raw -> Ingest -> Query -> Check` 走通 quickstart 后，可以明确看到三条路径共享同一套边界、同一套 evidence language、同一套命令层心智。

- [ ] T016 [US3] 对照 `specs/20260518-knowledge-system-unified/contracts/system-consistency-contract.md`，统一 `.claude/commands/xk-ingest.md`、`.claude/commands/xk-check.md`、`.claude/commands/xk-query.md` 的边界表述
- [ ] T017 [US3] 对照 `specs/20260518-knowledge-system-unified/contracts/xk-query-command.md` 与 `data-model.md`，统一 query/check/ingest 对 Wiki Page、Index、Link、Raw Citation Chain 的字段命名与消费契约
- [ ] T018 [US3] 在 `tests/unit/test_ingest_commit_helper.py`、`tests/unit/test_query_runtime.py`、`tests/unit/test_check_runtime.py`、`tests/unit/test_query_cli.py` 中补齐一致性回归断言，覆盖一体化结果面和禁止内部 Claude 调用链的边界
- [ ] T019 [US3] 以 `specs/20260518-knowledge-system-unified/quickstart.md` 为脚本，手工完成一次 `Raw -> Ingest -> Query -> Check` 全链路 walkthrough，并修正文档与实现漂移

**Checkpoint**: 三条能力现在已经是一个统一系统，而不是仅仅“看起来相关”的三份能力

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 收口所有跨故事的一致性残差。

- [ ] T020 [Polish] 回读 `specs/20260518-knowledge-system-unified/spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md`，删除任何会误导为“新增能力开发”的表述，保持本轮只做风格与契约收紧
- [ ] T021 [P] [Polish] 运行现有单元测试与本地 CLI 帮助输出检查，确认本轮改动没有破坏当前最小能力
- [ ] T022 [Polish] 复核仓库内相关实现，确认没有任何脚本/runtime/helper 在内部新增 Claude Code、Claude CLI、Claude SDK 或新 Claude 进程调用

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion；可与 US1 局部交错，但以统一结果面为主
- **User Story 3 (Phase 5)**: Depends on US1 + US2 完成后再做系统级收口
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies
- **US1**: 收紧 ingest 口径，不改变 ingest 核心功能
- **US2**: 收紧 query/check 结果面与命令面，是本轮一致性工作的主体
- **US3**: 在 US1/US2 基础上完成系统级统一 walkthrough 和契约收口

### Parallel Opportunities
- T002、T004、T013、T014、T021 可并行
- US1 与 US2 可以在共享模型落定后分别推进不同文件
- Polish 阶段的验证任务可与文档回读并行

---

## Parallel Example: User Story 2

```bash
Task: "新增或规范化 .claude/commands/xk-query.md"
Task: "新增 src/claude_knowledge_mvp/runtime/query_cli.py"
Task: "收紧 src/claude_knowledge_mvp/prompts/query/prompt.md 与 src/claude_knowledge_mvp/prompts/check/phase1.md、phase2.md"
```

---

## Implementation Strategy

### MVP First
1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: US1
4. 完成 Phase 4: US2
5. **STOP and VALIDATE**：确认本轮确实只是收紧系统风格、一致性和契约，而不是扩展新能力

### Incremental Delivery
1. 先统一共享模型与路径约定
2. 再统一 ingest 的命令和错误语义
3. 再统一 query/check 的结果面与命令面
4. 最后完成全链路 walkthrough 与禁止内部 Claude 调用链复核

## Notes
- 本轮建议的 MVP 范围其实是 **US1 + US2**，因为“仅为收紧风格”至少要覆盖 ingest 与 query/check 两侧
- 如果中途发现某项工作开始引入新能力，而不是统一已有能力，应及时回退范围
- 当前任务列表刻意不包含批量检查、复杂 lint、检索增强、复杂 link 语义等扩展项
