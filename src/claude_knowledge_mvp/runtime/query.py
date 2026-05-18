from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from claude_knowledge_mvp.prompts.paths import QUERY_PROMPT_PATH


@dataclass(slots=True)
class QueryPage:
    page_id: str
    path: str
    content: str
    source_chunks: list[str]


@dataclass(slots=True)
class QueryContext:
    question: str
    constitution_text: str
    global_index_excerpt: str
    global_link_excerpt: str
    matched_pages: list[QueryPage]
    linked_pages: list[QueryPage]
    prompt_pack: str


def build_query_context(repo_root: Path, question: str) -> QueryContext:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")

    constitution_path = repo_root / "CONSTITUTION.md"
    prompt_path = repo_root / QUERY_PROMPT_PATH
    index_path = repo_root / "WIKI" / "INDEX.md"
    link_path = repo_root / "WIKI" / "LINK.md"

    if not constitution_path.exists():
        raise ValueError("CONSTITUTION.md is required")
    if not prompt_path.exists():
        raise ValueError("query prompt pack is required")
    if not index_path.exists():
        raise ValueError("WIKI/INDEX.md is required")

    index_text = index_path.read_text(encoding="utf-8")
    link_text = link_path.read_text(encoding="utf-8") if link_path.exists() else ""
    matched_ids = _match_page_ids(question, index_text)
    matched_pages = [_read_query_page(repo_root, page_id) for page_id in matched_ids]
    linked_ids = _expand_one_hop(repo_root, matched_ids, link_text)
    linked_pages = [_read_query_page(repo_root, page_id) for page_id in linked_ids]

    return QueryContext(
        question=question,
        constitution_text=constitution_path.read_text(encoding="utf-8"),
        global_index_excerpt=index_text,
        global_link_excerpt=link_text,
        matched_pages=matched_pages,
        linked_pages=linked_pages,
        prompt_pack=prompt_path.read_text(encoding="utf-8"),
    )


def prepare_query_payload(repo_root: Path, question: str) -> dict:
    context = build_query_context(repo_root=repo_root, question=question)
    return {
        "question": context.question,
        "constitution_text": context.constitution_text,
        "global_index_excerpt": context.global_index_excerpt,
        "global_link_excerpt": context.global_link_excerpt,
        "matched_pages": [
            {
                "page_id": page.page_id,
                "path": page.path,
                "content": page.content,
                "source_chunks": page.source_chunks,
            }
            for page in context.matched_pages
        ],
        "linked_pages": [
            {
                "page_id": page.page_id,
                "path": page.path,
                "content": page.content,
                "source_chunks": page.source_chunks,
            }
            for page in context.linked_pages
        ],
        "prompt_pack": context.prompt_pack,
    }


def execute_query(repo_root: Path, question: str, answer_generator=None) -> dict:
    payload = prepare_query_payload(repo_root=repo_root, question=question)
    if not payload["matched_pages"]:
        return {
            "answer": "Not enough knowledge found in the local knowledge base.",
            "citations": [],
            "raw_chunks": [],
        }

    generator = answer_generator or generate_answer_with_claude
    answer = generator(payload)
    if not isinstance(answer, dict):
        raise ValueError("query answer must be a dict")

    return {
        "answer": answer.get("answer", ""),
        "citations": answer.get("citations", []),
        "raw_chunks": answer.get("raw_chunks", []),
    }


def generate_answer_with_claude(payload: dict) -> dict:
    raise ValueError("Claude-backed query answer generation is not wired yet")


def _match_page_ids(question: str, index_text: str) -> list[str]:
    lowered = question.lower()
    matches: list[str] = []
    for line in index_text.splitlines():
        if "->" not in line:
            continue
        remainder = line[2:] if line.startswith("- ") else line
        topic, page_id = [part.strip() for part in remainder.split("->", 1)]
        if topic and topic.lower() in lowered:
            matches.append(page_id)
    return matches


def _expand_one_hop(repo_root: Path, page_ids: list[str], link_text: str) -> list[str]:
    if not link_text or not page_ids:
        return []

    expanded: list[str] = []
    for line in link_text.splitlines():
        if not line.startswith("- ") or "-[" not in line or "]->" not in line:
            continue
        source, remainder = line[2:].split("-[", 1)
        _, target_part = remainder.split("]->", 1)
        target = target_part.split("(", 1)[0].strip()
        if source.strip() not in page_ids or not target or target in page_ids or target in expanded:
            continue
        if not _page_exists(repo_root, target):
            continue
        expanded.append(target)
    return expanded


def _page_exists(repo_root: Path, page_id: str) -> bool:
    return any((repo_root / "WIKI").glob(f"*/pages/{page_id}.md"))


def _read_query_page(repo_root: Path, page_id: str) -> QueryPage:
    candidates = sorted((repo_root / "WIKI").glob(f"*/pages/{page_id}.md"))
    if not candidates:
        raise ValueError(f"wiki page not found for page_id: {page_id}")

    page_path = candidates[0]
    content = page_path.read_text(encoding="utf-8")
    return QueryPage(
        page_id=page_id,
        path=page_path.relative_to(repo_root).as_posix(),
        content=content,
        source_chunks=re.findall(r"^- ([^\n]+)$", content, flags=re.MULTILINE),
    )
