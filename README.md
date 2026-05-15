# XK-Knowledge

一个基于本地仓库的知识库 MVP，用来把 `RAW/` 中的原始材料整理为 `WIKI/` 中可检索、可引用、可审计的知识页面。

当前项目围绕 3 个基础能力展开：

- **Ingest**：把单个 `RAW/*.md` 整理并写入知识库
- **Query**：基于本地 `WIKI/`、`INDEX.md`、`LINK.md` 回答问题
- **Check**：对单个 wiki 页面做只读审计，输出 markdown 报告

## 核心原则

项目行为受 `CONSTITUTION.md` 约束，最重要的几条是：

- 只有当前 RAW 文档支持的知识才能写入仓库
- 不允许引入外部事实或未被当前 RAW 支持的推断
- 每个写入的结论都必须能追溯到至少一个 RAW chunk
- `index` / `link` 也必须保守、基于证据
- 审计结果只读，不自动修复、不自动改写文件

## 目录结构

```text
RAW/                 原始资料输入
WIKI/                结构化知识输出
  INDEX.md           全局索引
  LINK.md            全局关联
  */pages/*.md       各类型 wiki 页面
LOG/                 ingest 生成的日志
src/claude_knowledge_mvp/
  runtime/           本地 runtime
  prompts/           prompt pack
tests/               单元测试
.claude/commands/    Claude Code 命令入口
skills/              Claude Code 技能入口
```

## 功能概览

### 1. Ingest

把一个 RAW 文档整理成知识库内的原子提交，通常会写入：

- wiki 页面
- `WIKI/INDEX.md`
- `WIKI/LINK.md`
- `LOG/`

命令入口：

```text
/xk-ingest RAW/article/transformer-core.md
```

特点：

- 一次只处理一个 RAW 文件
- 依赖当前 Claude 会话生成 mutation 内容
- 本地 runtime 只负责 prepare / validate / commit
- 不在脚本内部启动 Claude 或其他二次模型调用链路

### 2. Query

从本地知识库检索并回答问题。

当前模式：

- 先看 `WIKI/INDEX.md`
- 需要时通过 `WIKI/LINK.md` 扩展一跳
- 读取相关 wiki 页面
- 返回答案，并附带页面引用和 Raw chunk 依据

在 Claude Code 里直接自然语言提问即可，例如：

```text
what does the knowledge base say about paxos?
```

或中文：

```text
根据本地知识库，paxos 这页主要讲了什么？
```

### 3. Check

对单个 wiki 页面做显式审计。

命令入口：

```text
/xk-check WIKI/notes/pages/paxos.md
```

特点：

- 一次只检查一个 `WIKI/*/pages/*.md`
- **Phase 1**：检查 RAW ↔ WIKI 表达一致性
- **Phase 2**：在 Phase 1 完成后，再做最小 `INDEX/LINK` 全局检查
- 只返回审计报告
- 不写 wiki、不写 index/link、不写 log

返回内容是人读 markdown 报告，典型结构如下：

```md
# Check Report: paxos

## Scope
## Phase 1 Summary
## Phase 1 Findings
## Phase 2 Summary
## Phase 2 Findings
## Evidence Limits
## Result
```

## 最常用的使用方式

### 1) 新增知识

当你有一篇新的 RAW 文档，希望落到知识库：

```text
/xk-ingest RAW/article/unstable-lexicon.md
```

适用场景：

- 新增文章导入
- 已有 RAW 需要转成 wiki 页面
- 需要同步补全 index / link / log

### 2) 查询已有知识

当你想问“仓库里已有知识怎么说”：

```text
根据本地知识库，总结一下 post-query-containment-actions
```

适用场景：

- 查某个主题已有结论
- 看相关页面和一跳关联
- 基于现有 wiki 做简短问答

### 3) 审计单页质量

当你想检查某个 wiki 页面是否在证据边界内表达稳妥：

```text
/xk-check WIKI/notes/pages/post-query-containment-actions.md
```

适用场景：

- 检查页面是否有无来源陈述
- 检查页面是否有过强结论
- 检查与该页面直接相关的最小 link 关联是否正确

## 推荐工作流

### 工作流 A：从 RAW 到可用知识

```text
RAW 文档 → /xk-ingest → 生成 wiki/index/link/log → 自然语言 query 验证 → /xk-check 审计单页
```

### 工作流 B：只做现有页面复核

```text
选中一个 wiki 页面 → /xk-check → 查看 markdown 报告 → 人工决定是否修订
```

## 输入约束

### `/xk-ingest`

- 输入必须是单个仓库相对路径
- 必须位于 `RAW/` 下

### Query

- 问题应尽量围绕本地知识库已有主题
- 如果 `INDEX.md` 找不到相关页面，回答会偏保守

### `/xk-check`

- 输入必须是单个仓库相对路径
- 必须位于 `WIKI/*/pages/*.md`
- 当前版本不支持直接传文件夹或全仓扫描

## 输出边界

### Ingest 会修改仓库

可能写入：

- `WIKI/*/pages/*.md`
- `WIKI/INDEX.md`
- `WIKI/LINK.md`
- `LOG/*.md`

### Query 不修改仓库

- 只读取知识库并返回答案

### Check 不修改仓库

- 只返回报告
- 不生成修复建议
- 不生成修订草稿
- 不自动改写任何文件

## 调试入口（内部）

如果你在调试 runtime，而不是走主要用户流程，可以使用本地 CLI。

### Ingest runtime

```bash
PYTHONPATH=src python3 -m claude_knowledge_mvp.runtime.ingest_cli prepare --repo-root . --raw-path RAW/article/transformer-core.md
```

```bash
PYTHONPATH=src python3 -m claude_knowledge_mvp.runtime.ingest_cli run --repo-root . --raw-path RAW/article/transformer-core.md --mutation-json /path/to/mutation.json
```

### Check runtime

```bash
PYTHONPATH=src python3 -m claude_knowledge_mvp.runtime.check_cli prepare --repo-root . --wiki-path WIKI/notes/pages/paxos.md
```

```bash
PYTHONPATH=src python3 -m claude_knowledge_mvp.runtime.check_cli run --repo-root . --wiki-path WIKI/notes/pages/paxos.md
```

说明：这些 CLI 主要用于本地调试，**不是**主要产品形态。正常使用时优先走 Claude Code 命令与对话入口。

## 运行测试

```bash
pytest tests/unit/test_ingest_commit_helper.py tests/unit/test_query_runtime.py tests/unit/test_check_runtime.py
```

如果只想验证 check：

```bash
pytest tests/unit/test_check_runtime.py
```

## 当前能力边界

当前项目仍然是 MVP，已明确收敛在以下范围：

- ingest 以单个 RAW 为最小粒度
- check 以单个 wiki 页面为最小粒度
- query 以本地知识库为唯一事实来源
- check 的 link 审计目前只做最小正确性检查
- 不做批量自动修复
- 不做脚本内模型调用
- 不把 runtime 做成规则引擎或独立服务

## 一个完整例子

### 导入

```text
/xk-ingest RAW/article/paxos.md
```

### 查询

```text
根据本地知识库，总结一下 paxos
```

### 审计

```text
/xk-check WIKI/notes/pages/paxos.md
```

如果你只是第一次上手，建议按这个顺序使用：

1. 先准备一篇 `RAW/article/*.md`
2. 用 `/xk-ingest` 落库
3. 用自然语言 query 验证是否能检索到
4. 用 `/xk-check` 审计生成后的页面
