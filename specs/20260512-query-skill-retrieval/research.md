# Phase 0 Research: 20260512-query-skill-retrieval

## Decision 1: query 复用 ingest 的 Agent 调用方式
- **Decision**: query 延续 ingest 的调用模式：`runtime/query.py` 负责组装问题、Index、Link 与相关 WIKI 页面上下文，再把这些上下文交给 AI Agent；当前阶段不额外引入 `query_output_schema.json` 或更重的中间模型。
- **Rationale**: 当前 MVP 的关键不是定义更多对象，而是让 Agent 感知到相关 Knowledge，并能顺着 index/link 找到相关页面后作答。
- **Alternatives considered**:
  - 维护独立 `query_output_schema.json`：当前阶段约束过重。
  - 增加更多中间实体：会让 MVP 承载过多能力。

## Decision 2: query 采用“index 缩圈 + link 一跳扩展”的最小检索路径
- **Decision**: query 的基础检索流固定为：识别 query intent → 读取 `WIKI/INDEX.md` 命中主页面 → 读取 `WIKI/LINK.md` 扩展一跳关联页面 → 把相关上下文提供给 Agent → 由 Agent 读取相关 wiki 页面并组织答案。
- **Rationale**: 这与 query spec 保持一致，也与当前知识库的结构化设计契合；它已经足够支撑 MVP。
- **Alternatives considered**:
  - 全仓库全文搜索：会绕开 `index.md`/`link.md` 的结构价值。
  - 多跳图扩展或向量检索：超出当前产品与实现范围。

## Decision 3: MVP 只保留最小概念
- **Decision**: 设计文档只保留 `Question`、`Query Context`、`Answer` 三个最小概念。
- **Rationale**: 这些概念已经足够描述输入、runtime 提供给 Agent 的上下文、以及最终输出。
- **Alternatives considered**:
  - 保留更多实体名词：会放大设计感，但不增加 MVP 价值。

## Decision 4: `/xk-query` 仅作为共享 runtime 的显式薄别名
- **Decision**: 若实现 `/xk-query`，它必须直接委托到同一 query runtime，不允许存在第二套 prompt、检索顺序或输出边界。
- **Rationale**: query 的主产品形态是 skill-first；保留可选别名仅为演示、脚本化和减少歧义。
- **Alternatives considered**:
  - 提供独立 command 实现：与 spec 冲突，并增加维护成本。
