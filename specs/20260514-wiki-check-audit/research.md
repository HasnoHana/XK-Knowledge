# Phase 0 Research: `/xk-check` 单页引用审计

## 决策 1：沿用 command-first 命令入口，而不是单独做 skill-first 能力
- **Decision**: 新能力通过 `.claude/commands/xk-check.md` 暴露，与现有 `/xk-ingest` 对齐。
- **Rationale**: 用户明确要求 `/xk-check` 是显式维护命令；现有命令形态已经沉淀了“当前会话完成 Agent 判断，runtime 只做本地 prepare/validate”的心智模型。
- **Alternatives considered**:
  - 纯 Python CLI 子命令：对最终用户不够直接，且弱化 command-first 产品形态。
  - skill-first：与当前 ingest/query 的使用方式不对齐。

## 决策 2：runtime 采用两阶段 prepare → check → merge 的串行结构
- **Decision**: Phase 1 先装配目标页面、页内声明 Raw 引用、constitution、候选 laws 与 phase1 prompt；Phase 2 仅在 Phase 1 成功后，继承其全量上下文并补充 `WIKI/INDEX.md`、`WIKI/LINK.md` 与 phase2 prompt。
- **Rationale**: 这直接满足 spec 的顺序约束，也与现有 query/ingest runtime 的“先准备上下文，再让会话完成核心判断”的模式一致。
- **Alternatives considered**:
  - 一次性把所有上下文打包给单个 prompt：会模糊阶段边界，削弱 Link 检查依托前序上下文的要求。
  - 并行双阶段：违反“先页内、再全局”的硬约束。

## 决策 3：核心审计结果使用注入式 checker/session bridge，而不是 runtime 内部调用模型
- **Decision**: `execute_check(...)` 接收可注入的 phase checker；默认桥接只从当前 Claude 会话获得阶段结果，不在本地脚本里发起新的模型调用。
- **Rationale**: 这与 ingest 中通过当前会话提供 mutation 的边界一致，能够满足“绝不能让脚本在内部启动 Claude”的要求，同时保留单元测试可替换性。
- **Alternatives considered**:
  - 在 runtime 内直接调用 Claude SDK/CLI：违反 spec 与用户明确指令。
  - 把判断全部写成规则：会削弱“提示词主要引导、Agent 主导判断”的设计目标。

## 决策 4：Phase 1 和 Phase 2 共用轻量结果结构，再统一组装 markdown 报告
- **Decision**: 每个阶段先返回结构化结果（状态、finding、证据受限说明），最终由 runtime 组装成单份 markdown 报告。
- **Rationale**: 这样既能保持报告人读优先，也能让阶段 gate、错误传播与单元测试更稳定。
- **Alternatives considered**:
  - 只返回纯 markdown：测试难以精确断言阶段状态与 finding。
  - 引入复杂输出 schema：超出 MVP，只会增加中间模型与参数数量。

## 决策 5：Link 检查先收敛为目标文件存在性与指向正确性
- **Decision**: Phase 2 当前只验证 `WIKI/LINK.md` 中与目标页面相关的关联文件是否存在、是否能解析到正确页面，不做复杂语义裁决；runtime 只截取与目标 page id 直接相关的 link excerpt 供第二阶段使用。
- **Rationale**: 这符合 spec 中“先简化 Link，只看关联文件是否正确”的范围控制，也与现有 query 的 one-hop link 读取方式兼容，同时避免把 phase2 扩张成整图扫描器。
- **Alternatives considered**:
  - 全图语义一致性检查：超出当前阶段。
  - 完全跳过 Link：会遗漏 spec 明确要求的第二阶段最小全局检查。

## 决策 6：测试以 runtime 单元测试为主，覆盖阶段门禁与只读保证
- **Decision**: 新增 `tests/unit/test_check_runtime.py`，重点覆盖路径校验、页内引用缺失、Phase 2 gate、Link 目标错误、无仓库写入、注入式 checker 行为。
- **Rationale**: 现有 query/ingest 已经采用 tmp repo + injected fake 的测试方式，最适合当前 MVP。
- **Alternatives considered**:
  - 端到端真实会话测试：成本高且不稳定。
  - 只测 CLI：难以覆盖阶段上下文装配和只读约束。
