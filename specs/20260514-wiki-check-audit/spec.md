# Feature Specification: `/xk-check` 单页引用审计

**Feature**: `20260514-wiki-check-audit`
**Created**: 2026-05-14
**Status**: Draft
**Input**: User description: "当前阶段 Ingest 和 Query 均已初步完成 MVP，可以开始下一个阶段的 Spec。下一阶段选择 Check；主产品形态为 command-first 的 `/xk-check`；这一阶段只输出问题报告，不给修复建议、不生成修订草稿、不直接落盘；finding 类型只保留 `无来源陈述` 与 `过强结论` 两类；证据边界只看目标 wiki 页面和页面内已经声明的 Raw 引用证据，不主动扩展到整份 Raw 或关联 wiki 页；输出形态以人读报告优先；整体方案采用最小审计器，延续当前 ingest/query 的 AI Agent 主导、runtime 薄层装配上下文的架构；先以指定单个 wiki 文件作为最小检查粒度，后续文件夹或全量扫描仅作为遍历单文件检查的扩展；整个扫描必须按顺序分成两步：先检查 RAW 与落成 WIKI 的表达一致性，再检查 INDEX/LINK 等全局性内容；当前阶段 Link 先简化为只看关联文件是否正确；Link 审查依托前一步加载的全量上下文；两个步骤都应主要由提示词引导；Check 必须在当前对话内完成，绝不能让脚本在内部启动 Claude 或其他二次模型调用链路；spec 需要继续遵循 TTADK 约束。" Related context: [../20260511-skills-ingest-mvp/spec.md](../20260511-skills-ingest-mvp/spec.md), [../20260512-query-skill-retrieval/spec.md](../20260512-query-skill-retrieval/spec.md), [../../src/claude_knowledge_mvp/runtime/query.py](../../src/claude_knowledge_mvp/runtime/query.py)

## Clarifications

### Session 2026-05-14
- Q: 下一阶段 spec 重点是什么？ → A: 先做 Check。
- Q: `/xk-check` 的主产品形态是什么？ → A: command-first。
- Q: 这一阶段的结果停在哪一层？ → A: 只出问题报告。
- Q: 本轮 spec 的 finding 类型怎么定？ → A: 只保留“无来源陈述”和“过强结论”。
- Q: `/xk-check` 判断时依据什么证据？ → A: 只看该 wiki 页和页内已经声明的 Raw 引用证据。
- Q: 输出更偏哪种形态？ → A: 人读报告优先。
- Q: 采用哪种方案？ → A: 采用最小审计器，延续 runtime 组装上下文、Agent 主导判断的架构。
- Q: Check 的最小检查粒度与扫描扩展关系是什么？ → A: 先以指定单个 wiki 文件作为最小粒度，后续文件夹或全量扫描仅作为遍历单文件检查的扩展。
- Q: 整体扫描顺序如何定义？ → A: 必须先做 RAW 与落成 WIKI 的表达一致性检查，再做 INDEX/LINK 等全局性检查。
- Q: 当前阶段 Link 检查收敛到什么边界？ → A: 先只看关联文件是否正确，并依托前一步加载的全量上下文。
- Q: Check 的执行与模型调用边界是什么？ → A: 两个步骤都由提示词主要引导，且必须在当前对话内完成，脚本绝不能在内部启动 Claude 或其他二次模型调用链路。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 通过 `/xk-check` 显式审计单页 wiki (Priority: P1)

作为知识库维护者，我可以显式执行 `/xk-check` 检查一个指定 wiki 文件，并得到一份可直接阅读的 markdown 审计报告，从而先以最小粒度跑通单页引用审计，再为后续文件夹或全量扫描扩展奠定基础。

**Why this priority**: 这是 Check 阶段的主入口和最小可交付价值；没有稳定的单页审计入口，就无法闭合 ingest → query → check 的最小质量回路。

**Technical Implementation**:
- `/xk-check` MUST 是 command-first 的显式入口，而不是 skill-first 能力。
- 当前最小检查粒度固定为指定单个 wiki 文件；后续文件夹扫描或全量扫描只可被定义为对单文件检查流程的遍历扩展，而不是另一套独立检查语义。
- runtime 先围绕目标 wiki 文件装配第一阶段上下文：目标页面内容、页面内声明的 Raw 引用、`CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md` 与第一阶段 check prompt，用于检查 RAW 与落成 WIKI 的表达一致性。
- 只有当第一阶段完成后，runtime 才能基于已加载的页面与证据全量上下文进入第二阶段，继续装配 `WIKI/INDEX.md`、`WIKI/LINK.md` 与第二阶段 prompt，检查全局性内容是否符合要求。
- 两个阶段都应由提示词主要引导，由 AI Agent 在当前 Claude / Claude Code 会话中完成判断与报告撰写；runtime/helper 不主动调用 Claude SDK、Claude CLI 或形成第二条内部模型调用链。
- 输出只面向人工审阅，优先为 markdown 报告；runtime 同时保留最小结构化结果字段（如 `status`、`phase1_findings`、`phase2_findings`、`evidence_limits`、`report_markdown`）供命令层与测试复用，但不扩展为复杂外部协议。
- `/xk-check` 只返回检查结果，不直接修改 wiki 页面，不生成修订草稿，也不写入 `INDEX.md`、`LINK.md`、`LOG/` 或其他仓库文件。

