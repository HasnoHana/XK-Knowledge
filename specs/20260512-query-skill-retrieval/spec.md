# Feature Specification: Skill 优先的知识查询能力

**Feature**: `20260512-query-skill-retrieval`
**Created**: 2026-05-12
**Status**: Draft
**Input**: User description: "Draft a query skill specification for this repository's knowledge system. Context: current spec keeps ingest/query/check in the blueprint, with implementation scope currently ingest-only. The user believes ingest should remain command-first, while query should be skill-first because it is passively triggered inside conversation. Need a draft spec for query as a skill-oriented capability, likely with an optional thin /xk-query command alias, aligned to existing index.md/link.md/raw citation model and current xk-ingest experience."

## Clarifications

### Session 2026-05-13
- Q: 当前阶段 query 是否需要独立的 `query_output_schema` 与强结构化结果契约？ → A: 不需要。当前 query 应沿用 ingest 的 AI Agent 调用方式：由脚本/runtime 先把相关的 Index 与 Link 上下文加载给 Agent，再由 Agent 去读取相关 WIKI 页面并返回答案、引用内容与 Raw chunk；现阶段只需要让 Agent 感知到相关 Knowledge，不必额外引入专门的 query 输出 schema。
- Q: MVP 阶段是否需要保留较重的概念建模与过多能力？ → A: 不需要。MVP 只保留最小必要能力：问题输入、Index/Link 缩圈、相关 WIKI 页面上下文、Agent 回答、引用内容与 Raw chunk；不额外引入不必要的实体和能力。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 在对话中直接触发知识查询 (Priority: P1)

作为知识库使用者，我可以在 Claude Code 对话中直接提出问题，由 query skill 自动识别知识查询意图并执行查询流程，基于现有知识库返回答案、引用内容和 Raw chunk，而无需先显式输入命令名。

**Why this priority**: 这是 query 的 MVP 主路径，也是它与 ingest 的根本分工。ingest 是主动触发的生产动作，适合 command-first；query 是在对话中自然发生的消费动作，应以 skill-first 作为默认入口。

**Technical Implementation**:
- query 的主入口 MUST 是 skill-first，而不是 command-first。
- skill 负责识别当前消息是否表达出知识库查询意图；一旦命中，即进入受约束的 query 工作流。
- query skill 延续当前 ingest 经验，继续依赖本地 Markdown 知识库，不引入 Web UI、独立在线服务或向量数据库。
- query runtime 先加载与问题相关的 `index.md` 与 `link.md` 上下文，再把这些上下文交给 AI Agent。
- Agent 在收到相关上下文后，继续读取命中的 WIKI 页面内容，并基于页面中的引用信息返回答案、引用内容与 Raw chunk。
- 当前阶段只要求最小输出：答案、引用内容、Raw chunk；不额外定义独立输出 schema。
- query 输出只能建立在现有 wiki 页面及其 Raw 引用链之上，不得把模型常识伪装成知识库结论。

**Independent Test**: 在知识库中已存在至少一篇相关 wiki 页的前提下，用户直接在对话中提出覆盖该主题的问题；若 query skill 被正确触发，则系统可返回可读答案、引用内容与对应 Raw chunk，而无需用户先调用显式命令。

**Acceptance Scenarios**:
1. **Given** 知识库中已有与问题相关的 wiki 页面，**When** 用户在对话中直接提问，**Then** query skill 自动触发，并返回模型组织的答案、引用内容和 Raw chunk。
2. **Given** 用户未显式输入命令，**When** 问题表达出明确的知识查询意图，**Then** 系统仍按 query skill 流程执行，而不是要求用户重试 `/xk-query`。
3. **Given** 问题超出知识库已有覆盖范围，**When** query skill 执行检索，**Then** 系统明确说明知识库依据不足，而不是将模型常识包装成知识库答案。

---

### User Story 2 - 基于索引缩圈并按 link 扩一跳上下文 (Priority: P2)

作为知识库使用者，我希望 query skill 在回答前先基于 `index.md` 缩小候选范围，再按 `link.md` 扩展一跳相关页面，以便在保持上下文可控的前提下获得更完整的答案和引用依据。

**Why this priority**: 这是 query 相比普通问答的最小结构化价值，但仍属于 US1 之后的增强，而不是 MVP 首个交付阻塞项。

**Technical Implementation**:
- query 的基础检索顺序 MUST 为：先读 `index.md` 定位候选页面，再读这些页面对应的 `link.md` 关系，最多扩展一跳相关页面作为补充上下文。
- runtime 将命中的 index/link 上下文提供给 Agent，Agent 再按上下文去读取相关 wiki 页面并组织回答。
- Agent 返回的答案必须附带引用内容与对应 Raw chunk，不自动做矛盾裁决。
- 当前阶段不引入多跳扩展、向量检索、自动知识沉淀或复杂重排序。

**Independent Test**: 准备至少 2 篇存在 link 关系的 wiki 页面，提出一个需要主页面与关联页面共同支撑的问题；若 query skill 正常工作，则答案会体现 link 扩展带来的上下文补充，并展示对应引用内容与 Raw chunk。

