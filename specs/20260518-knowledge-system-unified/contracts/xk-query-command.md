# Contract: `/xk-query`

## Request

### Invocation
```text
/xk-query <question>
```

### Input Rules
- `<question>` 是当前知识查询问题文本
- 允许作为薄命令别名存在，但不能形成第二套独立 query 实现

## Runtime Workflow
1. 解析问题文本
2. 读取 `WIKI/INDEX.md` 进行候选页面缩圈
3. 读取 `WIKI/LINK.md` 做一跳扩展
4. 在当前 Claude Code 会话内完成答案组织
5. 返回统一结构化 query 结果

## Output
- `answer`: 答案正文
- `citations`: 页面引用列表，每项至少包含 `page_id`、`wiki_path`、`raw_chunk_ids`
- `evidence_limits`: 证据不足或边界受限说明

## Error Contract
| Condition | Result |
|-----------|--------|
| 问题为空 | `input_error` |
| `WIKI/INDEX.md` 缺失 | `input_error` |
| 没有命中页面 | 返回空 `citations` 与明确 `evidence_limits` |
| 生成结果结构非法 | `query_result_error` |

## Non-Goals
- 不在脚本内部调用新的 Claude 链路
- 不引入独立 query service
- 不扩展为向量检索协议