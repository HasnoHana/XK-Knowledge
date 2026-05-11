---
description: "Implementation plan for AI-proxy-led Claude Code knowledge MVP"
---

# Implementation Plan: Claude Code 知识管理系统 MVP

**Feature**: `20260509-claude-knowledge-mvp` | **Date**: 2026-05-09 | **Spec**: `/Users/bytedance/Desktop/Dev/specs/20260509-claude-knowledge-mvp/spec.md`
**Input**: Feature specification from `/specs/20260509-claude-knowledge-mvp/spec.md`

## Summary

保持 `Raw -> Ingest -> Query -> Check` 的产品流程不变，但实现策略进一步收敛为“AI Proxy + 预设提示词 + 工程兜底”。`ingest / query / check` 的核心判断、chunk 划分、知识提炼、关系判定、完整性自检与答案组织由大模型在 `CONSTITUTION.md + WIKI/<type>/LAWS.md + Prompt Pack + 当前知识上下文` 的约束下完成；工程层只负责输入批准校验、上下文装配、结构化输出校验、原子提交与失败回滚。

当前实现中需要明确纠偏两点：第一，`RawChunk` 不能再由固定工程规则先行切分后驱动页面结构，而要由 Claude Code 风格 AI Proxy 在 ingest prompt 引导下完成 chunk 划分与证据组织；第二，`wiki/index/link/log` 的目标产物必须作为同一轮模型输出的一部分统一生成，工程层不能在核心知识内容缺失时用模板逻辑补齐。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer、Pydantic v2、PyYAML、pytest；Claude Code/AI Proxy 调用边界由 `ClaudeCodeRunner` 承担；预设提示词资产位于 `src/claude_knowledge_mvp/prompts/`  
**Storage**: 本地 Markdown 文件系统：`XK-Knowledge/RAW/`、`WIKI/`、`LOG/`，以及内部 `.system/` staging/transaction 目录  
**Testing**: pytest；以 AI Proxy 输出结构校验、CLI 集成测试、原子提交失败回滚验证、prompt 驱动路径验证为主  
**Target Platform**: 本地 macOS / Linux 下的 Claude Code CLI 会话  
**Project Type**: 单项目本地 CLI  
**Performance Goals**: 以正确性、完整性、可完成性、可回滚性为先；`query` 在不超过约 500 页 wiki 的范围内保持交互式响应  
**Constraints**: 全程 AI 主导；所有核心生成都由预设提示词引导；工程层不得用固定规则替代 chunk 划分、类型判定、章节组织、关系推断或日志/索引/关联草稿生成；MVP 不引入向量检索、Web UI、多用户协作或复杂版本治理  
**Scale/Scope**: 10-50 份 Raw、最多约 500 篇 wiki 页面、单用户本地演示闭环  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS**: 只允许人工批准的 Raw 进入 ingest，工程层负责阻止未批准输入。
- **PASS**: 每篇 wiki 页面必须至少保留一条有效 Raw 引用；AI Proxy 若未给出可验证引用，提交必须失败。
- **PASS**: page、全局/局部 `INDEX.md`、全局/局部 `LINK.md`、`LOG/<date>.md` 必须单次原子提交；任一写入失败必须整体回滚。
- **PASS**: MVP 范围仍限定在本地 CLI 与 Markdown 知识库，不扩展 lint、矛盾网络、向量检索、多用户、Web UI、复杂版本治理。
- **PASS**: 本轮新增执行约束——chunk 划分、页面类型、标题、摘要、章节、关系、完整性自检与 `index/link/log` 修正草稿全部由 AI Proxy 在 prompt 约束下生成；工程逻辑只允许做必要约束与事务保护。
- **PASS**: prompt 资产本身属于功能范围的一部分，必须与模型输出 schema 一起设计，而不是留作实现阶段临时补充。
- **Post-Phase 1 Re-check**: `research.md`、`data-model.md`、`contracts/`、`quickstart.md` 均遵守上述约束，无需额外豁免。

## Project Structure

### Documentation (this feature)

```text
specs/20260509-claude-knowledge-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── knowledge-mvp.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
XK-Knowledge/
├── CONSTITUTION.md
├── RAW/
├── WIKI/
│   ├── INDEX.md
│   ├── LINK.md
│   ├── concept/
│   ├── workflow/
│   └── cli/
├── LOG/
├── .system/
├── pyproject.toml
├── src/claude_knowledge_mvp/
│   ├── adapters/
│   ├── commands/
│   ├── domain/
│   ├── prompts/
│   │   ├── ingest.md
│   │   ├── query.md
│   │   └── check.md
│   ├── services/
│   └── wrappers/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: 保持现有单项目 Python CLI 结构不变，但调整职责边界为：`prompts/` 定义预设提示词与输出契约；`ClaudeCodeRunner` 负责经由 Claude Code 风格 AI Proxy 执行 prompt 并返回结构化结果；`services` 负责上下文装配、最小必要校验、索引/关系/日志物化与事务提交；`domain` 承载 prompt 输入输出、知识草稿与原子提交不变量。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |
