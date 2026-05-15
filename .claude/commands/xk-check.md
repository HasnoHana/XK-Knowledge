---
description: Audit one repository-local wiki markdown page through the direct xk-check flow.
---

## User Input

```text
$ARGUMENTS
```

You MUST treat `$ARGUMENTS` as exactly one repository-relative path under `WIKI/*/pages/*.md`.

## Goal

Provide a direct command UX:

```text
/xk-check WIKI/notes/pages/post-query-containment-actions.md
```

This project relies on the active Claude / Claude Code session to complete the audit reasoning in the current conversation. The repository-local runtime is only responsible for local prepare, phase gating, parse, validate, and report shaping steps, and must not actively call Claude internally.

The user should not need to manually run `prepare`, manage phase payloads, or learn a separate runtime workflow.

## Execution Rules

1. Validate that `$ARGUMENTS` is a single repository-relative path under `WIKI/*/pages/*.md`.
2. Reuse the unified check runtime for the full command flow: input validation, phase1 context assembly, phase gate enforcement, phase2 context assembly, structured result normalization, and markdown report shaping.
3. In the current Claude session, supply the phase judgments to that runtime flow in order: complete phase1 first, then phase2 only if phase1 completed.
4. Return only the check result summary and markdown report; keep any intermediate payloads or runtime details internal to the command.
5. Do not modify wiki pages, `WIKI/INDEX.md`, `WIKI/LINK.md`, `LOG/`, or any other repository file as part of `/xk-check`.
6. Keep `prepare` and runtime debug commands as internal tooling only; do not redirect the user into a manual workflow unless they explicitly ask for debugging guidance.

## Debug Note

Low-level runtime `prepare` or local CLI debug entry points are internal/debug interfaces, not the primary user workflow.
