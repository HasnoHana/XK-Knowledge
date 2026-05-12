# Richer Ingest Prompt and Constitution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the ingest prompt and repository constitution so mutation generation follows Constitution first, expands RAW into richer wiki pages, and keeps index/link generation conservative.

**Architecture:** Keep the Python runtime, helper, and schemas unchanged. Modify only the policy layer in `CONSTITUTION.md` and the model-instruction layer in `src/claude_knowledge_mvp/prompts/ingest.md`, with the Constitution acting as the top-level rule set and the prompt translating those rules into concrete drafting behavior.

**Tech Stack:** Markdown prompt assets, Python runtime context wiring, pytest, CLI smoke checks

---

## File Structure

- Modify: `CONSTITUTION.md`
  - Expand from 3 short rules into a stable policy document.
  - Define hard constraints: RAW-only facts, citation discipline, coverage-first drafting, atomic commit requirement, conservative graph updates.
  - Define recommended page section families without turning them into a rigid template.

- Modify: `src/claude_knowledge_mvp/prompts/ingest.md`
  - Reframe the prompt so `constitution_text` is the highest-priority instruction source.
  - Shift from summary-first behavior to coverage-first drafting.
  - Explicitly separate rich page generation from conservative `index_draft` / `link_draft` generation.

- Verify: `tests/unit/test_ingest_commit_helper.py`
  - Existing regression suite for runtime/helper behavior.
  - No schema/runtime changes are expected, so this suite should stay green.

### Task 1: Expand the repository constitution

**Files:**
- Modify: `CONSTITUTION.md`
- Verify: `CONSTITUTION.md`

- [ ] **Step 1: Replace the Constitution with a richer policy document**

Replace the entire file with:

```md
# Constitution

## Hard Rules

- Only knowledge supported by the current RAW document may be committed.
- Do not introduce external facts, background knowledge, or inferred claims that are not grounded in the current RAW document.
- Every committed claim must be traceable to at least one RAW chunk.
- If a statement cannot be cited, it must not appear in the committed wiki page, index, link graph, or log-derived knowledge summary.
- Helper commits must be atomic.
- The repository root is the knowledge base root.

## Writing Policy

- The default ingest behavior is coverage-first, not compression-first.
- When the RAW document is rich, the wiki page should be correspondingly rich: expand important ideas into structured sections instead of collapsing the page into a short summary.
- Prefer reorganizing and clarifying RAW material over shortening it.
- Extract and preserve important concepts, mechanisms, procedures, constraints, examples, formulas, edge cases, and caveats when they are present in the RAW document.
- Summary is an entry point, not a substitute for the body.
- The page body should capture the main substance of the RAW document, not only its headline conclusions.

## Page Organization

- Wiki pages should use a semi-structured layout.
- Prefer sections such as: overview, core concepts, mechanisms or workflow, important details, constraints or limitations, and related knowledge when the RAW document supports them.
- Do not force empty sections when the RAW document does not support them.
- Section choice and ordering should follow the structure of the RAW document.

## Graph Policy

- `index.md` entries should be conservative and evidence-based.
- `link.md` entries should be conservative and evidence-based.
- Do not create topic aliases or page relationships unless they are clearly supported by the RAW document or by existing naming context already provided to the ingest run.
- Richer page content does not justify speculative graph expansion.
```

- [ ] **Step 2: Verify the Constitution contains the new rule groups**

Run:

```bash
grep -n "## Hard Rules\|## Writing Policy\|## Page Organization\|## Graph Policy" CONSTITUTION.md
```

Expected output:

```text
<line>:## Hard Rules
<line>:## Writing Policy
<line>:## Page Organization
<line>:## Graph Policy
```

- [ ] **Step 3: Commit the Constitution change**

Run:

```bash
git add CONSTITUTION.md
git commit -m "docs: expand ingest constitution rules"
```

Expected output:

```text
[main <hash>] docs: expand ingest constitution rules
 1 file changed, ... insertions(+), ... deletions(-)
```

### Task 2: Rewrite the ingest prompt to execute the Constitution

**Files:**
- Modify: `src/claude_knowledge_mvp/prompts/ingest.md`
- Verify: `src/claude_knowledge_mvp/prompts/ingest.md`

- [ ] **Step 1: Replace the current ingest prompt with a Constitution-first prompt**

Replace the entire file with:

