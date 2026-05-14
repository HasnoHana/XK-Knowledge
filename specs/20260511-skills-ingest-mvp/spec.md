# Feature Specification: Claude Code 命令驱动的知识管理系统 MVP

**Feature**: `20260511-skills-ingest-mvp`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "Rewrite the current feature spec suite for this project to a command-first TTADK architecture. Preserve the overall MVP vision with ingest/query/check in the product blueprint, but make the current implementation scope ingest only. Runtime is `ttadk code` with a custom model. `/xk-ingest` is the primary product interface; use a thin helper only for schema validation, path materialization, and atomic commit/rollback." Related context: [../../docs/llm-wiki-architecture.md](../../docs/llm-wiki-architecture.md), existing feature artifacts under `../20260509-claude-knowledge-mvp/`. Update request on 2026-05-12: 明确 WIKI 不是 RAW 的精简摘要，而是 AI Agent ingest 后重组、归纳、组织过的知识页；先修改 spec，不改实现代码。 Additional update on 2026-05-12: 删除外露 xk-ingest skill，保留 `/xk-ingest` 作为唯一公开入口。

## Clarifications

### Session 2026-05-11
- Q: 系统的主产品形态是什么？ → A: 不继续作为独立 CLI 产品，而应围绕 Claude Code 的直接命令入口组织；这套体系本质上依赖 AI Agent 才成立。
- Q: 新的运行环境假设是什么？ → A: 用户通过 `ttadk code` 启动 Claude Code 风格工作流，并使用 custom model，而不是官方默认模型。
- Q: 是否保留工程层？ → A: 保留薄 helper，仅负责 schema 校验、目标路径物化、原子写入与失败回滚。
- Q: 当前 MVP 的交付范围是什么？ → A: 总蓝图保留 ingest/query/check 三段式能力，但当前只实现和验证 ingest。
- Q: command/runtime 内承载多少逻辑？ → A: `/xk-ingest` 负责触发 prompt 编排、调用和流程控制，并允许通过 helper 完成少量结构校验与原子提交。

### Session 2026-05-12
- Q: WIKI 页面与 RAW 的关系应该如何定义？ → A: WIKI 不是 RAW 的精简摘要，而是 AI Agent 在 ingest 过程中基于 Raw 证据做重组、归纳、组织后的知识页。
- Q: 这次 spec 更新是否同时修改实现代码？ → A: 否，本次先只修正 spec 对产品目标的定义，不直接扩展实现代码。
- Q: 外露 xk-ingest skill 是否还需要作为公开能力边界？ → A: 不需要；删除外露 skill，保留 `/xk-ingest` 作为唯一公开入口。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 通过 `/xk-ingest` 将 Raw 落库为知识页 (Priority: P1)

作为知识库维护者，我可以在人工筛选 Raw 文档后，通过 `/xk-ingest` 发起一次摄入，由 AI Agent 在规则和提示词约束下完成知识重组、页面生成和索引修正，并由 helper 以原子方式提交，从而验证命令入口驱动的工作流可以稳定落库知识。

**Why this priority**: 这是当前 MVP 的入口能力；如果 `/xk-ingest` 不能稳定工作，后续 `/xk-query` 和 `/xk-check` 都没有基础。

