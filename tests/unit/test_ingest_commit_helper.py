import json
from pathlib import Path

import pytest

from claude_knowledge_mvp.helpers.ingest_commit_helper import (
    MUTATION_SET_SCHEMA_NAME,
    MUTATION_SET_SCHEMA_VERSION,
    commit_mutation_set,
    validate_commit_ready_mutation,
    validate_mutation_set,
)
from claude_knowledge_mvp.runtime.ingest import (
    PREPARE_OUTPUT_SCHEMA_NAME,
    PREPARE_OUTPUT_SCHEMA_VERSION,
    commit_ingest_artifacts,
    execute_ingest,
    execute_ingest_debug,
    generate_mutation_with_claude,
    prepare_ingest_payload,
    run_ingest,
)
from claude_knowledge_mvp.runtime.ingest_cli import main as ingest_cli_main


def sample_mutation_set(
    *,
    page_id: str = "page-1",
    slug: str = "claude-code-skills-ingest",
    title: str = "Claude Code Skills Ingest",
    wiki_type: str = "architecture",
    topic: str = "command-driven ingest",
    aliases: list[str] | None = None,
    target_page_id: str | None = None,
    relation_type: str = "related",
    note: str = "Self-reference for demo graph",
    log_date: str = "2026-05-11",
    raw_id: str = "raw-1",
    chunk_id: str = "chunk-1",
    chunk_text: str = "Claude Code commands can orchestrate ingest safely.",
    message: str = "Ingested sample knowledge page.",
) -> dict:
    return {
        "schema_name": MUTATION_SET_SCHEMA_NAME,
        "schema_version": MUTATION_SET_SCHEMA_VERSION,
        "raw_chunks": [
            {
                "chunk_id": chunk_id,
                "raw_id": raw_id,
                "locator": "L1-L3",
                "text": chunk_text,
                "order": 1,
            }
        ],
        "wiki_page_draft": {
            "page_id": page_id,
            "slug": slug,
            "title": title,
            "wiki_type": wiki_type,
            "summary": "How command-driven ingest works.",
            "body_sections": [
                {
                    "heading": "Key Points",
                    "content": "- Commands orchestrate ingest.\n- Helper commits atomically.",
                }
            ],
            "source_chunk_ids": [chunk_id],
            "status": "active",
        },
        "index_draft": {
            "entries": [
                {
                    "scope": "global",
                    "type_name": wiki_type,
                    "topic": topic,
                    "aliases": aliases or ["xk-ingest"],
                    "page_id": page_id,
                    "rank": 1,
                }
            ]
        },
        "link_draft": {
            "entries": [
                {
                    "scope": "global",
                    "type_name": wiki_type,
                    "source_page_id": page_id,
                    "target_page_id": target_page_id or page_id,
                    "relation_type": relation_type,
                    "note": note,
                }
            ]
        },
        "log_draft": {
            "log_date": log_date,
            "action": "ingest",
            "page_ids": [page_id],
            "raw_id": raw_id,
            "message": message,
        },
        "completeness_report": {
            "summary": "Covers the full sample raw document.",
            "covered_chunk_ids": [chunk_id],
        },
    }


def test_validate_mutation_set_rejects_missing_citations():
    mutation = sample_mutation_set()
    mutation["wiki_page_draft"]["source_chunk_ids"] = []

    with pytest.raises(ValueError, match="source_chunk_ids"):
        validate_mutation_set(mutation)


def test_validate_mutation_set_requires_schema_metadata():
    mutation = sample_mutation_set()
    mutation.pop("schema_name")

    with pytest.raises(ValueError, match="schema_name"):
        validate_mutation_set(mutation)


def test_validate_commit_ready_mutation_rejects_summary_equal_to_title():
    mutation = validate_mutation_set(sample_mutation_set())
    mutation["wiki_page_draft"]["summary"] = mutation["wiki_page_draft"]["title"]

    with pytest.raises(ValueError, match="summary must add information beyond the title"):
        validate_commit_ready_mutation(mutation)


