# Data Model — Claude Code 知识管理系统 MVP

## 1. RawDocument
- **Purpose**: 表示一份经过人工筛选、允许被 AI Proxy 摄入的原始资料。
- **Fields**:
  - `raw_id`: 稳定唯一标识
  - `source_path`: 原始文件路径
  - `source_type`: `markdown | pdf | web_export | text`
  - `title`: 原始资料标题
  - `ingest_allowed`: 是否通过人工筛选
  - `content`: 原始内容快照
- **Validation Rules**:
  - `source_path` 必须存在且可读
  - `ingest_allowed=true` 才允许进入 ingest

## 2. RawChunk
- **Purpose**: 由 AI Proxy 在 ingest prompt 引导下划定的稳定证据单元，用于建立回到 Raw 的引用链。
- **Fields**:
  - `chunk_id`: `raw/<raw_id>#chunk-<n>`
  - `raw_id`: 所属 RawDocument
  - `locator`: 文档内定位信息
  - `text`: 锚点对应的原文内容
  - `order`: 在原文中的顺序
- **Validation Rules**:
  - `chunk_id` 在同一 RawDocument 内唯一
  - `text` 不能为空
  - chunk 边界由模型决定，工程层只负责稳定编号与合法性校验

## 3. GlobalConstitution
- **Purpose**: 表示系统唯一最高层 `CONSTITUTION.md` 的规则集合，是模型运行时的首要约束。
- **Fields**:
  - `path`: `XK-Knowledge/CONSTITUTION.md`
  - `rules`: 全局规则条目集合
  - `version_hint`: 规则版本或摘要
- **Validation Rules**:
  - 系统只允许存在一份 GlobalConstitution
  - 任何类型级规则和模型输出都不得违反 GlobalConstitution

## 4. TypeLaw
- **Purpose**: 表示某个知识类型的准入和表达规则文件 `WIKI/<type>/LAWS.md`。
- **Fields**:
  - `type_name`: `concept | workflow | cli`
  - `path`: `XK-Knowledge/WIKI/<type>/LAWS.md`
  - `rules`: 该类型的结构、命名、引用与边界规则
- **Validation Rules**:
  - 每个 type 最多一份 TypeLaw
  - TypeLaw 只能补充类型约束，不能替代 Constitution

## 5. PromptPack
- **Purpose**: 预设提示词资产，定义 ingest/query/check 的模型执行路径、输出 schema 与失败条件。
- **Fields**:
  - `name`: `ingest | query | check`
  - `path`: 对应 prompt 文件路径
  - `version`: prompt 版本标识
  - `output_contract`: 该 prompt 要求模型返回的结构化字段约束
- **Validation Rules**:
  - 每条主路径必须有一份 PromptPack
  - PromptPack 必须显式要求加载 Constitution，ingest 还必须要求加载相关 TypeLaw

## 6. ModelIngestContext
- **Purpose**: 一次 ingest 提供给 AI Proxy 的完整上下文包。
- **Fields**:
  - `raw_document`: 待摄入 RawDocument
  - `constitution`: GlobalConstitution
  - `candidate_type_laws`: 可选 TypeLaw 列表
  - `prompt_pack`: ingest PromptPack
  - `existing_page_refs`: 现有页面摘要引用
  - `global_index_excerpt`: 当前全局索引摘要
  - `global_link_excerpt`: 当前全局关系摘要
- **Validation Rules**:
  - 必须同时包含原始资料、规则约束与 ingest PromptPack
  - 若缺少 Constitution、PromptPack 或可读 Raw，不允许调用模型生成可提交草稿

## 7. KnowledgeMutationSet
- **Purpose**: ingest 过程中由 AI Proxy 一次性生成的统一知识变更集合。
- **Fields**:
  - `raw_chunks`: 模型划分出的 RawChunk 列表
  - `wiki_page_draft`: WikiPage 草稿
  - `index_draft`: IndexEntry 列表
  - `link_draft`: LinkEntry 列表
  - `log_draft`: LogEntry 草稿
  - `completeness_report`: 对 Raw 覆盖范围、引用充分性和省略原因的说明
- **Validation Rules**:
  - 必须同时包含 `raw_chunks`、`wiki_page_draft`、`index_draft`、`link_draft`、`log_draft`
  - `completeness_report` 不能为空
  - 任一关键组成部分缺失时不得提交

