from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week1.chunking import SentenceChunker
from ntu_rag_week1.models import Document
from ntu_rag_week1.pipeline import build_demo_pipeline


class SentenceChunkerTest(unittest.TestCase):
    def test_chunker_keeps_overlap(self) -> None:
        document = Document(
            path="memory.md",
            title="Memory",
            text="第一句。第二句。第三句。第四句。",
        )
        chunker = SentenceChunker(chunk_size=2, overlap=1)
        chunks = chunker.split(document)

        self.assertEqual(len(chunks), 3)
        self.assertIn("第二句。", chunks[0].text)
        self.assertIn("第二句。", chunks[1].text)


class MinimalRAGPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = build_demo_pipeline(ROOT / "data" / "week1_corpus")

    def test_pipeline_answers_five_stage_question(self) -> None:
        result = self.pipeline.ask("RAG 的最小闭环包含哪些环节？")

        self.assertIn("文档读取", result.answer)
        self.assertIn("检索", result.answer)
        self.assertGreaterEqual(len(result.evidence), 1)

    def test_pipeline_surfaces_evaluation_message(self) -> None:
        result = self.pipeline.ask("为什么不能只看回答像不像样？")

        self.assertTrue("测试集" in result.answer or "幻觉" in result.answer)
        self.assertGreaterEqual(len(result.evidence), 1)


if __name__ == "__main__":
    unittest.main()