def test_validate_commit_ready_mutation_rejects_single_extract_dump_section():
    mutation = validate_mutation_set(sample_mutation_set())
    mutation["wiki_page_draft"]["body_sections"] = [
        {"heading": "Extracted Knowledge", "content": "Full RAW dump."}
    ]

    with pytest.raises(ValueError, match="body_sections must reflect knowledge organization"):
        validate_commit_ready_mutation(mutation)


def test_validate_commit_ready_mutation_rejects_speculative_link_expansion():
    mutation = validate_mutation_set(sample_mutation_set())
    mutation["link_draft"]["entries"] = [
        {
            "scope": "global",
            "type_name": "architecture",
            "source_page_id": "page-1",
            "target_page_id": "totally-new-page",
            "relation_type": "related",
            "note": "Speculative relation",
        }
    ]

    with pytest.raises(ValueError, match="link_draft must remain conservative"):
        validate_commit_ready_mutation(mutation)


def test_commit_mutation_set_rolls_back_on_write_failure(tmp_path: Path):
    repo_root = tmp_path
    mutation = validate_mutation_set(sample_mutation_set())

    with pytest.raises(RuntimeError, match="forced write failure"):
        commit_mutation_set(repo_root, mutation, fail_on_relative_path="WIKI/LINK.md")

    assert not (repo_root / "WIKI").exists()
    assert not (repo_root / "LOG").exists()


