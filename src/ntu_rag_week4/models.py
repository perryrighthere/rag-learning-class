from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ParsedSection:
    heading: str
    text: str
    order: int
    page: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    source_id: str
    title: str
    source_ref: str
    published_at: str
    format: str
    authority_type: str
    parser_used: str
    clean_text: str
    sections: list[ParsedSection]


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    source_id: str
    document_title: str
    source_ref: str
    published_at: str
    format: str
    authority_type: str
    strategy: str
    chunk_index: int
    text: str
    char_count: int
    section_headings: list[str]
    page_numbers: list[int]
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ChunkHit:
    chunk: ChunkRecord
    score: float


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    parameters: dict[str, object]
    chunks: list[ChunkRecord]
    average_chunk_chars: float
    chunk_counts_by_source: dict[str, int]


@dataclass(frozen=True)
class Week4ChunkingReport:
    input_path: str
    total_documents: int
    source_ids: list[str]
    strategy_results: list[StrategyResult]


@dataclass(frozen=True)
class ChunkingRequest:
    input_path: Path
    strategies: list[str] | None = None
    fixed_chunk_size: int = 3
    fixed_overlap: int = 1
    structure_max_chars: int = 220
    structure_min_chunk_chars: int = 80
    langchain_chunk_size: int = 90
    langchain_chunk_overlap: int = 20
    preview_chunks: int = 2


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    api_key_env: str
    base_url: str
    timeout_seconds: int = 60
    app_name: str = "NTU RAG Teaching Repo"
    referer: str | None = None


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatCompletionResult:
    provider: str
    model: str
    content: str
    raw_response: dict[str, object]
    usage: dict[str, object]


@dataclass(frozen=True)
class Week4LiveAnswer:
    question: str
    answer: str
    provider: str
    model: str
    chunk_strategy: str
    evidence: list[ChunkHit]
    prompt_preview: str
    usage: dict[str, object]
