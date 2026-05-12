---
description: "Implementation plan for Claude Code command-driven knowledge MVP"
---

# Implementation Plan: Claude Code 命令驱动的知识管理系统 MVP

**Feature**: `20260511-skills-ingest-mvp` | **Date**: 2026-05-11 | **Spec**: `/Users/bytedance/Desktop/XK-Knowledge/specs/20260511-skills-ingest-mvp/spec.md`
**Input**: Feature specification from `/specs/20260511-skills-ingest-mvp/spec.md`

## Summary

保持 `Raw -> Ingest -> Query -> Check` 的产品蓝图不变，但入口从额外外露 skill 收敛为 Claude Code 直接命令 `/xk-ingest`。当前 MVP 的主产品入口是 `.claude/commands/xk-ingest.md`：命令负责定义输入/输出约束并触发 direct ingest runtime；thin helper 仅负责 schema 校验、目标路径物化、原子提交与失败回滚。当前 ingest 的产品目标不是把 Raw 压缩成摘要页，而是在 Raw 证据约束下生成一个可供后续 query/check 消费的知识页：Agent 负责重组、归纳、规范化命名与结构化组织，`/xk-query` 与 `/xk-check` 继续保留在产品蓝图和后续计划中，但本轮实现范围只覆盖 ingest。

## Implementation Status

- **[已实现]** `/xk-ingest` 作为当前唯一 MVP 产品入口
- **[已实现]** 命令上下文装配、统一 mutation set 校验、page/index/link/log 原子提交与失败回滚
- **[已实现]** 产品定义已切换为“知识页优先”，不再把 WIKI 视为 Raw 摘要页
- **[规划中]** `/xk-query` 与 `/xk-check` 仍保留在产品蓝图中，当前不进入实现范围

## Technical Context

**Language/Version**: Markdown spec + Claude Code command runtime；helper 使用 Python 3.11  
**Primary Dependencies**: Claude Code commands、Prompt Pack、Pydantic v2、PyYAML、pytest  
**Storage**: 本地 Markdown 文件系统；仓库根目录本身就是知识库根：`RAW/`、`WIKI/`、`LOG/`、`.system/`  
**Testing**: command walkthrough、helper 单元测试、原子提交/回滚验证、结构化输出校验  
**Target Platform**: 本地 Claude Code 风格环境（当前通过 `ttadk code` + custom model 运行）  
**Project Type**: 单项目命令工作流 + 本地 helper  
**Performance Goals**: 优先保证正确性、完整性、可回滚性和可演示性；单次 ingest 对单份 Raw 稳定完成  
**Constraints**: 产品入口必须是 `/xk-ingest` 命令；helper 不得承载核心知识判断；MVP 不引入向量检索、Web UI、多用户协作、复杂版本治理  
**Scale/Scope**: 10-50 份 Raw、最多约 500 篇 wiki 页面、单用户本地知识库演示闭环

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS**: 只允许人工批准的 Raw 进入 ingest，命令/runtime 必须在进入 Agent 调用前完成输入准入检查。
- **PASS**: 每篇 wiki 页面必须至少保留一条有效 Raw 引用；若 Agent 未返回可验证引用，helper 必须拒绝提交。
- **PASS**: page、`INDEX.md`、`LINK.md`、`LOG/<date>.md` 必须单次原子提交；任一写入失败必须整体回滚。
- **PASS**: MVP 仍限定在本地知识库与命令工作流，不扩展 lint、矛盾网络、向量检索、多用户、Web UI、复杂版本治理。
- **PASS**: 核心知识工作由 Agent 在 prompt 约束下完成；helper 只承担机械性兜底，不得回退为规则驱动流水线。
- **PASS**: ingest 产物必须是知识页而不是摘要页；页面组织应服务于知识消费与后续 query/check，而不是按 Raw 原文顺序做压缩复述。
- **PASS**: prompt 资产本身属于正式交付物，必须与命令行为和 helper 校验契约一起版本化。
- **Post-Phase 1 Re-check**: `research.md`、`data-model.md`、`quickstart.md` 与 `contracts/` 均遵守上述边界，无需额外豁免。

## Project Structure

### Documentation (this feature)

```text
specs/20260511-skills-ingest-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── xk-ingest-helper.contract.yaml
└── tasks.md
```

### Source Code (repository root)

```text
.claude/commands/
├── xk-ingest.md
└── xk-ingest-debug.md

CONSTITUTION.md
RAW/
WIKI/
LOG/
.system/
src/claude_knowledge_mvp/
├── prompts/
│   └── ingest.md
├── domain/
├── runtime/
│   ├── ingest.py
│   └── ingest_cli.py
└── helpers/
    └── ingest_commit_helper.py

tests/
├── integration/
└── unit/
```

**Structure Decision**: 产品入口收敛到 `.claude/commands/xk-ingest.md`；仓库根目录本身就是知识库根，因此 Prompt Pack 位于 `src/claude_knowledge_mvp/prompts/`，知识内容位于 `RAW/`、`WIKI/`、`LOG/` 与 `.system/`，helper 作为命令/runtime 的内部提交组件存在于 `src/claude_knowledge_mvp/helpers/`。该结构的目标不是落一篇摘要页，而是让 Agent 把 Raw 组织成稳定的知识节点与页面结构，再由 helper 以事务方式提交。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |
