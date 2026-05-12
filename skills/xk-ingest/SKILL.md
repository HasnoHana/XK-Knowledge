---
name: xk-ingest
description: Use when ingesting one repository-local RAW markdown file into the knowledge base through a direct /xk-ingest command flow.
---

# xk-ingest

## Overview
`/xk-ingest` is the user-facing ingest entrypoint.

Give it exactly one repository-relative file under `RAW/`, and the runtime will do the rest internally:
- load ingest context
- generate one mutation set
- validate citations and completeness
- atomically commit wiki/index/link/log outputs

## When to Use
- You want to ingest one local markdown file under `RAW/`
- You want the direct command UX, not the internal prepare/commit workflow
- You want the final result as a success/failure summary instead of runtime plumbing

Do not use this skill for batch ingest, query, or check flows.

## User Input
Pass exactly one repository-relative RAW path:

```text
/xk-ingest RAW/article/transformer-core.md
```

## Expected Flow
1. Read the RAW file from `RAW/...`
2. Load `CONSTITUTION.md`
3. Load candidate `WIKI/<type>/LAWS.md`
4. Load current `WIKI/INDEX.md` and `WIKI/LINK.md` context
5. Use the formal ingest prompt pack and schema contracts
6. Generate one mutation set
7. Validate and atomically commit page / index / link / log
8. Report committed or failed status to the user

## Success Output
Report:
- whether ingest committed or failed
- which files were written
- structured diagnostics when it fails

## Internal Notes
The direct user flow should not require the user to manually run:
- `prepare`
- `commit`
- `PYTHONPATH=...`
- intermediate `mutation.json` files

Those remain internal/debug surfaces only.

## Common Mistakes
- Passing a file outside `RAW/`
- Passing more than one file
- Exposing prepare/model/commit internals as the main user workflow
- Returning uncited knowledge in the mutation output
- Writing files directly instead of going through the runtime commit path
