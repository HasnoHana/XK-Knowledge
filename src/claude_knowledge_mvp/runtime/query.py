from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

from claude_knowledge_mvp.domain.models import QueryAnswer, QueryCitation
from claude_knowledge_mvp.prompts.paths import QUERY_PROMPT_PATH, read_repo_prompt_text


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
    index_path = repo_root / "WIKI" / "INDEX.md"
    link_path = repo_root / "WIKI" / "LINK.md"

    if not constitution_path.exists():
        raise ValueError("CONSTITUTION.md is required")
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
        prompt_pack=read_repo_prompt_text(
            repo_root=repo_root,
            prompt_path=QUERY_PROMPT_PATH,
            missing_message="query prompt pack is required",
        ),
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
    try:
        payload = prepare_query_payload(repo_root=repo_root, question=question)
    except ValueError as exc:
        return _error_result(error_code="input_error", error_stage="prepare_query_payload", diagnostics=[str(exc)])

    if not payload["matched_pages"]:
        return asdict(
            QueryAnswer(
                answer="Not enough knowledge found in the local knowledge base.",
                evidence_limits=["No matching wiki pages were found in WIKI/INDEX.md for the current question."],
            )
        )

    generator = answer_generator or generate_answer_with_claude
    try:
        answer = generator(payload)
        return asdict(_normalize_query_answer(answer))
    except ValueError as exc:
        return _error_result(error_code="query_result_error", error_stage="generate_answer_with_claude", diagnostics=[str(exc)])


def generate_answer_with_claude(payload: dict) -> dict:
    raise ValueError("Claude-backed query answer generation is not wired yet")


def render_query_result_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _normalize_query_answer(answer: dict) -> QueryAnswer:
    if not isinstance(answer, dict):
        raise ValueError("query answer must be a dict")

    citations = [_normalize_query_citation(item) for item in answer.get("citations", [])]
    evidence_limits = [str(item) for item in answer.get("evidence_limits", [])]
    return QueryAnswer(
        answer=str(answer.get("answer", "")),
        citations=citations,
        evidence_limits=evidence_limits,
    )


def _normalize_query_citation(citation: dict) -> QueryCitation:
    if not isinstance(citation, dict):
        raise ValueError("query citation must be a dict")

    page_id = str(citation.get("page_id", "")).strip()
    wiki_path = str(citation.get("wiki_path", citation.get("path", ""))).strip()
    raw_chunk_ids = citation.get("raw_chunk_ids", citation.get("source_chunks", []))
    if not isinstance(raw_chunk_ids, list):
        raise ValueError("query citation raw_chunk_ids must be a list")

    return QueryCitation(
        page_id=page_id,
        wiki_path=wiki_path,
        raw_chunk_ids=[str(item) for item in raw_chunk_ids],
    )


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


def _error_result(*, error_code: str, error_stage: str, diagnostics: list[str]) -> dict:
    return {
        "answer": "",
        "citations": [],
        "evidence_limits": [],
        "error_code": error_code,
        "error_stage": error_stage,
        "diagnostics": diagnostics,
    }
