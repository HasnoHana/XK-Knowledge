---
description: Debug one repository-local RAW markdown ingest and return the mutation payload alongside the ingest result.
---

## User Input

```text
$ARGUMENTS
```

You MUST treat `$ARGUMENTS` as exactly one repository-relative path under `RAW/`.

## Goal

Provide a debug ingest UX:

```text
/xk-ingest-debug RAW/article/transformer-core.md
```

This command is for inspecting the generated mutation payload together with the final ingest result.

## Execution Rules

1. Validate that `$ARGUMENTS` is a single repository-relative path under `RAW/`.
2. Use the debug ingest runtime path.
3. Return both:
   - the ingest result summary
   - the `mutation` object
4. Reuse the existing runtime/helper validation and atomic commit flow.
5. Keep `prepare` and `commit` as internal/debug plumbing only; do not redirect the user into the manual workflow.
