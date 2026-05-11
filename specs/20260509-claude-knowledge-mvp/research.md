# Phase 0 Research — Claude Code 知识管理系统 MVP

## Decision 1: Ingest 改为 AI Proxy + Prompt Pack 主导
- **Decision**: `Raw -> Wiki` 的 chunk 划分、知识提炼、类型判定、标题命名、章节组织、关系推断、完整性自检与 `wiki/index/link/log` 草稿生成，统一由 Claude Code 风格 AI Proxy 在预设提示词引导下完成。
- **Rationale**: 用户已明确纠偏：问题不是流程，而是之前把 ingest 设计成了 chunk-first / heuristic-first 的工程流水线；真正需要的是由 LLM 主导知识建模，工程层只做必要约束。
- **Alternatives considered**:
  - 固定规则切分后拼接页面：实现简单，但本质上仍是工程主导，无法满足本轮目标。
  - 纯人工整理页面：质量可控，但失去模型驱动知识沉淀的核心价值。

## Decision 2: Constitution + Type Laws + Prompt Pack 是模型第一输入
- **Decision**: `CONSTITUTION.md`、`WIKI/<type>/LAWS.md` 与预设 `Prompt Pack` 共同构成 ingest/query/check 的核心执行约束，优先级高于工程层任何启发式规则。
- **Rationale**: 这样系统才是“模型按制度与提示词生成”，而不是“工程规则先做主，再让模型补文字”。
- **Alternatives considered**:
  - Constitution 只在提交前校验：模型阶段缺少真正的行为约束。
  - 只给模型喂 Raw，不给规则与 prompt：输出会漂移，难以形成稳定资产。

## Decision 3: Chunk 仍保留，但由模型完成划分并服务于证据链
- **Decision**: `RawChunk` 仍然是稳定引用单元，但 chunk 边界与证据组织由 AI Proxy 在 ingest prompt 引导下完成；工程层只负责给 chunk 分配稳定标识并校验引用合法性。
- **Rationale**: 用户明确要求连 Raw chunk 划分都要由 LLM 完成；因此 chunk 不能再是工程先验切分逻辑，而应成为模型组织证据的结果。
- **Alternatives considered**:
  - 完全取消 chunk：削弱稳定回链能力，与 Constitution 不兼容。
  - 继续由工程规则切 chunk：会保留当前错误方向。

## Decision 4: `wiki/index/link/log` 作为统一 mutation set 由模型产出
- **Decision**: ingest 的模型输出不是单独 page draft，而是一组统一的 knowledge mutation：包含 wiki 页面草稿、index 修正草稿、link 修正草稿、log 记录草稿与完整性报告。
- **Rationale**: 用户要求整个流程都应由 LLM 完成，原子提交的多个落库目标应来自同一轮模型判断，而不是由工程层在下游补齐。
- **Alternatives considered**:
  - 模型只产出 page，索引/关系/日志由工程生成：会重新回到工程主导。
  - 每个文件分别独立跑模型：事务一致性更难保证，且上下文容易漂移。

## Decision 5: Query 与 Check 也采用“Prompt 驱动 + 模型主导 + 工程兜底”
- **Decision**: `query` 仍先通过 `INDEX.md` / `LINK.md` 为模型缩圈，但答案组织由模型完成；`check` 由模型对照 wiki 页面、Raw 证据与 Constitution 生成 finding，工程层只装配上下文并校验输出结构。
- **Rationale**: 用户强调“全程 AI 主导”，因此 query/check 也不能退化为规则模板或字符串拼接。
- **Alternatives considered**:
  - 规则检索 + 模板回答：可控但僵硬，偏离设计目标。
  - 让模型直接扫全库：上下文成本过高，也削弱 index/link 的价值。

## Decision 6: 工程层只承担五类职责
- **Decision**: 工程层仅承担输入批准校验、Prompt 上下文装配、结构化输出校验、稳定 ID 分配、原子写入与回滚五类职责。
- **Rationale**: 这既落实“纯工程化内容仅仅是兜底使用”，也保留了系统可靠性边界。
- **Alternatives considered**:
  - 完全放弃工程兜底：一旦模型输出缺字段或写入失败，系统无法稳定运行。
  - 工程层深度接管分类/抽取：会重新把系统拉回规则流水线。

## Decision 7: Prompt 资产是 MVP 的正式交付物
- **Decision**: `prompts/ingest.md`、`prompts/query.md`、`prompts/check.md` 不是占位物，而是功能行为的一部分；其内容必须明确输入上下文、Constitution/Laws 加载方式、输出 schema、完整性要求和失败条件。
- **Rationale**: 用户明确提出“你需要把提示词写好”，因此 prompt 设计不能被留到实现细节中隐式处理。
- **Alternatives considered**:
  - 运行时拼 prompt：不稳定，难以版本化。
  - 只写高层说明不写具体 prompt：无法约束模型真实行为。

## Resolved Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: Typer、Pydantic v2、PyYAML、pytest；Claude Code/AI Proxy 边界由 `ClaudeCodeRunner` 承担
- **Storage**: `XK-Knowledge/RAW/`、`WIKI/`、`LOG/` 与 `.system/` 本地文件系统
- **Testing**: pytest + CLI 集成测试 + AI Proxy 输出结构校验 + 原子回滚验证 + prompt 驱动路径验证
- **Platform**: 本地 macOS / Linux，单用户 Claude Code 会话
- **Performance**: 不追求严格 SLA；优先保证正确性、完整性、可回滚性和演示闭环
- **Scope**: 10-50 份 Raw，最多约 500 篇 wiki 页面
