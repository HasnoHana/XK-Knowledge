# Quickstart: `/xk-check` 单页引用审计

## 目标
用一次显式命令检查单个 wiki 页面，先完成页内 RAW↔WIKI 一致性审计，再完成 INDEX/LINK 最小全局检查，最后返回一份人读 markdown 报告。

## 前置条件
- 目标文件位于 `WIKI/*/pages/*.md`
- 页面内已经声明可解析的 Raw 引用；若没有，结果应明确报告证据边界不足
- 当前 Claude / Claude Code 会话可直接执行仓库命令
- 仓库中存在 `CONSTITUTION.md`

## 最小使用方式

```text
/xk-check WIKI/notes/pages/post-query-containment-actions.md
```

## 预期流程
1. 校验输入路径，定位单个目标页面
2. 装配 Phase 1 上下文：页面内容、页内声明 Raw 引用、constitution、候选 laws、phase1 prompt
3. 在当前会话内完成 Phase 1 审计，识别“无来源陈述”“过强结论”或“证据受限”
4. 仅当 Phase 1 完成后，装配 Phase 2 上下文：继承前一步全量上下文，并补充 `WIKI/INDEX.md`、与目标页面相关的 `WIKI/LINK.md` 片段
5. 在当前会话内完成 Phase 2 审计，只检查最小化的 INDEX/LINK 要求，尤其是关联文件是否正确
6. 返回一份 markdown 报告；不修改仓库任何文件

## 预期输出骨架

命令面对用户返回“结果摘要 + markdown 报告”；runtime 内部会同时保留结构化字段（如 `status`、`phase1_findings`、`phase2_findings`、`evidence_limits`、`report_markdown`）供测试与桥接复用。

```md
# Check Report: post-query-containment-actions

## Scope
- Target: WIKI/notes/pages/post-query-containment-actions.md
- Phase 1: RAW ↔ WIKI consistency
- Phase 2: INDEX/LINK minimal global audit

## Phase 1 Summary
- ...

## Phase 1 Findings
- [无来源陈述] ...
- [过强结论] ...

## Phase 2 Summary
- ...

## Phase 2 Findings
- [关联文件不正确] ...

## Evidence Limits
- ...

## Result
- findings
```

## 失败示例
- 输入路径不存在：直接返回输入错误
- 页面无可解析 Raw 引用：返回“缺少可审计证据边界”，不伪造正常通过结果
- Phase 1 未完成：阻止进入 Phase 2，并返回可诊断错误或 blocked 状态

## 本阶段非目标
- 不批量扫描整个文件夹或全仓
- 不生成修订草稿或修复建议
- 不自动改写 `WIKI/INDEX.md`、`WIKI/LINK.md`、wiki 页面或 `LOG/`
- 不在脚本内部启动 Claude SDK、Claude CLI 或其他模型链路
