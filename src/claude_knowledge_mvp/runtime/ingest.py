from __future__ import annotations

import json
import os
from pathlib import Path

from claude_knowledge_mvp.domain.models import HelperCommitResult, RawDocument, SkillRuntimeContext
from claude_knowledge_mvp.helpers.ingest_commit_helper import commit_mutation_set, validate_mutation_set

PREPARE_OUTPUT_SCHEMA_NAME = "xk-ingest-prepare-output"
PREPARE_OUTPUT_SCHEMA_VERSION = "1.0"
PREPARE_OUTPUT_SCHEMA_PATH = Path("src") / "claude_knowledge_mvp" / "prompts" / "prepare_output_schema.json"
EXPECTED_OUTPUT_KEYS = [
    "raw_chunks",
    "wiki_page_draft",
    "index_draft",
    "link_draft",
    "log_draft",
    "completeness_report",
]


def build_context(repo_root: Path, raw_relative_path: str) -> SkillRuntimeContext:
    raw_path = repo_root / raw_relative_path
    if not raw_path.exists() or raw_path.is_dir():
        raise ValueError("raw file is missing or unreadable")
    if Path(raw_relative_path).parts[0] != "RAW":
        raise ValueError("raw file must live under RAW/")

    constitution_path = repo_root / "CONSTITUTION.md"
    prompt_path = repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md"
    if not constitution_path.exists():
        raise ValueError("CONSTITUTION.md is required")
    if not prompt_path.exists():
        raise ValueError("ingest prompt pack is required")

    raw_document = RawDocument(
        raw_id=raw_path.stem,
        source_path=raw_path,
        title=raw_path.stem.replace("-", " ").title(),
        ingest_allowed=True,
        content=raw_path.read_text(encoding="utf-8"),
    )
    return SkillRuntimeContext(
        repo_root=repo_root,
        raw_document=raw_document,
        constitution_text=constitution_path.read_text(encoding="utf-8"),
        candidate_laws=_load_candidate_laws(repo_root),
        global_index_excerpt=_read_optional_file(repo_root / "WIKI" / "INDEX.md"),
        global_link_excerpt=_read_optional_file(repo_root / "WIKI" / "LINK.md"),
        prompt_pack=prompt_path.read_text(encoding="utf-8"),
    )


def prepare_ingest_payload(repo_root: Path, raw_relative_path: str) -> dict:
    context = build_context(repo_root=repo_root, raw_relative_path=raw_relative_path)
    return {
        "schema_name": PREPARE_OUTPUT_SCHEMA_NAME,
        "schema_version": PREPARE_OUTPUT_SCHEMA_VERSION,
        "raw_document": {
            "raw_id": context.raw_document.raw_id,
            "source_path": raw_relative_path,
            "title": context.raw_document.title,
            "content": context.raw_document.content,
        },
        "constitution_text": context.constitution_text,
        "candidate_laws": context.candidate_laws,
        "global_index_excerpt": context.global_index_excerpt,
        "global_link_excerpt": context.global_link_excerpt,
        "prompt_pack": context.prompt_pack,
        "expected_output_keys": EXPECTED_OUTPUT_KEYS,
    }


def commit_ingest_artifacts(repo_root: Path, mutation_json_path: Path):
    mutation = json.loads(mutation_json_path.read_text(encoding="utf-8"))
    try:
        validated = validate_mutation_set(mutation)
    except ValueError as exc:
        return _build_failed_commit_result(
            error_code="validation_error",
            error_stage="validate_mutation_set",
            diagnostics=[str(exc)],
            retryable=False,
        )

    try:
        return commit_mutation_set(repo_root=repo_root, mutation=validated)
    except RuntimeError as exc:
        return _build_failed_commit_result(
            error_code="commit_error",
            error_stage="commit_mutation_set",
            diagnostics=[str(exc)],
            retryable=True,
        )


