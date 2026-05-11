# Data Model — Claude Code Skills 驱动的知识管理系统 MVP

## 1. RawDocument
- **Purpose**: 表示一份经过人工筛选、允许被 `xk-ingest` 摄入的原始资料。
- **Fields**:
  - `raw_id`
  - `source_path`
  - `source_type`
  - `title`
  - `ingest_allowed`
  - `content`
- **Validation Rules**:
  - `source_path` 必须存在且可读
  - `ingest_allowed=true` 才允许进入 ingest

## 2. RawChunk
- **Purpose**: 由 AI Agent 在 ingest prompt 引导下划定的稳定证据单元。
- **Fields**:
  - `chunk_id`
  - `raw_id`
  - `locator`
  - `text`
  - `order`
- **Validation Rules**:
  - `chunk_id` 在同一 Raw 内唯一
  - `text` 不能为空

## 3. SkillRuntimeContext
- **Purpose**: `xk-ingest` skill 在调用 Agent 前组装的完整上下文包。
- **Fields**:
  - `raw_document`
  - `constitution_text`
  - `candidate_laws`
  - `global_index_excerpt`
  - `global_link_excerpt`
  - `prompt_pack`
- **Validation Rules**:
  - 缺少 Raw、Constitution 或 Prompt Pack 时不得进入 Agent 调用

## 4. PromptPack
- **Purpose**: 定义 ingest 执行路径、输出 schema 与失败条件的正式提示词资产。
- **Fields**:
  - `name`
  - `path`
  - `version`
  - `output_contract`
- **Validation Rules**:
  - 必须显式要求加载 Constitution
  - ingest 必须声明 KnowledgeMutationSet 输出格式

## 5. KnowledgeMutationSet
- **Purpose**: AI Agent 一次性生成的统一知识变更集合。
- **Fields**:
  - `raw_chunks`
  - `wiki_page_draft`
  - `index_draft`
  - `link_draft`
  - `log_draft`
  - `completeness_report`
- **Validation Rules**:
  - 任一关键组成缺失时 helper 必须拒绝提交
  - `completeness_report` 不能为空

## 6. WikiPage
- **Purpose**: 从 mutation set 物化出来的正式知识页面。
- **Fields**:
  - `page_id`
  - `slug`
  - `title`
  - `wiki_type`
  - `summary`
  - `body_sections`
  - `source_chunk_ids`
  - `status`
- **Validation Rules**:
  - `source_chunk_ids` 至少包含一条有效 Raw 引用
  - 页面内容必须源自 Agent 草稿而非 helper 模板补齐

## 7. IndexEntry
- **Purpose**: `INDEX.md` 中的主题索引项。
- **Fields**:
  - `scope`
  - `type_name`
  - `topic`
  - `aliases`
  - `page_id`
  - `rank`
- **Validation Rules**:
  - `page_id` 必须引用存在的 WikiPage

## 8. LinkEntry
- **Purpose**: `LINK.md` 中的页面关系记录。
- **Fields**:
  - `scope`
  - `type_name`
  - `source_page_id`
  - `target_page_id`
  - `relation_type`
  - `note`
- **Validation Rules**:
  - 关系类型至少支持 `related`、`depends_on`、`superseded_by`

## 9. LogEntry
- **Purpose**: `LOG/<date>.md` 中记录一次 ingest 产生的变更。
- **Fields**:
  - `log_date`
  - `action`
  - `page_ids`
  - `raw_id`
  - `message`
- **Validation Rules**:
  - 必须能回溯到一次实际提交

## 10. HelperCommitResult
- **Purpose**: helper 返回给 skill 的结构化提交结果。
- **Fields**:
  - `status`
  - `written_paths`
  - `rolled_back`
  - `diagnostics`
- **Validation Rules**:
  - 成功时必须列出写入路径
  - 失败时必须明确是否已回滚

## 11. QueryAnswerDraft
- **Purpose**: 后续 `xk-query` 的结构化答案草稿。
- **Fields**:
  - `answer`
  - `page_refs`
  - `citations`

## 12. CheckFinding
- **Purpose**: 后续 `xk-check` 产生的单页问题。
- **Fields**:
  - `finding_id`
  - `page_id`
  - `finding_type`
  - `severity`
  - `excerpt`
  - `related_chunk_ids`

## Relationships
- `SkillRuntimeContext 1 -> 1 RawDocument`
- `RawDocument 1 -> N RawChunk`
- `SkillRuntimeContext 1 -> 1 PromptPack`
- `SkillRuntimeContext 1 -> 1 KnowledgeMutationSet`
- `KnowledgeMutationSet 1 -> 1 WikiPage`
- `WikiPage 1 -> N IndexEntry`
- `WikiPage N -> N WikiPage` through `LinkEntry`
- `KnowledgeMutationSet 1 -> 1 LogEntry`
- `KnowledgeMutationSet 1 -> 1 HelperCommitResult`

## Transaction Invariants
- 只有在 `wiki_page_draft`、`index_draft`、`link_draft`、`log_draft` 同时合法时，helper 才允许进入提交。
- 任一目标文件写入失败时，helper 必须整体回滚，不得留下部分可见状态。
- `xk-query` 与 `xk-check` 未来只读取已提交完成的知识库状态，不读取 staging 中间态。