**Technical Implementation**:
- 系统运行于本地 Markdown 知识库；仓库根目录本身就是知识库根，围绕 `RAW/`、`WIKI/`、`LOG/` 与 `.system/` 组织内容，不依赖 Web UI。
- 主入口是 Claude Code 中的 `/xk-ingest` 命令，而不是独立 CLI 产品，也不再依赖额外外露 skill 文件。
- `/xk-ingest` 命令通过 `.claude/commands/xk-ingest.md` 定义输入协议与结果输出约束，并复用现有 direct ingest runtime。
- runtime 负责读取单份 Raw、仓库根目录下的 `CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md`、现有 `INDEX.md` / `LINK.md` 知识上下文与正式 ingest prompt；本项目依托当前 Claude / Claude Code 会话完成模型生成，runtime 自身不主动调用 Claude。
- AI Agent 必须在当前 Claude 会话中、受预设提示词引导完成 Raw chunk 划分、知识重组、类型判定、标题命名、章节组织、关系建议，以及 `wiki/index/link/log` 草稿生成；这些草稿随后交由本地 runtime/helper 做结构校验与原子提交。
- Wiki Page 的目标不是生成 Raw 的压缩摘要，而是生成一个以知识消费为中心的知识页：Agent 应在 Raw 证据约束下对内容做重组、归纳、规范化命名与结构化组织，使页面更适合后续 query/check 消费，而不是沿着 Raw 原文顺序做缩写式复述。
- Agent 应优先按知识结构组织页面，而不是按 Raw 原始排版逐段压缩；允许把 Raw 中分散出现的定义、机制、约束、边界条件、工程意义和示例重新归并到更稳定的知识章节中，但不得引入 Raw 之外的事实。
- helper 只负责结构化输出校验、目标路径解析、原子写入与失败回滚；helper MUST NOT 用固定规则替代核心知识判断。
- 页面必须包含摘要、结构化知识、溯源标注和基础元信息；每条知识都必须能回链到 Raw 的具体段落或 chunk；无引用内容不得落库。
- 本次提交必须原子地完成 wiki 页面写入，以及 `index.md`、`link.md`、`log.md` 的同步更新；任一环节失败时不得留下部分成功状态。
- 对 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 的更新必须保留既有有效条目，并将本次 ingest 产出的增量条目与已有内容做合并，而不是把文件整体重写成只包含本次变更的快照。
- 对同一日期下的 `LOG/<date>.md` 更新必须以追加/合并方式保留当日既有记录，不得因为一次新 ingest 覆盖当天先前日志内容。
- helper 的提交语义必须把 `index_draft`、`link_draft`、`log_draft` 视为本次提交的增量草稿，而不是目标文件的完整快照；重复条目可去重，但既有无关条目不得被删除。
- `/xk-ingest` 的用户体验应围绕知识摄入，而不是暴露 `PYTHONPATH`、绝对路径拼接或底层 helper 调用细节。

**Independent Test**: 给定一份已人工筛选的 Raw 文档，执行一次 `/xk-ingest`；若成功，则新增 wiki 页面与 `index.md`、`link.md`、`log.md` 必须同时可见；若 AI 输出不合法或任一落盘失败，则不得留下部分产物。

**Acceptance Scenarios**:
1. **Given** 一份已通过人工筛选的 Raw 文档，**When** 维护者执行 `/xk-ingest`，**Then** 命令入口会加载规则与 prompt，调用 AI Agent 生成带引用的 wiki 页面，并同时更新 `index.md`、`link.md`、`log.md`。
2. **Given** Raw 文档中同一主题的信息分散在多个段落或章节中，**When** AI Agent 生成 wiki 页面，**Then** 输出应按知识结构进行重组与归纳，而不是把 Raw 按原顺序压缩成一篇缩写摘要。
3. **Given** AI Agent 返回的结果缺少合法引用、缺少关键草稿，或明显未覆盖 Raw 的核心内容，**When** helper 进行校验，**Then** 本次 ingest 必须失败，且不产生落盘结果。
4. **Given** 仓库中已有历史 `index.md`、`link.md` 条目与同日 `log.md` 记录，**When** 新的 `/xk-ingest` 成功提交，**Then** helper 必须保留历史有效内容，并只把本次新增条目合并进目标文件，而不是覆盖整个文件。
5. **Given** 任一目标文件写入失败，**When** runtime 进入提交阶段，**Then** helper 必须整体回滚，不得暴露部分更新状态。
6. **Given** 用户通过 `/xk-ingest` 发起 ingest，**When** 执行完成，**Then** 用户看到的是知识摄入结果摘要，而不是底层 helper/路径拼装细节。

---

### User Story 2 - 通过 `/xk-query` 基于索引和关联返回答案 (Priority: P2)

作为知识库使用者，我可以通过 `/xk-query` 提问，系统基于 `index.md` 和 `link.md` 检索相关 wiki 页面，由 AI Agent 组织答案并附上回到 Raw 的引用链，从而验证知识库具备可消费价值。

**Why this priority**: 这是知识库落库后的消费面，也是命令入口工作流的第二段价值证明；但它依赖 ingest 先稳定。

