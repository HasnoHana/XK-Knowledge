from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RawDocument:
    raw_id: str
    source_path: Path
    title: str
    ingest_allowed: bool
    content: str


@dataclass(slots=True)
class SkillRuntimeContext:
    repo_root: Path
    raw_document: RawDocument
    constitution_text: str
    candidate_laws: dict[str, str]
    global_index_excerpt: str
    global_link_excerpt: str
    prompt_pack: str


@dataclass(slots=True)
class HelperCommitResult:
    status: str
    written_paths: list[str]
    rolled_back: bool
    diagnostics: list[str]
    error_code: str | None = None
    error_stage: str | None = None
    retryable: bool = False