## 8. WikiPage
- **Purpose**: 从 `KnowledgeMutationSet` 物化出来的正式知识页面。
- **Fields**:
  - `page_id`: 页面稳定标识
  - `slug`: 页面文件名
  - `title`: 页面标题
  - `wiki_type`: 所属知识类型
  - `summary`: TL;DR 摘要
  - `body_sections`: 结构化知识内容
  - `source_chunk_ids`: 模型选中的证据锚点列表
  - `status`: `active | stale`
- **Validation Rules**:
  - `source_chunk_ids` 至少包含一个 chunk
  - `slug` 在同一类型目录中唯一
  - 页面内容必须来自模型草稿，而不是工程模板补齐

## 9. IndexEntry
- **Purpose**: 全局或类型局部 `INDEX.md` 中的索引项。
- **Fields**:
  - `scope`: `global | local`
  - `type_name`: 当 `scope=local` 时对应知识类型
  - `topic`: 主题名称
  - `aliases`: 主题别名列表
  - `page_id`: 指向的 WikiPage
  - `rank`: 排序位置
- **Validation Rules**:
  - `page_id` 必须引用存在的 WikiPage
  - 同一 `scope + type_name + topic + page_id` 组合不可重复

## 10. LinkEntry
- **Purpose**: 全局或类型局部 `LINK.md` 中的页面关系记录。
- **Fields**:
  - `scope`: `global | local`
  - `type_name`: 当 `scope=local` 时对应知识类型
  - `source_page_id`: 源页面
  - `target_page_id`: 目标页面
  - `relation_type`: `related | depends_on | superseded_by`
  - `note`: 关系说明
- **Validation Rules**:
  - 页面关系由模型提出，工程层仅做合法性校验与去重
  - 局部 Link 仅记录同类型关系；跨类型关系必须进入全局 Link

## 11. LogEntry
- **Purpose**: `LOG/<date>.md` 中记录一次 ingest 或修订产生的变更。
- **Fields**:
  - `log_date`: 日期分区键
  - `action`: `add_page | update_page | initialize_store`
  - `page_ids`: 受影响页面列表
  - `raw_id`: 来源 RawDocument
  - `message`: 面向人类的日志描述
- **Validation Rules**:
  - 每条日志必须能回溯到一次实际提交
  - 日志草稿由模型给出，工程层只做物化与一致性校验

## 12. QueryAnswerDraft
- **Purpose**: query prompt 产生的结构化答案草稿。
- **Fields**:
  - `answer`: 最终回答正文
  - `page_refs`: 命中的 WikiPage 引用列表
  - `citations`: 回到 Raw 的引用链
- **Validation Rules**:
  - `answer` 不能为空
  - `citations` 至少包含一条合法 Raw 引用

## 13. CheckFinding
- **Purpose**: check 命令识别出的单页问题。
- **Fields**:
  - `finding_id`: 唯一标识
  - `page_id`: 被检查页面
  - `finding_type`: `missing_citation | overstated_claim`
  - `severity`: `warning | error`
  - `excerpt`: 问题片段
  - `related_chunk_ids`: 支撑或缺失的证据锚点
- **Validation Rules**:
  - finding 由模型根据页面、Raw 与 Constitution 产生
  - `page_id` 必须存在于当前已提交知识目录中

## Relationships
- `GlobalConstitution 1 -> N TypeLaw`
- `PromptPack 1 -> N ModelIngestContext`
- `RawDocument 1 -> N RawChunk`
- `ModelIngestContext 1 -> 1 RawDocument`
- `ModelIngestContext 1 -> 1 KnowledgeMutationSet`
- `KnowledgeMutationSet 1 -> 1 WikiPage`
- `WikiPage 1 -> N IndexEntry`
- `WikiPage N -> N WikiPage` 通过 `LinkEntry` 建立关系
- `WikiPage 1 -> N CheckFinding`
- `LogEntry` 记录 `RawDocument` 到 `WikiPage` 的提交事件

## Transaction Invariants
- `query` 与 `check` 只读取 `XK-Knowledge/WIKI/` 下已提交完成的目录状态。
- 任一次 ingest 只有在目标 page、全局/局部 `INDEX.md`、全局/局部 `LINK.md` 和 `LOG/` 都写好后，才允许提交本次变更。
- 若 AI Proxy 未产出完整合法的 `KnowledgeMutationSet`、引用校验失败或任一目标文件写入失败，则本次 ingest 必须整体失败，不得留下部分可见状态。
