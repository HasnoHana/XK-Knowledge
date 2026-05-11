# Quickstart — Claude Code Skills 驱动的知识管理系统 MVP

## Prerequisites
- Claude Code 风格运行环境可用
- 当前会话可使用 custom model
- `XK-Knowledge/CONSTITUTION.md` 与候选 `WIKI/<type>/LAWS.md` 已存在
- `XK-Knowledge/src/claude_knowledge_mvp/prompts/ingest.md` 已写成正式 Prompt Pack
- 本地知识库目录 `RAW/`、`WIKI/`、`LOG/`、`.system/` 可访问

## 1. 准备一份可摄入的 Raw
- 将原始资料放入 `XK-Knowledge/RAW/` 下的合适子目录
- 人工确认该资料可信且值得进入知识库
- 确认该 Raw 可被 skill 读取，并且来源路径稳定

## 2. 通过 `/xk-ingest` 发起摄入
在 Claude Code 会话中运行：

```text
/xk-ingest XK-Knowledge/RAW/article/llm-wiki-architecture.md
```

预期执行流：
1. skill 读取 Raw、Constitution、候选 Laws、现有 `INDEX.md` / `LINK.md` 摘要与 ingest prompt
2. skill 调用 AI Agent 生成 `KnowledgeMutationSet`
3. thin helper 校验返回结构、引用合法性与完整性
4. thin helper 原子写入 page / index / link / log
5. skill 向用户返回结果摘要或失败原因

## 3. 成功结果验证
执行成功后，应能看到：
- `WIKI/<type>/pages/` 下新增 wiki 页面
- 页面包含 TL;DR、结构化知识与 Raw 引用
- `WIKI/INDEX.md` 与 `WIKI/LINK.md` 被同步更新
- `LOG/<date>.md` 被追加
- skill 返回本次 ingest 的结果摘要，而不是 helper 内部细节

## 4. 失败结果验证
以下情况应整体失败且无部分落盘：
- Agent 输出缺少合法引用
- Agent 输出缺少 `index/link/log` 任一关键草稿
- `completeness_report` 不足以证明覆盖了 Raw 核心内容
- 任一目标文件写入失败

## 5. 当前 MVP 边界
- 当前只交付 `/xk-ingest`
- `/xk-query` 与 `/xk-check` 仍保留在产品蓝图中，但本轮不实现
- helper 只负责 schema 校验、路径物化、原子提交与回滚，不承担知识判断

## 6. 最小验证建议
- 用一份真实 Raw 跑通一次成功 ingest
- 人为构造一份缺引用或缺草稿的模型返回，验证 helper 拒绝提交
- 人为构造一次落盘失败，验证回滚后 `WIKI/` 与 `LOG/` 不出现部分结果
