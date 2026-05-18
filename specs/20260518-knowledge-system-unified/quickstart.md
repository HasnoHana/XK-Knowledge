# Quickstart: 系统一致性收敛

## 目标
验证当前知识系统已经具备的三段能力，并检查下一阶段收敛工作的目标是否清晰：统一边界、统一契约、统一结果面、统一验收。

## 前置条件
- 仓库根目录存在 `CONSTITUTION.md`
- 本地知识库目录 `RAW/`、`WIKI/`、`LOG/` 可访问
- 当前 Claude Code 会话可直接执行仓库命令
- 本地脚本、runtime、helper 不会在内部启动新的 Claude 调用链

## 已有能力快速验证

### 1. Ingest
```text
/xk-ingest RAW/article/example.md
```

预期：
- 生成或更新一个 Wiki Page
- 同步更新 `WIKI/INDEX.md`、`WIKI/LINK.md`、`LOG/<date>.md`
- 失败时没有部分结果残留

### 2. Query
```text
/xk-query 这个主题在知识库里是怎么定义的？
```
或直接在对话中自然提问。

预期：
- 返回答案正文
- 返回命中的 wiki 页面引用
- 返回对应 Raw chunk 引用链
- 证据不足时明确说明 evidence limits

### 3. Check
```text
/xk-check WIKI/notes/pages/example-page.md
```

预期：
- 先完成页内 RAW↔WIKI 一致性检查
- 再完成最小 INDEX/LINK 全局检查
- 返回 markdown 报告
- 不改写仓库文件

## 下一阶段收敛验证点
1. 三条路径都明确遵守 Claude Code → 本地脚本 的单向边界
2. query 与 check 都显式暴露 evidence limits 语义
3. 命令层与 runtime 层的输入/输出措辞尽量一致
4. query/check/ingest 对 Wiki Page、Index、Link、Raw Citation Chain 的理解一致
5. 统一 walkthrough 可以覆盖 `Raw -> Ingest -> Query -> Check` 全链路

## 本阶段非目标
- 不在本轮引入批量检查
- 不在本轮引入重型 lint 体系
- 不在本轮引入复杂 link 语义裁决
- 不在本轮引入向量检索、Web UI、独立在线服务或多用户协作