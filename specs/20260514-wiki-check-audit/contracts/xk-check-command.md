# Contract: `/xk-check` Command

## Request

### Invocation
```text
/xk-check <wiki-page-path>
```

### Input Rules
- `<wiki-page-path>` MUST 是单个仓库相对路径
- 路径 MUST 位于 `WIKI/*/pages/*.md`
- 当前版本一次只允许一个目标页面

## Runtime Workflow
1. 解析并验证目标路径
2. 组装 Phase 1 payload
3. 在当前 Claude 会话内执行 Phase 1 checker
4. 若 Phase 1 完成，组装 Phase 2 payload（继承 Phase 1 全量上下文，并只补充目标页相关的 INDEX/LINK 最小全局输入）
5. 在当前 Claude 会话内执行 Phase 2 checker
6. 合并阶段结果，输出 markdown 报告

## Output
- 命令面对用户返回检查结果摘要与单份 markdown 报告
- runtime 结果对象至少包含：
  - `status`
  - `report_markdown`
  - `phase1_findings`
  - `phase2_findings`
  - `evidence_limits`
- `report_markdown` 必须包含：
  - Target
  - Phase 1 Summary
  - Phase 1 Findings
  - Phase 2 Summary
  - Phase 2 Findings
  - Evidence Limits
  - Final Result

## Error Contract
| Condition | Result |
|-----------|--------|
| 路径不存在或不可读 | `input_error` |
| 目标不在 `WIKI/*/pages/*.md` | `input_error` |
| 页面没有可解析 Raw 引用 | `evidence_boundary_missing` |
| Phase 1 checker 失败 | `phase1_failed` |
| Phase 1 未完成却尝试进入 Phase 2 | `phase_gate_error` |
| `WIKI/INDEX.md` 缺失 | `phase2_input_error` |

## Non-Goals
- 不写回仓库文件
- 不生成修订草稿
- 不在脚本内部调用 Claude SDK、Claude CLI 或其他模型服务
