# Quickstart — Claude Code 命令驱动的知识管理系统 MVP

## Prerequisites
- Claude Code 风格运行环境可用
- 当前会话可使用 custom model
- 仓库根目录下的 `CONSTITUTION.md` 与候选 `WIKI/<type>/LAWS.md` 已存在
- `src/claude_knowledge_mvp/prompts/ingest.md` 已写成正式 Prompt Pack
- 本地知识库目录 `RAW/`、`WIKI/`、`LOG/`、`.system/` 可访问

## 当前实现状态
- **[已实现]** `/xk-ingest` 作为当前唯一 MVP 产品入口
- **[已实现]** Raw 读取、Constitution/Laws/Prompt 上下文装配、统一 `KnowledgeMutationSet` 校验、page/index/link/log 原子提交与失败回滚
- **[已实现]** Wiki Page 的产品定义已切换为“知识页”，目标是知识组织而不是 Raw 摘要压缩
- **[规划中]** `/xk-query` 与 `/xk-check` 仍保留在产品蓝图中，但当前未实现

## 1. 准备一份可摄入的 Raw
- 将原始资料放入仓库根目录下 `RAW/` 的合适子目录
- 人工确认该资料可信且值得进入知识库
- 确认该 Raw 可被 `/xk-ingest` 的 runtime 读取，并且来源路径稳定

## 2. 通过 `/xk-ingest` 发起摄入
在 Claude Code 会话中运行：

```text
/xk-ingest RAW/article/llm-wiki-architecture.md
```

这是当前 MVP 的主用户路径。

预期执行流：
1. `.claude/commands/xk-ingest.md` 负责定义用户输入协议与结果输出约束
2. 当前 Claude / Claude Code 会话读取 Raw、Constitution、候选 Laws、现有 `INDEX.md` / `LINK.md` 知识上下文与 ingest prompt，并基于这些输入生成 `KnowledgeMutationSet`
3. 会话层可通过临时 mutation JSON 文件或等价桥接方式，把该 `KnowledgeMutationSet` 交给 local runtime 的 `run` / `debug-run` 路径；这是内部桥接细节，不是用户手动工作流的一部分
4. local runtime 只负责接收该 `KnowledgeMutationSet`，执行 parse / validate / commit 等本地步骤；runtime/helper 不主动调用 Claude
5. Agent 在 Raw 证据约束下把内容重组为适合知识消费的 Wiki Page，而不是按原文顺序压缩成摘要页
6. thin helper 校验返回结构、引用合法性与完整性
7. thin helper 原子写入 page / index / link / log
8. 用户看到的是本次 ingest 的结果摘要或失败原因，而不是 helper 内部细节

## 3. 成功结果验证
执行成功后，应能看到：
- `WIKI/<type>/pages/` 下新增 wiki 页面
- 页面不是 TL;DR 摘要页，而是经过重组与归纳的知识页，包含摘要、结构化知识与 Raw 引用
- 页面结构应体现知识组织，而不是沿 Raw 原始章节顺序压缩复述
- `WIKI/INDEX.md` 与 `WIKI/LINK.md` 被同步更新
- `LOG/<date>.md` 被追加
- `/xk-ingest` 返回本次 ingest 的结果摘要，而不是内部运行细节

## 4. 失败结果验证
以下情况应整体失败且无部分落盘：
- Agent 输出缺少合法引用
- Agent 输出缺少 `index/link/log` 任一关键草稿
- `completeness_report` 不足以证明覆盖了 Raw 核心内容
- Agent 虽然生成了结构化页面，但本质上仍只是按 Raw 顺序压缩出的摘要页，没有形成知识重组产物
- 任一目标文件写入失败

## 5. 当前 MVP 边界
- 当前只交付 `/xk-ingest`
- `/xk-query` 与 `/xk-check` 仍保留在产品蓝图中，但本轮不实现
- helper 只负责 schema 校验、路径物化、原子提交与回滚，不承担知识判断

## 6. 已验证演示记录

### 演示输入
- RAW: `RAW/article/PPO-core.md`
- 会话层先生成一份 `KnowledgeMutationSet`，再通过 direct `run` 路径桥接给 local runtime

### 本次演示使用的本地 runtime 命令
```text
PYTHONPATH="/Users/bytedance/Desktop/XK-Knowledge/src" python3 -m claude_knowledge_mvp.runtime.ingest_cli run --repo-root "/Users/bytedance/Desktop/XK-Knowledge" --raw-path "RAW/article/PPO-core.md" --mutation-json "<temporary-session-bridge-file>"
```

### 演示结果摘要
- status: `committed`
- written_paths:
  - `WIKI/architecture/pages/PPO-core.md`
  - `WIKI/INDEX.md`
  - `WIKI/LINK.md`
  - `LOG/2026-05-14.md`

### 本次演示暴露出的后续改进点
- direct ingest 的会话桥接链路已打通：当前 Claude 会话可生成 mutation，并由 local runtime 完成本地提交。
- 缺失会话层 mutation 时，runtime 现已返回结构化 `session_bridge_error`，不再直接抛 traceback。
- 当前 `PPO-core` 产出的 wiki 页面虽然成功提交，但组织质量仍偏弱：`Summary` 基本等于标题，正文仍接近整文搬运，说明后续仍需补“知识页质量 / graph 保守性”闸门。

## 7. 调试说明
`prepare` / `commit` CLI 仍可保留为内部调试接口，但不是用户主流程。
用户不应被要求手动操作 `PYTHONPATH`、中间 `mutation.json` 或内部路径拼接。

## 8. 最小验证建议
- 用一份真实 Raw 跑通一次成功 ingest
- 人为构造一份缺引用或缺草稿的模型返回，验证 helper 拒绝提交
- 人为构造一次落盘失败，验证回滚后 `WIKI/` 与 `LOG/` 不出现部分结果
