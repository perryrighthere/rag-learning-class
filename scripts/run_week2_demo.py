from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week2.langchain_pipeline import build_week2_report_with_langchain
from ntu_rag_week2.models import Week2Request
from ntu_rag_week2.pipeline import build_week2_report, render_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Week 2 domain-scoping and corpus-audit demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py \\
    --question "涉及个人信息的临时访问申请需要谁审批？" \\
    --question "怎样设计一套最受欢迎的数据商业化产品？"
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope cyber_incident_ops
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance \\
    --question "高风险 AI 系统提供者需要建立什么样的质量管理体系？" \\
    --question "这家 AI 公司未来三年一定会不会因为 AI Act 被重罚？"
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope cyber_incident_ops \\
    --question "日志管理指南建议保留哪些类型的安全日志以支持事件分析？" \\
    --question "我们现在最应该买哪一家的 EDR 产品？"
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --engine langchain --json
  PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance --json
"""
    )
    parser.add_argument(
        "--scope",
        default="compliance_ops",
        help="Which Week 2 scope bundle under data/week2_scope to load.",
    )
    parser.add_argument(
        "--engine",
        choices=("python", "langchain"),
        default="python",
        help="Choose the orchestration engine for the Week 2 demo.",
    )
    parser.add_argument(
        "--question",
        action="append",
        default=None,
        help="Optional question to test against the domain boundary. Repeat the flag for multiple questions.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.engine == "langchain":
        report = build_week2_report_with_langchain(
            Week2Request(scope_name=args.scope, questions=args.question)
        )
    else:
        report = build_week2_report(scope_name=args.scope, questions=args.question)

    payload = {
        "engine": args.engine,
        "domain": report.domain_blueprint.domain_name,
        "goal": report.domain_blueprint.goal,
        "candidate_scores": [
            {
                "name": item.candidate.name,
                "score": item.total_score,
                "verdict": item.verdict,
                "reasons": item.reasons,
            }
            for item in report.candidate_scores
        ],
        "manifest_audit": {
            "total_sources": report.manifest_audit.total_sources,
            "format_counts": report.manifest_audit.format_counts,
            "authority_counts": report.manifest_audit.authority_counts,
            "earliest_date": report.manifest_audit.earliest_date,
            "latest_date": report.manifest_audit.latest_date,
            "issues": [
                {"severity": item.severity, "message": item.message}
                for item in report.manifest_audit.issues
            ],
        },
        "source_previews": [
            {
                "source_id": item.source_id,
                "title": item.title,
                "excerpt": item.excerpt,
            }
            for item in report.source_previews
        ],
        "boundary_decisions": [
            {
                "question": item.question,
                "label": item.label,
                "reason": item.reason,
                "matched_keywords": item.matched_keywords,
            }
            for item in report.boundary_decisions
        ],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
