from __future__ import annotations

import json
from pathlib import Path

from .models import DomainCandidate, DomainScore


def load_domain_candidates(path: Path) -> list[DomainCandidate]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [DomainCandidate(**item) for item in raw_items]


def score_candidate(candidate: DomainCandidate) -> DomainScore:
    total_score = (
        candidate.evidence_clarity * 3
        + candidate.terminology_stability * 2
        + candidate.citation_readiness * 3
        - candidate.collection_friction
        - candidate.open_endedness * 3
    )

    if total_score >= 28:
        verdict = "recommended"
    elif total_score >= 18:
        verdict = "usable"
    else:
        verdict = "avoid"

    reasons: list[str] = []
    if candidate.evidence_clarity >= 4:
        reasons.append("证据文本清晰，适合做可追溯回答。")
    else:
        reasons.append("证据边界不够稳定，后续很难做高质量评测。")

    if candidate.citation_readiness >= 4:
        reasons.append("来源容易记录标题、日期和出处，便于后续建立测试集。")
    else:
        reasons.append("来源不利于做引用和验收，容易让系统只会泛泛而谈。")

    if candidate.open_endedness >= 4:
        reasons.append("问题过于开放，答案会依赖经验和主观判断。")
    elif candidate.collection_friction <= 2:
        reasons.append("资料收集阻力较低，适合在前几周快速形成稳定语料。")

    return DomainScore(
        candidate=candidate,
        total_score=total_score,
        verdict=verdict,
        reasons=reasons,
    )


def rank_domain_candidates(candidates: list[DomainCandidate]) -> list[DomainScore]:
    scored = [score_candidate(candidate) for candidate in candidates]
    return sorted(scored, key=lambda item: item.total_score, reverse=True)
