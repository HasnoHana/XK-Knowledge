# Contract: System Consistency

## Scope
本契约约束当前知识系统在一致性收敛阶段必须保持的统一行为。

## Unified Boundary
- Claude Code 是唯一合法的 AI orchestrator
- 本地脚本、runtime、helper 只负责本地机械性工作
- 禁止在本地执行层内部启动 Claude Code、Claude CLI、Claude SDK 或新的 Claude 进程

## Unified Capability Surface
- ingest: command-first，负责把 Raw 落成知识页并原子更新索引、关系、日志
- query: skill-first，可带薄命令别名，负责返回答案、页面引用与 Raw chunk 引用链
- check: command-first，负责返回两阶段审计报告

## Unified Evidence Rules
- Wiki Page 是知识页，不是 Raw 摘要
- query 和 check 只能建立在仓库内显式证据之上
- 证据不足时必须显式输出 evidence limits，而不是伪造确定性结论

## Unified Result Surface
- ingest 必须返回结构化成功/失败结果与诊断信息
- query 必须返回：`answer`、`citations`、`evidence_limits`
- check 必须返回：`status`、`phase1_findings`、`phase2_findings`、`evidence_limits`、`report_markdown`

## Non-Goals
- 不在本契约内定义外部 HTTP API
- 不扩展为批量系统、在线服务协议或多租户协议