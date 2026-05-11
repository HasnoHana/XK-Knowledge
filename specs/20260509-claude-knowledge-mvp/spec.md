# Feature Specification: Claude Code 知识管理系统 MVP

**Feature**: `20260509-claude-knowledge-mvp`
**Created**: 2026-05-09
**Status**: Draft
**Input**: User description: "基于 [docs/llm-wiki-architecture.md](../../docs/llm-wiki-architecture.md)，为 Claude Code 搭建一套知识管理系统的 MVP。系统围绕本地 Markdown 知识库运行，核心目标是验证最小闭环：人工筛选 Raw 文档后执行 ingest，生成带引用的 wiki 页面，并自动维护 index.md、link.md、log.md；用户可通过 query 提问，系统基于 index 和 link 检索相关页面并返回答案，同时附上回到 raw 的引用链；系统提供 check 命令，对单页 wiki 做引用一致性检查，识别无来源陈述和过强结论。MVP 暂不实现完整 lint、自动矛盾网络、向量检索、多用户协作、Web UI 和复杂版本治理，先做本地 CLI demo。"

## Clarifications

### Session 2026-05-09
- Q: 当前最小 MVP 如何以最小代价集成到 Claude Code？ → A: 优先用 Claude Code slash skill/command 作为入口层，命名采用 `/xk-ingest`、`/xk-query`、`/xk-check`；底层仍复用 `XK-Knowledge` 本地 CLI；目标是最小改造、保持可移植性，本轮不引入 MCP 作为前提。
- Q: Ingest 的执行主导权和实现边界是什么？ → A: 从 ingest 开始，必须经由 Claude Code 这类 AI Proxy 在预设提示词引导下完成 Raw chunk 划分、Raw 提炼、完整性检查、wiki 落库草稿，以及 index/link/log 修正草稿；全程由 LLM 主导，工程化只负责必要约束、结构化校验和原子提交兜底。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest 原始资料生成知识页 (Priority: P1)

作为知识库维护者，我可以在人工筛选 Raw 文档后执行 ingest，将单份 Raw 原子地落库为带引用的 wiki 页面，并在同一次提交中同步更新 `index.md`、`link.md`、`log.md`，从而验证知识可以稳定落库。

**Why this priority**: 这是 MVP 的入口能力；没有稳定的 ingest，就没有可查询、可检查的知识资产。

**Technical Implementation**:
- 系统运行于本地 Markdown 知识库，不依赖 Web UI。
- Raw 文档由人先判断“是否可信、是否值得摄入”，系统只处理通过人工筛选的输入。
- ingest 必须经由 Claude Code 风格的 AI Proxy 执行，而不是由工程规则直接主导页面生成。
- ingest 读取单份 Raw、`CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md`、现有索引/关系上下文与预设提示词，由大模型完成 Raw chunk 划分、知识提炼、类型判定、标题命名、章节组织、关系建议和引用选择。
- 页面必须包含摘要、结构化知识、溯源标注和基础元信息。
- 面向 Claude Code 的首选用户入口采用 slash skill/command `/xk-ingest`；该入口只负责调用底层本地 CLI，不额外承载业务逻辑。
- 每条知识都必须能回链到 Raw 的具体段落或 chunk；无引用内容不得落库。
- ingest MUST 以原子方式完成 wiki 页面写入，以及 `index.md`（主题索引）、`link.md`（页面关系）、`log.md`（追加操作记录）的同步更新；任一写入失败时不得留下部分成功状态。
- 页面间关系在 MVP 中至少支持 `related`、`depends_on`、`superseded_by` 三类；反向关系可由系统补齐。
- ingest 必须保证对 Raw 的处理具有完整性：模型不能只抽取前几段或局部片段；若模型未覆盖足够证据、未返回合法引用集或产物结构不完整，提交必须失败。
- 本故事的需求来源与设计背景参考 `../../docs/llm-wiki-architecture.md`。

**Independent Test**: 给定一份已人工筛选的 Raw 文档，执行一次 ingest；若命令成功，则新增 wiki 页面与 `index.md`、`link.md`、`log.md` 必须同时可见；若任一写入失败，或模型输出缺少合法引用/明显不完整，则不得留下部分产物。

**Acceptance Scenarios**:
1. **Given** 一份已通过人工筛选的 Raw 文档，**When** 维护者执行 ingest 且本次写入成功，**Then** AI Proxy 在预设提示词引导下生成带引用的 wiki 页面，并同时更新 `index.md`、`link.md`、`log.md`。
2. **Given** ingest 在写入任一目标文件时失败，**When** 维护者检查知识库目录，**Then** 不得观察到仅部分文件更新的中间状态。
3. **Given** Raw 中某条内容无法提供可验证引用，**When** ingest 处理该内容，**Then** 该内容不得写入 wiki 页面。
4. **Given** 模型只返回局部抽取结果、缺少完整引用集或未生成必要的 `index/link/log` 修正草稿，**When** ingest 尝试提交，**Then** 本次 ingest 必须失败并回滚。

