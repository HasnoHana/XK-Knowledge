from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

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


def validate_commit_ready_mutation(mutation: dict) -> dict:
    wiki_page = mutation["wiki_page_draft"]
    title = wiki_page.get("title", "").strip()
    summary = wiki_page.get("summary", "").strip()
    if title and summary and summary == title:
        raise ValueError("wiki_page_draft.summary must add information beyond the title")

    body_sections = wiki_page.get("body_sections") or []
    if len(body_sections) == 1:
        only_section = body_sections[0]
        heading = str(only_section.get("heading", "")).strip().lower()
        if heading == "extracted knowledge":
            raise ValueError("wiki_page_draft.body_sections must reflect knowledge organization")

    allowed_page_ids = {
        wiki_page.get("page_id", "").strip(),
        wiki_page.get("slug", "").strip(),
    }
    allowed_page_ids = {page_id for page_id in allowed_page_ids if page_id}
    for entry in mutation.get("link_draft", {}).get("entries", []):
        source_page_id = str(entry.get("source_page_id", "")).strip()
        target_page_id = str(entry.get("target_page_id", "")).strip()
        if source_page_id not in allowed_page_ids or target_page_id not in allowed_page_ids:
            raise ValueError("link_draft must remain conservative and avoid speculative page expansion")

    return mutation


def commit_mutation_set(repo_root: Path, mutation: dict, fail_on_relative_path: str | None = None) -> HelperCommitResult:
    mutation = validate_commit_ready_mutation(mutation)
    wiki_page = mutation["wiki_page_draft"]
    page_relative = Path("WIKI") / wiki_page["wiki_type"] / "pages" / f"{wiki_page['slug']}.md"
    index_relative = Path("WIKI") / "INDEX.md"
    link_relative = Path("WIKI") / "LINK.md"
    log_relative = Path("LOG") / f"{mutation['log_draft']['log_date']}.md"

    index_existing = _read_optional_text(repo_root / index_relative)
    link_existing = _read_optional_text(repo_root / link_relative)
    log_existing = _read_optional_text(repo_root / log_relative)

    writes = {
        page_relative: _render_wiki_page(mutation),
        index_relative: _render_index(index_existing, mutation),
        link_relative: _render_link(link_existing, mutation),
        log_relative: _render_log(log_existing, mutation),
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


def _render_index(existing_text: str, mutation: dict) -> str:
    entries = _parse_index_entries(existing_text)
    for entry in mutation["index_draft"]["entries"]:
        key = (entry["topic"], entry["page_id"])
        entries[key] = entry
    lines = ["# Index"]
    for _, entry in sorted(entries.items(), key=lambda item: (item[1]["topic"], item[1]["page_id"])):
        lines.append(f"- {entry['topic']} -> {entry['page_id']}")
    return "\n".join(lines) + "\n"


def _render_link(existing_text: str, mutation: dict) -> str:
    entries = _parse_link_entries(existing_text)
    for entry in mutation["link_draft"]["entries"]:
        key = (
            entry["source_page_id"],
            entry["relation_type"],
            entry["target_page_id"],
            entry["note"],
        )
        entries[key] = entry
    lines = ["# Link Graph"]
    for _, entry in sorted(
        entries.items(),
        key=lambda item: (
            item[1]["source_page_id"],
            item[1]["relation_type"],
            item[1]["target_page_id"],
            item[1]["note"],
        ),
    ):
        lines.append(
            f"- {entry['source_page_id']} -[{entry['relation_type']}]-> {entry['target_page_id']} ({entry['note']})"
        )
    return "\n".join(lines) + "\n"


def _render_log(existing_text: str, mutation: dict) -> str:
    log = mutation["log_draft"]
    entries = _parse_log_entries(existing_text)
    entry = {
        "action": log["action"],
        "raw_id": log["raw_id"],
        "page_ids": list(log["page_ids"]),
        "message": log["message"],
    }
    key = (entry["action"], entry["raw_id"], tuple(entry["page_ids"]), entry["message"])
    if key not in {(
        existing["action"],
        existing["raw_id"],
        tuple(existing["page_ids"]),
        existing["message"],
    ) for existing in entries}:
        entries.append(entry)
    return _format_log(log["log_date"], entries)


def _read_optional_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_index_entries(text: str) -> dict[tuple[str, str], dict]:
    entries: dict[tuple[str, str], dict] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or " -> " not in line:
            continue
        topic, page_id = line[2:].split(" -> ", 1)
        entry = {"topic": topic.strip(), "page_id": page_id.strip()}
        entries[(entry["topic"], entry["page_id"])] = entry
    return entries


def _parse_link_entries(text: str) -> dict[tuple[str, str, str, str], dict]:
    entries: dict[tuple[str, str, str, str], dict] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or " -[" not in line or "]-> " not in line or not line.endswith(")"):
            continue
        source, remainder = line[2:].split(" -[", 1)
        relation, remainder = remainder.split("]-> ", 1)
        target, note = remainder.rsplit(" (", 1)
        entry = {
            "source_page_id": source.strip(),
            "relation_type": relation.strip(),
            "target_page_id": target.strip(),
            "note": note[:-1].strip(),
        }
        entries[(entry["source_page_id"], entry["relation_type"], entry["target_page_id"], entry["note"])] = entry
    return entries


def _parse_log_entries(text: str) -> list[dict]:
    entries: list[dict] = []
    current: dict[str, object] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                entries.append(_normalize_log_entry(current))
                current = {}
            continue
        if line.startswith("# "):
            continue
        if not line.startswith("- ") or ": " not in line:
            continue
        key, value = line[2:].split(": ", 1)
        if key == "page_ids":
            current[key] = [part.strip() for part in value.split(",") if part.strip()]
        else:
            current[key] = value.strip()
    if current:
        entries.append(_normalize_log_entry(current))
    return entries


def _normalize_log_entry(entry: dict[str, object]) -> dict:
    return {
        "action": str(entry.get("action", "")).strip(),
        "raw_id": str(entry.get("raw_id", "")).strip(),
        "page_ids": list(entry.get("page_ids", [])),
        "message": str(entry.get("message", "")).strip(),
    }


def _format_log(log_date: str, entries: Iterable[dict]) -> str:
    blocks = []
    for entry in entries:
        blocks.append(
            "\n".join(
                [
                    f"- action: {entry['action']}",
                    f"- raw_id: {entry['raw_id']}",
                    f"- page_ids: {', '.join(entry['page_ids'])}",
                    f"- message: {entry['message']}",
                ]
            )
        )
    body = "\n\n".join(blocks)
    if body:
        return f"# {log_date}\n\n{body}\n"
    return f"# {log_date}\n"


def helper_result_to_dict(result: HelperCommitResult) -> dict:
    return asdict(result)


def mutation_to_json(mutation: dict) -> str:
    return json.dumps(mutation, ensure_ascii=False, indent=2)
