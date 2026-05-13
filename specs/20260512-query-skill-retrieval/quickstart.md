# Quickstart: 20260512-query-skill-retrieval

## Goal
验证 query 作为 skill-first 能力是否能在当前本地 Markdown 知识库中稳定工作，并与可选 `/xk-query` 薄别名保持一致行为。

## Prerequisites
- 仓库中已有至少一篇由 ingest 生成的 wiki 页面。
- `WIKI/INDEX.md` 与 `WIKI/LINK.md` 可被读取。
- Claude Code / `ttadk code` 运行环境可触发 skill 或命令入口。

## Golden Path
1. 准备一个已被知识库覆盖的主题。
2. 在 Claude Code 对话中直接提问。
3. 确认系统自动进入 query skill 工作流。
4. 确认 runtime 已将相关 `INDEX.md` / `LINK.md` 上下文提供给 Agent。
5. 检查 Agent 最终返回结果至少包含：
   - 一段答案
   - 相关引用内容
   - 对应的 Raw chunk
6. 若启用了 `/xk-query`，再用显式入口重复同一问题。
7. 对比两次结果，确认答案内容与引用边界保持一致。

## Edge Verification
- 提一个知识库中不存在的问题，确认结果明确返回“未找到足够知识”或等价语义。
- 提一个依赖关联页面的问题，确认系统会利用 `LINK.md` 做一跳扩展。
- 构造一个引用链不完整的页面，确认结果降级为部分依据，而不是强结论。

## Expected Artifacts
- `src/claude_knowledge_mvp/runtime/query.py`
- `src/claude_knowledge_mvp/prompts/query.md`
- `.claude/commands/xk-query.md`（如果保留显式薄别名）
