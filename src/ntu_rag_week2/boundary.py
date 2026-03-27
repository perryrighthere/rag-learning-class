from __future__ import annotations

from .models import BoundaryDecision, DomainBlueprint


GENERIC_INCLUDE_KEYWORDS = {"数据"}


def _normalize(text: str) -> str:
    return "".join(text.lower().split())


class DomainBoundaryJudge:
    def __init__(self, blueprint: DomainBlueprint) -> None:
        self.blueprint = blueprint

    def decide(self, question: str) -> BoundaryDecision:
        normalized_question = _normalize(question)
        excluded = [
            keyword
            for keyword in self.blueprint.exclude_keywords
            if _normalize(keyword) in normalized_question
        ]
        if excluded:
            return BoundaryDecision(
                question=question,
                label="out_of_scope",
                reason=(
                    "问题命中了出界关键词，说明它更像预测、策略建议或价值判断，"
                    "不能直接从本周语料中做证据式回答。"
                ),
                matched_keywords=excluded,
            )

        included = [
            keyword
            for keyword in self.blueprint.include_keywords
            if _normalize(keyword) in normalized_question
        ]
        strong_included = [
            keyword for keyword in included if keyword not in GENERIC_INCLUDE_KEYWORDS
        ]
        if strong_included or len(included) >= 2:
            return BoundaryDecision(
                question=question,
                label="in_scope",
                reason="问题命中了制度、流程、职责或时限相关关键词，适合纳入本周领域边界。",
                matched_keywords=strong_included or included,
            )
        if included:
            return BoundaryDecision(
                question=question,
                label="needs_clarification",
                reason="问题只命中了过于宽泛的领域词，老师需要继续追问它到底对应哪条制度、流程或责任边界。",
                matched_keywords=included,
            )

        return BoundaryDecision(
            question=question,
            label="needs_clarification",
            reason="问题没有命中清晰的纳入或排除关键词，需要老师先追问证据来源和业务对象。",
            matched_keywords=[],
        )

    def decide_many(self, questions: list[str]) -> list[BoundaryDecision]:
        return [self.decide(question) for question in questions]
