---
description: Ingest one repository-local RAW markdown file into the knowledge base through the direct xk-ingest flow.
---

## User Input

```text
$ARGUMENTS
```

You MUST treat `$ARGUMENTS` as exactly one repository-relative path under `RAW/`.

## Goal

Provide a direct command UX:

```text
/xk-ingest RAW/article/transformer-core.md
```

This project relies on the active Claude / Claude Code session to produce the mutation content for ingest. The repository-local runtime/helper is only responsible for local prepare / parse / validate / commit steps and must not actively call Claude internally.

The user should not need to manually run `prepare`, save a mutation file, or call `commit`.

## Execution Rules

1. Validate that `$ARGUMENTS` is a single repository-relative path under `RAW/`.
2. In the current Claude session, assemble the ingest payload, generate exactly one `KnowledgeMutationSet` JSON object that satisfies `src/claude_knowledge_mvp/prompts/mutation_set_schema.json`, and hand that mutation to the local runtime via the direct `run` path.
3. Reuse the existing runtime/helper validation and atomic commit flow; if you materialize a temporary mutation JSON file for the bridge, keep it internal to the command workflow rather than exposing a manual prepare/commit experience to the user.
4. Report only the ingest result summary:
   - committed or failed
   - written paths
   - structured diagnostics when failed
5. Do not ask the user to manage `PYTHONPATH`, intermediate JSON files, or internal helper details unless they explicitly ask for debugging guidance.

## Debug Note

Low-level `prepare` and `commit` CLI commands are internal/debug interfaces, not the primary user workflow.