**Acceptance Scenarios**:
1. **Given** `index.md` 可命中一个主页面，**When** query skill 执行检索，**Then** 系统先以该页面作为主上下文组织答案。
2. **Given** 主页面在 `link.md` 中存在直接关联页面，**When** query skill 需要补足上下文，**Then** 系统最多扩展一跳关联页面后再回答。
3. **Given** 多个候选页面存在冲突证据，**When** query skill 组织结果，**Then** 系统返回带来源的候选答案与引用，而不是伪造统一结论。

---

### User Story 3 - 通过薄命令别名显式进入同一查询流程 (Priority: P3)

作为已经熟悉本系统的维护者或演示者，我可以在需要时显式调用一个薄的 `/xk-query` 命令别名，以强制进入同一套 query skill 工作流；但这个命令只是显式入口，而不是独立的第二套产品边界。

**Why this priority**: 这是可选补充能力，主要服务演示和减少歧义，不是 query 的核心产品形态。

**Technical Implementation**:
- 若保留 `/xk-query`，它 MUST 只是 query skill 的薄别名或显式触发壳层，不得复制一套独立实现。
- command 与 skill 必须共享同一套 prompt、检索顺序和证据边界，避免同一问题在两条入口下出现行为漂移。

**Independent Test**: 在同一知识库状态下，分别通过自然语言提问和 `/xk-query` 查询同一主题；若设计正确，两次结果在答案内容、命中范围与引用边界上应保持一致。

**Acceptance Scenarios**:
1. **Given** 用户直接输入 `/xk-query` 加问题文本，**When** 系统执行查询，**Then** 应进入与 query skill 相同的工作流并返回一致语义的结果。
2. **Given** 用户通过自然语言或 `/xk-query` 查询同一主题，**When** 两次都命中同一批知识页，**Then** 两者的答案内容与引用边界保持一致。

### Edge Cases
- 用户问题表述模糊、无法判断是否在询问知识库内容时，query skill 必须优先澄清范围，而不是假定命中或直接自由发挥。
- `index.md` 无命中时，query skill 必须明确说明未找到足够知识，不得伪造答案。
- `link.md` 缺失、损坏或无法解析时，系统可仅基于主命中页面回答，但必须放弃扩一跳上下文，并在结果中体现上下文受限。
- 多个候选页面存在冲突证据时，系统只返回带来源的候选结论与引用，不自动做矛盾裁决。
- 命中页面存在 wiki 引用但引用链无法回到 Raw 时，该部分内容不得作为强结论输出。

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 系统 MUST 将 query 定义为 skill-first 的知识消费能力，而不是 command-first 的主产品入口。
- **FR-002**: 用户 MUST 能在 Claude Code 对话中通过自然语言直接触发知识查询，而无需预先记住命令名。
- **FR-003**: query runtime MUST 基于 `index.md` 缩小候选 wiki 页面范围。
- **FR-004**: query runtime MUST 在需要时读取 `link.md`，并最多扩展一跳关联页面作为补充上下文。
- **FR-005**: query runtime MUST 先把相关 Index 与 Link 上下文加载给 AI Agent，再由 Agent 读取相关 wiki 页面并组织回答。
- **FR-006**: query 输出 MUST 至少包含答案、引用内容，以及可回到 Raw 的 chunk 依据。
- **FR-007**: 当知识库中缺少足够依据时，query skill MUST 明确说明未找到足够知识，而不是伪造答案。
- **FR-008**: query skill MUST NOT 把模型常识或仓库外信息伪装成知识库结论。
- **FR-009**: 系统 MAY 提供 `/xk-query` 作为显式入口，但该入口 MUST 只是 query skill 的薄别名，不得形成独立实现。
- **FR-010**: query 当前阶段 MUST 继续复用本地 Markdown 知识库架构，不引入向量检索、自动知识沉淀、复杂重排序、Web UI、独立在线服务或独立 `query_output_schema`。

### Key Entities *(include if feature involves data)*
- **Question**: 用户在对话中输入的知识查询问题。
- **Query Context**: runtime 提供给 Agent 的最小上下文集合，至少包含问题文本、命中的 index/link 信息和相关 wiki 页面内容。
- **Answer**: Agent 基于 Query Context 生成的回答，包含答案正文、引用内容和 Raw chunk。

## Dependencies & Assumptions
- 当前仓库中的 ingest 流程已能稳定产出带引用的 wiki 页面，以及可供 query 使用的 `index.md` 与 `link.md`。
- query 延续现有本地 Markdown 知识库架构，不依赖 Web UI、独立在线服务或额外数据库。
- 当前阶段 query 的重点是把相关 Knowledge 暴露给 Agent，而不是先设计更重的中间模型或输出模型。

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: 对至少 80% 的已覆盖主题问题，用户可直接通过自然语言提问触发 query skill，而无需先输入显式命令。
- **SC-002**: 在命中知识库的查询中，返回结果能够稳定包含答案、引用内容和 Raw chunk 依据。
- **SC-003**: 当知识库无命中或证据不足时，系统 100% 明确返回“未找到足够知识”或“部分依据”语义，而不是伪造确定性答案。
- **SC-004**: 通过自然语言触发和通过 `/xk-query` 显式触发同一查询时，结果在答案内容、命中范围与引用边界上保持一致。
