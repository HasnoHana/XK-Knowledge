---
description: "Implementation plan for Claude Code skills-first knowledge MVP"
---

# Implementation Plan: Claude Code Skills 驱动的知识管理系统 MVP

**Feature**: `20260511-skills-ingest-mvp` | **Date**: 2026-05-11 | **Spec**: `/Users/bytedance/Desktop/Dev/specs/20260511-skills-ingest-mvp/spec.md`
**Input**: Feature specification from `/specs/20260511-skills-ingest-mvp/spec.md`

## Summary

保持 `Raw -> Ingest -> Query -> Check` 的产品蓝图不变，但架构从 CLI-first 重写为 Claude Code 原生 skills-first。`/xk-ingest` 成为当前 MVP 的主产品入口：skill 负责上下文收集、Prompt Pack 注入、AI Agent 调用、结果解释与提交控制；thin helper 仅负责 schema 校验、目标路径物化、原子提交与失败回滚。`xk-query` 与 `xk-check` 继续保留在产品蓝图和后续计划中，但本轮实现范围只覆盖 ingest。

## Technical Context

**Language/Version**: Markdown spec + Claude Code skill runtime；helper 使用 Python 3.11  
**Primary Dependencies**: Claude Code skills、Prompt Pack、Pydantic v2、PyYAML、pytest  
**Storage**: 本地 Markdown 文件系统：`XK-Knowledge/RAW/`、`WIKI/`、`LOG/`、`.system/`  
**Testing**: skill walkthrough、helper 单元测试、原子提交/回滚验证、结构化输出校验  
**Target Platform**: 本地 Claude Code 风格环境（当前通过 `ttadk code` + custom model 运行）  
**Project Type**: 单项目技能工作流 + 本地 helper  
**Performance Goals**: 优先保证正确性、完整性、可回滚性和可演示性；单次 ingest 对单份 Raw 稳定完成  
**Constraints**: 产品入口必须是 Claude Code skill；helper 不得承载核心知识判断；MVP 不引入向量检索、Web UI、多用户协作、复杂版本治理  
**Scale/Scope**: 10-50 份 Raw、最多约 500 篇 wiki 页面、单用户本地知识库演示闭环

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS**: 只允许人工批准的 Raw 进入 ingest，skill 必须在进入 Agent 调用前完成输入准入检查。
- **PASS**: 每篇 wiki 页面必须至少保留一条有效 Raw 引用；若 Agent 未返回可验证引用，helper 必须拒绝提交。
- **PASS**: page、`INDEX.md`、`LINK.md`、`LOG/<date>.md` 必须单次原子提交；任一写入失败必须整体回滚。
- **PASS**: MVP 仍限定在本地知识库与 skills 工作流，不扩展 lint、矛盾网络、向量检索、多用户、Web UI、复杂版本治理。
- **PASS**: 核心知识工作由 Agent 在 prompt 约束下完成；helper 只承担机械性兜底，不得回退为规则驱动流水线。
- **PASS**: prompt 资产本身属于正式交付物，必须与 skill 行为和 helper 校验契约一起版本化。
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
skills/
└── xk-ingest/
    └── SKILL.md

XK-Knowledge/
├── CONSTITUTION.md
├── RAW/
├── WIKI/
├── LOG/
├── .system/
└── src/claude_knowledge_mvp/
    ├── prompts/
    │   └── ingest.md
    ├── domain/
    ├── adapters/
    └── helpers/
        └── ingest_commit_helper.py

tests/
├── integration/
└── unit/
```

**Structure Decision**: 产品入口收敛到 `skills/xk-ingest/SKILL.md`；Prompt Pack 与本地知识库仍放在 `XK-Knowledge/` 体系内；helper 作为 skill 的内部提交组件存在于 `XK-Knowledge/src/claude_knowledge_mvp/helpers/`，不再以 `cli.py` / `commands/*.py` 作为主骨架。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |
