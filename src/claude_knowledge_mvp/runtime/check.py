from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re

from claude_knowledge_mvp.domain.models import (
    CheckFinding,
    CheckReport,
    CheckTarget,
    DeclaredRawCitation,
    Phase1CheckContext,
    Phase2GlobalContext,
)
from claude_knowledge_mvp.prompts.paths import CHECK_PHASE1_PROMPT_PATH, CHECK_PHASE2_PROMPT_PATH


PHASE_ALLOWED_KINDS = {
    "phase1": {"无来源陈述", "过强结论", "证据受限"},
    "phase2": {"关联文件不正确", "证据受限"},
}

LINK_LINE_PATTERN = re.compile(r"^-\s+(.+?)\s+-\[(.+?)\]->\s+([^\(\n]+?)(?:\s+\((.*)\))?$")


def build_check_target(repo_root: Path, wiki_relative_path: str) -> CheckTarget:
    wiki_relative_path = wiki_relative_path.strip()
    if not wiki_relative_path:
        raise ValueError("wiki path must not be empty")

    wiki_path = repo_root / wiki_relative_path
    if not wiki_path.exists() or wiki_path.is_dir():
        raise ValueError("wiki file is missing or unreadable")

    relative = Path(wiki_relative_path)
    if len(relative.parts) < 4 or relative.parts[0] != "WIKI" or relative.parts[2] != "pages" or relative.suffix != ".md":
        raise ValueError("wiki file must live under WIKI/*/pages/*.md")

    return CheckTarget(
        wiki_path=wiki_relative_path,
        page_id=relative.stem,
        wiki_type=relative.parts[1],
    )


def build_phase1_context(repo_root: Path, wiki_relative_path: str) -> Phase1CheckContext:
    target = build_check_target(repo_root=repo_root, wiki_relative_path=wiki_relative_path)
    constitution_text = _read_required_file(repo_root / "CONSTITUTION.md", "CONSTITUTION.md is required")
    prompt_text = _read_required_file(
        repo_root / CHECK_PHASE1_PROMPT_PATH,
        "phase1 prompt pack is required",
    )
    page_content = (repo_root / wiki_relative_path).read_text(encoding="utf-8")
    declared_citations = _extract_declared_citations(repo_root=repo_root, page_content=page_content)
    if not declared_citations:
        raise ValueError("missing auditable evidence boundary: no declared raw citations found in page")

    return Phase1CheckContext(
        target=target,
        page_content=page_content,
        declared_citations=declared_citations,
        constitution_text=constitution_text,
        candidate_laws=_load_candidate_laws(repo_root),
        prompt_text=prompt_text,
    )


def build_phase2_context(repo_root: Path, phase1_context: Phase1CheckContext, phase1_result: dict) -> Phase2GlobalContext:
    if phase1_result.get("status") not in {"passed", "findings"}:
        raise ValueError("phase1 must complete before phase2")

    index_text = _read_required_file(repo_root / "WIKI" / "INDEX.md", "WIKI/INDEX.md is required")
    link_text = _read_optional_file(repo_root / "WIKI" / "LINK.md")
    prompt_text = _read_required_file(
        repo_root / CHECK_PHASE2_PROMPT_PATH,
        "phase2 prompt pack is required",
    )

    return Phase2GlobalContext(
        phase1_context=phase1_context,
        phase1_findings=_normalize_findings(phase1_result, phase="phase1"),
        global_index_excerpt=index_text,
        global_link_excerpt=_extract_target_link_excerpt(link_text, phase1_context.target.page_id),
        available_page_ids=_list_available_page_ids(repo_root),
        prompt_text=prompt_text,
    )


def prepare_check_payload(repo_root: Path, wiki_relative_path: str) -> dict:
    context = build_phase1_context(repo_root=repo_root, wiki_relative_path=wiki_relative_path)
    return {
        "target": asdict(context.target),
        "page_content": context.page_content,
        "declared_citations": [asdict(citation) for citation in context.declared_citations],
        "constitution_text": context.constitution_text,
        "candidate_laws": context.candidate_laws,
        "prompt_text": context.prompt_text,
    }


def prepare_phase2_payload(repo_root: Path, phase1_context: Phase1CheckContext, phase1_result: dict) -> dict:
    context = build_phase2_context(
        repo_root=repo_root,
        phase1_context=phase1_context,
        phase1_result=phase1_result,
    )
    return {
        "target": asdict(context.phase1_context.target),
        "page_content": context.phase1_context.page_content,
        "declared_citations": [asdict(citation) for citation in context.phase1_context.declared_citations],
        "phase1_findings": [asdict(finding) for finding in context.phase1_findings],
        "global_index_excerpt": context.global_index_excerpt,
        "global_link_excerpt": context.global_link_excerpt,
        "available_page_ids": context.available_page_ids,
        "prompt_text": context.prompt_text,
    }