**Technical Implementation**:
- `/xk-query` 是规划中的命令入口，当前不在本轮 MVP 交付范围内。
- query 先基于 `index.md` 定位候选页面，再读取 `link.md` 中的关联关系，扩展一跳上下文。
- query 的最终答案组织、证据取舍和引用链表达由 AI Agent 在预设提示词引导下完成，而不是由固定模板拼接。
- 输出中必须同时包含答案、命中的 wiki 页面标识，以及回到 Raw 的引用链。
- MVP 暂不实现向量检索、自动知识沉淀或复杂重排序。

**Independent Test**: 在至少存在一篇 wiki 页的情况下，对已覆盖主题发起 query，可返回可读答案并展示引用链。

**Acceptance Scenarios**:
1. **Given** 知识库中已有与问题相关的 wiki 页面，**When** 用户执行 `/xk-query`，**Then** 系统返回模型组织的答案并附带 wiki 页面和 Raw 引用链。
2. **Given** 候选页面存在关联页面，**When** `/xk-query` 读取 `link.md`，**Then** 系统可将关联页面纳入上下文后再回答。
3. **Given** 问题无命中页面，**When** 用户执行 `/xk-query`，**Then** 系统明确说明未找到足够知识，而不是伪造答案。

---

### User Story 3 - 通过 `/xk-check` 核查单页引用一致性 (Priority: P3)

作为知识库维护者，我可以对单页 wiki 执行 `/xk-check`，识别无来源陈述和过强结论，从而在不实现完整 Lint 体系的前提下先控制知识污染风险。

**Why this priority**: 这是最小质量保障能力，但依赖 ingest 先落地，因此优先级低于 ingest。

**Technical Implementation**:
- `/xk-check` 是规划中的命令入口，当前不在本轮 MVP 交付范围内。
- 检查重点是引用一致性：页面中的关键陈述是否能被 Raw 支持，以及表述强度是否超过 Raw 证据。
- finding 的生成由 AI Agent 在预设提示词引导下完成，helper 只负责装配页面、Raw 证据和规则上下文并校验输出结构。
- 输出为报告或问题列表，至少区分“无来源陈述”和“过强结论”两类问题。
- MVP 不实现完整 lint、自动矛盾网络、自动修复、多页一致性巡检。

**Independent Test**: 准备一篇包含正确引用、缺失引用和过强措辞的 wiki 页面，执行 `/xk-check` 后可看到对应问题被识别。

**Acceptance Scenarios**:
1. **Given** wiki 页面中存在没有 Raw 依据的陈述，**When** 维护者执行 `/xk-check`，**Then** 系统标记该陈述为无来源。
2. **Given** wiki 页面把弱证据写成强结论，**When** 维护者执行 `/xk-check`，**Then** 系统标记该陈述为过强结论。

