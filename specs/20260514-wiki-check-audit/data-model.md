# Phase 1 Data Model: `/xk-check` 单页引用审计

## 设计原则
- 保持中间结构最小化，只承载阶段装配、finding 表达和最终报告所需字段。
- 不为未来批量扫描、自动修复或复杂图谱裁决预留参数。
- 数据模型服务于只读审计流，不包含任何 commit/mutation 字段。

## Entities

### 1. CheckTarget
- **Purpose**: 标识一次 `/xk-check` 的唯一目标页面。
- **Fields**:
  - `wiki_path`: 仓库相对路径，必须位于 `WIKI/*/pages/*.md`
  - `page_id`: 由文件名导出的页面标识
  - `wiki_type`: 页面所属类型目录，如 `notes`、`architecture`
- **Validation**:
  - 路径必须存在且可读
  - 每次调用只允许一个目标

### 2. DeclaredRawCitation
- **Purpose**: 表示目标页面内已经声明、可用于 Phase 1 审计的 Raw 证据单元。
- **Fields**:
  - `chunk_id`: 页面内声明的 chunk 标识
  - `raw_path`: 被引用的仓库相对路径
  - `locator`: 页内可解析到的引用定位符
  - `raw_excerpt`: 供 Agent 判断的实际证据文本；当前 MVP 保留为空字符串
  - `parse_status`: `ok | raw_missing`
- **Validation**:
  - 仅接受页面内显式声明的引用
  - `parse_status != ok` 时必须在报告中体现证据受限或输入错误

### 3. Phase1CheckContext
- **Purpose**: Phase 1 提供给 Agent 的最小页面级审计上下文。
- **Fields**:
  - `target`: `CheckTarget`
  - `page_content`: 目标页面完整内容
  - `declared_citations`: `DeclaredRawCitation[]`
  - `constitution_text`: 生效 constitution 文本
  - `candidate_laws`: 候选 `WIKI/<type>/LAWS.md` 内容映射
  - `prompt_text`: `check_phase1.md`
- **Validation**:
  - 不得包含页外 wiki 内容、整份未声明 Raw 或外部知识

### 4. Phase2GlobalContext
- **Purpose**: 在 Phase 1 完成后继承并补充的全局检查上下文。
- **Fields**:
  - `phase1_context`: `Phase1CheckContext`
  - `phase1_findings`: 第一阶段 finding 列表
  - `global_index_excerpt`: `WIKI/INDEX.md` 内容
  - `global_link_excerpt`: 仅截取与目标页面相关的 `WIKI/LINK.md` 片段
  - `available_page_ids`: 仓库内当前可解析页面 id 列表
  - `prompt_text`: `check_phase2.md`
- **Validation**:
  - 只有在 Phase 1 成功完成后才能构建
  - 当前只允许面向 INDEX/LINK 的最小检查

### 5. CheckFinding
- **Purpose**: 表达一条审计结论。
- **Fields**:
  - `phase`: `phase1 | phase2`
  - `kind`: `无来源陈述 | 过强结论 | 关联文件不正确 | 证据受限`
  - `location`: 页面段落、引用位置或全局文件位置
  - `message`: 面向人的简短说明
  - `evidence_refs`: 相关 Raw 引用、页面路径或全局文件路径列表
- **Validation**:
  - `kind` 必须来自当前阶段允许的最小集合
  - `evidence_refs` 只能引用本次上下文中真实存在的证据

### 6. CheckReport
- **Purpose**: 一次 `/xk-check` 的最终结果对象。
- **Fields**:
  - `target`: `CheckTarget`
  - `phase1_findings`: `CheckFinding[]`
  - `phase2_findings`: `CheckFinding[]`
  - `evidence_limits`: 证据受限说明列表
  - `status`: `passed | findings | blocked | failed`
  - `report_markdown`: 最终返回给用户的 markdown
- **Validation**:
  - `blocked` 仅用于 Phase 1 未完成导致无法进入 Phase 2
  - `report_markdown` 必须与结构化 finding 一致

## Relationships
- `CheckTarget` 1→N `DeclaredRawCitation`
- `Phase1CheckContext` 1→1 `CheckTarget`
- `Phase1CheckContext` 1→N `DeclaredRawCitation`
- `Phase2GlobalContext` 1→1 `Phase1CheckContext`
- `CheckReport` 聚合两个阶段的 `CheckFinding`

## State Flow
1. 解析输入路径，生成 `CheckTarget`
2. 从目标页面提取 `DeclaredRawCitation`
3. 组装 `Phase1CheckContext`
4. 运行 Phase 1，产出页面级 `CheckFinding`
5. 若 Phase 1 完成，则组装 `Phase2GlobalContext`
6. 运行 Phase 2，补充全局 `CheckFinding`
7. 组装 `CheckReport` 并返回 markdown
