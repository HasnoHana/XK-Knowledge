from __future__ import annotations

from pathlib import Path

PROMPTS_ROOT = Path("src") / "claude_knowledge_mvp" / "prompts"

INGEST_PROMPTS_DIR = PROMPTS_ROOT / "ingest"
QUERY_PROMPTS_DIR = PROMPTS_ROOT / "query"
CHECK_PROMPTS_DIR = PROMPTS_ROOT / "check"

INGEST_PROMPT_PATH = INGEST_PROMPTS_DIR / "prompt.md"
INGEST_PREPARE_OUTPUT_SCHEMA_PATH = INGEST_PROMPTS_DIR / "prepare_output_schema.json"
INGEST_MUTATION_SET_SCHEMA_PATH = INGEST_PROMPTS_DIR / "mutation_set_schema.json"

QUERY_PROMPT_PATH = QUERY_PROMPTS_DIR / "prompt.md"

CHECK_PHASE1_PROMPT_PATH = CHECK_PROMPTS_DIR / "phase1.md"
CHECK_PHASE2_PROMPT_PATH = CHECK_PROMPTS_DIR / "phase2.md"


def resolve_repo_prompt_path(repo_root: Path, prompt_path: Path) -> Path:
    return repo_root / prompt_path


def read_repo_prompt_text(repo_root: Path, prompt_path: Path, *, missing_message: str) -> str:
    resolved_path = resolve_repo_prompt_path(repo_root=repo_root, prompt_path=prompt_path)
    if not resolved_path.exists() or resolved_path.is_dir():
        raise ValueError(missing_message)
    return resolved_path.read_text(encoding="utf-8")