### Edge Cases
- Raw 文档为空、提取失败或不含可引用内容时，`/xk-ingest` 必须失败并说明原因，不得生成空洞知识页。
- `index.md`、`link.md`、`log.md` 任一文件不存在时，helper 必须能初始化最小文件结构，并将初始化与本次 ingest 一并纳入同一次原子提交。
- 仓库中已存在历史 `index.md`、`link.md`、同日 `log.md` 内容时，helper 必须在原子提交中完成合并与去重，保留既有有效条目，不得因为一次新 ingest 删除无关历史项。
- AI Agent 返回的 chunk 划分若只覆盖 Raw 局部内容、遗漏关键章节或无法形成完整引用集，系统必须拒绝提交。
- AI Agent 若只是按 Raw 原始章节顺序生成一篇压缩式摘要、没有完成知识重组与归纳，导致页面虽然有引用但不适合作为知识页消费，系统必须将其视为不符合产品目标的低质量输出。
- AI Agent 若未返回 `wiki/index/link/log` 所需的完整草稿集合，系统必须拒绝提交，而不是用工程模板补齐核心知识内容。
- `/xk-query` 命中多个页面但证据冲突时，后续阶段只返回带来源的候选答案与引用，不自动做矛盾裁决。
- `/xk-check` 发现问题时，只输出报告，不直接改写 wiki 页面。
- custom model 的输出格式若发生漂移，helper 必须将其视为结构化校验失败，而不是宽松接收后继续提交。

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 系统 MUST 运行在本地 Markdown 知识库之上，并以 Claude Code 直接命令作为主产品入口。
- **FR-002**: 系统 MUST 依托 AI Agent 完成核心知识工作流，不将自身定义为可脱离 Agent 独立使用的传统 CLI 产品。
- **FR-003**: 系统 MUST 只处理经过人工筛选的 Raw 文档，不负责替代人工做资料可信度初筛。
- **FR-004**: 系统 MUST 提供 `/xk-ingest` 入口，将单份 Raw 文档转换为一篇 wiki 页面并同步更新索引与日志。
- **FR-005**: `/xk-ingest` MUST 在执行前加载 `CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md`、现有索引/关系上下文和正式 ingest prompt。
- **FR-006**: `/xk-ingest` MUST 依托当前 Claude / Claude Code 会话完成模型生成步骤，而不是把项目 runtime/helper 设计成主动调用 Claude 的内部调用方。
- **FR-007**: 项目内部的 runtime / helper / CLI MUST NOT 主动调用 Claude SDK、Claude CLI 或其他内部二次调用链路；它们只负责本地 prepare、parse、validate、commit 与失败回滚。
- **FR-008**: ingest 生成的 wiki 页面 MUST 包含摘要、结构化知识、溯源标注和基础元信息。
- **FR-009**: Wiki Page MUST 被定义为从 Raw 派生的知识页，而不是 Raw 的精简摘要；页面组织目标应服务于知识消费、后续 query/check 使用与稳定引用，而不是按原文顺序做缩写式复述。
- **FR-010**: 系统 MUST 为每条落库知识保存回到 Raw 的引用链；没有引用支撑的内容 MUST NOT 落库。
- **FR-011**: ingest MUST 原子地同时写入 wiki 页面并更新 `index.md`、`link.md`、`log.md`；任一写入失败时 MUST NOT 留下部分成功状态。
- **FR-012**: 对 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 的 ingest 更新 MUST 采用保留历史有效条目的 merge-preserving 语义；系统 MUST 合并本次增量条目并允许去重，但 MUST NOT 因一次 ingest 删除无关既有条目。
- **FR-013**: 对同一日期下的 `LOG/<date>.md` 更新 MUST 保留当日既有记录，并以追加或等价的合并方式纳入本次日志；系统 MUST NOT 用单次 ingest 的日志草稿覆盖当天已有日志内容。
- **FR-014**: 系统 MUST 保留一个薄 helper 层，负责 schema 校验、目标路径物化、原子提交与失败回滚。
- **FR-015**: helper MUST NOT 用固定规则替代 AI Agent 的核心知识判断、chunk 划分、类型判定、章节组织或关系推断。
- **FR-016**: AI Agent MUST 在当前 Claude 会话中、受预设提示词引导完成 Raw chunk 划分、知识重组、类型判定、标题命名、章节组织、关系建议与 `wiki/index/link/log` 草稿生成。
- **FR-017**: AI Agent 在生成 Wiki Page 时 MUST 以知识结构而不是原始排版为主导，对 Raw 支持的内容进行重组、归纳、抽象与归并，并允许把分散证据整理成更稳定的知识章节，但 MUST NOT 引入 Raw 之外的事实。
- **FR-018**: ingest MUST 对 AI 输出做完整性约束；若模型输出仅覆盖局部内容、缺少必要草稿、无法形成合法引用集，或虽然有引用但本质上只是 Raw 的压缩摘要而未形成知识页，系统 MUST 拒绝提交。
- **FR-019**: 系统 MUST 提供预设提示词资产，分别服务于 ingest、query、check 三条主路径，并将其视为正式交付物的一部分。
- **FR-020**: 系统 MUST 在产品蓝图中保留 `/xk-query` 与 `/xk-check` 作为后续命令入口。
- **FR-021**: `/xk-query` MUST 在后续阶段基于 `index.md` 与 `link.md` 缩圈检索并返回带 Raw 引用链的答案。
- **FR-022**: `/xk-check` MUST 在后续阶段对单页 wiki 做引用一致性检查，并识别“无来源陈述”和“过强结论”。
- **FR-023**: `/xk-ingest` SHOULD 尽量避免向用户暴露 `PYTHONPATH`、绝对路径拼接或运行时内部实现细节。
- **FR-024**: MVP MUST NOT 实现完整 lint、自动矛盾网络、向量检索、多用户协作、Web UI 或复杂版本治理。
- **FR-025**: 本轮实现范围 MUST 仅覆盖 `/xk-ingest`，而 `/xk-query`、`/xk-check` 仅保留在产品蓝图与后续规划中。

