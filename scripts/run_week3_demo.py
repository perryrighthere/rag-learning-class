from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week3 import PdfParseRequest, PdfParserService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Week 3 standalone PDF parser service demo.",
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF file.")
    parser.add_argument(
        "--mineru-api-url",
        default=None,
        help="Optional MinerU API base URL. If set, the service returns raw MinerU JSON.",
    )
    parser.add_argument(
        "--parser",
        choices=("auto", "pypdf", "pymupdf"),
        default="auto",
        help="Local fallback parser when MinerU is not used.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service = PdfParserService()
    result = service.parse(
        PdfParseRequest(
            pdf_path=Path(args.pdf),
            mineru_api_url=args.mineru_api_url,
            fallback_parser=args.parser,
        )
    )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 0

    print(f"pdf_path: {result.pdf_path}")
    print(f"parser_used: {result.parser_used}")
    if result.mineru_response is not None:
        keys = sorted(result.mineru_response.keys()) if isinstance(result.mineru_response, dict) else []
        print(f"mineru_response_keys: {keys}")
        print("note: MinerU raw response is returned as-is for students to clean later.")
        return 0

    print(f"pages: {len(result.pages)}")
    preview = (result.text or "")[:300]
    print(f"text_preview: {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
