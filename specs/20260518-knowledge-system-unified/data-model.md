# Phase 1 Data Model: 系统一致性收敛

## 设计原则
- 模型只服务于当前一致性收敛目标，不为未来复杂增强预埋多余字段。
- 优先统一 evidence model、结果面和命令边界，不新增业务能力。
- 保持与当前本地 Markdown 知识库结构一致。

## Entities

### 1. RawDocument
- **Purpose**: ingest 的证据输入起点。
- **Fields**:
  - `raw_id`: 原始资料标识
  - `source_path`: 仓库内相对路径
  - `title`: 人类可读标题
  - `content`: 原始内容
- **Validation**:
  - 必须位于 `RAW/` 下
  - ingest 前必须可读

### 2. WikiPage
- **Purpose**: 系统统一消费的知识页对象。
- **Fields**:
  - `page_id`: 页面唯一标识
  - `wiki_path`: 仓库内相对路径
  - `wiki_type`: 页面类型目录
  - `content`: 页面正文
  - `source_chunk_ids`: 回溯到 Raw 的引用链
- **Validation**:
  - 必须来自 `WIKI/*/pages/*.md`
  - 页面被定义为知识页，而不是 Raw 摘要

### 3. IndexEntry
- **Purpose**: query 缩圈的最小索引单元。
- **Fields**:
  - `topic`: 用户查询可命中的主题词
  - `page_id`: 命中的页面标识
- **Validation**:
  - 必须能解析到实际存在的页面

### 4. LinkEntry
- **Purpose**: query 一跳扩展和 check 全局最小检查的关系单元。
- **Fields**:
  - `source_page_id`: 源页面
  - `target_page_id`: 目标页面
  - `relation_type`: 当前最小关系类型
  - `note`: 关系说明
- **Validation**:
  - 目标页面必须可解析，否则属于不正确关联

### 5. QueryCitation
- **Purpose**: query 结果中的统一引用项。
- **Fields**:
  - `page_id`: 引用来源页面标识
  - `wiki_path`: 引用来源页面路径
  - `raw_chunk_ids`: 支撑该引用的 Raw chunk 列表
- **Validation**:
  - `wiki_path` 必须指向实际页面
  - `raw_chunk_ids` 只能包含页面已声明证据

### 6. QueryAnswer
- **Purpose**: query 的统一结果对象。
- **Fields**:
  - `answer`: 答案正文
  - `citations`: `QueryCitation[]`
  - `evidence_limits`: 证据受限说明列表
- **Validation**:
  - 即使没有命中，也必须显式返回 `evidence_limits`

### 7. CheckFinding
- **Purpose**: check 的最小审计结论。
- **Fields**:
  - `phase`: `phase1 | phase2`
  - `kind`: finding 类型
  - `location`: 页面位置或全局文件位置
  - `message`: 面向人的说明
  - `evidence_refs`: 对应证据引用
- **Validation**:
  - `kind` 必须属于当前阶段允许集合

### 8. CheckReport
- **Purpose**: `/xk-check` 的统一结果对象。
- **Fields**:
  - `status`: `passed | findings | blocked | failed`
  - `phase1_findings`: 第一阶段发现
  - `phase2_findings`: 第二阶段发现
  - `evidence_limits`: 证据受限说明列表
  - `report_markdown`: 返回给用户的人读报告
- **Validation**:
  - 无论是否发现问题，都必须保留 `evidence_limits`
  - `report_markdown` 必须与结构化 finding 一致

### 9. OrchestrationBoundary
- **Purpose**: 表达系统统一执行边界的规则对象。
- **Fields**:
  - `orchestrator`: 固定为 `Claude Code`
  - `local_tools`: 本地脚本、runtime、helper
  - `forbidden_internal_callers`: `Claude Code | Claude CLI | Claude SDK | new Claude process`
- **Validation**:
  - 本地执行层只允许机械性工作，不允许内部发起新的 Claude 调用链

## Relationships
- `RawDocument` 1→N `WikiPage`
- `WikiPage` 1→N `QueryCitation`
- `WikiPage` 1→N `CheckFinding`
- `IndexEntry` N→1 `WikiPage`
- `LinkEntry` N→1 `WikiPage`
- `QueryAnswer` 聚合 `QueryCitation`
- `CheckReport` 聚合 `CheckFinding`
- `OrchestrationBoundary` 约束 ingest/query/check 三条主路径

## State Flow
1. ingest 从 `RawDocument` 生成 `WikiPage` 与关联索引/关系/日志
2. query 通过 `IndexEntry` 与 `LinkEntry` 找到 `WikiPage`
3. query 产出 `QueryAnswer` 与 `QueryCitation`
4. check 读取 `WikiPage`，产出 `CheckFinding` 与 `CheckReport`
5. `OrchestrationBoundary` 在整个过程中约束 Claude Code 与本地脚本的单向调用关系