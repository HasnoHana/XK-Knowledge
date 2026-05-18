# Phase 0 Research: 系统一致性收敛

## 决策 1：保持 Claude Code 为唯一 AI 编排者
- **Decision**: 一致性阶段继续坚持单向调用边界：Claude Code 在当前对话内完成 AI 推理与生成；本地脚本、runtime、helper 只负责 prepare、parse、validate、commit、rollback、report shaping。
- **Rationale**: 当前 ingest 与 check 的 command 定义都已经把这一边界写成了显式规则；系统收敛阶段的首要目标是统一和固化它，而不是重新引入脚本内二次模型调用链。
- **Alternatives considered**:
  - 在 runtime 内直接调用 Claude SDK / Claude CLI：违反当前 spec 与已实现命令边界。
  - 让脚本内部再拉起新的 Claude 进程：会破坏职责分层、调试边界与结果一致性。

## 决策 2：补齐 query 的显式薄命令外壳，但不改变其 skill-first 定位
- **Decision**: 新增或规范化 `/xk-query` 的薄命令外壳，使三条能力在命令表面上可对齐；同时保持 query 的产品定位仍然是 skill-first。
- **Rationale**: 当前仓库已有 `/xk-ingest` 和 `/xk-check` 命令文件，但缺少对称的 `/xk-query` 命令载体；这会让系统表面不统一，也不利于后续统一 quickstart、walkthrough 和调试入口。
- **Alternatives considered**:
  - 完全不提供 `/xk-query`：保留了 query 的被动触发心智，但会让三条路径在命令面不对齐。
  - 把 query 改成 command-first：与现有 spec 对 query 的定位不一致。

## 决策 3：统一结果面，优先统一 evidence model，而不是继续扩展能力
- **Decision**: 下一阶段优先把 query 的 answer/citation 结构、check 的 report/evidence_limits 结构、ingest 的错误与桥接语义收敛成一致系统口径。
- **Rationale**: 当前三条能力都已具备最小功能，但结果面仍存在字段命名、错误措辞、报告层次和显式 evidence limit 暴露不完全一致的问题；这是系统收敛阶段最直接的用户感知差异。
- **Alternatives considered**:
  - 先做批量检查或更完整 lint：会扩大能力面，但不能先解决系统已经暴露出的不一致。
  - 先做检索增强：会继续扩展 query，而不是先统一现有系统边界。

## 决策 4：通过共享 domain model 与共享测试夹具收敛能力边界
- **Decision**: 在 `domain/models.py` 中补齐 query/check 共用的结果模型，并在 `tests/conftest.py` 中建立统一 repo fixture，减少三条路径各自定义最小世界的问题。
- **Rationale**: 当前 query 仍以裸 dict 为主，check 以 dataclass + dict 混合返回；测试也各自维护略有差异的 repo 结构。共享模型和共享 fixture 是最低成本的收敛点。
- **Alternatives considered**:
  - 只靠文档约定统一：无法形成代码层与测试层约束。
  - 一次性重构全部 runtime：成本高，且超出当前收敛阶段需要。

## 决策 5：统一 prompt contract 的证据语言与输出期望
- **Decision**: 统一 ingest/query/check prompt pack 的证据边界措辞、evidence limit 语义和输出契约表述。
- **Rationale**: 当前三个 prompt pack 的核心约束相近，但表达强度、字段命名和结果期望不完全统一；一致性阶段应该先保证 prompt 层讲的是同一种系统语言。
- **Alternatives considered**:
  - 保持各自 prompt 独立演化：短期省事，但会持续放大系统行为差异。
  - 引入一个重型统一 schema：超出当前 MVP 收敛需求。

## 决策 6：Phase 1 产物以本地契约文档为主，而不是外部 API 协议
- **Decision**: 本特性在 `contracts/` 下输出命令契约和一致性契约文档，而不是强行生成 HTTP/OpenAPI 风格接口协议。
- **Rationale**: 当前系统是 Claude Code + 本地脚本 + 本地 Markdown 知识库的命令型工作流；真正需要统一的是命令输入、结果结构和 orchestration boundary，而不是 REST API。
- **Alternatives considered**:
  - 生成 OpenAPI：与当前系统形态不匹配。
  - 不输出任何 contracts：会削弱 TTADK plan 产物的可审阅性。