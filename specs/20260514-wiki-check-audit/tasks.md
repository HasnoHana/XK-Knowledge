# Tasks: 20260514-wiki-check-audit

**Input**: Design documents from `/specs/20260514-wiki-check-audit/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 保留实现所需的单元测试与 quickstart 验证任务，重点验证两阶段顺序、只读边界与报告输出。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 明确 `/xk-check` 的新增落点，并对齐现有 ingest/query 的命令与 runtime 模式。

- [ ] T001 [Setup] 对齐 `specs/20260514-wiki-check-audit/plan.md`、`research.md`、`data-model.md` 与现有 `src/claude_knowledge_mvp/runtime/ingest.py`、`src/claude_knowledge_mvp/runtime/query.py` 的可复用模式
- [x] T002 [P] [Setup] 新增 `.claude/commands/xk-check.md` 文件骨架，固定 command-first 的单页检查入口与单参数约束
- [x] T003 [P] [Setup] 新增 `src/claude_knowledge_mvp/prompts/check_phase1.md` 与 `src/claude_knowledge_mvp/prompts/check_phase2.md` 文件骨架，预留两阶段 prompt pack 位置

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有用户故事共享的检查数据结构、上下文装配、阶段门禁与结果整形能力。

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [Foundation] 在 `src/claude_knowledge_mvp/domain/models.py` 中新增 `CheckTarget`、`DeclaredRawCitation`、`Phase1CheckContext`、`Phase2GlobalContext`、`CheckFinding`、`CheckReport` 等最小数据结构
- [x] T005 [P] [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中建立 check runtime 骨架：输入校验、prepare、phase gate、报告组装与结构化错误返回
- [x] T006 [P] [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现目标页面路径校验与 `page_id` / `wiki_type` 解析，严格限制输入为 `WIKI/*/pages/*.md`
- [x] T007 [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现生效规则读取：`CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md`、phase1/phase2 prompt
- [x] T008 [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现页面内声明 Raw 引用的提取与解析骨架，确保只装配页内已声明证据，不扩展到整份 Raw 或关联 wiki 页面
- [x] T009 [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 Phase 1 → Phase 2 的强顺序门禁，禁止在第一阶段未完成时直接检查 `WIKI/INDEX.md` / `WIKI/LINK.md`
- [x] T010 [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现阶段结果到统一 markdown 报告的整形逻辑，并对齐 `specs/20260514-wiki-check-audit/contracts/check-stage-result.schema.json`
- [x] T011 [Foundation] 在 `src/claude_knowledge_mvp/runtime/check.py` 中建立注入式 phase checker/session bridge 边界，保证 runtime 不主动调用 Claude SDK、Claude CLI 或其他二次模型链路

**Checkpoint**: Foundation ready - `/xk-check` shared runtime boundary is stable.

---

## Phase 3: User Story 1 - 通过 `/xk-check` 显式审计单页 wiki (Priority: P1) 🎯 MVP

**Goal**: 让维护者可以对一个指定 wiki 页面执行 command-first 检查，并拿到一份只读的 markdown 审计报告。

**Independent Test**: 对一个存在的 `WIKI/*/pages/*.md` 页面执行 `/xk-check`，若路径合法且阶段输入齐备，则命令在不修改仓库文件的前提下返回一份包含 Scope、Phase 1、Phase 2、Result 的 markdown 报告。

- [x] T012 [US1] 在 `.claude/commands/xk-check.md` 中定义 `/xk-check <wiki-page-path>` 的主路径，隐藏底层 prepare/check/bridge 细节
- [x] T013 [US1] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 `prepare_check_payload(...)`，输出单页检查所需的 phase1 初始 payload
- [x] T014 [US1] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 `execute_check(...)` 主流程，串联两阶段 checker 结果并生成最终 `CheckReport`
- [x] T015 [US1] 在 `.claude/commands/xk-check.md` 与 runtime 输出中固化“只返回报告、不写任何 wiki/index/link/log 文件”的用户可见边界
- [x] T016 [US1] 在 `src/claude_knowledge_mvp/runtime/check.py` 中补全失败路径：路径非法、文件缺失、页面无可解析 Raw 引用、缺少 `CONSTITUTION.md` 或 phase 输入损坏时返回结构化错误
- [x] T017 [US1] 在 `specs/20260514-wiki-check-audit/quickstart.md` 的示例场景上跑通一次主路径 walkthrough，并修正文案与报告骨架中的偏差

**Checkpoint**: User Story 1 delivers the minimal command-first single-page audit flow.

---

## Phase 4: User Story 2 - 基于页内已声明证据识别两类最小问题并补充 Link 最小检查 (Priority: P2)

**Goal**: 让检查流程先识别“无来源陈述”“过强结论”，再在第二阶段仅做基于同次上下文的最小 INDEX/LINK 检查。

**Independent Test**: 准备一个页面，使其同时包含已声明证据支持的陈述、无来源陈述、过强结论，以及至少一个可核对的 link 目标；执行 `/xk-check` 后，报告应先输出页面级 finding，再输出最小化的全局 finding。

- [x] T018 [US2] 在 `src/claude_knowledge_mvp/prompts/check_phase1.md` 中明确第一阶段提示词：只允许依据目标页面与页内声明 Raw 证据判断“无来源陈述”“过强结论”“证据受限”
- [x] T019 [US2] 在 `src/claude_knowledge_mvp/prompts/check_phase2.md` 中明确第二阶段提示词：继承第一阶段全量上下文，只检查 `WIKI/INDEX.md` / `WIKI/LINK.md` 的最小要求，尤其是关联文件是否正确
- [x] T020 [US2] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 Phase 1 payload 细化，向 checker 提供页面内容、声明引用、constitution、candidate laws 与 phase1 prompt
- [x] T021 [US2] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 Phase 2 payload 细化，继承第一阶段结果并补充 `WIKI/INDEX.md`、`WIKI/LINK.md` 与可解析页面 id 集合
- [x] T022 [US2] 在 `src/claude_knowledge_mvp/runtime/check.py` 中实现 `WIKI/LINK.md` 的最小正确性检查辅助逻辑，仅校验关联文件存在性、可解析性与目标指向正确性
- [x] T023 [US2] 在 `src/claude_knowledge_mvp/runtime/check.py` 中收敛 finding 类型，确保页面级只暴露“无来源陈述”“过强结论”，全局级仅补充最小 `关联文件不正确` / `证据受限`
- [x] T024 [US2] 在 `specs/20260514-wiki-check-audit/contracts/xk-check-command.md` 与 `contracts/check-stage-result.schema.json` 对齐实际阶段结果字段，避免 prompt/runtime/contract 漂移

**Checkpoint**: User Story 2 adds the bounded two-phase audit semantics.

---

## Phase 5: User Story 3 - 延续当前命令驱动知识工作流的最小审计架构 (Priority: P3)

**Goal**: 确保 `/xk-check` 与 ingest/query 保持同构：当前会话内完成 Agent 判断，runtime 只做薄层装配、阶段衔接和结果整形。

**Independent Test**: 审查实现后，`/xk-check` 不依赖独立服务、不在脚本内部发起模型调用，并且其命令/运行时结构能与 `xk-ingest`、`query.py` 的模式对应起来。

- [x] T025 [US3] 在 `src/claude_knowledge_mvp/runtime/check.py` 中明确注入式 checker 接口，保证测试与真实会话桥接共用同一执行流
- [x] T026 [US3] 新增 `src/claude_knowledge_mvp/runtime/check_cli.py`，提供与现有 runtime 一致的本地 debug/prepare 入口，但不把它暴露为主要用户产品形态
- [x] T027 [US3] 在 `.claude/commands/xk-check.md` 中把命令层收敛为对统一 check runtime 的薄包装，避免形成第二套检查语义
- [x] T028 [US3] 对照 `src/claude_knowledge_mvp/runtime/ingest.py`、`src/claude_knowledge_mvp/runtime/query.py` 复核边界，删除任何会让 runtime 退化为规则引擎或模型调用器的实现偏差

**Checkpoint**: All user stories now share the intended thin-runtime architecture.

---

## Phase 6: Verification & Polish

**Purpose**: 用自动化与手工验证收口只读边界、阶段顺序与文档一致性。

- [x] T029 [P] [Polish] 在 `tests/unit/test_check_runtime.py` 中补充路径非法、页面缺少引用、Phase 2 gate、缺少 `WIKI/LINK.md`、错误 link 目标、注入式 checker 返回 finding 等单元测试
- [x] T030 [P] [Polish] 在 `tests/unit/test_check_runtime.py` 中增加“成功与失败场景均不写仓库文件”的只读回归测试
- [x] T031 [Polish] 按 `specs/20260514-wiki-check-audit/quickstart.md` 手工验证主路径、证据受限场景、Link 错误场景，并确认报告仍为人读 markdown
- [x] T032 [Polish] 对齐 `specs/20260514-wiki-check-audit/spec.md`、`plan.md`、`quickstart.md`、`contracts/` 与实际实现，确保没有漂移到批量扫描、自动修复或二次模型调用

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user story work
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 main flow completion
- **User Story 3 (Phase 5)**: Depends on Foundational completion，并在 US1/US2 明确后收口架构边界
- **Verification & Polish (Phase 6)**: Depends on desired implementation work being complete

### User Story Dependencies
- **User Story 1 (P1)**: MVP 主交付，先跑通 command-first 单页检查
- **User Story 2 (P2)**: 依赖 US1 的命令主路径与两阶段执行骨架
- **User Story 3 (P3)**: 依赖前述实现已成型后再统一收口架构一致性

### Within Each User Story
- 先完成命令/运行时入口与数据结构
- 再完成两阶段 payload 与 prompt 约束
- 然后完成 Link 最小检查与结果整形
- 最后完成单元测试与 quickstart 验证

### Parallel Opportunities
- Setup 阶段的 T002、T003 可并行
- Foundation 阶段的 T005、T006 可并行，随后串行完成 T007-T011
- US2 阶段的 T018、T019 可并行；T020、T021 在 prompt 定义后推进
- Polish 阶段的 T029、T030 可并行

---

## Parallel Example: User Story 2

```bash
Task: "在 src/claude_knowledge_mvp/prompts/check_phase1.md 中定义第一阶段 prompt"
Task: "在 src/claude_knowledge_mvp/prompts/check_phase2.md 中定义第二阶段 prompt"
Task: "在 src/claude_knowledge_mvp/runtime/check.py 中实现 Phase 1 payload 细化"
```

---

## Implementation Strategy

### MVP First
1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **STOP and VALIDATE**：确认 `/xk-check` 可以对单页返回只读 markdown 报告，且不会改写仓库文件
5. 若验证通过，再进入 User Story 2 的 finding 细化与 Link 最小检查

### Incremental Delivery
1. 先交付 command-first 单页检查骨架
2. 再补两阶段 prompt 与最小 finding 语义
3. 最后收口 check runtime 与 ingest/query 的同构边界
4. 每一步都必须坚持“当前会话内判断 + runtime 薄层 + 不写仓库”原则

## Notes
- 建议的最小 MVP 范围是 **User Story 1**，先证明单页命令入口与只读报告闭环
- User Story 2 才引入“无来源陈述”“过强结论”和最小 Link 检查的完整语义
- User Story 3 负责收口架构一致性，不应反向扩张产品 scope
- 当前任务列表刻意避免为批量扫描、自动修复、复杂 link 语义、多页一致性检查预留实现任务
- 若后续需要支持文件夹或全量扫描，应作为复用单文件流程的遍历扩展追加新任务，而不是改写当前语义