---

### User Story 2 - Query 基于索引和关联返回答案 (Priority: P2)

作为知识库使用者，我可以通过 query 提问，系统基于 `index.md` 和 `link.md` 检索相关 wiki 页面，组织答案并附上回到 Raw 的引用链，从而验证知识库具备可消费价值。

**Why this priority**: 这是 MVP 的价值展示面，证明知识沉淀后可以被 Claude Code 风格的查询流程使用。

**Technical Implementation**:
- query 先基于 `index.md` 定位候选页面，再读取 `link.md` 中与候选页面相关的关系，扩展一跳上下文。
- query 的最终答案组织、证据取舍和引用链表达由大模型在预设提示词引导下完成，而不是规则模板直接拼接。
- 系统从命中的 wiki 页面读取结构化知识并组织答案。
- 面向 Claude Code 的首选用户入口采用 slash skill/command `/xk-query`；底层仍复用本地 CLI 的 query 实现。
- 输出中必须同时包含答案、命中的 wiki 页面标识，以及回到 Raw 的引用链。
- MVP 不实现向量检索、自动知识沉淀或复杂重排序；优先使用基于 index 与 link 的确定性检索路径为模型缩小上下文。

**Independent Test**: 在至少存在一篇 wiki 页的情况下，对已覆盖主题发起 query，可返回可读答案并展示引用链。

**Acceptance Scenarios**:
1. **Given** 知识库中已有与问题相关的 wiki 页面，**When** 用户执行 query，**Then** 系统返回模型组织的答案并附带对应 wiki 页面和 Raw 引用链。
2. **Given** 候选页面存在关联页面，**When** query 读取 `link.md`，**Then** 系统可将关联页面纳入上下文后再回答。
3. **Given** 问题无命中页面，**When** 用户执行 query，**Then** 系统明确说明未找到足够知识，而不是伪造答案。

---

### User Story 3 - Check 单页引用一致性核查 (Priority: P3)

作为知识库维护者，我可以对单页 wiki 执行 check，识别无来源陈述和过强结论，从而在不实现完整 Lint 体系的前提下先控制知识污染风险。

**Why this priority**: 该能力为 MVP 提供最小质量保障，但依赖前两项能力先落地，因此优先级低于 ingest 和 query。

**Technical Implementation**:
- check 面向单页 wiki 执行，不要求批量巡检。
- 检查重点是引用一致性：页面中的关键陈述是否能被 Raw 支持，以及表述强度是否超过 Raw 证据。
- check 的 finding 生成由大模型在预设提示词引导下完成，工程层只负责装配页面、Raw 证据和规则上下文并校验输出结构。
- 输出为报告或问题列表，至少区分“无来源陈述”和“过强结论”两类问题。
- 面向 Claude Code 的首选用户入口采用 slash skill/command `/xk-check`；底层仍复用本地 CLI 的 check 实现。
- MVP 不实现完整 lint、自动矛盾网络、自动修复、多页一致性巡检。

**Independent Test**: 准备一篇包含正确引用、缺失引用和过强措辞的 wiki 页面，执行 check 后可看到对应问题被识别。

**Acceptance Scenarios**:
1. **Given** wiki 页面中存在没有 Raw 依据的陈述，**When** 维护者执行 check，**Then** 系统标记该陈述为无来源。
2. **Given** wiki 页面把弱证据写成强结论，**When** 维护者执行 check，**Then** 系统标记该陈述为过强结论。

### Edge Cases

