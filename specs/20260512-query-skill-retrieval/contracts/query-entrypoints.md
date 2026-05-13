# Query MVP Contract

## Skill-first entry
- **Trigger**: 用户在 Claude Code 对话中直接提出知识查询问题。
- **Behavior**:
  - 识别是否为知识库查询意图。
  - 进入统一 query runtime。
  - 由 runtime 把相关 Index、Link 与 WIKI 页面上下文提供给 Agent。
  - Agent 返回答案、引用内容与 Raw chunk。

## Optional `/xk-query` thin alias
- **Trigger**: 用户显式输入 `/xk-query <question>`。
- **Behavior**:
  - 跳过意图识别，直接进入与 skill-first 相同的 query runtime。
  - 返回与 skill-first 一致语义的答案、引用内容与 Raw chunk。
- **Constraint**:
  - 不允许独立 prompt。
  - 不允许独立检索顺序。
  - 不允许独立证据边界。

## Current-stage output
- 当前阶段不要求单独维护 `query_output_schema`。
- 当前阶段的最小输出要求是：
  - 一段答案
  - 相关引用内容
  - 可回到 Raw 的 chunk 依据
