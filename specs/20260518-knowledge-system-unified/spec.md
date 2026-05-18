# Feature Specification: Claude Code 知识系统当前总纲

**Feature**: `20260518-knowledge-system-unified`
**Created**: 2026-05-18
**Status**: Draft
**Input**: 当前阶段需要一份新的总 Spec，只体现三件事：已经做了什么、现在系统实现了什么功能、下一步应该实现什么。当前阶段必须坚持单向调用边界：Claude Code 调用本地脚本；脚本、runtime、helper 绝不能在内部启动 Claude Code、Claude CLI、Claude SDK 或新的 Claude 进程。

## Current System Baseline

当前系统已经形成一个由 Claude Code 驱动的本地知识工作流，围绕 `RAW/`、`WIKI/`、`LOG/` 与 `.system/` 运行。

当前已经实现的能力：
- 已实现 `/xk-ingest`：将单份 Raw 摄入为知识页，并同步更新索引、关系与日志。
- 已实现 query 最小能力：在对话中基于现有知识进行检索和回答，并返回对应引用内容与 Raw chunk。
- 已实现 `/xk-check`：对单个 wiki 页面做最小引用审计，输出问题报告。

当前系统已经明确的产品边界：
- Wiki Page 是知识页，不是 Raw 的压缩摘要。
- ingest / query / check 的核心知识判断由当前 Claude Code 对话中的 Agent 完成。
- 本地脚本、runtime、helper 只负责本地读取、上下文装配、结构校验、提交、回滚和结果整形。
- 当前阶段只能是 Claude Code 调脚本，不能是脚本反向再起 Claude。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 已经可以把 Raw 落成可消费的知识页 (Priority: P1)

作为知识库维护者，我已经可以通过当前系统把人工筛选后的 Raw 文档摄入为结构化知识页，让知识真正落到本地知识库里，并成为后续 query 和 check 的输入基础。

**Why this priority**: 这是整个系统成立的前提。没有稳定的 ingest，就不存在后续查询和审计的对象。

**Technical Implementation**:
- 当前系统已经提供 `/xk-ingest` 作为 command-first 入口。
- Claude Code 在当前会话中完成知识提炼、页面组织、引用选择，以及 `wiki/index/link/log` 草稿生成。
- 生成出的 Wiki Page 是面向知识消费的知识页，不是 Raw 的压缩复述。
- helper 负责结构化校验、目标路径物化、原子提交与失败回滚。
- `WIKI/INDEX.md`、`WIKI/LINK.md`、`LOG/<date>.md` 已采用保留历史内容的 merge-preserving 更新语义，而不是整文件覆盖。
- 若引用不合法、草稿不完整、结构校验失败或任一落盘失败，本次 ingest 必须失败且不留下部分结果。

**Independent Test**: 准备一份已人工筛选的 Raw，执行一次 ingest；若成功，则能看到新增 Wiki Page 与同步更新的索引、关系、日志；若失败，则没有部分更新残留。

**Acceptance Scenarios**:
1. **Given** 一份已人工筛选的 Raw 文档，**When** 执行 `/xk-ingest`，**Then** 系统生成知识页并同步更新 `INDEX`、`LINK` 与 `LOG`。
2. **Given** 生成结果缺少合法引用或提交过程失败，**When** ingest 结束，**Then** 仓库中不得留下部分成功状态。

---

### User Story 2 - 已经可以基于现有知识进行查询和审计 (Priority: P1)

作为知识库使用者或维护者，我已经可以基于现有知识页进行最小查询和最小审计：一方面在对话中查询知识，另一方面对单页做引用一致性检查，从而让知识库具备“可消费 + 可审计”的基本能力。

**Why this priority**: 这说明系统已经不只是“会写入知识”，而是已经具备最小闭环：知识可以被读取、被引用、被检查。

**Technical Implementation**:
- query 已具备最小能力：基于 `WIKI/INDEX.md` 缩圈候选页面，再按 `WIKI/LINK.md` 扩展一跳上下文，由当前 Claude Code 对话中的 Agent 组织答案。
- query 输出已包含最小必要结果：答案、引用内容、Raw chunk 依据。
- query 的核心定位是知识消费能力；默认在对话中触发，必要时可保留薄命令别名，但不能形成第二套独立实现。
- `/xk-check` 已具备最小能力：对单个 wiki 页面执行两阶段审计，先检查页内 RAW↔WIKI 表达一致性，再检查最小全局内容。
- check 当前只输出人读报告，finding 收敛为最小问题集合，不直接改写仓库内容。
- check 必须继续保持单页粒度、两阶段顺序和只读报告流。

**Independent Test**: 对一个已有知识页的主题直接发起 query，应返回答案与引用链；对一个包含引用问题的 wiki 页面执行 `/xk-check`，应返回对应问题报告。

**Acceptance Scenarios**:
1. **Given** 知识库中已有相关 wiki 页面，**When** 发起 query，**Then** 系统返回答案、引用内容和 Raw chunk。
2. **Given** 某个 wiki 页面存在引用缺口或表述过强问题，**When** 执行 `/xk-check`，**Then** 系统返回可阅读的问题报告且不修改仓库文件。

---

### User Story 3 - 下一阶段要把三个能力收敛成更稳定的统一系统 (Priority: P2)

作为系统负责人，我希望下一阶段不再优先新增分散功能，而是先把 ingest、query、check 三段能力收敛成一个边界稳定、行为一致、可统一验收的系统。

