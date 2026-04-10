from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week4 import ChunkingRequest, FixedWindowChunker, StructureAwareChunker
from ntu_rag_week4.langchain_chunking import LangChainRecursiveChunker
from ntu_rag_week4.models import ParsedDocument, ParsedSection
from ntu_rag_week4.pipeline import (
    build_week4_chunking_report,
    export_week4_chunking_artifacts,
    load_parsed_documents,
)


def build_sample_document() -> ParsedDocument:
    return ParsedDocument(
        source_id="doc-1",
        title="样例制度",
        source_ref="internal://sample",
        published_at="2025-01-01",
        format="md",
        authority_type="policy",
        parser_used="markdown-normalizer",
        clean_text=(
            "访问审批要记录申请人。审批链要可追踪。导出动作要留痕。"
            "例外情况需要主管签字。"
        ),
        sections=[
            ParsedSection(
                heading="记录要求",
                text="访问审批要记录申请人。审批链要可追踪。导出动作要留痕。",
                order=1,
                page=1,
            ),
            ParsedSection(
                heading="例外处理",
                text="例外情况需要主管签字。",
                order=2,
                page=2,
            ),
        ],
    )


class FixedWindowChunkerTest(unittest.TestCase):
    def test_fixed_window_keeps_overlap_and_metadata(self) -> None:
        chunks = FixedWindowChunker(chunk_size=2, overlap=1).split(build_sample_document())

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].section_headings, ["记录要求"])
        self.assertEqual(chunks[1].section_headings, ["记录要求"])
        self.assertEqual(chunks[2].section_headings, ["记录要求", "例外处理"])
        self.assertEqual(chunks[2].page_numbers, [1, 2])
        self.assertEqual(chunks[1].metadata["start_sentence_index"], 1)


class StructureAwareChunkerTest(unittest.TestCase):
    def test_structure_aware_merges_short_tail(self) -> None:
        document = ParsedDocument(
            source_id="doc-structure",
            title="结构化样例",
            source_ref="internal://structure",
            published_at="2025-01-01",
            format="md",
            authority_type="policy",
            parser_used="markdown-normalizer",
            clean_text=(
                "访问审批要记录申请人。审批链要可追踪。导出动作要留痕。"
                "复核结果要归档。超期申请要升级。例外情况需要主管签字。"
            ),
            sections=[
                ParsedSection(
                    heading="记录要求",
                    text=(
                        "访问审批要记录申请人。审批链要可追踪。导出动作要留痕。"
                        "复核结果要归档。超期申请要升级。"
                    ),
                    order=1,
                    page=1,
                ),
                ParsedSection(
                    heading="例外处理",
                    text="例外情况需要主管签字。",
                    order=2,
                    page=2,
                ),
            ],
        )
        chunks = StructureAwareChunker(max_chars=35, min_chunk_chars=15).split(
            document
        )

        self.assertEqual(len(chunks), 2)
        self.assertIn("例外处理", chunks[-1].section_headings)
        self.assertGreaterEqual(chunks[-1].char_count, 15)


class LangChainRecursiveChunkerTest(unittest.TestCase):
    def test_langchain_chunker_can_run_with_patched_splitter(self) -> None:
        class FakeSplitter:
            def __init__(self, **_: object) -> None:
                pass

            def split_documents(self, documents: list[object]) -> list[object]:
                results: list[object] = []
                for item in documents:
                    midpoint = max(1, len(item.page_content) // 2)
                    results.append(type(item)(page_content=item.page_content[:midpoint], metadata=item.metadata))
                    results.append(type(item)(page_content=item.page_content[midpoint:], metadata=item.metadata))
                return results

        with patch("ntu_rag_week4.langchain_chunking.RecursiveCharacterTextSplitter", FakeSplitter):
            chunks = LangChainRecursiveChunker(chunk_size=20, chunk_overlap=5).split(
                build_sample_document()
            )

        self.assertGreaterEqual(len(chunks), 4)
        self.assertEqual(chunks[0].strategy, "langchain-recursive")
        self.assertEqual(chunks[0].section_headings, ["记录要求"])


class PipelineTest(unittest.TestCase):
    def test_load_parsed_documents_and_export_artifacts(self) -> None:
        payload = {
            "source_id": "doc-1",
            "title": "样例制度",
            "source_ref": "internal://sample",
            "published_at": "2025-01-01",
            "format": "md",
            "authority_type": "policy",
            "parser_used": "markdown-normalizer",
            "clean_text": "访问审批要记录申请人。审批链要可追踪。",
            "sections": [
                {
                    "heading": "记录要求",
                    "text": "访问审批要记录申请人。审批链要可追踪。",
                    "order": 1,
                    "page": 1,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "parsed_documents.jsonl"
            input_path.write_text(
                json.dumps(payload, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            documents = load_parsed_documents(input_path)
            self.assertEqual(documents[0].sections[0].heading, "记录要求")

            with patch("ntu_rag_week4.langchain_chunking.RecursiveCharacterTextSplitter") as splitter_cls:
                splitter = splitter_cls.return_value
                splitter.split_documents.side_effect = lambda docs: docs

                report = build_week4_chunking_report(
                    ChunkingRequest(
                        input_path=input_path,
                        strategies=["fixed-window", "structure-aware", "langchain-recursive"],
                        fixed_chunk_size=2,
                        fixed_overlap=1,
                        structure_max_chars=35,
                        structure_min_chunk_chars=10,
                        langchain_chunk_size=30,
                        langchain_chunk_overlap=5,
                    )
                )

            export_dir = Path(temp_dir) / "exports"
            export_week4_chunking_artifacts(report, export_dir)

            self.assertEqual(report.total_documents, 1)
            self.assertEqual(len(report.strategy_results), 3)
            self.assertTrue((export_dir / "chunk_report.json").exists())
            self.assertTrue((export_dir / "fixed-window.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