def test_prepare_ingest_payload_collects_runtime_context(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    (repo_root / "WIKI").mkdir(parents=True)
    (repo_root / "WIKI" / "INDEX.md").write_text("# Index\n- existing topic -> page-a\n", encoding="utf-8")
    (repo_root / "WIKI" / "LINK.md").write_text("# Link Graph\n- page-a -[related]-> page-b\n", encoding="utf-8")
    (repo_root / "WIKI" / "notes").mkdir(parents=True)
    (repo_root / "WIKI" / "notes" / "LAWS.md").write_text("# Notes Laws\n- Keep source traceability.\n", encoding="utf-8")

    payload = prepare_ingest_payload(repo_root=repo_root, raw_relative_path="RAW/article/sample-skills-ingest.md")

    assert payload["schema_name"] == PREPARE_OUTPUT_SCHEMA_NAME
    assert payload["schema_version"] == PREPARE_OUTPUT_SCHEMA_VERSION
    assert payload["raw_document"]["raw_id"] == "sample-skills-ingest"
    assert payload["raw_document"]["source_path"] == "RAW/article/sample-skills-ingest.md"
    assert "Only cited knowledge may be committed." in payload["constitution_text"]
    assert "Keep source traceability." in payload["candidate_laws"]["notes"]
    assert "existing topic" in payload["global_index_excerpt"]
    assert "page-a -[related]-> page-b" in payload["global_link_excerpt"]
    assert "Return a KnowledgeMutationSet." in payload["prompt_pack"]
    assert payload["expected_output_keys"] == [
        "raw_chunks",
        "wiki_page_draft",
        "index_draft",
        "link_draft",
        "log_draft",
        "completeness_report",
    ]


def test_commit_mutation_set_preserves_existing_index_and_link_entries(tmp_path: Path):
    repo_root = tmp_path

    first = validate_mutation_set(
        sample_mutation_set(
            page_id="page-a",
            slug="page-a",
            title="Page A",
            topic="topic-a",
            aliases=["page-a"],
            note="first-note",
            raw_id="raw-a",
            chunk_id="chunk-a",
            message="Ingested page A.",
        )
    )
    second = validate_mutation_set(
        sample_mutation_set(
            page_id="page-b",
            slug="page-b",
            title="Page B",
            topic="topic-b",
            aliases=["page-b"],
            note="second-note",
            raw_id="raw-b",
            chunk_id="chunk-b",
            message="Ingested page B.",
        )
    )

    commit_mutation_set(repo_root, first)
    commit_mutation_set(repo_root, second)

    index_text = (repo_root / "WIKI" / "INDEX.md").read_text(encoding="utf-8")
    link_text = (repo_root / "WIKI" / "LINK.md").read_text(encoding="utf-8")

    assert "- topic-a -> page-a" in index_text
    assert "- topic-b -> page-b" in index_text
    assert "- page-a -[related]-> page-a (first-note)" in link_text
    assert "- page-b -[related]-> page-b (second-note)" in link_text


def test_commit_mutation_set_appends_same_day_log_entries(tmp_path: Path):
    repo_root = tmp_path

    first = validate_mutation_set(
        sample_mutation_set(
            page_id="page-a",
            slug="page-a",
            title="Page A",
            raw_id="raw-a",
            chunk_id="chunk-a",
            message="Ingested page A.",
        )
    )
    second = validate_mutation_set(
        sample_mutation_set(
            page_id="page-b",
            slug="page-b",
            title="Page B",
            raw_id="raw-b",
            chunk_id="chunk-b",
            message="Ingested page B.",
        )
    )

    commit_mutation_set(repo_root, first)
    commit_mutation_set(repo_root, second)

    log_text = (repo_root / "LOG" / "2026-05-11.md").read_text(encoding="utf-8")

    assert log_text.count("- action: ingest") == 2
    assert "- raw_id: raw-a" in log_text
    assert "- raw_id: raw-b" in log_text
    assert "- message: Ingested page A." in log_text
    assert "- message: Ingested page B." in log_text


def test_commit_ingest_artifacts_accepts_model_mutation_json(tmp_path: Path):
    repo_root = tmp_path
    mutation_path = repo_root / "mutation.json"
    mutation_path.write_text(json.dumps(sample_mutation_set()), encoding="utf-8")

    result = commit_ingest_artifacts(repo_root=repo_root, mutation_json_path=mutation_path)

    assert result.status == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()
    assert (repo_root / "WIKI" / "INDEX.md").read_text(encoding="utf-8")
    assert (repo_root / "WIKI" / "LINK.md").read_text(encoding="utf-8")
    assert (repo_root / "LOG" / "2026-05-11.md").read_text(encoding="utf-8")


def test_execute_ingest_accepts_session_mutation_file(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    mutation_path = repo_root / "mutation.json"
    mutation_path.write_text(json.dumps(sample_mutation_set()), encoding="utf-8")

    result = execute_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
        mutation_json_path=mutation_path,
    )

    assert result.status == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()


def test_commit_ingest_artifacts_returns_structured_validation_failure(tmp_path: Path):
    repo_root = tmp_path
    mutation_path = repo_root / "mutation.json"
    mutation = sample_mutation_set()
    mutation["wiki_page_draft"]["source_chunk_ids"] = []
    mutation_path.write_text(json.dumps(mutation), encoding="utf-8")

    result = commit_ingest_artifacts(repo_root=repo_root, mutation_json_path=mutation_path)

    assert result.status == "failed"
    assert result.rolled_back is False
    assert result.written_paths == []
    assert result.diagnostics == ["wiki_page_draft.source_chunk_ids must not be empty"]
    assert result.error_code == "validation_error"
    assert result.error_stage == "validate_mutation_set"
    assert result.retryable is False


def test_cli_commit_returns_structured_failure_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    mutation_path = repo_root / "mutation.json"
    mutation = sample_mutation_set()
    mutation["wiki_page_draft"]["source_chunk_ids"] = []
    mutation_path.write_text(json.dumps(mutation), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "commit",
            "--repo-root",
            str(repo_root),
            "--mutation-json",
            str(mutation_path),
        ],
    )
    ingest_cli_main()
    commit_output = json.loads(capsys.readouterr().out)

    assert commit_output["status"] == "failed"
    assert commit_output["error_code"] == "validation_error"
    assert commit_output["error_stage"] == "validate_mutation_set"
    assert commit_output["retryable"] is False
    assert commit_output["diagnostics"] == ["wiki_page_draft.source_chunk_ids must not be empty"]


