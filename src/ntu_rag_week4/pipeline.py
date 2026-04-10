from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .chunking import FixedWindowChunker, StructureAwareChunker
from .langchain_chunking import LangChainRecursiveChunker
from .models import (
    ChunkRecord,
    ChunkingRequest,
    ParsedDocument,
    ParsedSection,
    StrategyResult,
    Week4ChunkingReport,
)


SUPPORTED_STRATEGIES = (
    "fixed-window",
    "structure-aware",
    "langchain-recursive",
)


def default_week4_input_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "week3_parsing"
        / "compliance_ops"
        / "exports"
        / "parsed_documents.jsonl"
    )


def load_parsed_documents(input_path: Path) -> list[ParsedDocument]:
    documents: list[ParsedDocument] = []
    for line in Path(input_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        sections_payload = payload.get("sections") or [
            {
                "heading": "正文",
                "text": payload.get("clean_text", ""),
                "order": 1,
                "page": None,
            }
        ]
        sections = [
            ParsedSection(
                heading=str(section.get("heading") or "正文"),
                text=str(section.get("text") or ""),
                order=int(section.get("order") or index),
                page=section.get("page"),
            )
            for index, section in enumerate(sections_payload, start=1)
        ]
        documents.append(
            ParsedDocument(
                source_id=str(payload["source_id"]),
                title=str(payload["title"]),
                source_ref=str(payload["source_ref"]),
                published_at=str(payload["published_at"]),
                format=str(payload["format"]),
                authority_type=str(payload["authority_type"]),
                parser_used=str(payload["parser_used"]),
                clean_text=str(payload.get("clean_text") or ""),
                sections=sections,
            )
        )
    return documents


def build_week4_chunking_report(
    request: ChunkingRequest | None = None,
) -> Week4ChunkingReport:
    request = request or ChunkingRequest(input_path=default_week4_input_path())
    strategy_names = request.strategies or list(SUPPORTED_STRATEGIES)
    _validate_strategies(strategy_names)

    documents = load_parsed_documents(request.input_path)
    strategy_results: list[StrategyResult] = []
    for strategy_name in strategy_names:
        chunks = _run_strategy(
            strategy_name=strategy_name,
            documents=documents,
            request=request,
        )
        chunk_counts = Counter(chunk.source_id for chunk in chunks)
        average = (
            round(sum(chunk.char_count for chunk in chunks) / len(chunks), 2)
            if chunks
            else 0.0
        )
        strategy_results.append(
            StrategyResult(
                strategy=strategy_name,
                parameters=_strategy_parameters(strategy_name, request),
                chunks=chunks,
                average_chunk_chars=average,
                chunk_counts_by_source=dict(chunk_counts),
            )
        )

    return Week4ChunkingReport(
        input_path=str(request.input_path),
        total_documents=len(documents),
        source_ids=[document.source_id for document in documents],
        strategy_results=strategy_results,
    )


def export_week4_chunking_artifacts(
    report: Week4ChunkingReport,
    export_dir: Path,
) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    report_payload = asdict(report)
    (export_dir / "chunk_report.json").write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for strategy_result in report.strategy_results:
        chunk_path = export_dir / f"{strategy_result.strategy}.jsonl"
        with chunk_path.open("w", encoding="utf-8") as handle:
            for chunk in strategy_result.chunks:
                handle.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def render_week4_report(report: Week4ChunkingReport, preview_chunks: int = 2) -> str:
    lines = [
        f"Week 4 input: {report.input_path}",
        f"documents: {report.total_documents}",
        f"source_ids: {', '.join(report.source_ids)}",
    ]
    for strategy_result in report.strategy_results:
        lines.extend(
            [
                "",
                f"[{strategy_result.strategy}]",
                f"  parameters: {strategy_result.parameters}",
                f"  total_chunks: {len(strategy_result.chunks)}",
                f"  average_chunk_chars: {strategy_result.average_chunk_chars}",
                f"  chunk_counts_by_source: {strategy_result.chunk_counts_by_source}",
                "  sample_chunks:",
            ]
        )
        for chunk in strategy_result.chunks[:preview_chunks]:
            preview = chunk.text.replace("\n", " ")[:120]
            lines.append(
                f"    - {chunk.chunk_id} | chars={chunk.char_count} | sections={chunk.section_headings} | preview={preview}"
            )
    return "\n".join(lines)


def _validate_strategies(strategy_names: list[str]) -> None:
    unknown = sorted(set(strategy_names) - set(SUPPORTED_STRATEGIES))
    if unknown:
        raise ValueError(f"Unsupported strategy names: {unknown}")


def _run_strategy(
    strategy_name: str,
    documents: list[ParsedDocument],
    request: ChunkingRequest,
) -> list[ChunkRecord]:
    if strategy_name == "fixed-window":
        chunker = FixedWindowChunker(
            chunk_size=request.fixed_chunk_size,
            overlap=request.fixed_overlap,
        )
    elif strategy_name == "structure-aware":
        chunker = StructureAwareChunker(
            max_chars=request.structure_max_chars,
            min_chunk_chars=request.structure_min_chunk_chars,
        )
    else:
        chunker = LangChainRecursiveChunker(
            chunk_size=request.langchain_chunk_size,
            chunk_overlap=request.langchain_chunk_overlap,
        )

    chunks: list[ChunkRecord] = []
    for document in documents:
        chunks.extend(chunker.split(document))
    return chunks


def _strategy_parameters(
    strategy_name: str,
    request: ChunkingRequest,
) -> dict[str, object]:
    if strategy_name == "fixed-window":
        return {
            "chunk_size": request.fixed_chunk_size,
            "overlap": request.fixed_overlap,
            "unit": "sentence",
        }
    if strategy_name == "structure-aware":
        return {
            "max_chars": request.structure_max_chars,
            "min_chunk_chars": request.structure_min_chunk_chars,
            "unit": "section-first",
        }
    return {
        "chunk_size": request.langchain_chunk_size,
        "chunk_overlap": request.langchain_chunk_overlap,
        "splitter": "RecursiveCharacterTextSplitter",
    }
