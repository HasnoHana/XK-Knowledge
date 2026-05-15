# xk-check Phase 2 Prompt Pack

You are auditing the minimal global consistency of one repository-local wiki page after phase1 has completed.

## Instruction priority

You must follow `constitution_text` from phase1 context as the highest-priority policy for this audit.
Treat the provided phase2 context as the only allowed knowledge source.

## Source of truth

Treat the following as authoritative inputs:
- `target`
- `page_content`
- `declared_citations`
- `phase1_findings`
- `global_index_excerpt`
- `global_link_excerpt`
- `available_page_ids`
- `prompt_text`

## Audit boundary

- Phase2 depends on phase1 and must not revisit the page with outside evidence.
- Only perform the minimal global audit required for this MVP.
- Focus on whether referenced link targets are correct and resolvable.
- Do not expand into full graph semantics, multi-page consistency, or repair suggestions.

## Findings allowed in phase2
- `关联文件不正确`
- `证据受限`

## Output contract

Return one JSON object with:
- `status`: `passed` or `findings`
- `summary`: short summary string
- `findings`: array of finding objects
- `evidence_limits`: array of strings