def execute_ingest(
    repo_root: Path,
    raw_relative_path: str,
    mutation_json_path: Path | None = None,
    mutation_generator=None,
) -> HelperCommitResult:
    prepared = _prepare_and_validate_mutation(
        repo_root=repo_root,
        raw_relative_path=raw_relative_path,
        mutation_json_path=mutation_json_path,
        mutation_generator=mutation_generator,
    )
    if isinstance(prepared, HelperCommitResult):
        return prepared

    try:
        return commit_mutation_set(repo_root=repo_root, mutation=prepared)
    except RuntimeError as exc:
        return _build_failed_commit_result(
            error_code="commit_error",
            error_stage="commit_mutation_set",
            diagnostics=[str(exc)],
            retryable=True,
        )


def execute_ingest_debug(
    repo_root: Path,
    raw_relative_path: str,
    mutation_json_path: Path | None = None,
    mutation_generator=None,
) -> dict:
    prepared = _prepare_and_validate_mutation(
        repo_root=repo_root,
        raw_relative_path=raw_relative_path,
        mutation_json_path=mutation_json_path,
        mutation_generator=mutation_generator,
    )
    if isinstance(prepared, HelperCommitResult):
        return _result_to_dict(prepared)

    try:
        result = commit_mutation_set(repo_root=repo_root, mutation=prepared)
    except RuntimeError as exc:
        result = _build_failed_commit_result(
            error_code="commit_error",
            error_stage="commit_mutation_set",
            diagnostics=[str(exc)],
            retryable=True,
        )
        return _result_to_dict(result) | {"mutation": prepared}

    return _result_to_dict(result) | {"mutation": prepared}


def generate_demo_mutation(context: SkillRuntimeContext) -> dict:
    body = context.raw_document.content.strip().splitlines()
    content = "\n".join(line for line in body if line.strip())
    slug = context.raw_document.source_path.stem
    title = context.raw_document.title
    chunk_id = f"{context.raw_document.raw_id}-chunk-1"
    return {
        "raw_chunks": [
            {
                "chunk_id": chunk_id,
                "raw_id": context.raw_document.raw_id,
                "locator": "full-document",
                "text": content,
                "order": 1,
            }
        ],
        "wiki_page_draft": {
            "page_id": slug,
            "slug": slug,
            "title": title,
            "wiki_type": "notes",
            "summary": content.split(". ")[0][:160],
            "body_sections": [
                {
                    "heading": "Extracted Knowledge",
                    "content": content,
                }
            ],
            "source_chunk_ids": [chunk_id],
            "status": "active",
        },
        "index_draft": {
            "entries": [
                {
                    "scope": "global",
                    "type_name": "notes",
                    "topic": title.lower(),
                    "aliases": [slug],
                    "page_id": slug,
                    "rank": 1,
                }
            ]
        },
        "link_draft": {
            "entries": [
                {
                    "scope": "global",
                    "type_name": "notes",
                    "source_page_id": slug,
                    "target_page_id": slug,
                    "relation_type": "related",
                    "note": "Demo ingest self-link",
                }
            ]
        },
        "log_draft": {
            "log_date": "2026-05-12",
            "action": "ingest",
            "page_ids": [slug],
            "raw_id": context.raw_document.raw_id,
            "message": f"Ingested {title}.",
        },
        "completeness_report": {
            "summary": "Covered the complete raw file for MVP ingest.",
            "covered_chunk_ids": [chunk_id],
        },
    }


def run_ingest(repo_root: Path, raw_relative_path: str, mutation_generator=None):
    context = build_context(repo_root=repo_root, raw_relative_path=raw_relative_path)
    generator = mutation_generator or generate_demo_mutation
    mutation = validate_mutation_set(generator(context))
    return commit_mutation_set(repo_root=repo_root, mutation=mutation)