**Independent Test**: 准备一个指定的 wiki 文件并显式执行 `/xk-check`；若命令成功，应先完成 RAW↔WIKI 一致性检查，再在同次流程中进入 INDEX/LINK 全局检查，最终返回一份可阅读的审计报告且仓库内容保持不变。

**Acceptance Scenarios**:
1. **Given** 维护者指定了一个存在的 wiki 文件，**When** 执行 `/xk-check`，**Then** 系统先按最小粒度运行单文件检查，并返回一份面向人工阅读的 markdown 审计报告。
2. **Given** 后续需要支持文件夹扫描或全量扫描，**When** 扩展 `/xk-check`，**Then** 该能力只能通过遍历同一单文件检查流程实现，而不是切换为另一套检查语义。
3. **Given** 页面检查完成，**When** 维护者查看仓库内容，**Then** 不应看到任何 wiki、索引、关系或日志文件被改写。

---

### User Story 2 - 基于页内已声明证据识别两类最小问题 (Priority: P2)

作为知识库维护者，我希望 `/xk-check` 先检查目标 wiki 与其声明的 Raw 证据是否表达一致，再在同一流程的第二步检查 INDEX/LINK 等全局性内容，并继续把 finding 收敛在最小范围内，以便先建立保守、顺序明确、边界清晰的质量门。

**Why this priority**: 这决定了 Check 的证据边界和问题范围；如果边界不收敛，Check 很容易从最小审计器膨胀成通用 lint 或事实核查系统。

**Technical Implementation**:
- 整体检查流程 MUST 按固定顺序分成两步：第一步检查目标 WIKI 页面与其已声明 Raw 引用之间的表达一致性；第二步在继承前一步全量上下文的前提下检查 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 等全局性内容。
- 第一步的检查上下文只包含目标 wiki 页面正文与其已经声明的 Raw 引用证据；系统 MUST NOT 主动扩展到整份 Raw 全文、关联 wiki 页面或仓库外知识。
- 第二步当前先做最小化检查：Link 只看关联文件是否正确，不扩展到复杂关系语义、跨页推理或全图一致性裁决；运行时只向该阶段提供与目标页面相关的 Link 片段，而不是整份 `WIKI/LINK.md`。
- finding 类型在本轮至少包括两类核心页面问题：`无来源陈述` 与 `过强结论`；全局检查只在此基础上补充 INDEX/LINK 是否满足当前最小要求。
- “无来源陈述”指页面中的关键陈述无法被其声明的引用证据支持；“过强结论”指页面表述强度超出了其声明证据所能支撑的范围。
- Agent 必须依据提供的页面内容、引用证据与第二步加载的全局上下文完成判断，不得把模型常识、外部背景知识或“如果去看整份 Raw 也许能支持”的推测当作通过依据。
- 当证据不足以支持确定判断时，报告应明确指出证据受限，而不是伪造确定性结论。

**Independent Test**: 准备一个 wiki 文件，其页面内容同时覆盖正确陈述、缺少支撑的陈述、表述过强的陈述，并在全局索引或关联文件中包含可核对项；执行 `/xk-check` 后应先完成页面一致性检查，再进入全局检查，并至少识别出页面问题与关联文件正确性边界。

**Acceptance Scenarios**:
1. **Given** 页面包含没有被其已声明 Raw 引用支持的陈述，**When** 执行 `/xk-check` 的第一步检查，**Then** 报告将该内容标记为“无来源陈述”。
2. **Given** 页面把弱证据写成强确定性结论，**When** 执行 `/xk-check` 的第一步检查，**Then** 报告将该内容标记为“过强结论”。
3. **Given** 某个判断若查看整份 Raw 可能成立但页内并未声明对应证据，**When** 执行 `/xk-check`，**Then** 系统不得因为潜在外部证据而放行该陈述。
4. **Given** 第一阶段已经加载了页面与证据的全量上下文，**When** 进入第二阶段 Link 检查，**Then** 系统当前只核对关联文件是否正确，而不扩展到复杂 link 语义审查。

---

### User Story 3 - 延续当前命令驱动知识工作流的最小审计架构 (Priority: P3)