**Why this priority**: 当前最小能力已经具备，下一阶段真正影响系统质量的重点是收敛、联调和统一标准，而不是继续平行扩张。

**Technical Implementation**:
- 下一阶段第一优先级：补齐 `Raw -> Ingest -> Query -> Check` 的端到端联调路径，形成统一 walkthrough、黄金路径和失败路径验证方式。
- 下一阶段第二优先级：统一 ingest、query、check 对 Wiki Page、引用链、Index、Link 的消费契约，减少三条路径之间的理解偏差。
- 下一阶段第三优先级：统一入口心智与行为边界，明确 command-first 与 skill-first 的分工，但保持背后是一套一致的系统能力。
- 下一阶段第四优先级：补齐质量门，包括页面质量、引用完整性、关系表达保守性、失败结果可诊断性。
- 下一阶段第五优先级：在系统已经稳定收敛后，再决定是否引入批量检查、更完整 lint、更强 link 语义、检索增强或其他扩展能力。
- 整个下一阶段必须继续坚持当前单向调用边界：Claude Code 负责 AI 工作流，本地脚本只做本地机械性工作，绝不允许脚本内部再启动新的 Claude 调用链。

**Independent Test**: 根据这份总纲安排下一阶段任务时，可以明确区分“系统收敛任务”和“后续增强任务”，并把收敛任务排在前面。

**Acceptance Scenarios**:
1. **Given** 当前 ingest、query、check 都已具备最小能力，**When** 规划下一阶段工作，**Then** 优先项应是联调、统一契约、统一验收和质量门。
2. **Given** 有新的增强能力候选项，**When** 判断是否现在进入实现范围，**Then** 只有在当前系统收敛完成后才决定是否推进。

### Edge Cases

- 若 ingest、query、check 对同一类引用链的理解不一致，下一阶段必须优先统一契约，而不是继续各自扩展。
- 若某个能力需要通过脚本内部再次启动 Claude 才能工作，该方案必须判定为当前阶段不可接受。
- 若 query 或 check 想引入更重的外部服务、额外数据库或新调用链，必须先确认是否破坏当前系统边界。
- 若批量能力、增强 lint 或复杂关系语义会打断当前端到端闭环建设，应延后到系统收敛之后再进入实现。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 作为一个由 Claude Code 驱动的本地知识工作流运行。
- **FR-002**: 系统 MUST 已支持 ingest、query、check 三段基础能力。
- **FR-003**: 系统 MUST 提供 `/xk-ingest` 作为 ingest 的 command-first 入口。
- **FR-004**: ingest MUST 将单份 Raw 转换为可消费的 Wiki Page，并同步更新索引、关系与日志。
- **FR-005**: 系统 MUST 将 Wiki Page 定义为知识页，而不是 Raw 的压缩摘要。
- **FR-006**: query MUST 基于现有知识页、索引、关系和 Raw 引用链返回答案。
- **FR-007**: `/xk-check` MUST 提供单页最小引用审计能力，并只输出报告。
- **FR-008**: ingest、query、check 的核心知识判断 MUST 发生在当前 Claude Code 对话中。
- **FR-009**: Claude Code MUST 负责调用本地脚本并编排 AI 工作流。
- **FR-010**: 本地脚本、runtime、helper MUST 只承担本地 prepare、read、parse、validate、commit、rollback、report formatting 等职责。
- **FR-011**: 本地脚本、runtime、helper MUST NOT 在内部启动 Claude Code、Claude CLI、Claude SDK、Claude 子进程或新的 Claude 进程。
- **FR-012**: 系统下一阶段 MUST 优先完成端到端联调、统一契约、统一验收与质量门建设。
- **FR-013**: 批量检查、更完整 lint、复杂关系语义、检索增强等增强项 MUST 排在系统收敛之后。
- **FR-014**: 当前阶段系统 MUST NOT 依赖 Web UI、独立在线服务、向量数据库、多用户协作或复杂版本治理作为前置条件。

### Key Entities *(include if feature involves data)*

- **Raw Document**: 经人工筛选后进入系统的原始资料。
- **Wiki Page**: 从 Raw 派生、可供查询与审计的知识页。
- **Index Entry**: 用于 query 缩圈的索引项。
- **Link Entry**: 用于页面关联扩展的关系项。
- **Log Entry**: 记录知识变更行为的日志项。
- **Raw Citation Chain**: 从答案或页面内容回溯到 Raw chunk 的证据链。
- **Check Report**: `/xk-check` 输出的人读审计报告。

## Dependencies & Assumptions

- 当前系统继续基于本地 Markdown 知识库工作。
- 当前实现继续沿用 Claude Code + 本地脚本 + 本地文件系统 的工作方式。
- 下一阶段的重点不是新增一个平行子系统，而是把现有三段能力收敛成统一产品面。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 维护者能够只通过这份总纲，清楚说明当前系统已经实现的三段能力以及它们各自的作用。
- **SC-002**: 团队能够明确区分当前已经具备的能力与下一阶段待完成的系统收敛工作，不再混写为同一层内容。
- **SC-003**: 对任何新方案评审时，都能明确判断其是否违反“Claude Code 调脚本、脚本不反向拉 Claude”的边界。
- **SC-004**: 下一阶段排期时，端到端闭环、统一契约、统一验收和质量门会被排在增强功能之前。
- **SC-005**: 在系统收敛完成前，团队不会把批量检查、重型 lint、复杂检索增强等扩展项误判为当前最高优先级。