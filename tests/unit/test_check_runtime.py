from pathlib import Path

import pytest

from claude_knowledge_mvp.prompts.paths import CHECK_PHASE1_PROMPT_PATH, CHECK_PHASE2_PROMPT_PATH, PROMPTS_ROOT
from claude_knowledge_mvp.runtime.check import (
    build_phase1_context,
    execute_check,
    prepare_check_payload,
    prepare_phase2_payload,
)


@pytest.fixture()
def check_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path
    (repo_root / "CONSTITUTION.md").write_text("Use only declared repository evidence.\n", encoding="utf-8")
    (repo_root / PROMPTS_ROOT).mkdir(parents=True)
    (repo_root / CHECK_PHASE1_PROMPT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (repo_root / CHECK_PHASE1_PROMPT_PATH).write_text(
        "Phase1 prompt.\n",
        encoding="utf-8",
    )
    (repo_root / CHECK_PHASE2_PROMPT_PATH).write_text(
        "Phase2 prompt.\n",
        encoding="utf-8",
    )

    (repo_root / "RAW" / "article").mkdir(parents=True)
    (repo_root / "RAW" / "article" / "target-page.md").write_text(
        "Target raw content.\n",
        encoding="utf-8",
    )

    (repo_root / "WIKI" / "notes" / "pages").mkdir(parents=True)
    (repo_root / "WIKI" / "notes" / "LAWS.md").write_text(
        "Notes law.\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "notes" / "pages" / "target-page.md").write_text(
        "# Target Page\n\nTarget content.\n\n## Sources\n- target-page-chunk-1\n- missing-raw-chunk-2\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "notes" / "pages" / "related-page.md").write_text(
        "# Related Page\n\n## Sources\n- related-page-chunk-1\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "notes" / "pages" / "no-sources.md").write_text(
        "# No Sources\n\nThis page forgot to declare evidence.\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "architecture" / "pages").mkdir(parents=True)
    (repo_root / "WIKI" / "architecture" / "pages" / "other-page.md").write_text(
        "# Other Page\n\n## Sources\n- other-page-chunk-1\n",
        encoding="utf-8",
    )

    (repo_root / "WIKI" / "INDEX.md").write_text(
        "# Index\n- target -> target-page\n- related -> related-page\n",
        encoding="utf-8",
    )
    (repo_root / "WIKI" / "LINK.md").write_text(
        "# Link Graph\n"
        "- target-page -[related]-> related-page (valid target)\n"
        "- target-page -[related]-> missing-page (broken target)\n"
        "- other-page -[related]-> related-page (unrelated)\n",
        encoding="utf-8",
    )
    return repo_root


def test_prepare_check_payload_includes_declared_citations_and_candidate_laws(check_repo: Path):
    payload = prepare_check_payload(check_repo, "WIKI/notes/pages/target-page.md")

    assert payload["target"]["page_id"] == "target-page"
    assert payload["candidate_laws"] == {"notes": "Notes law.\n"}
    assert payload["declared_citations"][0]["raw_path"] == "RAW/article/target-page.md"
    assert payload["declared_citations"][0]["parse_status"] == "ok"
    assert payload["declared_citations"][1]["raw_path"] == "RAW/article/missing-raw.md"
    assert payload["declared_citations"][1]["parse_status"] == "raw_missing"


def test_prepare_phase2_payload_filters_link_excerpt_for_target_page(check_repo: Path):
    phase1_context = build_phase1_context(check_repo, "WIKI/notes/pages/target-page.md")
    payload = prepare_phase2_payload(
        check_repo,
        phase1_context,
        _stage_result(status="passed", summary="phase1 ok", phase="phase1"),
    )

    assert payload["available_page_ids"] == ["no-sources", "other-page", "related-page", "target-page"]
    assert "target-page -[related]-> related-page" in payload["global_link_excerpt"]
    assert "target-page -[related]-> missing-page" in payload["global_link_excerpt"]
    assert "other-page -[related]-> related-page" not in payload["global_link_excerpt"]


def test_execute_check_runs_phase1_then_phase2_and_renders_markdown_report(check_repo: Path):
    phases: list[str] = []

    def checker(payload: dict) -> dict:
        phases.append(payload["phase"])
        if payload["phase"] == "phase1":
            assert payload["target"]["page_id"] == "target-page"
            return _stage_result(
                status="findings",
                summary="phase1 found one issue",
                phase="phase1",
                findings=[
                    {
                        "kind": "无来源陈述",
                        "location": "line 3",
                        "message": "statement has no citation",
                        "evidence_refs": ["target-page-chunk-1"],
                    }
                ],
            )

        assert payload["global_link_excerpt"]
        return _stage_result(
            status="findings",
            summary="phase2 found one link issue",
            phase="phase2",
            findings=[
                {
                    "kind": "关联文件不正确",
                    "location": "WIKI/LINK.md:3",
                    "message": "missing-page does not resolve",
                    "evidence_refs": ["missing-page"],
                }
            ],
            evidence_limits=["missing raw chunk text"],
        )

    result = execute_check(check_repo, "WIKI/notes/pages/target-page.md", phase_checker=checker)

    assert phases == ["phase1", "phase2"]
    assert result["status"] == "findings"
    assert result["phase1_findings"][0]["kind"] == "无来源陈述"
    assert result["phase2_findings"][0]["kind"] == "关联文件不正确"
    assert "# Check Report: target-page" in result["report_markdown"]
    assert "phase1 found one issue" in result["report_markdown"]
    assert "missing-page does not resolve" in result["report_markdown"]
    assert result["evidence_limits"] == ["missing raw chunk text"]


def test_execute_check_returns_phase_gate_error_when_phase1_does_not_complete(check_repo: Path):
    result = execute_check(
        check_repo,
        "WIKI/notes/pages/target-page.md",
        phase_checker=lambda payload: _stage_result(
            status="blocked",
            summary="phase1 blocked",
            phase=payload["phase"],
            evidence_limits=["declared citations are insufficient"],
        ),
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "phase_gate_error"
    assert result["error_stage"] == "phase2"
    assert result["diagnostics"] == ["phase1 must complete before phase2"]


def test_execute_check_returns_evidence_boundary_error_for_page_without_sources(check_repo: Path):
    result = execute_check(check_repo, "WIKI/notes/pages/no-sources.md")

    assert result["status"] == "failed"
    assert result["error_code"] == "evidence_boundary_missing"
    assert result["error_stage"] == "build_phase1_context"


def test_execute_check_allows_missing_link_file(check_repo: Path):
    (check_repo / "WIKI" / "LINK.md").unlink()

    def checker(payload: dict) -> dict:
        if payload["phase"] == "phase1":
            return _stage_result(status="passed", summary="phase1 ok", phase="phase1")
        assert payload["global_link_excerpt"] == ""
        return _stage_result(status="passed", summary="phase2 ok", phase="phase2")

    result = execute_check(check_repo, "WIKI/notes/pages/target-page.md", phase_checker=checker)

    assert result["status"] == "passed"
    assert "- passed" in result["report_markdown"]


def test_execute_check_is_read_only_for_success_and_failure_paths(check_repo: Path):
    before_success = _snapshot_repo_files(check_repo)
    success_result = execute_check(
        check_repo,
        "WIKI/notes/pages/target-page.md",
        phase_checker=lambda payload: _stage_result(status="passed", summary=f"{payload['phase']} ok", phase=payload["phase"]),
    )
    after_success = _snapshot_repo_files(check_repo)

    before_failure = _snapshot_repo_files(check_repo)
    failure_result = execute_check(check_repo, "WIKI/notes/pages/no-sources.md")
    after_failure = _snapshot_repo_files(check_repo)

    assert success_result["status"] == "passed"
    assert failure_result["error_code"] == "evidence_boundary_missing"
    assert before_success == after_success
    assert before_failure == after_failure


def _stage_result(*, status: str, summary: str, phase: str, findings: list[dict] | None = None, evidence_limits: list[str] | None = None) -> dict:
    return {
        "phase": phase,
        "status": status,
        "summary": summary,
        "findings": findings or [],
        "evidence_limits": evidence_limits or [],
    }


def _snapshot_repo_files(repo_root: Path) -> dict[str, str]:
    return {
        path.relative_to(repo_root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(p for p in repo_root.rglob("*") if p.is_file())
    }
