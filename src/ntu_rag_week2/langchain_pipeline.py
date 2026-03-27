from __future__ import annotations

from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from .boundary import DomainBoundaryJudge
from .manifest import CorpusManifestAuditor
from .models import BoundaryDecision, DomainBlueprint, Week2Report, Week2Request
from .pipeline import assemble_week2_report, load_week2_state
from .preview import build_source_previews


def build_week2_report_chain():
    return (
        RunnableLambda(load_week2_state)
        | RunnablePassthrough.assign(
            manifest_audit=lambda state: CorpusManifestAuditor(
                state["blueprint"], state["scope_dir"]
            ).audit(state["records"]),
            source_previews=lambda state: build_source_previews(
                state["records"], state["scope_dir"]
            ),
            boundary_decisions=lambda state: DomainBoundaryJudge(
                state["blueprint"]
            ).decide_many(state["questions"]),
        )
        | RunnableLambda(assemble_week2_report)
    )


def build_boundary_question_chain(blueprint: DomainBlueprint):
    judge = DomainBoundaryJudge(blueprint)
    return RunnableLambda(lambda question: judge.decide(question))


def build_week2_report_with_langchain(request: Week2Request) -> Week2Report:
    return build_week2_report_chain().invoke(request)


def decide_boundary_many_with_langchain(
    blueprint: DomainBlueprint,
    questions: list[str],
) -> list[BoundaryDecision]:
    chain = build_boundary_question_chain(blueprint)
    return chain.batch(questions)