def test_execute_ingest_commits_from_direct_command_flow(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")

    result = execute_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
        mutation_generator=lambda payload: sample_mutation_set(),
    )

    assert result.status == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()
    assert (repo_root / "WIKI" / "INDEX.md").read_text(encoding="utf-8")
    assert (repo_root / "WIKI" / "LINK.md").read_text(encoding="utf-8")
    assert (repo_root / "LOG" / "2026-05-11.md").read_text(encoding="utf-8")


def test_execute_ingest_rejects_invalid_model_output(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")

    result = execute_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
        mutation_generator=lambda payload: "not json",
    )

    assert result.status == "failed"
    assert result.error_code == "model_output_error"
    assert result.error_stage == "parse_model_output"
    assert result.retryable is True
    assert result.written_paths == []
    assert not (repo_root / "WIKI").exists()
    assert not (repo_root / "LOG").exists()


def test_generate_mutation_with_claude_reads_session_supplied_json(monkeypatch: pytest.MonkeyPatch):
    payload = {"raw_document": {"raw_id": "sample-skills-ingest"}, "prompt_pack": "Return JSON only."}

    monkeypatch.setenv("XK_INGEST_MUTATION_JSON", json.dumps(sample_mutation_set(), ensure_ascii=False))

    mutation = generate_mutation_with_claude(payload)

    assert mutation["schema_name"] == MUTATION_SET_SCHEMA_NAME
    assert mutation["wiki_page_draft"]["slug"] == "claude-code-skills-ingest"


def test_execute_ingest_commits_from_session_supplied_mutation_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    monkeypatch.setenv("XK_INGEST_MUTATION_JSON", json.dumps(sample_mutation_set(), ensure_ascii=False))

    result = execute_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
    )

    assert result.status == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()


def test_execute_ingest_returns_structured_failure_when_session_mutation_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    monkeypatch.delenv("XK_INGEST_MUTATION_JSON", raising=False)

    result = execute_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
    )

    assert result.status == "failed"
    assert result.error_code == "session_bridge_error"
    assert result.error_stage == "generate_mutation_with_claude"
    assert result.retryable is False
    assert result.written_paths == []
    assert result.diagnostics == [
        "Claude session did not supply XK_INGEST_MUTATION_JSON for the local ingest runtime bridge"
    ]


def test_cli_run_flow_returns_committed_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    monkeypatch.setenv("XK_INGEST_MUTATION_JSON", json.dumps(sample_mutation_set(), ensure_ascii=False))
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "run",
            "--repo-root",
            str(repo_root),
            "--raw-path",
            "RAW/article/sample-skills-ingest.md",
        ],
    )
    ingest_cli_main()
    run_output = json.loads(capsys.readouterr().out)

    assert run_output["status"] == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()


def test_cli_run_flow_accepts_session_mutation_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    mutation_path = repo_root / "mutation.json"
    mutation_path.write_text(json.dumps(sample_mutation_set()), encoding="utf-8")
    monkeypatch.delenv("XK_INGEST_MUTATION_JSON", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "run",
            "--repo-root",
            str(repo_root),
            "--raw-path",
            "RAW/article/sample-skills-ingest.md",
            "--mutation-json",
            str(mutation_path),
        ],
    )
    ingest_cli_main()
    run_output = json.loads(capsys.readouterr().out)

    assert run_output["status"] == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()


