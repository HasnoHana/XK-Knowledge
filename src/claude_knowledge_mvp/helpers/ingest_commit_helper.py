from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

from claude_knowledge_mvp.domain.models import HelperCommitResult

MUTATION_SET_SCHEMA_NAME = "xk-ingest-mutation-set"
MUTATION_SET_SCHEMA_VERSION = "1.0"
MUTATION_SET_SCHEMA_PATH = Path("src") / "claude_knowledge_mvp" / "prompts" / "mutation_set_schema.json"
REQUIRED_MUTATION_KEYS = {
    "schema_name",
    "schema_version",
    "raw_chunks",
    "wiki_page_draft",
    "index_draft",
    "link_draft",
    "log_draft",
    "completeness_report",
}


def validate_mutation_set(mutation: dict) -> dict:
    missing = REQUIRED_MUTATION_KEYS - mutation.keys()
    if missing:
        raise ValueError(f"missing mutation keys: {sorted(missing)}")

    if mutation["schema_name"] != MUTATION_SET_SCHEMA_NAME:
        raise ValueError("schema_name must match mutation set schema")
    if mutation["schema_version"] != MUTATION_SET_SCHEMA_VERSION:
        raise ValueError("schema_version must match mutation set schema")

    raw_chunks = mutation["raw_chunks"]
    if not raw_chunks:
        raise ValueError("raw_chunks must not be empty")

    chunk_ids = {chunk["chunk_id"] for chunk in raw_chunks}
    if not chunk_ids:
        raise ValueError("raw_chunks must include chunk_id values")

    wiki_page = mutation["wiki_page_draft"]
    source_chunk_ids = wiki_page.get("source_chunk_ids") or []
    if not source_chunk_ids:
        raise ValueError("wiki_page_draft.source_chunk_ids must not be empty")

    if any(chunk_id not in chunk_ids for chunk_id in source_chunk_ids):
        raise ValueError("wiki_page_draft.source_chunk_ids must reference raw_chunks")

    completeness = mutation["completeness_report"]
    if not completeness or not completeness.get("covered_chunk_ids"):
        raise ValueError("completeness_report must include covered_chunk_ids")

    return mutation


def commit_mutation_set(repo_root: Path, mutation: dict, fail_on_relative_path: str | None = None) -> HelperCommitResult:
    wiki_page = mutation["wiki_page_draft"]
    page_relative = Path("WIKI") / wiki_page["wiki_type"] / "pages" / f"{wiki_page['slug']}.md"
    index_relative = Path("WIKI") / "INDEX.md"
    link_relative = Path("WIKI") / "LINK.md"
    log_relative = Path("LOG") / f"{mutation['log_draft']['log_date']}.md"

    writes = {
        page_relative: _render_wiki_page(mutation),
        index_relative: _render_index(mutation),
        link_relative: _render_link(mutation),
        log_relative: _render_log(mutation),
    }

    backups: list[tuple[Path, Path | None]] = []
    created_dirs: set[Path] = set()
    written_paths: list[str] = []

    try:
        for relative_path, content in writes.items():
            destination = repo_root / relative_path
            if not destination.parent.exists():
                missing_directories = [
                    parent for parent in reversed(destination.parents) if parent != repo_root and not parent.exists()
                ]
                destination.parent.mkdir(parents=True, exist_ok=True)
                created_dirs.update(missing_directories)

            backup_path = None
            if destination.exists():
                backup_path = destination.with_suffix(destination.suffix + ".bak")
                shutil.copy2(destination, backup_path)
            backups.append((destination, backup_path))

            if fail_on_relative_path and relative_path.as_posix() == fail_on_relative_path:
                raise RuntimeError("forced write failure")

            destination.write_text(content, encoding="utf-8")
            written_paths.append(relative_path.as_posix())

        return HelperCommitResult(
            status="committed",
            written_paths=written_paths,
            rolled_back=False,
            diagnostics=["mutation set committed"],
        )
    except Exception as exc:
        for destination, backup_path in reversed(backups):
            if backup_path and backup_path.exists():
                shutil.move(str(backup_path), str(destination))
            elif destination.exists():
                destination.unlink()
        for directory in sorted(created_dirs, key=lambda path: len(path.parts), reverse=True):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        raise RuntimeError(str(exc)) from exc
    finally:
        for _, backup_path in backups:
            if backup_path and backup_path.exists():
                backup_path.unlink()


def _render_wiki_page(mutation: dict) -> str:
    wiki_page = mutation["wiki_page_draft"]
    sections = "\n\n".join(
        f"## {section['heading']}\n{section['content']}" for section in wiki_page["body_sections"]
    )
    citations = "\n".join(f"- {chunk_id}" for chunk_id in wiki_page["source_chunk_ids"])
    return (
        f"# {wiki_page['title']}\n\n"
        f"> Summary: {wiki_page['summary']}\n\n"
        f"{sections}\n\n"
        f"## Sources\n{citations}\n"
    )


def _render_index(mutation: dict) -> str:
    lines = ["# Index"]
    for entry in mutation["index_draft"]["entries"]:
        lines.append(f"- {entry['topic']} -> {entry['page_id']}")
    return "\n".join(lines) + "\n"


def _render_link(mutation: dict) -> str:
    lines = ["# Link Graph"]
    for entry in mutation["link_draft"]["entries"]:
        lines.append(
            f"- {entry['source_page_id']} -[{entry['relation_type']}]-> {entry['target_page_id']} ({entry['note']})"
        )
    return "\n".join(lines) + "\n"


def _render_log(mutation: dict) -> str:
    log = mutation["log_draft"]
    return (
        f"# {log['log_date']}\n\n"
        f"- action: {log['action']}\n"
        f"- raw_id: {log['raw_id']}\n"
        f"- page_ids: {', '.join(log['page_ids'])}\n"
        f"- message: {log['message']}\n"
    )


def helper_result_to_dict(result: HelperCommitResult) -> dict:
    return asdict(result)


def mutation_to_json(mutation: dict) -> str:
    return json.dumps(mutation, ensure_ascii=False, indent=2)