### Key Entities *(include if feature involves data)*
- **Raw Document**: 人工筛选后进入系统的原始资料，包含来源标识、原始内容和可供 AI Agent 划分的输入。
- **Raw Chunk**: 由 AI Agent 在 ingest prompt 引导下划定的稳定引用单元，用于建立回到 Raw 的证据链。
- **Wiki Page**: 从 Raw 派生的知识页面，不是 Raw 的精简摘要，而是 AI Agent 在证据约束下完成重组、归纳、规范化命名与结构化组织后的知识产物，包含摘要、结构化知识、引用、元信息和页面标识。
- **Index Entry**: `index.md` 中的主题索引项，用于将主题或关键词映射到 wiki 页面；在后续 ingest 中应按增量合并和去重保留。
- **Link Entry**: `link.md` 中的页面关系记录，描述页面之间的关联类型与方向；在后续 ingest 中应按增量合并和去重保留。
- **Log Entry**: `log.md` 中的操作记录，描述某次 ingest 或修订产生的变更；同日记录必须支持连续追加或等价合并，保留当天历史条目。
- **Knowledge Mutation Set**: AI Agent 一次性返回的统一知识变更集合，包含页面草稿与索引/关系/日志草稿。
- **Skill Runtime Context**: 当前实现中的上下文结构体名称，表示 runtime 执行时组装的上下文包，包含 Raw、Constitution、Laws、Prompt Pack 与现有知识上下文。
- **Helper Commit Result**: helper 对一次 mutation set 校验与提交后的结果摘要，供 `/xk-ingest` 返回给用户。
- **Query Answer Draft**: 后续 `/xk-query` 生成的结构化答案草稿。
- **Check Finding**: 后续 `/xk-check` 产出的核查结果，记录问题类型、问题位置和对应引用缺口。

## Dependencies & Assumptions
- 运行时依赖当前 Claude Code 风格环境可用；现阶段用户通过 `ttadk code` 启动，并使用 custom model，但这属于运行入口细节而不是产品边界。
- 本地知识库目录 `RAW/`、`WIKI/`、`LOG/` 与 `.system/` 已存在，或可由 helper 在首次提交时初始化最小结构。
- 仓库根目录下的 `CONSTITUTION.md` 与至少一组候选 `WIKI/<type>/LAWS.md` 可被 runtime 在执行时读取。
- ingest、query、check 的 prompt 资产会被单独版本化维护，但本轮只交付 ingest 的正式执行链路。
- query 与 check 保留在产品蓝图中，后续规划应复用相同的边界：命令入口负责触发工作流，helper 只负责稳定提交与结构校验。

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: 对一份已人工筛选的 Raw 文档，维护者可以通过一次 `/xk-ingest` 成功执行后原子地得到 1 篇 wiki 页面和同步更新的 `index.md`、`link.md`、`log.md`；若执行失败，则看不到部分更新结果。
- **SC-002**: 在连续多次成功 ingest 的场景下，`WIKI/INDEX.md` 与 `WIKI/LINK.md` 必须同时保留历史有效条目和本次新增条目；同日 `LOG/<date>.md` 必须同时保留当天已有记录和本次新增记录。
- **SC-003**: 在成功的 ingest 案例中，AI Agent 产物必须同时给出合法 chunk 引用、wiki 页面草稿以及 `index/link/log` 修正草稿；若任一关键部分缺失，提交必须失败。
- **SC-004**: 在成功的 ingest 案例中，生成出的 Wiki Page 必须能体现基于 Raw 证据的知识重组与归纳，而不是沿原文顺序压缩形成的一篇缩写摘要。
- **SC-005**: `/xk-ingest` 的用户体验以直接命令为中心，用户不需要显式操作底层 helper 路径、环境拼接或内部运行细节。
- **SC-006**: 在当前 Claude Code 风格环境与 custom model 运行面下，系统能够稳定完成至少一个真实 Raw 文档的 ingest 演示闭环。
- **SC-007**: 产品规格完整保留 `/xk-query` 与 `/xk-check` 的后续目标与约束，但本轮 implementation scope 不扩展到这两个能力。
- **SC-008**: 在结构化输出不合法、引用非法、完整性不足、仅形成压缩摘要而未形成知识页，或任一落盘失败时，helper 能稳定拒绝提交并返回可诊断的失败结果。