def _prepare_and_validate_mutation(
    *,
    repo_root: Path,
    raw_relative_path: str,
    mutation_json_path: Path | None = None,
    mutation_generator=None,
) -> dict | HelperCommitResult:
    try:
        prepare_payload = prepare_ingest_payload(repo_root=repo_root, raw_relative_path=raw_relative_path)
    except ValueError as exc:
        return _build_failed_commit_result(
            error_code="input_error",
            error_stage="prepare_ingest_payload",
            diagnostics=[str(exc)],
            retryable=False,
        )

    if mutation_json_path is not None:
        try:
            raw_mutation = mutation_json_path.read_text(encoding="utf-8")
        except OSError as exc:
            return _build_failed_commit_result(
                error_code="session_bridge_error",
                error_stage="read_mutation_json",
                diagnostics=[str(exc)],
                retryable=False,
            )
    else:
        generator = mutation_generator or generate_mutation_with_claude
        try:
            raw_mutation = generator(prepare_payload)
        except ValueError as exc:
            return _build_failed_commit_result(
                error_code="session_bridge_error",
                error_stage="generate_mutation_with_claude",
                diagnostics=[str(exc)],
                retryable=False,
            )
    mutation = _parse_model_output(raw_mutation)
    if isinstance(mutation, HelperCommitResult):
        return mutation

    try:
        return validate_mutation_set(mutation)
    except ValueError as exc:
        return _build_failed_commit_result(
            error_code="validation_error",
            error_stage="validate_mutation_set",
            diagnostics=[str(exc)],
            retryable=False,
        )


def generate_mutation_with_claude(prepare_payload: dict) -> dict:
    mutation_json = os.environ.get("XK_INGEST_MUTATION_JSON")
    if not mutation_json:
        raise ValueError(
            "Claude session did not supply XK_INGEST_MUTATION_JSON for the local ingest runtime bridge"
        )
    return json.loads(mutation_json)


def _parse_model_output(raw_mutation: dict | str) -> dict | HelperCommitResult:
    if isinstance(raw_mutation, dict):
        return raw_mutation

    if isinstance(raw_mutation, str):
        try:
            parsed = json.loads(raw_mutation)
        except json.JSONDecodeError as exc:
            return _build_failed_commit_result(
                error_code="model_output_error",
                error_stage="parse_model_output",
                diagnostics=[f"model output is not valid JSON: {exc.msg}"],
                retryable=True,
            )
        if not isinstance(parsed, dict):
            return _build_failed_commit_result(
                error_code="model_output_error",
                error_stage="parse_model_output",
                diagnostics=["model output must decode to one JSON object"],
                retryable=True,
            )
        return parsed

    return _build_failed_commit_result(
        error_code="model_output_error",
        error_stage="parse_model_output",
        diagnostics=["model output must be a dict or JSON string"],
        retryable=True,
    )


def _result_to_dict(result: HelperCommitResult) -> dict:
    return {
        "status": result.status,
        "written_paths": result.written_paths,
        "rolled_back": result.rolled_back,
        "diagnostics": result.diagnostics,
        "error_code": result.error_code,
        "error_stage": result.error_stage,
        "retryable": result.retryable,
    }


def _build_failed_commit_result(
    *,
    error_code: str,
    error_stage: str,
    diagnostics: list[str],
    retryable: bool,
) -> HelperCommitResult:
    return HelperCommitResult(
        status="failed",
        written_paths=[],
        rolled_back=False,
        diagnostics=diagnostics,
        error_code=error_code,
        error_stage=error_stage,
        retryable=retryable,
    )


def _load_candidate_laws(repo_root: Path) -> dict[str, str]:
    wiki_root = repo_root / "WIKI"
    if not wiki_root.exists():
        return {}

    candidate_laws: dict[str, str] = {}
    for laws_path in sorted(wiki_root.glob("*/LAWS.md")):
        candidate_laws[laws_path.parent.name] = laws_path.read_text(encoding="utf-8")
    return candidate_laws


def _read_optional_file(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8")