作为该知识系统的维护者，我希望 `/xk-check` 的实现方式与当前 ingest/query 保持一致：runtime 负责按顺序装配上下文，AI Agent 负责核心判断，工程层保持最薄边界，并且整个检查必须在当前对话内完成，不允许脚本在内部再启动 Claude 或其他模型调用链路，从而让三条主路径形成统一的产品心智与实现约束。

**Why this priority**: 统一的架构边界可以减少后续演进成本，避免 check 提前滑向规则堆砌或独立子系统。

**Technical Implementation**:
- `/xk-check` 的工作流应遵循“第一阶段准备页面上下文 → Agent 审计 RAW↔WIKI 一致性 → 第二阶段补充全局上下文 → Agent 审计 INDEX/LINK → 返回报告”的最小闭环，与 ingest 的“准备上下文 → Agent 生成 → helper 提交”和 query 的“准备上下文 → Agent 回答”保持同构。
- runtime/helper 只负责本地 prepare、parse、最小结构校验、阶段衔接与错误返回；工程层 MUST NOT 用固定规则替代 Agent 的核心引用一致性判断，也 MUST NOT 在脚本内部启动 Claude、Claude CLI、Claude SDK 或其他二次模型调用链路。
- check prompt 是正式交付物的一部分，需至少包含页面一致性检查 prompt 与全局 INDEX/LINK 检查 prompt，并与 `constitution_text` 共同定义两个阶段的审计边界与输出约束。
- 本轮不引入完整 lint、自动修复、修订建议生成、自动矛盾网络、多页一致性巡检、复杂 link 语义裁决、向量检索、Web UI 或复杂版本治理。

**Independent Test**: 在同一仓库与会话约束下，能够通过一次 `/xk-check` 跑通“两阶段 prepare → 两阶段 Agent 审计 → 报告返回”闭环，且不需要新增独立服务、重型中间层或任何脚本内部二次模型调用。

**Acceptance Scenarios**:
1. **Given** runtime 已准备好第一阶段所需的页面内容、引用证据和规则上下文，**When** `/xk-check` 触发 Agent 审计，**Then** 系统必须先完成 RAW↔WIKI 一致性检查后才能进入第二阶段。
2. **Given** 第一阶段尚未完成，**When** 系统尝试检查 INDEX/LINK，**Then** 该操作必须被禁止，以保证全局检查依托前一步加载的全量上下文。
3. **Given** 报告生成失败或上下文装配失败，**When** 命令结束，**Then** 系统应返回可诊断错误而不是用规则模板伪造检查结论或旁路到独立系统。

### Edge Cases

- 目标 wiki 页面不存在、路径非法或无法读取时，`/xk-check` 必须失败并返回明确错误。
- 目标页面不存在任何可解析的 Raw 引用时，系统必须明确报告“缺少可审计证据边界”，而不是假装完成正常审计。
- 页面中的引用格式损坏、引用的 Raw 片段缺失或无法解析时，系统必须将其视为证据不足或输入错误，而不是静默跳过。
- 第一阶段尚未完成或未能形成可继承的全量上下文时，系统不得进入 INDEX/LINK 全局检查。
- 第二阶段执行 Link 检查时，如发现关联文件不存在、指向错误或无法解析，系统必须按当前最小规则报告该关联文件不正确。
- 页面中存在大量陈述但只有极少数引用时，系统应按“仅对已声明证据负责”的边界输出结果，不得扩展到整份 Raw 补证。
- 页面中的所有陈述都被当前证据支持且关联文件正确时，报告应明确说明本次检查未发现当前阶段定义的问题，而不是强行产出 finding。

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 系统 MUST 将 `/xk-check` 定义为 command-first 的显式维护命令。
- **FR-002**: `/xk-check` 当前 MUST 以指定单个 wiki 文件作为最小检查粒度。
- **FR-003**: 后续文件夹扫描或全量扫描 MUST 仅作为遍历单文件检查流程的扩展，而 MUST NOT 形成另一套独立检查语义。
- **FR-004**: `/xk-check` MUST 按固定顺序分成两个阶段执行：先检查 RAW 与落成 WIKI 的表达一致性，再检查 `WIKI/INDEX.md` 与 `WIKI/LINK.md` 等全局性内容。
- **FR-005**: `/xk-check` MUST 读取目标 wiki 页面内容作为第一阶段检查的核心输入。
- **FR-006**: 第一阶段 MUST 只装配并使用目标页面内已经声明的 Raw 引用证据。
- **FR-007**: 第一阶段 MUST NOT 主动扩展到整份 Raw 全文、关联 wiki 页面或仓库外知识。
- **FR-008**: 只有在第一阶段完成并形成可继承的全量上下文后，系统才 MAY 进入第二阶段的 INDEX/LINK 全局检查。
- **FR-009**: 系统 MUST 在执行前加载 `CONSTITUTION.md`、候选 `WIKI/<type>/LAWS.md` 与正式 check prompts。
- **FR-010**: AI Agent MUST 在当前 Claude / Claude Code 会话中完成两个阶段的核心审计判断与报告生成。
- **FR-011**: runtime / helper / CLI MUST NOT 用固定规则替代 Agent 的核心引用一致性判断或全局检查判断。
- **FR-012**: runtime / helper / CLI MUST NOT 在脚本内部启动 Claude SDK、Claude CLI、Claude 子进程或其他二次模型调用链路。
- **FR-013**: 本轮页面级核心 finding 类型 MUST 包含“无来源陈述”和“过强结论”。
- **FR-014**: 当页面陈述无法被其已声明的 Raw 引用支持时，系统 MUST 报告“无来源陈述”。
- **FR-015**: 当页面表述强度超过其已声明证据所能支撑的范围时，系统 MUST 报告“过强结论”。
- **FR-016**: 第二阶段当前对 Link 的检查 MUST 先收敛为“关联文件是否正确”。
- **FR-017**: 当关联文件不存在、指向错误或无法解析时，系统 MUST 报告该 Link 不正确。
- **FR-018**: 两个阶段的审计过程 MUST 主要由提示词引导。
- **FR-019**: `/xk-check` 输出 MUST 以人读 markdown 报告为主。
- **FR-020**: `/xk-check` MUST NOT 直接修改 wiki 页面、索引、关系图或日志文件。
- **FR-021**: `/xk-check` MUST NOT 生成修订草稿或自动修复结果作为本轮交付的一部分。
- **FR-022**: 当证据不足、引用缺失或引用无法解析时，系统 MUST 明确返回证据受限或输入错误语义，而不是伪造确定性判断。
- **FR-023**: 系统 MUST 在报告中区分“发现问题”和“未发现当前阶段定义的问题”两种结果。
- **FR-024**: 系统 MUST 将 check prompt 视为正式交付物的一部分，并区分两个阶段的 prompt 角色。
- **FR-025**: 本轮实现 MUST NOT 扩展到完整 lint、自动矛盾网络、批量巡检语义重构、多页一致性检查、复杂 link 语义裁决、向量检索、Web UI 或复杂版本治理。