def execute_check(repo_root: Path, wiki_relative_path: str, phase_checker=None) -> dict:
    try:
        phase1_context = build_phase1_context(repo_root=repo_root, wiki_relative_path=wiki_relative_path)
    except ValueError as exc:
        return _error_result(
            error_code=_classify_phase1_context_error(str(exc)),
            error_stage="build_phase1_context",
            diagnostics=[str(exc)],
        )

    checker = phase_checker or generate_check_result_with_claude
    phase1_payload = {
        "phase": "phase1",
        **prepare_check_payload(repo_root=repo_root, wiki_relative_path=wiki_relative_path),
    }
    try:
        raw_phase1_result = checker(phase1_payload)
        phase1_result = _normalize_stage_result(raw_phase1_result, phase="phase1")
    except ValueError as exc:
        return _error_result(error_code="phase1_failed", error_stage="phase1", diagnostics=[str(exc)])

    if phase1_result["status"] not in {"passed", "findings"}:
        return _error_result(
            error_code="phase_gate_error",
            error_stage="phase2",
            diagnostics=["phase1 must complete before phase2"],
        )

    try:
        phase2_payload = {
            "phase": "phase2",
            **prepare_phase2_payload(
                repo_root=repo_root,
                phase1_context=phase1_context,
                phase1_result=phase1_result,
            ),
        }
    except ValueError as exc:
        return _error_result(
            error_code=_classify_phase2_context_error(str(exc)),
            error_stage="phase2",
            diagnostics=[str(exc)],
        )

    try:
        raw_phase2_result = checker(phase2_payload)
        phase2_result = _normalize_stage_result(raw_phase2_result, phase="phase2")
    except ValueError as exc:
        return _error_result(error_code="phase2_failed", error_stage="phase2", diagnostics=[str(exc)])

    report = _build_report(phase1_context.target, phase1_result, phase2_result)
    return {
        "status": report.status,
        "report_markdown": report.report_markdown,
        "phase1_findings": [asdict(finding) for finding in report.phase1_findings],
        "phase2_findings": [asdict(finding) for finding in report.phase2_findings],
        "evidence_limits": report.evidence_limits,
    }


def generate_check_result_with_claude(payload: dict) -> dict:
    raise ValueError("Claude-backed check generation is not wired yet")


def _extract_declared_citations(repo_root: Path, page_content: str) -> list[DeclaredRawCitation]:
    citations: list[DeclaredRawCitation] = []
    for line in page_content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        chunk_id = stripped[2:].strip()
        if "-chunk-" not in chunk_id:
            continue
        raw_id = chunk_id.split("-chunk-", 1)[0]
        raw_relative_path = f"RAW/article/{raw_id}.md"
        raw_path = repo_root / raw_relative_path
        citations.append(
            DeclaredRawCitation(
                chunk_id=chunk_id,
                raw_path=raw_relative_path,
                locator=chunk_id,
                raw_excerpt="",
                parse_status="ok" if raw_path.exists() and raw_path.is_file() else "raw_missing",
            )
        )
    return citations


def _normalize_stage_result(raw_result: dict, *, phase: str) -> dict:
    if not isinstance(raw_result, dict):
        raise ValueError("stage result must be a dict")

    status = str(raw_result.get("status", "")).strip()
    if status not in {"passed", "findings", "blocked", "failed"}:
        raise ValueError("stage status is invalid")

    findings = []
    for finding in raw_result.get("findings", []):
        kind = str(finding.get("kind", "")).strip()
        if kind not in PHASE_ALLOWED_KINDS[phase]:
            raise ValueError(f"{phase} finding kind is invalid: {kind}")
        findings.append(
            {
                "phase": phase,
                "kind": kind,
                "location": str(finding.get("location", "")).strip() or "unknown",
                "message": str(finding.get("message", "")).strip() or kind,
                "evidence_refs": [str(ref) for ref in finding.get("evidence_refs", [])],
            }
        )

    summary = str(raw_result.get("summary", "")).strip()
    if not summary:
        raise ValueError("stage summary is required")

    evidence_limits = [str(item) for item in raw_result.get("evidence_limits", [])]
    return {
        "phase": phase,
        "status": status,
        "summary": summary,
        "findings": findings,
        "evidence_limits": evidence_limits,
    }


def _normalize_findings(stage_result: dict, *, phase: str) -> list[CheckFinding]:
    normalized = _normalize_stage_result(stage_result, phase=phase)
    return [
        CheckFinding(
            phase=phase,
            kind=finding["kind"],
            location=finding["location"],
            message=finding["message"],
            evidence_refs=finding["evidence_refs"],
        )
        for finding in normalized["findings"]
    ]


