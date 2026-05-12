# Phase 0 Research — Claude Code 命令驱动的知识管理系统 MVP

## Decision 1: 产品入口收敛为 Claude Code 直接命令
- **Decision**: `/xk-ingest` 作为 MVP 的主产品接口，知识摄入流程通过 Claude Code 命令入口触发，而不是依赖额外外露的 skill 文件。
- **Rationale**: 当前体系本质上依赖 AI Agent 才能成立，但对用户来说真正需要的是稳定的 `/xk-ingest` 命令体验，而不是再理解一层外露 skill 资产。保留命令入口可以减少概念重复，同时不影响 prompt 编排、上下文收集与结果解释。
- **Alternatives considered**:
  - 保留外露 skill-first：概念重复，且会让文档和实际命令入口更容易漂移。
  - 纯手工运行多步工具：可行但体验割裂，难以保证入口一致性。

## Decision 2: thin helper 只保留机械性职责
- **Decision**: helper 仅负责 schema 校验、目标路径物化、原子提交与失败回滚，不承载 chunk 划分、类型判定、关系推断或知识组织。
- **Rationale**: 这样既能保留可靠性边界，又不会让系统重新退回工程规则主导。
- **Alternatives considered**:
  - 纯命令无 helper：原子提交与失败回滚会变脆。
  - 厚 helper：会慢慢重新长回 service/CLI-first 架构。

## Decision 3: `ttadk code` 是运行入口细节，不是产品边界
- **Decision**: 计划文档和实现边界都以 Claude Code 的 `/xk-ingest` 命令体验为中心描述；`ttadk code` + custom model 只作为当前运行环境假设写入约束，不作为产品定义。
- **Rationale**: 用户关心的是命令入口是否自然、闭环是否稳定，而不是运行时包装细节。
- **Alternatives considered**:
  - 继续以 TTADK 作为架构中心：会把运行时细节错误提升为产品边界。

## Decision 4: ingest 仍输出统一 KnowledgeMutationSet
- **Decision**: Agent 一次性返回 `raw_chunks`、`wiki_page_draft`、`index_draft`、`link_draft`、`log_draft` 与完整性报告，helper 只做结构校验和提交。
- **Rationale**: 统一 mutation set 让知识判断和多文件提交保持同一轮语义上下文，也便于 runtime 在提交前做单点判断。
- **Alternatives considered**:
  - 分文件多轮生成：语义漂移与事务一致性风险更高。
  - 只生成 page draft，再由工程补索引/日志：回退成工程主导。

## Decision 5: WIKI 是知识组织产物，不是 Raw 摘要产物
- **Decision**: `wiki_page_draft` 的目标是生成一个适合知识消费的知识页，而不是把 Raw 压缩成一篇高质量摘要。Agent 必须在 Raw 证据约束下，对分散内容做重组、归纳、规范化命名与结构化组织。
- **Rationale**: 后续 `xk-query` 与 `xk-check` 依赖的是稳定的知识结构，而不是按原文顺序压缩出来的复述页。若 ingest 产物只是摘要，知识库很难形成可复用的知识节点与关系。
- **Alternatives considered**:
  - 摘要优先：更容易快速出页，但会把 WIKI 退化成 Raw 的缩写展示层。
  - 完全自由生成：容易失控并引入 Raw 之外的知识，不利于证据约束。

## Decision 6: 本轮只交付 ingest，但保留 query/check 蓝图
- **Decision**: 当前实现与验证只覆盖 `/xk-ingest`；`/xk-query` 与 `/xk-check` 保留在产品蓝图、数据模型和契约命名中，待后续阶段扩展。
- **Rationale**: 先证明命令入口驱动的 ingest 能稳定跑通，能最大化降低重写范围并快速验证方向。
- **Alternatives considered**:
  - 同轮一起落地 query/check：扩 scope，降低 MVP 验证速度。

## Resolved Technical Context
- **Command Entry**: Claude Code `/xk-ingest` 直接命令入口
- **Helper Runtime**: Python 3.11
- **Storage**: 仓库根目录本身就是知识库根：`RAW/`、`WIKI/`、`LOG/` 与 `.system/`
- **Prompt Assets**: `src/claude_knowledge_mvp/prompts/ingest.md`
- **Testing Focus**: 命令 walkthrough、结构化输出校验、原子提交失败回滚、真实 Raw 演示闭环
- **Scope**: 单用户本地知识库、10-50 份 Raw、最多约 500 篇 wiki 页面
