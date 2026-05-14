---
name: xk-query
description: Use when the user asks what the local repository knowledge base says about a topic. Start from WIKI/INDEX.md, optionally use one-hop links from WIKI/LINK.md, read relevant WIKI pages, and answer with citations plus Raw chunk references.
---

# xk-query

## Overview
Use the local knowledge base as the source of truth. Read `WIKI/INDEX.md` first, optionally expand one hop through `WIKI/LINK.md`, then read the relevant WIKI pages and answer briefly with citations and Raw chunk references.

## When to Use
- The user is asking what the knowledge base says about a topic
- The answer should come from local WIKI pages, not general model knowledge
- The question can be narrowed using `INDEX.md` and optionally expanded one hop via `LINK.md`
- The user asks naturally in conversation; no explicit command is required
- Typical prompts: "what does the knowledge base say about X?", "summarize X from the repo wiki", "according to the local wiki, ..."

Do not use this skill for ingesting RAW documents or editing the knowledge base.

## Core Pattern
1. Parse the user question.
2. Read `WIKI/INDEX.md` to find the most relevant page candidates.
3. Read `WIKI/LINK.md` only to expand one hop of related context when useful.
4. Read the relevant WIKI pages.
5. Answer using the WIKI content.
6. Include supporting citations and the corresponding Raw chunk references.
7. If evidence is missing or weak, say so explicitly.

## Output Rules
- Prefer a direct answer first.
- Keep the answer lightly structured unless the user asks for a formal format.
- Include the WIKI page references that support the answer.
- Include the Raw chunk references that back the cited WIKI content.
- Do not invent knowledge outside the repository.
- Do not pretend weak evidence is conclusive.

## Common Mistakes
- Skipping `INDEX.md` and searching everything blindly
- Expanding beyond one hop in `LINK.md`
- Answering from model background knowledge instead of repository evidence
- Returning an answer without citations or Raw chunk support
- Treating query like ingest and over-structuring the output
