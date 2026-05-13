# Implementation Plan: Skill 优先的知识查询能力

**Feature**: `20260512-query-skill-retrieval` | **Date**: 2026-05-12 | **Spec**: [/Users/bytedance/Desktop/XK-Knowledge/specs/20260512-query-skill-retrieval/spec.md](/Users/bytedance/Desktop/XK-Knowledge/specs/20260512-query-skill-retrieval/spec.md)
**Input**: Feature specification from `/specs/20260512-query-skill-retrieval/spec.md`

## Summary

为当前本地 Markdown 知识库补齐 query 能力，主入口采用 skill-first 形态：用户在 Claude Code 对话中直接提问即可触发知识查询；系统基于 `WIKI/INDEX.md` 缩圈命中候选页面，再按 `WIKI/LINK.md` 扩一跳补充上下文，并由 runtime 将相关上下文提供给 AI Agent。Agent 再读取相关 WIKI 页面并在证据约束下组织答案、引用内容和 Raw chunk。实现保持 MVP 取向：只做最小查询路径，不引入额外的输出 schema、复杂中间模型或多余能力；若保留 `/xk-query`，它仅作为共享同一 runtime 的薄别名。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: 标准库、现有 `claude_knowledge_mvp` runtime 分层、Claude Code command/skill 入口  
**Storage**: 本地 Markdown 文件（`WIKI/INDEX.md`、`WIKI/LINK.md`、`WIKI/<type>/pages/*.md`、Raw 引用链）  
**Testing**: pytest（如后续单独补测）  
**Target Platform**: macOS / Claude Code 本地仓库运行环境  
**Project Type**: 单仓库本地知识库工具  
**Performance Goals**: 单次 query 在命中少量候选页与一跳扩展范围内完成，保持交互式响应  
**Constraints**: query 必须 skill-first、证据绑定、只读；不得引入向量检索、独立在线服务、Web UI、独立 `query_output_schema`、复杂中间模型或与 `/xk-ingest` 分叉的第二套证据模型  
**Scale/Scope**: 当前范围仅覆盖单仓库知识查询 MVP：自然语言触发、Index/Link 缩圈、一跳扩展、答案/引用内容/Raw chunk 输出、可选 `/xk-query` 薄别名

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- 当前 `docs/CONSTITUTION.md` 与 `.ttadk/memory/constitution.md` 均不存在，无法执行项目级硬性门禁校验。
- 本计划改为遵循已存在的仓库事实约束：
  - 延续现有 `src/claude_knowledge_mvp/runtime/ingest.py` 的 runtime 分层风格。
  - 遵守 query spec 中的固定产品边界：skill-first、只读、证据绑定、复用 `index.md`/`link.md`/Raw 引用链。
  - 做减法：不新增与 spec 冲突的独立服务、向量检索、独立输出 schema、复杂中间模型或第二套入口语义。
- Gate 结果：**PASS（按现有 spec 与代码边界执行）**。

## Project Structure

### Documentation (this feature)

```
specs/20260512-query-skill-retrieval/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```
src/
└── claude_knowledge_mvp/
    ├── prompts/
    │   ├── ingest.md
    │   └── query.md                      # new
    └── runtime/
        ├── ingest.py
        └── query.py                      # new

.claude/
└── commands/
    ├── xk-ingest.md
    └── xk-query.md                       # optional thin alias
```

**Structure Decision**: 在现有单项目 Python 结构内扩展 query；沿用 ingest 的 runtime/prompts 分层，只新增最小必要的 query runtime 与 query prompt 资产。MVP 不要求新增更重的 helper、schema 或复杂模型文件。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |

## Phase 0: Research Summary

- 已确认 query 应复用 ingest 的 Agent 调用方式：runtime 负责组装上下文，Agent 负责读取相关 WIKI 页面并作答。
- 已确认检索路径固定为 `INDEX.md` 缩圈 + `LINK.md` 一跳扩展。
- 已确认当前阶段不需要独立的 `query_output_schema`。
- 已确认 MVP 只保留最小必要概念：问题、查询上下文、答案。
- 已确认 `/xk-query` 若保留，只能作为共享 runtime 的薄别名。

## Phase 1: Design & Contracts

### Data Model
- 产出 `data-model.md`，仅保留 `Question`、`Query Context`、`Answer` 三个最小概念。
- 当前阶段重点描述 runtime 如何把相关知识交给 Agent，以及 Agent 最终要返回什么。

### Contracts
- 保留一个轻量 contract，描述 skill-first 主入口、可选 `/xk-query` 薄别名，以及当前阶段最小输出要求。
- 不再拆更多 contract，也不维护结果 schema。

### Quickstart
- 产出 `quickstart.md`，覆盖自然语言触发、无命中、link 扩展与 `/xk-query` 对照验证。

## Implementation Strategy

1. 新增 `src/claude_knowledge_mvp/runtime/query.py`，负责：
   - 接收问题
   - 读取并解析 `WIKI/INDEX.md`
   - 装配主命中页面与 `WIKI/LINK.md` 一跳扩展页面
   - 把相关 index/link/wiki 页面内容组装为 Agent 可消费的查询上下文
   - 调用 Agent，并接收答案、引用内容与 Raw chunk
2. 新增 `src/claude_knowledge_mvp/prompts/query.md`，将查询约束、证据边界和回答要求固化为正式 prompt 资产。
3. 若保留显式入口，则新增 `.claude/commands/xk-query.md`，但仅做 query runtime 的薄封装。
4. 当前实现不额外引入 query helper、输出 schema 校验或复杂中间模型。

## Testing Strategy

- 当前计划不强制拆分独立测试任务。
- 最小验证方式以 `quickstart.md` 中的人工验证路径为主。
- 如后续需要补测试，优先围绕 index 命中、一跳扩展、无命中与 `/xk-query` 一致性补充。

## Post-Design Constitution Check

- 设计仍保持单仓库本地工具边界，未引入额外服务或存储层。
- query 继续复用现有知识库结构与 ingest 的 Agent 调用模式，没有产生第二套证据模型。
- `/xk-query` 被限制为可选薄别名，未违反 skill-first 主入口决策。
- 设计已做减法，未引入额外 `query_output_schema`、复杂中间模型或多余能力。
- 复查结果：**PASS**。
