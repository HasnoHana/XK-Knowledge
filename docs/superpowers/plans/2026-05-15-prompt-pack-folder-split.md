# Prompt Pack Folder Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize prompt assets into separate ingest/query/check folders without changing runtime behavior, so prompt growth stays local to each operation.

**Architecture:** Keep the runtime behavior the same, but stop resolving prompt files from one flat `prompts/` directory. Add one tiny prompt-path module that owns the relative paths, move the markdown/json assets into operation-specific subfolders, and update the runtimes/tests to use those shared paths. This keeps the code simple while preventing path drift as prompt packs expand.

**Tech Stack:** Python 3.11, pathlib, dataclasses, pytest

---

## File Structure

### Create
- `src/claude_knowledge_mvp/prompts/paths.py` — single source of truth for prompt/schema relative paths.
- `src/claude_knowledge_mvp/prompts/ingest/prompt.md` — ingest prompt body moved from the flat directory.
- `src/claude_knowledge_mvp/prompts/ingest/prepare_output_schema.json` — ingest prepare schema moved under ingest.
- `src/claude_knowledge_mvp/prompts/ingest/mutation_set_schema.json` — ingest mutation schema moved under ingest.
- `src/claude_knowledge_mvp/prompts/query/prompt.md` — query prompt body moved from the flat directory.
- `src/claude_knowledge_mvp/prompts/check/phase1.md` — check phase1 prompt moved from the flat directory.
- `src/claude_knowledge_mvp/prompts/check/phase2.md` — check phase2 prompt moved from the flat directory.

### Modify
- `src/claude_knowledge_mvp/runtime/ingest.py` — load ingest prompt/schema from the new ingest folder.
- `src/claude_knowledge_mvp/runtime/query.py` — load query prompt from the new query folder.
- `src/claude_knowledge_mvp/runtime/check.py` — load phase1/phase2 prompts from the new check folder.
- `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` — point mutation schema constant at the new ingest schema path.
- `tests/unit/test_ingest_commit_helper.py` — build test repos with the new ingest folder layout.
- `tests/unit/test_query_runtime.py` — build test repos with the new query folder layout.
- `tests/unit/test_check_runtime.py` — build test repos with the new check folder layout.

### Keep Unchanged
- Prompt text content itself.
- Result contracts for ingest/query/check.
- CLI interfaces and command names.

---

### Task 1: Add a shared prompt path registry

**Files:**
- Create: `src/claude_knowledge_mvp/prompts/paths.py`
- Modify: `tests/unit/test_ingest_commit_helper.py`
- Modify: `tests/unit/test_query_runtime.py`
- Modify: `tests/unit/test_check_runtime.py`

- [ ] **Step 1: Write the failing tests that assert the new folder layout is the supported layout**

Add these assertions near the top of the existing test modules so the new layout is locked before runtime code changes.

```python
from claude_knowledge_mvp.prompts.paths import (
    CHECK_PHASE1_PROMPT_PATH,
    CHECK_PHASE2_PROMPT_PATH,
    INGEST_MUTATION_SET_SCHEMA_PATH,
    INGEST_PREPARE_OUTPUT_SCHEMA_PATH,
    INGEST_PROMPT_PATH,
    QUERY_PROMPT_PATH,
)


def test_prompt_paths_are_scoped_by_operation():
    assert INGEST_PROMPT_PATH.as_posix() == "src/claude_knowledge_mvp/prompts/ingest/prompt.md"
    assert INGEST_PREPARE_OUTPUT_SCHEMA_PATH.as_posix() == (
        "src/claude_knowledge_mvp/prompts/ingest/prepare_output_schema.json"
    )
    assert INGEST_MUTATION_SET_SCHEMA_PATH.as_posix() == (
        "src/claude_knowledge_mvp/prompts/ingest/mutation_set_schema.json"
    )
    assert QUERY_PROMPT_PATH.as_posix() == "src/claude_knowledge_mvp/prompts/query/prompt.md"
    assert CHECK_PHASE1_PROMPT_PATH.as_posix() == "src/claude_knowledge_mvp/prompts/check/phase1.md"
    assert CHECK_PHASE2_PROMPT_PATH.as_posix() == "src/claude_knowledge_mvp/prompts/check/phase2.md"
```

