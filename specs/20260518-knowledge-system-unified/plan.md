---
description: "Implementation plan for system consistency convergence"
---

# Implementation Plan: 系统一致性收敛

**Feature**: `20260518-knowledge-system-unified` | **Date**: 2026-05-18 | **Spec**: `/Users/bytedance/Desktop/XK-Knowledge/specs/20260518-knowledge-system-unified/spec.md`
**Input**: Feature specification from `/specs/20260518-knowledge-system-unified/spec.md`

## Summary

当前系统已经具备 ingest、query、check 三段最小能力，下一阶段不继续优先扩展新功能，而是先做系统收敛：统一 Claude Code → 本地脚本 的单向调用边界，统一 Wiki Page / Raw Citation Chain / Index / Link 的消费契约，统一 query 与 check 的结果面、evidence limits 语义、命令层表述和端到端验收路径。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: 标准库、dataclasses、现有 `claude_knowledge_mvp` runtime/helpers/prompts、Claude Code commands、pytest  
**Storage**: 本地 Markdown 文件系统（`RAW/`、`WIKI/`、`LOG/`、`.system/`）  
**Testing**: pytest 单元测试 + 命令 walkthrough + 本地 CLI 帮助输出校验  
**Target Platform**: 本地 Claude Code 会话 / macOS 或 Linux 开发环境  
**Project Type**: 单仓库本地命令工作流项目  
**Performance Goals**: 优先保证能力边界一致、结果结构一致、失败语义一致与可验收性；不以吞吐量扩展为当前目标  
**Constraints**: Claude Code 必须是唯一 AI orchestrator；脚本/runtime/helper 不得内部启动 Claude Code、Claude CLI、Claude SDK 或新的 Claude 进程；不引入 Web UI、独立在线服务、向量数据库或复杂版本治理  
**Scale/Scope**: 当前范围仅覆盖 ingest/query/check 三条主路径的一致性收敛，不扩展批量检查、复杂 link 语义、重型 lint 或检索增强

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS**: 系统继续运行在本地 Markdown 知识库上，没有引入 Web UI、外部服务、向量数据库或多用户协作前置条件。
- **PASS**: 一致性阶段继续坚持 Wiki Page 是知识页而不是 Raw 摘要，且 query/check 只能建立在仓库内显式证据之上。
- **PASS**: Claude Code 继续作为唯一 AI orchestrator；本地脚本、runtime、helper 仅承担机械性工作，不在内部启动新的 Claude 调用链。
- **PASS**: 当前阶段优先统一边界、结果面和验收路径，不扩展新能力面，符合“先收敛、后增强”的总 spec 主线。
- **Post-Phase 1 Re-check**: `research.md`、`data-model.md`、`contracts/`、`quickstart.md` 均维持上述边界，无需额外豁免。

## Project Structure

### Documentation (this feature)

```text
specs/20260518-knowledge-system-unified/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── system-consistency-contract.md
│   └── xk-query-command.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
.claude/commands/
├── xk-ingest.md
├── xk-check.md
└── xk-query.md                 # to be added or normalized

src/claude_knowledge_mvp/
├── domain/
│   └── models.py
├── prompts/
│   ├── ingest/
│   │   └── prompt.md
│   ├── query/
│   │   └── prompt.md
│   └── check/
│       ├── phase1.md
│       └── phase2.md
├── runtime/
│   ├── ingest.py
│   ├── ingest_cli.py
│   ├── query.py
│   ├── query_cli.py            # to be added
│   ├── check.py
│   └── check_cli.py
└── helpers/
    └── ingest_commit_helper.py

tests/
├── conftest.py
└── unit/
    ├── test_ingest_commit_helper.py
    ├── test_query_runtime.py
    ├── test_query_cli.py       # to be added
    └── test_check_runtime.py
```

**Structure Decision**: 保持现有单仓库命令工作流结构不变，不做大规模重构。当前计划只在命令层、runtime 层、prompt 层、domain model 层和测试夹具层做收敛性调整，以最小改动统一三条主路径的行为与语言。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |
