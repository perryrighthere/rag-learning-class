from __future__ import annotations

from pathlib import Path

from .chunking import SentenceChunker
from .embedding import HashingEmbedder
from .generation import ExtractiveAnswerGenerator
from .loader import load_markdown_documents
from .models import RagAnswer
from .retrieval import InMemoryRetriever


class MinimalRAGPipeline:
    def __init__(self, corpus_dir: Path, chunk_size: int = 2, overlap: int = 1) -> None:
        documents = load_markdown_documents(corpus_dir)
        chunker = SentenceChunker(chunk_size=chunk_size, overlap=overlap)
        chunks = [chunk for document in documents for chunk in chunker.split(document)]
        if not chunks:
            raise ValueError("No chunks were produced from the corpus.")

        self.retriever = InMemoryRetriever(HashingEmbedder(), chunks)
        self.generator = ExtractiveAnswerGenerator()

    def ask(self, question: str, top_k: int = 3) -> RagAnswer:
        evidence = self.retriever.query(question=question, top_k=top_k)
        return self.generator.generate(question=question, evidence=evidence)


def build_demo_pipeline(corpus_dir: Path | None = None) -> MinimalRAGPipeline:
    root = Path(__file__).resolve().parents[2]
    target = corpus_dir or root / "data" / "week1_corpus"
    return MinimalRAGPipeline(target)