- [ ] **Step 2: Run the targeted tests to verify the import fails before implementation**

Run:
```bash
pytest tests/unit/test_ingest_commit_helper.py::test_prompt_paths_are_scoped_by_operation -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'claude_knowledge_mvp.prompts.paths'`.

- [ ] **Step 3: Add the minimal prompt path module**

Create `src/claude_knowledge_mvp/prompts/paths.py` with exactly these constants.

```python
from __future__ import annotations

from pathlib import Path

PROMPTS_ROOT = Path("src") / "claude_knowledge_mvp" / "prompts"

INGEST_DIR = PROMPTS_ROOT / "ingest"
QUERY_DIR = PROMPTS_ROOT / "query"
CHECK_DIR = PROMPTS_ROOT / "check"

INGEST_PROMPT_PATH = INGEST_DIR / "prompt.md"
INGEST_PREPARE_OUTPUT_SCHEMA_PATH = INGEST_DIR / "prepare_output_schema.json"
INGEST_MUTATION_SET_SCHEMA_PATH = INGEST_DIR / "mutation_set_schema.json"

QUERY_PROMPT_PATH = QUERY_DIR / "prompt.md"

CHECK_PHASE1_PROMPT_PATH = CHECK_DIR / "phase1.md"
CHECK_PHASE2_PROMPT_PATH = CHECK_DIR / "phase2.md"
```

- [ ] **Step 4: Run the targeted tests to verify the registry passes**

Run:
```bash
pytest tests/unit/test_ingest_commit_helper.py::test_prompt_paths_are_scoped_by_operation -q
```

Expected: PASS.

- [ ] **Step 5: Commit the registry task**

```bash
git add src/claude_knowledge_mvp/prompts/paths.py tests/unit/test_ingest_commit_helper.py tests/unit/test_query_runtime.py tests/unit/test_check_runtime.py
git commit -m "refactor: centralize prompt asset paths"
```

---

### Task 2: Move ingest assets under `prompts/ingest` and update ingest runtime

**Files:**
- Create: `src/claude_knowledge_mvp/prompts/ingest/prompt.md`
- Create: `src/claude_knowledge_mvp/prompts/ingest/prepare_output_schema.json`
- Create: `src/claude_knowledge_mvp/prompts/ingest/mutation_set_schema.json`
- Modify: `src/claude_knowledge_mvp/runtime/ingest.py`
- Modify: `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py`
- Modify: `tests/unit/test_ingest_commit_helper.py`

- [ ] **Step 1: Update the ingest tests to build repo fixtures in the new ingest folder**

In every test fixture/setup that currently writes to `src/claude_knowledge_mvp/prompts/ingest.md`, `prepare_output_schema.json`, or `mutation_set_schema.json`, switch to the shared constants.

```python
from claude_knowledge_mvp.prompts.paths import (
    INGEST_MUTATION_SET_SCHEMA_PATH,
    INGEST_PREPARE_OUTPUT_SCHEMA_PATH,
    INGEST_PROMPT_PATH,
)


def _write_repo_file(repo_root: Path, relative_path: Path, content: str) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_write_repo_file(repo_root, INGEST_PROMPT_PATH, "Return a KnowledgeMutationSet.\n")
_write_repo_file(repo_root, INGEST_PREPARE_OUTPUT_SCHEMA_PATH, '{"title": "prepare"}\n')
_write_repo_file(repo_root, INGEST_MUTATION_SET_SCHEMA_PATH, '{"title": "mutation"}\n')
```

Also change the direct directory creation from:

```python
(repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
```

to helper-based writes only.

- [ ] **Step 2: Run one ingest prepare test to verify it fails on the old runtime path**

Run:
```bash
pytest tests/unit/test_ingest_commit_helper.py::test_prepare_ingest_payload_collects_runtime_context -q
```

Expected: FAIL with `ValueError: ingest prompt pack is required` because `runtime/ingest.py` still looks for `prompts/ingest.md`.