```md
# xk-ingest Prompt Pack

You are generating one `KnowledgeMutationSet` for a local markdown knowledge base ingest.

## Instruction priority

You must follow `constitution_text` as the highest-priority policy for this ingest.
If any default summarization habit conflicts with the Constitution, follow the Constitution.
Your job is not to write the shortest acceptable page. Your job is to produce the richest page that is still fully supported by the current RAW document.

## Source of truth

Use the prepare payload as the full ingest context and expect it to match `src/claude_knowledge_mvp/prompts/prepare_output_schema.json`.
Treat the following as authoritative:
- `schema_name`
- `schema_version`
- `raw_document`
- `constitution_text`
- `candidate_laws`
- `global_index_excerpt`
- `global_link_excerpt`
- `expected_output_keys`

## Knowledge boundary

- The current RAW document is the only source of committed knowledge.
- Do not introduce outside facts, background knowledge, or textbook explanations that are not supported by the RAW document.
- You may reorganize, clarify, compress, or expand the RAW material.
- You may make implicit structure explicit when it is directly supported by the RAW document.
- You must not add unsupported claims just because they are commonly true.

## Drafting strategy

- Read the RAW document for coverage before drafting.
- Prefer coverage-first drafting over summary-first drafting.
- When the RAW document is rich, the wiki page should also be rich.
- Expand the important substance of the RAW document into structured sections instead of collapsing it into a brief overview.
- Preserve important concepts, mechanisms, procedures, formulas, examples, constraints, caveats, and edge cases when present.
- The summary should orient the reader, but the body should carry the substance.
- Use a semi-structured layout: choose the sections that best fit the RAW document rather than forcing a rigid template.

## Recommended section families

Use these when supported by the RAW document:
- overview
- core concepts or entities
- mechanisms, workflow, or algorithm steps
- important details, parameters, or implementation-relevant specifics
- constraints, limitations, or failure modes
- examples or cases explicitly present in the RAW document
- related knowledge justified by the RAW document and current graph context

Do not create empty sections.
Do not add sections whose content would be thin or repetitive.

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
- Prefer broad chunk coverage when the RAW document contains multiple substantive sections.
- If the RAW document contains several important themes, ensure the page body reflects them rather than only the opening section.
- `index_draft.entries` must point to the page being created and remain conservative.
- `link_draft.entries` must contain only relationships justified by the RAW content or current graph context.
- Richer page content does not justify speculative aliases or speculative links.
- `log_draft` must describe this ingest action.
- Do not omit `index_draft`, `link_draft`, or `log_draft` even if graph updates are minimal.
- If the RAW content is weak, keep the drafts minimal and keep citations honest.
- If the RAW content is rich, do not artificially compress the page.

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

- Prefer complete coverage with valid citations over shallow compression.
- Prefer explicit structure over a single dense block of prose.
- Prefer fewer sections only when the RAW document is actually sparse.
- Reuse existing naming and graph context when justified by the prepare payload.
- Never output uncited knowledge.
```

- [ ] **Step 2: Verify the prompt now references Constitution priority and coverage-first drafting**

Run:

```bash
grep -n "Instruction priority\|constitution_text\|coverage-first\|Richer page content does not justify speculative" src/claude_knowledge_mvp/prompts/ingest.md
```

Expected output:

```text
<line>:## Instruction priority
<line>:You must follow `constitution_text` as the highest-priority policy for this ingest.
<line>:- Prefer coverage-first drafting over summary-first drafting.
<line>:- Richer page content does not justify speculative aliases or speculative links.
```

- [ ] **Step 3: Commit the prompt rewrite**

Run:

```bash
git add src/claude_knowledge_mvp/prompts/ingest.md
git commit -m "docs: rewrite ingest prompt for coverage-first drafting"
```

Expected output:

```text
[main <hash>] docs: rewrite ingest prompt for coverage-first drafting
 1 file changed, ... insertions(+), ... deletions(-)
```

### Task 3: Run regression and smoke verification

**Files:**
- Verify: `tests/unit/test_ingest_commit_helper.py`
- Verify: `CONSTITUTION.md`
- Verify: `src/claude_knowledge_mvp/prompts/ingest.md`

- [ ] **Step 1: Run the helper/runtime regression suite**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_ingest_commit_helper.py -q
```

Expected output:

```text
............
[100%]
```

- [ ] **Step 2: Run a prepare smoke check for a real RAW file**

Run:

```bash
PYTHONPATH=src python -m claude_knowledge_mvp.runtime.ingest_cli prepare --repo-root /Users/bytedance/Desktop/XK-Knowledge --raw-path RAW/article/transformer-core.md
```

Expected output:

```json
{
  "schema_name": "xk-ingest-prepare-output",
  "schema_version": "1.0",
  "raw_document": {
    "source_path": "RAW/article/transformer-core.md"
  },
  "constitution_text": "# Constitution...",
  "prompt_pack": "# xk-ingest Prompt Pack..."
}
```

- [ ] **Step 3: Spot-check that the prepare payload includes the rewritten Constitution and prompt**

Run:

```bash
PYTHONPATH=src python -m claude_knowledge_mvp.runtime.ingest_cli prepare --repo-root /Users/bytedance/Desktop/XK-Knowledge --raw-path RAW/article/transformer-core.md | grep -E 'Constitution|coverage-first|highest-priority policy|Graph Policy'
```

Expected output:

```text
... Constitution ...
... highest-priority policy ...
... coverage-first ...
... Graph Policy ...
```

- [ ] **Step 4: Commit the verification checkpoint**

Run:

```bash
git status --short
```

Expected output:

```text
```

This confirms the working tree is clean after the two documentation commits and verification runs.
