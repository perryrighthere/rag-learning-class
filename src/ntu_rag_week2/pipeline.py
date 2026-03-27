from __future__ import annotations

from pathlib import Path

from .boundary import DomainBoundaryJudge
from .domain_selection import load_domain_candidates, rank_domain_candidates
from .manifest import CorpusManifestAuditor, load_domain_blueprint, load_source_records
from .models import Week2Report, Week2Request
from .preview import build_source_previews


VERDICT_LABELS = {
    "recommended": "推荐",
    "usable": "可做但要收紧边界",
    "avoid": "不推荐",
}


BOUNDARY_LABELS = {
    "in_scope": "纳入范围",
    "out_of_scope": "超出范围",
    "needs_clarification": "需要澄清",
}


def build_week2_report(
    scope_root: Path | None = None,
    scope_name: str = "compliance_ops",
    questions: list[str] | None = None,
) -> Week2Report:
    request = Week2Request(
        scope_root=scope_root,
        scope_name=scope_name,
        questions=questions,
    )
    state = load_week2_state(request)
    state["manifest_audit"] = CorpusManifestAuditor(
        state["blueprint"], state["scope_dir"]
    ).audit(state["records"])
    state["source_previews"] = build_source_previews(state["records"], state["scope_dir"])
    state["boundary_decisions"] = DomainBoundaryJudge(state["blueprint"]).decide_many(
        state["questions"]
    )
    return assemble_week2_report(state)


def load_week2_state(request: Week2Request | dict[str, object]) -> dict[str, object]:
    if isinstance(request, dict):
        request = Week2Request(**request)

    root = Path(__file__).resolve().parents[2]
    data_root = request.scope_root or root / "data" / "week2_scope"
    scope_dir = data_root / request.scope_name

    candidate_scores = rank_domain_candidates(
        load_domain_candidates(data_root / "domain_candidates.json")
    )
    blueprint = load_domain_blueprint(scope_dir / "domain_brief.json")
    records = load_source_records(scope_dir / "corpus_manifest.json")
    questions = request.questions or (
        blueprint.in_scope_examples[:2] + blueprint.out_of_scope_examples[:2]
    )
    return {
        "candidate_scores": candidate_scores,
        "blueprint": blueprint,
        "records": records,
        "scope_dir": scope_dir,
        "questions": questions,
    }


def assemble_week2_report(state: dict[str, object]) -> Week2Report:
    return Week2Report(
        candidate_scores=state["candidate_scores"],
        domain_blueprint=state["blueprint"],
        manifest_audit=state["manifest_audit"],
        source_previews=state["source_previews"],
        boundary_decisions=state["boundary_decisions"],
    )


def render_report(report: Week2Report) -> str:
    lines = [
        f"Week 2 Domain: {report.domain_blueprint.domain_name}",
        f"Goal: {report.domain_blueprint.goal}",
        "",
        "Candidate Ranking:",
    ]
    for index, item in enumerate(report.candidate_scores, start=1):
        verdict = VERDICT_LABELS.get(item.verdict, item.verdict)
        lines.append(
            f"  {index}. {item.candidate.name} | score={item.total_score} | {verdict}"
        )
        for reason in item.reasons:
            lines.append(f"     - {reason}")

    audit = report.manifest_audit
    lines.extend(
        [
            "",
            "Corpus Audit:",
            f"  - total_sources: {audit.total_sources}",
            f"  - formats: {audit.format_counts}",
            f"  - authority_types: {audit.authority_counts}",
            f"  - date_range: {audit.earliest_date} -> {audit.latest_date}",
        ]
    )
    if audit.issues:
        lines.append("  - issues:")
        for issue in audit.issues:
            lines.append(f"      * [{issue.severity}] {issue.message}")
    else:
        lines.append("  - issues: none")

    lines.extend(["", "Source Previews:"])
    for item in report.source_previews:
        lines.append(f"  - {item.source_id} {item.title}")
        lines.append(f"    {item.excerpt}")

    lines.extend(["", "Boundary Decisions:"])
    for item in report.boundary_decisions:
        label = BOUNDARY_LABELS.get(item.label, item.label)
        lines.append(f"  - [{label}] {item.question}")
        lines.append(f"    {item.reason}")
        if item.matched_keywords:
            lines.append(f"    matched={', '.join(item.matched_keywords)}")

    return "\n".join(lines)
