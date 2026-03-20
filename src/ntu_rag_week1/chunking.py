from __future__ import annotations

import re

from .models import Chunk, Document


def split_sentences(text: str) -> list[str]:
    sentences = [item.strip() for item in re.findall(r"[^。！？!?]+[。！？!?]?", text)]
    return [sentence for sentence in sentences if sentence]


class SentenceChunker:
    def __init__(self, chunk_size: int = 2, overlap: int = 1) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, document: Document) -> list[Chunk]:
        sentences = split_sentences(document.text)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        step = self.chunk_size - self.overlap
        for start in range(0, len(sentences), step):
            window = sentences[start : start + self.chunk_size]
            if not window:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{document.title}-chunk-{len(chunks) + 1}",
                    document_path=document.path,
                    document_title=document.title,
                    text=" ".join(window),
                    start_sentence=start,
                    end_sentence=start + len(window) - 1,
                )
            )
            if start + self.chunk_size >= len(sentences):
                break
        return chunks