- [ ] **Step 3: Move the ingest assets and update the ingest runtime/helper constants**

Create these new files by copying the current contents verbatim:

`src/claude_knowledge_mvp/prompts/ingest/prompt.md`
```md
# xk-ingest Prompt Pack

You are generating one `KnowledgeMutationSet` for a local markdown knowledge base ingest.

## Instruction priority

You must follow `constitution_text` as the highest-priority policy for this ingest.
If any instruction in this prompt conflicts with the Constitution, follow the Constitution.
Do not treat this task as summarization. Treat it as knowledge organization under strict evidence constraints.

## Source of truth

Use the prepare payload as the full ingest context and expect it to match `src/claude_knowledge_mvp/prompts/ingest/prepare_output_schema.json`.
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
```

Update `src/claude_knowledge_mvp/runtime/ingest.py` imports/constants like this:

```python
from claude_knowledge_mvp.prompts.paths import (
    INGEST_PREPARE_OUTPUT_SCHEMA_PATH,
    INGEST_PROMPT_PATH,
)

PREPARE_OUTPUT_SCHEMA_PATH = INGEST_PREPARE_OUTPUT_SCHEMA_PATH
```

and replace:

```python
prompt_path = repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md"
```

with:

```python
prompt_path = repo_root / INGEST_PROMPT_PATH
```

Update `src/claude_knowledge_mvp/helpers/ingest_commit_helper.py` like this:

```python
from claude_knowledge_mvp.prompts.paths import INGEST_MUTATION_SET_SCHEMA_PATH

MUTATION_SET_SCHEMA_PATH = INGEST_MUTATION_SET_SCHEMA_PATH
```

Create the two schema files by copying the current JSON verbatim into:
- `src/claude_knowledge_mvp/prompts/ingest/prepare_output_schema.json`
- `src/claude_knowledge_mvp/prompts/ingest/mutation_set_schema.json`

- [ ] **Step 4: Run the ingest tests to verify the moved assets are wired correctly**

Run:
```bash
pytest tests/unit/test_ingest_commit_helper.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the ingest asset split**

```bash
git add src/claude_knowledge_mvp/prompts/ingest src/claude_knowledge_mvp/runtime/ingest.py src/claude_knowledge_mvp/helpers/ingest_commit_helper.py tests/unit/test_ingest_commit_helper.py
git commit -m "refactor: move ingest prompt assets into scoped folder"
```

---

### Task 3: Move query assets under `prompts/query` and update query runtime

**Files:**
- Create: `src/claude_knowledge_mvp/prompts/query/prompt.md`
- Modify: `src/claude_knowledge_mvp/runtime/query.py`
- Modify: `tests/unit/test_query_runtime.py`

- [ ] **Step 1: Update the query fixture to write the prompt into the new query folder**

Replace the current fixture setup with the shared path constant.

```python
from claude_knowledge_mvp.prompts.paths import QUERY_PROMPT_PATH


prompt_path = query_repo / QUERY_PROMPT_PATH
prompt_path.parent.mkdir(parents=True, exist_ok=True)
prompt_path.write_text("Answer with citations and Raw chunks.\n", encoding="utf-8")
```

- [ ] **Step 2: Run the query payload test to verify the old runtime path fails**

Run:
```bash
pytest tests/unit/test_query_runtime.py::test_prepare_query_payload_includes_prompt_and_page_context -q
```

Expected: FAIL with `ValueError: query prompt pack is required` because `runtime/query.py` still reads `prompts/query.md`.

- [ ] **Step 3: Move the query prompt and update the runtime import/path**

Create `src/claude_knowledge_mvp/prompts/query/prompt.md` with the current prompt text verbatim:

```md
# xk-query Prompt Pack

You are answering one repository-local knowledge question from a local markdown knowledge base.

## Instruction priority

You must follow `constitution_text` as the highest-priority policy for this query.
If any instruction in this prompt conflicts with the Constitution, follow the Constitution.
Treat the provided query context as the only allowed knowledge source.

## Source of truth