- Raw 文档为空、提取失败或不含可引用内容时，ingest 必须失败并说明原因，不得生成空洞知识页。
- `index.md`、`link.md`、`log.md` 任一文件不存在时，系统必须能先初始化最小文件结构，并将初始化与本次 ingest 写入纳入同一次原子提交。
- ingest 在写入 wiki 页面、`index.md`、`link.md`、`log.md` 的任一环节失败时，系统必须整体失败或回滚，不得留下部分成功状态。
- AI Proxy 返回的 chunk 划分若只覆盖 Raw 局部内容、遗漏关键章节或无法形成完整引用集，系统必须拒绝提交。
- AI Proxy 若未返回 `wiki/index/link/log` 所需的完整草稿集合，系统必须拒绝提交而不是用工程模板补齐核心知识内容。
- query 命中多个页面但证据冲突时，MVP 只返回带来源的候选答案与引用，不自动做矛盾裁决。
- check 发现问题时，只输出报告，不直接改写 wiki 页面。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 运行在本地 Markdown 知识库之上，并以 CLI demo 形式提供能力。
- **FR-002**: 系统 MUST 只处理经过人工筛选的 Raw 文档，不负责替代人工做资料可信度初筛。
- **FR-003**: 系统 MUST 提供 ingest 命令，将单份 Raw 文档转换为一篇 wiki 页面。
- **FR-004**: ingest 生成的 wiki 页面 MUST 包含摘要、结构化知识、溯源标注和基础元信息。
- **FR-005**: 系统 MUST 为每条落库知识保存回到 Raw 的引用链；没有引用支撑的内容 MUST NOT 落库。
- **FR-006**: ingest MUST 以原子方式同时写入 wiki 页面并更新 `index.md`、`link.md`、`log.md`；任一写入失败时 MUST NOT 留下部分成功状态。
- **FR-007**: 系统 MUST 提供 query 命令，基于 `index.md` 和 `link.md` 检索相关 wiki 页面并返回答案。
- **FR-008**: query 输出 MUST 包含答案、命中的 wiki 页面标识，以及回到 Raw 的引用链。
- **FR-009**: 系统 MUST 提供 check 命令，对单页 wiki 做引用一致性检查。
- **FR-010**: check MUST 识别并报告“无来源陈述”和“过强结论”。
- **FR-011**: MVP MUST NOT 实现完整 lint、自动矛盾网络、向量检索、多用户协作、Web UI 或复杂版本治理。
- **FR-012**: 系统 SHOULD 支持最小页面关系集合：`related`、`depends_on`、`superseded_by`。
- **FR-013**: 系统 SHOULD 优先通过 Claude Code slash skill/command 暴露 `/xk-ingest`、`/xk-query`、`/xk-check` 作为首选用户入口。
- **FR-014**: 上述 Claude Code 入口 MUST 复用 `XK-Knowledge` 本地 CLI 作为底层执行层，以最小改造保持可移植性；本轮实现 MUST NOT 以 MCP 作为前置条件。
- **FR-015**: ingest MUST 经由 Claude Code 风格的 AI Proxy 和预设提示词执行，Raw chunk 划分、知识提炼、类型判定、章节组织、关系建议与 `wiki/index/link/log` 草稿生成 MUST 由 LLM 主导完成。
- **FR-016**: 工程层 MUST 只承担必要约束：输入批准校验、模型上下文装配、结构化输出校验、原子提交与失败回滚；工程层 MUST NOT 用固定规则替代 LLM 的核心知识判断。
- **FR-017**: ingest MUST 对 Raw 处理结果做完整性约束；若模型输出仅覆盖局部内容、缺少必要草稿或无法形成合法引用集，系统 MUST 拒绝提交。
- **FR-018**: 系统 MUST 提供预设提示词资产，分别引导 ingest、query、check 的模型执行路径，并保证提示词显式加载 Constitution 与相关 Laws。

### Key Entities *(include if feature involves data)*

- **Raw Document**: 人工筛选后进入系统的原始资料，包含来源标识、原始内容和可供 AI Proxy 划分的输入。
- **Raw Chunk**: 由 AI Proxy 在提示词引导下划定的稳定引用单元，用于建立回到 Raw 的证据链。
- **Wiki Page**: 从 Raw 派生的知识页面，包含摘要、结构化知识、引用、元信息和页面标识。
- **Index Entry**: `index.md` 中的主题索引项，用于将主题或关键词映射到 wiki 页面。
- **Link Entry**: `link.md` 中的页面关系记录，描述页面之间的关联类型与方向。
- **Log Entry**: `log.md` 中的操作记录，描述某次 ingest 或修订产生的变更。
- **Check Finding**: check 产出的核查结果，记录问题类型、问题位置和对应引用缺口。
- **Prompt Pack**: 预设提示词资产，定义 ingest/query/check 在 Claude Code 风格 AI Proxy 下的执行约束与输出格式。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 对一份已人工筛选的 Raw 文档，维护者可以在一次 ingest 成功执行后原子地得到 1 篇 wiki 页面和 3 个同步更新的索引/日志文件；若执行失败，则看不到部分更新结果。
- **SC-002**: 对已覆盖主题发起 query 时，用户在一次命令执行内即可获得答案，并看到至少一条回到 Raw 的引用链。
- **SC-003**: 对包含问题陈述的单页 wiki 执行 check 时，系统能够识别出无来源陈述和过强结论这两类问题。
- **SC-004**: 在 MVP 演示范围内，核心闭环 Raw → Ingest → Query → Check 可由单人通过本地 CLI 完整跑通，无需 Web UI 或多人协作。
- **SC-005**: 在 Claude Code 中，用户可优先通过 `/xk-ingest`、`/xk-query`、`/xk-check` 访问同一套底层能力，而无需显式暴露 `PYTHONPATH`、绝对路径拼接或 MCP 前置配置。
- **SC-006**: ingest 成功案例中，模型产物必须同时给出合法 chunk 引用、wiki 页面草稿以及 `index/link/log` 修正草稿；若任一关键部分缺失，提交必须失败。 
