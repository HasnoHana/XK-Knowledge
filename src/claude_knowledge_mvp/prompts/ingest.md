# xk-ingest Prompt Pack

You are generating one `KnowledgeMutationSet` for a local markdown knowledge base ingest.

## Instruction priority

You must follow `constitution_text` as the highest-priority policy for this ingest.
If any instruction in this prompt conflicts with the Constitution, follow the Constitution.
Do not treat this task as summarization. Treat it as knowledge organization under strict evidence constraints.

## Source of truth

Use the prepare payload as the full ingest context and expect it to match `src/claude_knowledge_mvp/prompts/prepare_output_schema.json`.
Treat the following as authoritative inputs:
- `schema_name`
- `schema_version`
- `raw_document`
- `constitution_text`
- `candidate_laws`
- `global_index_excerpt`
- `global_link_excerpt`
- `expected_output_keys`

For committed factual content, the current RAW document is the only source of truth.
Use `constitution_text` for policy.
Use `candidate_laws`, `global_index_excerpt`, and `global_link_excerpt` only for naming consistency, type choice, and conservative relation decisions.

## Knowledge boundary

- Do not introduce outside facts, background knowledge, or textbook explanations that are not supported by the RAW document.
- You may reorganize, clarify, normalize naming, merge related evidence, compress local repetition, or expand implicit structure when the result stays fully supported by the RAW document.
- You must not add unsupported claims just because they are commonly true.

## Organization objective

- A Wiki Page is not a shortened rendering of RAW.
- A Wiki Page is a knowledge page built from RAW-supported content.
- Organize the page for later knowledge consumption, stable reference, and future query/check use.
- Prefer knowledge structure over document order.
- If the RAW document scatters related material across multiple sections, combine it into more stable knowledge sections when the grouping is clearly supported.
- Do not mirror the RAW table of contents unless it already matches the best knowledge structure.

## Drafting strategy

- Read the entire RAW document before drafting.
- Identify the main concepts, mechanisms, constraints, decisions, examples, and edge cases supported by the RAW document.
- Build `raw_chunks` as stable citation units first.
- Then build `wiki_page_draft` around the best knowledge structure you can justify from those chunks.
- Preserve important substance; do not collapse a rich document into a thin recap.
- Summary should orient the reader, but the body sections should carry the knowledge value.

## Recommended section families

Use these when supported by the RAW document:
- overview
- core concepts or entities
- mechanisms, workflow, or algorithm steps
- important details, parameters, or implementation-relevant specifics
- constraints, limitations, invariants, or failure modes
- examples or cases explicitly present in the RAW document
- related knowledge justified by the RAW document and current graph context

Do not create empty sections.
Do not add sections whose content would be thin, repetitive, or unsupported.

## Output contract

Return JSON only.
Do not return markdown fences.
Do not return explanation text before or after the JSON.
Return exactly one object with these top-level keys:
- `schema_name`
- `schema_version`
- `raw_chunks`
- `wiki_page_draft`
- `index_draft`
- `link_draft`
- `log_draft`
- `completeness_report`

## Mutation rules

- Set `schema_name` to `xk-ingest-mutation-set`.
- Set `schema_version` to `1.0`.
- Split the RAW document into stable citation units in `raw_chunks`.
- Every committed wiki claim must be traceable to at least one RAW chunk.
- `wiki_page_draft.source_chunk_ids` must reference chunk ids that exist in `raw_chunks`.
- `completeness_report.covered_chunk_ids` must list the chunk ids actually used.
- Prefer chunk coverage that supports the full knowledge structure of the page, not only the opening part of the RAW document.
- `wiki_page_draft` must reflect knowledge organization, not a section-by-section compression of the RAW document.
- `index_draft.entries` must point to the page being created and remain conservative.
- `link_draft.entries` must contain only relationships justified by the RAW content or current graph context.
- Richer page content does not justify speculative aliases or speculative links.
- `log_draft` must describe this ingest action.
- Do not omit `index_draft`, `link_draft`, or `log_draft` even if graph updates are minimal.
- If the RAW content is weak, keep the page minimal and keep citations honest.
- If the RAW content is rich, preserve its substance through organization rather than compression.

## Required wiki draft fields

`wiki_page_draft` must include:
- `page_id`
- `slug`
- `title`
- `wiki_type`
- `summary`
- `body_sections`
- `source_chunk_ids`
- `status`

## Quality bar

- Prefer knowledge organization with valid citations over shallow compression.
- Prefer stable sections built around concepts and mechanisms over a RAW-order recap.
- Prefer explicit structure over a single dense block of prose.
- Reuse existing naming and graph context when justified by the prepare payload.
- Never output uncited knowledge.
