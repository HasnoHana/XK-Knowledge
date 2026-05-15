from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(slots=True)
class CheckTarget:
    wiki_path: str
    page_id: str
    wiki_type: str


@dataclass(slots=True)
class DeclaredRawCitation:
    chunk_id: str
    raw_path: str
    locator: str
    raw_excerpt: str
    parse_status: str


@dataclass(slots=True)
class Phase1CheckContext:
    target: CheckTarget
    page_content: str
    declared_citations: list[DeclaredRawCitation]
    constitution_text: str
    candidate_laws: dict[str, str]
    prompt_text: str


@dataclass(slots=True)
class CheckFinding:
    phase: str
    kind: str
    location: str
    message: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Phase2GlobalContext:
    phase1_context: Phase1CheckContext
    phase1_findings: list[CheckFinding]
    global_index_excerpt: str
    global_link_excerpt: str
    available_page_ids: list[str]
    prompt_text: str


@dataclass(slots=True)
class CheckReport:
    target: CheckTarget
    phase1_findings: list[CheckFinding]
    phase2_findings: list[CheckFinding]
    evidence_limits: list[str]
    status: str
    report_markdown: str
