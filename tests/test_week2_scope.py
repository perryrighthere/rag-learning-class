from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week2.boundary import DomainBoundaryJudge
from ntu_rag_week2.domain_selection import load_domain_candidates, rank_domain_candidates
from ntu_rag_week2.langchain_pipeline import (
    build_week2_report_with_langchain,
    decide_boundary_many_with_langchain,
)
from ntu_rag_week2.manifest import load_domain_blueprint, load_source_records
from ntu_rag_week2.models import Week2Request
from ntu_rag_week2.pipeline import build_week2_report
from ntu_rag_week2.preview import load_source_preview


class DomainSelectionTest(unittest.TestCase):
    def test_compliance_domain_ranks_first(self) -> None:
        candidates = load_domain_candidates(ROOT / "data" / "week2_scope" / "domain_candidates.json")
        ranked = rank_domain_candidates(candidates)

        self.assertEqual(ranked[0].candidate.name, "企业数据合规与隐私内控")
        self.assertEqual(ranked[-1].verdict, "avoid")


class ManifestAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_week2_report()

    def test_sample_scope_has_ten_sources_and_no_errors(self) -> None:
        severities = [item.severity for item in self.report.manifest_audit.issues]

        self.assertEqual(self.report.manifest_audit.total_sources, 10)
        self.assertNotIn("error", severities)
        self.assertGreaterEqual(len(self.report.source_previews), 4)


class BoundaryJudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        blueprint = load_domain_blueprint(
            ROOT / "data" / "week2_scope" / "compliance_ops" / "domain_brief.json"
        )
        cls.judge = DomainBoundaryJudge(blueprint)

    def test_predictive_question_is_out_of_scope(self) -> None:
        decision = self.judge.decide("公司未来三年会不会因为隐私问题被监管处罚？")

        self.assertEqual(decision.label, "out_of_scope")
        self.assertIn("未来", decision.matched_keywords)

    def test_process_question_is_in_scope(self) -> None:
        decision = self.judge.decide("涉及个人信息的临时访问申请需要谁审批？")

        self.assertEqual(decision.label, "in_scope")
        self.assertTrue(decision.matched_keywords)

    def test_commercial_question_is_out_of_scope(self) -> None:
        decision = self.judge.decide("怎样设计一套最受欢迎的数据商业化产品？")

        self.assertEqual(decision.label, "out_of_scope")
        self.assertIn("商业化", decision.matched_keywords)


class SourcePreviewTest(unittest.TestCase):
    def test_html_preview_strips_tags(self) -> None:
        excerpt = load_source_preview(
            ROOT
            / "data"
            / "week2_scope"
            / "compliance_ops"
            / "sources"
            / "third-party-security-review.html",
            max_chars=220,
        )

        self.assertNotIn("<p>", excerpt)
        self.assertIn("供应商", excerpt)

    def test_html_preview_ignores_script_content(self) -> None:
        excerpt = load_source_preview(
            ROOT
            / "data"
            / "week2_scope"
            / "cyber_incident_ops"
            / "sources"
            / "incident-handling-guide.html",
            max_chars=220,
        )

        self.assertNotIn("window.NREUM", excerpt)
        self.assertIn("Computer Security Incident Handling Guide", excerpt)


class LangChainPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scope_dir = ROOT / "data" / "week2_scope" / "compliance_ops"
        cls.blueprint = load_domain_blueprint(cls.scope_dir / "domain_brief.json")
        cls.records = load_source_records(cls.scope_dir / "corpus_manifest.json")

    def test_langchain_report_matches_python_report(self) -> None:
        python_report = build_week2_report(
            scope_name="compliance_ops",
            questions=["涉及个人信息的临时访问申请需要谁审批？"],
        )
        langchain_report = build_week2_report_with_langchain(
            Week2Request(
                scope_name="compliance_ops",
                questions=["涉及个人信息的临时访问申请需要谁审批？"],
            )
        )

        self.assertEqual(langchain_report, python_report)

    def test_langchain_boundary_batch_matches_decide_many(self) -> None:
        questions = [
            "涉及个人信息的临时访问申请需要谁审批？",
            "公司未来三年会不会因为隐私问题被监管处罚？",
            "怎样设计一套最受欢迎的数据商业化产品？",
        ]

        self.assertEqual(
            decide_boundary_many_with_langchain(self.blueprint, questions),
            DomainBoundaryJudge(self.blueprint).decide_many(questions),
        )


if __name__ == "__main__":
    unittest.main()
