# Quickstart — Claude Code 知识管理系统 MVP

## Prerequisites
- Python 3.11
- 本地仓库工作目录
- Claude Code CLI 可用
- `XK-Knowledge/CONSTITUTION.md` 与目标类型 `LAWS.md` 已准备好
- `src/claude_knowledge_mvp/prompts/ingest.md`、`query.md`、`check.md` 已写成可执行 Prompt Pack

## 1. 初始化运行环境
```bash
cd XK-Knowledge
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. 初始化知识库目录
```bash
mkdir -p RAW/article RAW/paper RAW/note
mkdir -p WIKI/concept/pages WIKI/workflow/pages WIKI/cli/pages
mkdir -p LOG .system/staging .system/txns
```

## 3. 准备最高规则、类型规则、Prompt Pack 与一份 Raw 文档
```bash
cat > CONSTITUTION.md <<'EOF'
# XK-Knowledge Constitution
EOF

cat > WIKI/concept/LAWS.md <<'EOF'
# Concept Laws
EOF

cp ../docs/llm-wiki-architecture.md RAW/article/llm-wiki-architecture.md
```

确认以下提示词文件已存在并可被运行时加载：
- `src/claude_knowledge_mvp/prompts/ingest.md`
- `src/claude_knowledge_mvp/prompts/query.md`
- `src/claude_knowledge_mvp/prompts/check.md`

## 4. 执行 ingest（AI Proxy + Prompt Pack 主导）
`ingest` 的目标流程是：工程层读取 Raw、Constitution、Type Laws、现有索引/关系上下文和 ingest prompt 后交给 Claude Code 风格 AI Proxy；AI Proxy 负责完成 Raw chunk 划分、知识提炼、完整性检查、wiki 页面草稿以及 `index/link/log` 修正草稿；工程层只做结构化校验与原子提交。

```bash
python -m src.claude_knowledge_mvp.cli ingest RAW/article/llm-wiki-architecture.md --approved
```

如果已在 Claude Code 中接入最小入口层，优先通过：
```text
/xk-ingest RAW/article/llm-wiki-architecture.md
```

**Expected result**:
- `WIKI/<type>/pages/` 下出现新的 wiki 页面
- 页面包含 AI Proxy 生成的 TL;DR、结构化知识与 Raw 引用
- 本次输出同时驱动 `WIKI/INDEX.md`、`WIKI/LINK.md` 与对应类型目录下的 `INDEX.md`、`LINK.md` 更新
- `LOG/<date>.md` 被追加
- 若模型输出无合法引用、缺少完整 mutation set 或任一写入失败，则无部分结果暴露到 `WIKI/` 与 `LOG/`

## 5. 执行 query（模型回答，索引缩圈）
```bash
python -m src.claude_knowledge_mvp.cli query "index 是怎么工作的?"
```

如果已在 Claude Code 中接入最小入口层，优先通过：
```text
/xk-query index 是怎么工作的?
```

**Expected result**:
- 系统先用 `INDEX.md` / `LINK.md` 缩小候选页面范围
- `query.md` 提示词驱动 AI Proxy 基于命中的 wiki 页面组织答案
- 输出答案、命中的 wiki 页面和至少一条回到 Raw 的引用链

## 6. 执行 check（模型核查）
```bash
python -m src.claude_knowledge_mvp.cli check --page-id llm-wiki-architecture
```

如果已在 Claude Code 中接入最小入口层，优先通过：
```text
/xk-check --page-id llm-wiki-architecture
```

**Expected result**:
- `check.md` 提示词驱动 AI Proxy 对照 wiki 页面、Raw 引用与 Constitution 输出结构化 finding
- 对无来源陈述输出 `missing_citation`
- 对过强结论输出 `overstated_claim`
- check 只报告问题，不直接改写页面

## 7. 运行测试
```bash
pytest tests/unit tests/integration tests/contract
```

重点验证：
- ingest prompt 驱动路径被调用，而不是固定启发式逻辑
- AI Proxy 输出缺字段、引用非法或完整性不足时，ingest 拒绝提交
- 任一目标文件写入失败时，原子提交整体回滚
- query/check 的结构化输出可被稳定解析

## 8. 原子提交验证
- 构造一个写入失败场景（例如 mock `LOG/<date>.md` 写入异常）
- 重新运行 ingest
- 验证 `RAW / WIKI / LOG` 的可见目录没有出现部分更新结果，且 `.system/` 中的 staging 状态已被清理或回滚

## 9. Claude Code 最小入口层约束
- Claude Code 中的首选入口是 `/xk-ingest`、`/xk-query`、`/xk-check`
- slash 入口层只负责参数转发与体验收敛，底层继续复用 `XK-Knowledge` 本地 CLI
- 本轮不以 MCP 为前置条件，优先保证 Prompt Pack 驱动的 AI 主导流程与本地知识库可移植性
