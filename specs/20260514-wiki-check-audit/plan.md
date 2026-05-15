---
description: "Implementation plan for /xk-check wiki audit"
---

# Implementation Plan: `/xk-check` 单页引用审计

**Feature**: `20260514-wiki-check-audit` | **Date**: 2026-05-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/20260514-wiki-check-audit/spec.md`

## Summary

为仓库知识系统新增 command-first 的 `/xk-check`，以单个指定 wiki 文件作为最小检查粒度，按固定顺序完成两阶段审计：先做页内声明证据边界下的 RAW↔WIKI 表达一致性检查，再做依托前一阶段全量上下文的 INDEX/LINK 最小全局检查。实现延续 ingest/query 的边界：runtime 负责本地装配上下文、阶段衔接和结果整形，核心判断与报告撰写由当前 Claude 会话内的 Agent 完成，脚本内部不启动 Claude SDK、Claude CLI 或其他二次模型调用链路。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Python stdlib、现有 `claude_knowledge_mvp` runtime/helper 模块、Claude Code command workflow、pytest  
**Storage**: 仓库本地 Markdown 文件（`RAW/`、`WIKI/`、`LOG/`）；本功能为只读报告流，不新增持久化输出  
**Testing**: pytest 单元测试，使用临时 repo fixture 与注入式 checker fake  
**Target Platform**: 本地 Claude Code 会话 + 仓库内 Python CLI  
**Project Type**: 单仓库命令行/运行时项目  
**Performance Goals**: 单页检查在一次本地命令执行内完成；MVP 不设批量吞吐目标  
**Constraints**: 单文件最小粒度；两阶段强顺序；第二阶段必须继承第一阶段全量上下文；只输出人读 markdown 报告；不改写仓库文件；不得内部发起二次模型调用  
**Scale/Scope**: 每次调用只检查一个 wiki 页面；文件夹/全量扫描仅作为遍历同一单文件流程的后续扩展

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Pass: 审计证据边界继续服从仓库 constitution，不允许使用页外未声明证据或外部知识替代引用依据。
- Pass: `/xk-check` 只返回报告，不提交 wiki/index/link/log 变更，因此不会绕开“只有 RAW 支持的知识才能写入仓库”的硬规则。
- Pass: 方案保持 runtime 薄层，核心判断留在当前会话内完成，不在脚本内部启动额外 Claude/SDK/CLI 调用链。
- Pass: 第二阶段 Link 检查收敛为“关联文件是否正确”，避免在 MVP 阶段引入投机性图谱扩张。
- Re-check after design: Phase 1 设计产物仍保持上述边界，无需复杂度豁免。

## Project Structure

### Documentation (this feature)

```
specs/20260514-wiki-check-audit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── xk-check-command.md
│   └── check-stage-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```
.claude/
└── commands/
    └── xk-check.md

src/claude_knowledge_mvp/
├── domain/
│   └── models.py
├── prompts/
│   ├── check_phase1.md
│   ├── check_phase2.md
│   └── query.md
└── runtime/
    ├── check.py
    ├── check_cli.py
    ├── ingest.py
    └── query.py

tests/
└── unit/
    ├── test_check_runtime.py
    └── test_query_runtime.py
```

**Structure Decision**: 继续沿用当前单项目 CLI/runtime 结构；新增 command、runtime、prompt 与 unit test 资产，不引入独立服务、数据库或 Web 层。`check.py` 的职责收敛为输入校验、两阶段上下文装配、phase gate、最小结果归一化与 markdown 报告整形；默认 Claude bridge 保持未接线，避免 runtime 退化为规则引擎或内部模型调用器。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
