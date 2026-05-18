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
