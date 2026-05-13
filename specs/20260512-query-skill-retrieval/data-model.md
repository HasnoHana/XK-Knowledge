# Data Model: 20260512-query-skill-retrieval

## 1. Question
- **Purpose**: 表示用户提出的一次知识查询问题。
- **Fields**:
  - `question: str` — 用户原始问题文本。
  - `source: "skill" | "xk-query"` — 触发来源。
  - `conversation_context: str` — 必要的会话上下文摘录。
- **Validation Rules**:
  - `question` 不得为空。
  - 当问题表达模糊时，应先澄清，而不是直接进入回答。

## 2. Query Context
- **Purpose**: runtime 提供给 Agent 的最小上下文集合。
- **Contents**:
  - 与问题相关的 `WIKI/INDEX.md` 命中结果
  - 与主命中页面相关的一跳 `WIKI/LINK.md` 信息
  - 相关 WIKI 页面内容
  - 页面内可用的引用信息
- **Validation Rules**:
  - 必须至少包含用户问题和当前命中的主页面上下文。
  - link 扩展最多只取一跳。
  - 当前阶段 Query Context 的目标是让 Agent 感知相关 Knowledge，而不是承载独立输出 schema。

## 3. Answer
- **Purpose**: Agent 基于 Query Context 返回的最小回答结果。
- **Contents**:
  - `answer_text` — 回答正文
  - `citations` — 相关引用内容
  - `raw_chunks` — 可回到 Raw 的 chunk 依据
- **Validation Rules**:
  - `answer_text` 不得为空。
  - 回答中的强结论必须能被引用内容与 Raw chunk 支撑。
  - 当证据不足时，应明确暴露限制，而不是伪造结论。

## Relationships
- `Question` 决定一次 query 的输入范围。
- `Query Context` 由 runtime 基于 `Question` 组装并交给 Agent。
- `Answer` 由 Agent 基于 `Query Context` 生成。
