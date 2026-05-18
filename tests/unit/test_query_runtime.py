from pathlib import Path

import pytest

from claude_knowledge_mvp.prompts.paths import QUERY_PROMPT_PATH
from claude_knowledge_mvp.runtime.query import build_query_context, execute_query, prepare_query_payload


@pytest.fixture()
def query_repo(repo_factory) -> Path:
    return repo_factory(
        files={
            "CONSTITUTION.md": "Only repository evidence may be used.\n",
            QUERY_PROMPT_PATH.as_posix(): "Answer with citations and Raw chunks.\n",
            "WIKI/INDEX.md": "# Index\n- paxos -> paxos\n- raft -> raft\n",
            "WIKI/LINK.md": "# Link Graph\n- paxos -[related]-> raft (comparison)\n",
            "WIKI/architecture/pages/paxos.md": "# Paxos\n\n## Sources\n- paxos-chunk-01\n- paxos-chunk-02\n",
            "WIKI/architecture/pages/raft.md": "# Raft\n\n## Sources\n- raft-chunk-01\n",
        }
    )


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
            "citations": [
                {
                    "page_id": "paxos",
                    "wiki_path": "WIKI/architecture/pages/paxos.md",
                    "raw_chunk_ids": ["paxos-chunk-01"],
                }
            ],
            "evidence_limits": ["Linked pages were not needed for this answer."],
        },
    )

    assert result["answer"] == "Paxos uses majority quorums."
    assert result["citations"] == [
        {
            "page_id": "paxos",
            "wiki_path": "WIKI/architecture/pages/paxos.md",
            "raw_chunk_ids": ["paxos-chunk-01"],
        }
    ]
    assert result["evidence_limits"] == ["Linked pages were not needed for this answer."]


def test_execute_query_normalizes_legacy_citation_shape(query_repo: Path):
    result = execute_query(
        query_repo,
        "paxos",
        answer_generator=lambda payload: {
            "answer": "Paxos uses majority quorums.",
            "citations": [
                {
                    "page_id": "paxos",
                    "path": "WIKI/architecture/pages/paxos.md",
                    "source_chunks": ["paxos-chunk-01"],
                }
            ],
        },
    )

    assert result["citations"] == [
        {
            "page_id": "paxos",
            "wiki_path": "WIKI/architecture/pages/paxos.md",
            "raw_chunk_ids": ["paxos-chunk-01"],
        }
    ]
    assert result["evidence_limits"] == []


def test_execute_query_reports_missing_knowledge_when_no_match(query_repo: Path):
    result = execute_query(query_repo, "byzantine generals")

    assert result["answer"] == "Not enough knowledge found in the local knowledge base."
    assert result["citations"] == []
    assert result["evidence_limits"] == [
        "No matching wiki pages were found in WIKI/INDEX.md for the current question."
    ]


def test_execute_query_returns_structured_input_error_for_empty_question(query_repo: Path):
    result = execute_query(query_repo, "   ")

    assert result["answer"] == ""
    assert result["citations"] == []
    assert result["evidence_limits"] == []
    assert result["error_code"] == "input_error"
    assert result["error_stage"] == "prepare_query_payload"
    assert result["diagnostics"] == ["question must not be empty"]


def test_execute_query_returns_structured_result_error_for_invalid_generator_output(query_repo: Path):
    result = execute_query(query_repo, "paxos", answer_generator=lambda payload: "not a dict")

    assert result["answer"] == ""
    assert result["citations"] == []
    assert result["evidence_limits"] == []
    assert result["error_code"] == "query_result_error"
    assert result["error_stage"] == "generate_answer_with_claude"
    assert result["diagnostics"] == ["query answer must be a dict"]
