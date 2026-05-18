from pathlib import Path

import pytest

from claude_knowledge_mvp.prompts.paths import PROMPTS_ROOT, QUERY_PROMPT_PATH
from claude_knowledge_mvp.runtime.query import build_query_context, execute_query, prepare_query_payload


@pytest.fixture()
def query_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path
    (repo_root / "CONSTITUTION.md").write_text("Only repository evidence may be used.\n", encoding="utf-8")
    (repo_root / PROMPTS_ROOT).mkdir(parents=True)
    (repo_root / QUERY_PROMPT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (repo_root / QUERY_PROMPT_PATH).write_text(
        "Answer with citations and Raw chunks.\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "architecture" / "pages").mkdir(parents=True)
    (repo_root / "WIKI" / "INDEX.md").write_text(
        "# Index\n- paxos -> paxos\n- raft -> raft\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "LINK.md").write_text(
        "# Link Graph\n- paxos -[related]-> raft (comparison)\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "architecture" / "pages" / "paxos.md").write_text(
        "# Paxos\n\n## Sources\n- paxos-chunk-01\n- paxos-chunk-02\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "architecture" / "pages" / "raft.md").write_text(
        "# Raft\n\n## Sources\n- raft-chunk-01\n",
        encoding="utf-8",
    )
    return repo_root


def test_build_query_context_matches_index_and_one_hop_links(query_repo: Path):
    context = build_query_context(query_repo, "what does the knowledge base say about paxos?")

    assert [page.page_id for page in context.matched_pages] == ["paxos"]
    assert [page.page_id for page in context.linked_pages] == ["raft"]
    assert context.matched_pages[0].source_chunks == ["paxos-chunk-01", "paxos-chunk-02"]
    assert context.linked_pages[0].source_chunks == ["raft-chunk-01"]


def test_prepare_query_payload_includes_prompt_and_page_context(query_repo: Path):
    payload = prepare_query_payload(query_repo, "summarize paxos from the repo wiki")

    assert payload["question"] == "summarize paxos from the repo wiki"
    assert "Only repository evidence may be used." in payload["constitution_text"]
    assert payload["matched_pages"][0]["page_id"] == "paxos"
    assert payload["linked_pages"][0]["page_id"] == "raft"
    assert payload["matched_pages"][0]["source_chunks"] == ["paxos-chunk-01", "paxos-chunk-02"]
    assert "Answer with citations and Raw chunks." in payload["prompt_pack"]


def test_build_query_context_requires_non_empty_question(query_repo: Path):
    with pytest.raises(ValueError, match="question must not be empty"):
        build_query_context(query_repo, "   ")


def test_build_query_context_handles_missing_link_file(query_repo: Path):
    (query_repo / "WIKI" / "LINK.md").unlink()

    context = build_query_context(query_repo, "paxos")

    assert [page.page_id for page in context.matched_pages] == ["paxos"]
    assert context.linked_pages == []


def test_execute_query_returns_agent_answer_and_citations(query_repo: Path):
    result = execute_query(
        query_repo,
        "paxos",
        answer_generator=lambda payload: {
            "answer": "Paxos uses majority quorums.",
            "citations": ["WIKI/architecture/pages/paxos.md"],
            "raw_chunks": ["paxos-chunk-01"],
        },
    )

    assert result["answer"] == "Paxos uses majority quorums."
    assert result["citations"] == ["WIKI/architecture/pages/paxos.md"]
    assert result["raw_chunks"] == ["paxos-chunk-01"]


def test_execute_query_reports_missing_knowledge_when_no_match(query_repo: Path):
    result = execute_query(query_repo, "byzantine generals")

    assert result["answer"] == "Not enough knowledge found in the local knowledge base."
    assert result["citations"] == []
    assert result["raw_chunks"] == []
