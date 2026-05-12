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

The user should not need to manually run `prepare`, save a mutation file, or call `commit`.

## Execution Rules

1. Validate that `$ARGUMENTS` is a single repository-relative path under `RAW/`.
2. Use the direct ingest runtime path, not the manual prepare/model/commit walkthrough.
3. Reuse the existing runtime/helper validation and atomic commit flow.
4. Report only the ingest result summary:
   - committed or failed
   - written paths
   - structured diagnostics when failed
5. Do not ask the user to manage `PYTHONPATH`, intermediate JSON files, or internal helper details unless they explicitly ask for debugging guidance.

## Debug Note

Low-level `prepare` and `commit` CLI commands are internal/debug interfaces, not the primary user workflow.