def _build_report(target: CheckTarget, phase1_result: dict, phase2_result: dict) -> CheckReport:
    phase1_findings = _normalize_findings(phase1_result, phase="phase1")
    phase2_findings = _normalize_findings(phase2_result, phase="phase2")
    evidence_limits = _dedupe_preserving_order(
        [*phase1_result.get("evidence_limits", []), *phase2_result.get("evidence_limits", [])]
    )
    status = _derive_report_status(phase1_result["status"], phase2_result["status"], phase1_findings, phase2_findings)

    report_markdown = _render_report_markdown(
        target=target,
        phase1_summary=phase1_result["summary"],
        phase2_summary=phase2_result["summary"],
        phase1_findings=phase1_findings,
        phase2_findings=phase2_findings,
        evidence_limits=evidence_limits,
        status=status,
    )
    return CheckReport(
        target=target,
        phase1_findings=phase1_findings,
        phase2_findings=phase2_findings,
        evidence_limits=evidence_limits,
        status=status,
        report_markdown=report_markdown,
    )


def _derive_report_status(phase1_status: str, phase2_status: str, phase1_findings: list[CheckFinding], phase2_findings: list[CheckFinding]) -> str:
    if phase1_status == "failed" or phase2_status == "failed":
        return "failed"
    if phase1_status == "blocked" or phase2_status == "blocked":
        return "blocked"
    if phase1_findings or phase2_findings or phase1_status == "findings" or phase2_status == "findings":
        return "findings"
    return "passed"


def _render_report_markdown(
    *,
    target: CheckTarget,
    phase1_summary: str,
    phase2_summary: str,
    phase1_findings: list[CheckFinding],
    phase2_findings: list[CheckFinding],
    evidence_limits: list[str],
    status: str,
) -> str:
    lines = [
        f"# Check Report: {target.page_id}",
        "",
        "## Scope",
        f"- Target: {target.wiki_path}",
        "- Phase 1: RAW ↔ WIKI consistency",
        "- Phase 2: INDEX/LINK minimal global audit",
        "",
        "## Phase 1 Summary",
        f"- {phase1_summary}",
        "",
        "## Phase 1 Findings",
    ]
    lines.extend(_render_findings(phase1_findings, empty_message="- No phase1 findings."))
    lines.extend([
        "",
        "## Phase 2 Summary",
        f"- {phase2_summary}",
        "",
        "## Phase 2 Findings",
    ])
    lines.extend(_render_findings(phase2_findings, empty_message="- No phase2 findings."))
    lines.extend(["", "## Evidence Limits"])
    if evidence_limits:
        lines.extend(f"- {item}" for item in evidence_limits)
    else:
        lines.append("- None.")
    lines.extend(["", "## Result", f"- {status}"])
    return "\n".join(lines)


def _render_findings(findings: list[CheckFinding], *, empty_message: str) -> list[str]:
    if not findings:
        return [empty_message]
    return [f"- [{finding.kind}] {finding.location}: {finding.message}" for finding in findings]


def _list_available_page_ids(repo_root: Path) -> list[str]:
    return sorted(path.stem for path in (repo_root / "WIKI").glob("*/pages/*.md"))


def _load_candidate_laws(repo_root: Path) -> dict[str, str]:
    wiki_root = repo_root / "WIKI"
    if not wiki_root.exists():
        return {}

    candidate_laws: dict[str, str] = {}
    for laws_path in sorted(wiki_root.glob("*/LAWS.md")):
        candidate_laws[laws_path.parent.name] = laws_path.read_text(encoding="utf-8")
    return candidate_laws


def _extract_target_link_excerpt(link_text: str, target_page_id: str) -> str:
    if not link_text:
        return ""

    relevant_lines: list[str] = []
    for line in link_text.splitlines():
        if not line.startswith("- "):
            continue
        parsed = _parse_link_line(line)
        if parsed is None:
            if target_page_id in line:
                relevant_lines.append(f"- [UNPARSEABLE] {line[2:]}")
            continue
        if parsed["source"] == target_page_id or parsed["target"] == target_page_id:
            relevant_lines.append(line)

    if not relevant_lines:
        return ""

    return "\n".join(["# Link Graph", *relevant_lines])


def _parse_link_line(line: str) -> dict[str, str] | None:
    match = LINK_LINE_PATTERN.match(line)
    if not match:
        return None
    return {
        "source": match.group(1).strip(),
        "relation": match.group(2).strip(),
        "target": match.group(3).strip(),
        "note": (match.group(4) or "").strip(),
    }


def _read_required_file(path: Path, message: str) -> str:
    if not path.exists() or path.is_dir():
        raise ValueError(message)
    return path.read_text(encoding="utf-8")


def _read_optional_file(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8")


def _classify_phase1_context_error(message: str) -> str:
    if "missing auditable evidence boundary" in message:
        return "evidence_boundary_missing"
    return "input_error"


def _classify_phase2_context_error(message: str) -> str:
    if "phase1 must complete before phase2" in message:
        return "phase_gate_error"
    if "WIKI/INDEX.md is required" in message:
        return "phase2_input_error"
    return "phase2_failed"


def _dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _error_result(*, error_code: str, error_stage: str, diagnostics: list[str]) -> dict:
    return {
        "status": "failed",
        "report_markdown": "",
        "phase1_findings": [],
        "phase2_findings": [],
        "evidence_limits": [],
        "error_code": error_code,
        "error_stage": error_stage,
        "diagnostics": diagnostics,
    }