Treat the following as authoritative inputs:
- `question`
- `constitution_text`
- `global_index_excerpt`
- `global_link_excerpt`
- `matched_pages`
- `linked_pages`

For factual content, the provided WIKI page excerpts and their listed source chunk ids are the only source of truth.

## Query boundary

- Do not introduce outside facts or background knowledge.
- Prefer matched pages first.
- Use linked pages only as one-hop supporting context.
- If evidence is weak or missing, say so explicitly.

## Output rules

Return markdown.
Keep the answer lightly structured unless the user asked for a formal format.
Always include:
- a direct answer
- supporting WIKI page references
- the Raw chunk references that back those WIKI pages
```

Update `src/claude_knowledge_mvp/runtime/query.py` to import the constant and replace the hard-coded path:

```python
from claude_knowledge_mvp.prompts.paths import QUERY_PROMPT_PATH

prompt_path = repo_root / QUERY_PROMPT_PATH
```

- [ ] **Step 4: Run the query tests to verify the new folder layout works**

Run:
```bash
pytest tests/unit/test_query_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the query asset split**

```bash
git add src/claude_knowledge_mvp/prompts/query src/claude_knowledge_mvp/runtime/query.py tests/unit/test_query_runtime.py
git commit -m "refactor: move query prompt into scoped folder"
```

---

### Task 4: Move check assets under `prompts/check` and update check runtime

**Files:**
- Create: `src/claude_knowledge_mvp/prompts/check/phase1.md`
- Create: `src/claude_knowledge_mvp/prompts/check/phase2.md`
- Modify: `src/claude_knowledge_mvp/runtime/check.py`
- Modify: `tests/unit/test_check_runtime.py`

- [ ] **Step 1: Update the check fixture to write phase prompts into the new check folder**

Replace the current fixture setup with the shared path constants.

```python
from claude_knowledge_mvp.prompts.paths import CHECK_PHASE1_PROMPT_PATH, CHECK_PHASE2_PROMPT_PATH


phase1_path = repo_root / CHECK_PHASE1_PROMPT_PATH
phase1_path.parent.mkdir(parents=True, exist_ok=True)
phase1_path.write_text("Phase1 prompt.\n", encoding="utf-8")

phase2_path = repo_root / CHECK_PHASE2_PROMPT_PATH
phase2_path.parent.mkdir(parents=True, exist_ok=True)
phase2_path.write_text("Phase2 prompt.\n", encoding="utf-8")
```

- [ ] **Step 2: Run one check test to verify the old paths fail**

Run:
```bash
pytest tests/unit/test_check_runtime.py::test_prepare_check_payload_includes_declared_citations_and_candidate_laws -q
```

Expected: FAIL with `ValueError: phase1 prompt pack is required` because `runtime/check.py` still reads flat prompt paths.

- [ ] **Step 3: Move the check prompts and update the runtime imports/paths**

Create `src/claude_knowledge_mvp/prompts/check/phase1.md` with the current phase1 prompt text verbatim:

```md
# xk-check Phase 1 Prompt Pack

You are auditing one repository-local wiki page against only its declared evidence boundary.

## Instruction priority

You must follow `constitution_text` as the highest-priority policy for this audit.
If any instruction in this prompt conflicts with the Constitution, follow the Constitution.
Treat the provided phase1 context as the only allowed knowledge source.

## Source of truth

Treat the following as authoritative inputs:
- `target`
- `page_content`
- `declared_citations`
- `constitution_text`
- `candidate_laws`
- `prompt_text`

Do not use outside facts, unstated Raw content, linked wiki pages, or prior knowledge.

## Audit boundary

- Only inspect the target wiki page and the citations explicitly declared in that page.
- If evidence is missing, damaged, or insufficient, say so explicitly.
- Do not repair the page.
- Do not suggest edits.
- Do not judge INDEX or LINK in phase1.

## Findings allowed in phase1
- `无来源陈述`
- `过强结论`
- `证据受限`

## Output contract

Return one JSON object with:
- `status`: `passed` or `findings`
- `summary`: short summary string
- `findings`: array of finding objects
- `evidence_limits`: array of strings
```