### Key Entities *(include if feature involves data)*
- **Check Target**: 本次 `/xk-check` 指定的单个 wiki 文件，也是当前最小检查粒度。
- **Declared Raw Citation**: 页面内已经声明并可解析到 Raw 的引用证据单元。
- **Phase 1 Check Context**: runtime 提供给 Agent 的第一阶段最小审计上下文，至少包含页面内容、声明引用、constitution、laws 和页面一致性 prompt。
- **Phase 2 Global Context**: 在第一阶段完成后继承并补充的全局检查上下文，至少包含前一步加载的全量页面证据上下文以及 `WIKI/INDEX.md`、`WIKI/LINK.md`。
- **Check Finding**: 一条审计结论，可表现为页面级问题或当前最小化全局问题，并带有对应位置与证据说明。
- **Check Report**: 面向人工阅读的 markdown 结果，按阶段汇总检查范围、发现的问题和证据受限说明。

## Dependencies & Assumptions
- 当前仓库中的 ingest 流程已经能稳定产出带 Raw 引用的 wiki 页面，为 check 提供最小可审计输入。
- `/xk-check` 延续本地 Markdown 知识库架构，不依赖独立在线服务或额外数据库。
- query 已具备最小运行时与命令/skill 方向的设计基础，但本轮 spec 不要求 query 反向参与 check。
- 第二阶段的 INDEX/LINK 检查依托第一阶段已经加载的全量上下文，不允许跳过前置页面一致性检查直接进入全局检查。
- 本轮重点是建立按顺序执行的最小引用审计闭环，而不是构建通用质量平台。

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: 维护者可以通过一次显式 `/xk-check` 对指定单个 wiki 文件完成两阶段审计，并在一次命令执行内获得可直接阅读的报告。
- **SC-002**: 对包含“无来源陈述”和“过强结论”的测试页面，系统能够在第一阶段稳定识别这两类问题并在报告中分别呈现。
- **SC-003**: 对存在错误关联文件的测试输入，系统能够在第二阶段识别 Link 当前最小规则下的不正确关联。
- **SC-004**: 对证据不足、引用缺失或无法解析的输入，系统 100% 返回“证据受限”或“输入错误”语义，而不是伪造通过结果。
- **SC-005**: `/xk-check` 在成功或失败场景下都不会修改仓库中的 wiki、索引、关系或日志文件，也不会在脚本内部触发任何二次模型调用。
- **SC-006**: 该阶段的 Check 能与现有 ingest/query 一起形成命令驱动知识系统的最小三段式蓝图：生产、消费、审计。