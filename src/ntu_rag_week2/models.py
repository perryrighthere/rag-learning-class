from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DomainCandidate:
    name: str
    description: str
    evidence_clarity: int
    terminology_stability: int
    citation_readiness: int
    collection_friction: int
    open_endedness: int


@dataclass(frozen=True)
class DomainScore:
    candidate: DomainCandidate
    total_score: int
    verdict: str
    reasons: list[str]


@dataclass(frozen=True)
class DomainBlueprint:
    domain_name: str
    goal: str
    why_this_domain: str
    include_topics: list[str]
    exclude_topics: list[str]
    include_keywords: list[str]
    exclude_keywords: list[str]
    in_scope_examples: list[str]
    out_of_scope_examples: list[str]
    minimum_source_count: int
    maximum_source_count: int
    preferred_formats: list[str]


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    source_ref: str
    published_at: str
    format: str
    authority_type: str
    path: str
    summary: str
    reason_to_include: str


@dataclass(frozen=True)
class AuditIssue:
    severity: str
    message: str


@dataclass(frozen=True)
class ManifestAudit:
    total_sources: int
    format_counts: dict[str, int]
    authority_counts: dict[str, int]
    earliest_date: str
    latest_date: str
    issues: list[AuditIssue]


@dataclass(frozen=True)
class SourcePreview:
    source_id: str
    title: str
    excerpt: str


@dataclass(frozen=True)
class BoundaryDecision:
    question: str
    label: str
    reason: str
    matched_keywords: list[str]


@dataclass(frozen=True)
class Week2Request:
    scope_root: Path | None = None
    scope_name: str = "compliance_ops"
    questions: list[str] | None = None


@dataclass(frozen=True)
class Week2Report:
    candidate_scores: list[DomainScore]
    domain_blueprint: DomainBlueprint
    manifest_audit: ManifestAudit
    source_previews: list[SourcePreview]
    boundary_decisions: list[BoundaryDecision]
