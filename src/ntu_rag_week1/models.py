from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    path: str
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_path: str
    document_title: str
    text: str
    start_sentence: int
    end_sentence: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class RagAnswer:
    question: str
    answer: str
    evidence: list[RetrievedChunk]