def test_cli_run_flow_returns_structured_failure_when_session_mutation_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    monkeypatch.delenv("XK_INGEST_MUTATION_JSON", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "run",
            "--repo-root",
            str(repo_root),
            "--raw-path",
            "RAW/article/sample-skills-ingest.md",
        ],
    )
    ingest_cli_main()
    run_output = json.loads(capsys.readouterr().out)

    assert run_output["status"] == "failed"
    assert run_output["error_code"] == "session_bridge_error"
    assert run_output["error_stage"] == "generate_mutation_with_claude"
    assert run_output["retryable"] is False
    assert run_output["written_paths"] == []
    assert run_output["diagnostics"] == [
        "Claude session did not supply XK_INGEST_MUTATION_JSON for the local ingest runtime bridge"
    ]


def test_execute_ingest_debug_returns_mutation_on_success(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")

    result = execute_ingest_debug(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
        mutation_generator=lambda payload: sample_mutation_set(),
    )

    assert result["status"] == "committed"
    assert result["mutation"]["schema_name"] == MUTATION_SET_SCHEMA_NAME
    assert result["mutation"]["wiki_page_draft"]["slug"] == "claude-code-skills-ingest"


def test_cli_debug_run_returns_mutation_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")

    monkeypatch.setattr(
        "claude_knowledge_mvp.runtime.ingest.generate_mutation_with_claude",
        lambda payload: sample_mutation_set(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "debug-run",
            "--repo-root",
            str(repo_root),
            "--raw-path",
            "RAW/article/sample-skills-ingest.md",
        ],
    )
    ingest_cli_main()
    debug_output = json.loads(capsys.readouterr().out)

    assert debug_output["status"] == "committed"
    assert debug_output["mutation"]["schema_name"] == MUTATION_SET_SCHEMA_NAME
    assert debug_output["mutation"]["wiki_page_draft"]["slug"] == "claude-code-skills-ingest"


def test_cli_prepare_and_commit_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")
    mutation_path = repo_root / "mutation.json"
    mutation_path.write_text(json.dumps(sample_mutation_set()), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "prepare",
            "--repo-root",
            str(repo_root),
            "--raw-path",
            "RAW/article/sample-skills-ingest.md",
        ],
    )
    ingest_cli_main()
    prepared_output = capsys.readouterr().out
    assert '"schema_name"' in prepared_output
    assert '"schema_version"' in prepared_output
    assert '"expected_output_keys"' in prepared_output

    monkeypatch.setattr(
        "sys.argv",
        [
            "ingest_cli",
            "commit",
            "--repo-root",
            str(repo_root),
            "--mutation-json",
            str(mutation_path),
        ],
    )
    ingest_cli_main()
    commit_output = capsys.readouterr().out
    assert '"status": "committed"' in commit_output
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()
    assert MUTATION_SET_SCHEMA_NAME == "xk-ingest-mutation-set"


def test_run_ingest_writes_wiki_index_link_and_log(tmp_path: Path):
    repo_root = tmp_path
    raw_path = repo_root / "RAW" / "article" / "sample-skills-ingest.md"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Skills-first ingest\n\nClaude Code skills orchestrate ingest while a helper performs atomic commits.\n",
        encoding="utf-8",
    )
    (repo_root / "CONSTITUTION.md").write_text("Only cited knowledge may be committed.\n", encoding="utf-8")
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts").mkdir(parents=True)
    (repo_root / "src" / "claude_knowledge_mvp" / "prompts" / "ingest.md").write_text("Return a KnowledgeMutationSet.\n", encoding="utf-8")

    result = run_ingest(
        repo_root=repo_root,
        raw_relative_path="RAW/article/sample-skills-ingest.md",
        mutation_generator=lambda context: sample_mutation_set(),
    )

    assert result.status == "committed"
    assert (repo_root / "WIKI" / "architecture" / "pages" / "claude-code-skills-ingest.md").exists()
    assert (repo_root / "WIKI" / "INDEX.md").read_text(encoding="utf-8")
    assert (repo_root / "WIKI" / "LINK.md").read_text(encoding="utf-8")
    assert (repo_root / "LOG" / "2026-05-11.md").read_text(encoding="utf-8")
