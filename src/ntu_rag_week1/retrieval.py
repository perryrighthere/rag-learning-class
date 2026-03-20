from __future__ import annotations

from .embedding import HashingEmbedder, cosine_similarity
from .models import Chunk, RetrievedChunk


class InMemoryRetriever:
    def __init__(self, embedder: HashingEmbedder, chunks: list[Chunk]) -> None:
        self.embedder = embedder
        self.chunks = chunks
        self.chunk_vectors = [self.embedder.embed(chunk.text) for chunk in chunks]

    def query(self, question: str, top_k: int = 3) -> list[RetrievedChunk]:
        query_vector = self.embedder.embed(question)
        scored = [
            RetrievedChunk(chunk=chunk, score=cosine_similarity(query_vector, vector))
            for chunk, vector in zip(self.chunks, self.chunk_vectors)
        ]
        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        return ranked[:top_k]
