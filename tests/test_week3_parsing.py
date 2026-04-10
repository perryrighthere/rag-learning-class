from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week3 import PdfParseRequest, PdfParserService


class PdfParserServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PdfParserService()

    def test_mineru_api_returns_raw_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            payload = {"results": {"sample": {"content_list": "leave-for-students"}}}

            with patch(
                "ntu_rag_week3.pdf_parser._post_mineru_file_parse",
                return_value=payload,
            ) as post_mock:
                result = self.service.parse(
                    PdfParseRequest(
                        pdf_path=pdf_path,
                        mineru_api_url="http://127.0.0.1:18000",
                    )
                )

            self.assertEqual(result.parser_used, "mineru-api")
            self.assertEqual(result.mineru_response, payload)
            self.assertEqual(result.pages, [])
            self.assertIsNone(result.text)
            post_mock.assert_called_once()

    def test_local_pypdf_parser_returns_joined_text(self) -> None:
        class FakePage:
            def __init__(self, text: str) -> None:
                self._text = text

            def extract_text(self) -> str:
                return self._text

        class FakeReader:
            def __init__(self, _: str) -> None:
                self.pages = [FakePage("第一页"), FakePage("第二页")]

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            with patch("ntu_rag_week3.pdf_parser.PdfReader", FakeReader):
                result = self.service.parse(
                    PdfParseRequest(pdf_path=pdf_path, fallback_parser="pypdf")
                )

        self.assertEqual(result.parser_used, "pypdf")
        self.assertEqual(len(result.pages), 2)
        self.assertIn("第一页", result.text or "")
        self.assertIn("第二页", result.text or "")
        self.assertIsNone(result.mineru_response)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.service.parse(PdfParseRequest(pdf_path=Path("/tmp/does-not-exist.pdf")))

    def test_unsupported_fallback_parser_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with self.assertRaises(ValueError):
                self.service.parse(
                    PdfParseRequest(
                        pdf_path=pdf_path,
                        fallback_parser="unknown",
                    )
                )


if __name__ == "__main__":
    unittest.main()