Create `src/claude_knowledge_mvp/prompts/check/phase2.md` with the current phase2 prompt text verbatim:

```md
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
```

Update `src/claude_knowledge_mvp/runtime/check.py` imports and path use like this:

```python
from claude_knowledge_mvp.prompts.paths import CHECK_PHASE1_PROMPT_PATH, CHECK_PHASE2_PROMPT_PATH
```

Then replace:

```python
repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "check_phase1.md"
repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "check_phase2.md"
```

with:

```python
repo_root / CHECK_PHASE1_PROMPT_PATH
repo_root / CHECK_PHASE2_PROMPT_PATH
```

- [ ] **Step 4: Run the check tests to verify the new folder layout works**

Run:
```bash
pytest tests/unit/test_check_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the check asset split**

```bash
git add src/claude_knowledge_mvp/prompts/check src/claude_knowledge_mvp/runtime/check.py tests/unit/test_check_runtime.py
git commit -m "refactor: move check prompts into scoped folder"
```

---

### Task 5: Remove flat prompt asset usage and run the full targeted regression suite

**Files:**
- Modify: `src/claude_knowledge_mvp/prompts/ingest.md` (delete)
- Modify: `src/claude_knowledge_mvp/prompts/query.md` (delete)
- Modify: `src/claude_knowledge_mvp/prompts/check_phase1.md` (delete)
- Modify: `src/claude_knowledge_mvp/prompts/check_phase2.md` (delete)
- Modify: `src/claude_knowledge_mvp/prompts/prepare_output_schema.json` (delete)
- Modify: `src/claude_knowledge_mvp/prompts/mutation_set_schema.json` (delete)

- [ ] **Step 1: Delete the flat files after all runtime references are migrated**

Delete these files:

```text
src/claude_knowledge_mvp/prompts/ingest.md
src/claude_knowledge_mvp/prompts/query.md
src/claude_knowledge_mvp/prompts/check_phase1.md
src/claude_knowledge_mvp/prompts/check_phase2.md
src/claude_knowledge_mvp/prompts/prepare_output_schema.json
src/claude_knowledge_mvp/prompts/mutation_set_schema.json
```

- [ ] **Step 2: Run a repo-wide search to confirm no code still references the flat layout**

Run:
```bash
rg -n "prompts/(ingest\.md|query\.md|check_phase1\.md|check_phase2\.md|prepare_output_schema\.json|mutation_set_schema\.json)" src tests
```

Expected: no matches.

- [ ] **Step 3: Run the full targeted regression suite**

Run:
```bash
pytest tests/unit/test_ingest_commit_helper.py tests/unit/test_query_runtime.py tests/unit/test_check_runtime.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit the cleanup and verification**

```bash
git add src/claude_knowledge_mvp/prompts src/claude_knowledge_mvp/runtime src/claude_knowledge_mvp/helpers tests/unit
git commit -m "refactor: scope prompt packs by operation"
```

---

## Self-Review

### Coverage against the request
- Split prompts into three operation-specific folders: covered by Tasks 2, 3, and 4.
- Keep code organized as prompt packs grow: covered by Task 1 path registry and the folder move tasks.
- Avoid forcing ingest/query/check into one shared prompt blob: covered by deleting the flat prompt layout in Task 5.
- Keep current behavior stable while reorganizing: covered by the existing runtime regression tests in Tasks 2-5.

### Placeholder scan
- No `TODO`, `TBD`, or “implement later” markers remain.
- Every code-changing step includes explicit code or exact file moves.
- Every verification step includes the exact command and expected result.

### Type consistency
- Path constant names are used consistently across tasks:
  - `INGEST_PROMPT_PATH`
  - `INGEST_PREPARE_OUTPUT_SCHEMA_PATH`
  - `INGEST_MUTATION_SET_SCHEMA_PATH`
  - `QUERY_PROMPT_PATH`
  - `CHECK_PHASE1_PROMPT_PATH`
  - `CHECK_PHASE2_PROMPT_PATH`

Plan complete and saved to `docs/superpowers/plans/2026-05-15-prompt-pack-folder-split.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
