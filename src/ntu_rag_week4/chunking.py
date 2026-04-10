from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ChunkRecord, ParsedDocument, ParsedSection


def split_sentences(text: str) -> list[str]:
    sentences = [item.strip() for item in re.findall(r"[^。！？!?；;]+[。！？!?；;]?", text)]
    return [sentence for sentence in sentences if sentence]


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        items.append(value)
    return items


def ordered_unique_int(values: list[int | None]) -> list[int]:
    seen: set[int] = set()
    items: list[int] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        items.append(value)
    return items


@dataclass(frozen=True)
class SentenceSpan:
    text: str
    section_heading: str
    section_order: int
    page: int | None
    sentence_index: int


@dataclass(frozen=True)
class SectionUnit:
    text: str
    section_heading: str
    section_order: int
    page: int | None


class FixedWindowChunker:
    strategy_name = "fixed-window"

    def __init__(self, chunk_size: int = 3, overlap: int = 1) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, document: ParsedDocument) -> list[ChunkRecord]:
        spans = _flatten_sentence_spans(document)
        if not spans:
            return []

        chunks: list[ChunkRecord] = []
        step = self.chunk_size - self.overlap
        for start in range(0, len(spans), step):
            window = spans[start : start + self.chunk_size]
            if not window:
                continue
            chunks.append(
                _make_chunk_record(
                    document=document,
                    strategy=self.strategy_name,
                    chunk_index=len(chunks) + 1,
                    text="\n".join(span.text for span in window),
                    section_headings=[span.section_heading for span in window],
                    page_numbers=[span.page for span in window],
                    metadata={
                        "sentence_count": len(window),
                        "start_sentence_index": window[0].sentence_index,
                        "end_sentence_index": window[-1].sentence_index,
                        "start_section_order": window[0].section_order,
                        "end_section_order": window[-1].section_order,
                    },
                )
            )
            if start + self.chunk_size >= len(spans):
                break
        return chunks


class StructureAwareChunker:
    strategy_name = "structure-aware"

    def __init__(self, max_chars: int = 220, min_chunk_chars: int = 80) -> None:
        if max_chars < 20:
            raise ValueError("max_chars must be >= 20")
        if min_chunk_chars < 1:
            raise ValueError("min_chunk_chars must be >= 1")
        if min_chunk_chars > max_chars:
            raise ValueError("min_chunk_chars must be <= max_chars")
        self.max_chars = max_chars
        self.min_chunk_chars = min_chunk_chars

    def split(self, document: ParsedDocument) -> list[ChunkRecord]:
        units: list[SectionUnit] = []
        for section in document.sections:
            section_text = section.text.strip()
            if not section_text:
                continue
            units.extend(_split_large_section(section, max_chars=self.max_chars))

        if not units:
            return []

        grouped_units: list[list[SectionUnit]] = []
        buffer: list[SectionUnit] = []
        buffer_chars = 0
        for unit in units:
            projected = buffer_chars + len(unit.text) + (2 if buffer else 0)
            if buffer and projected > self.max_chars:
                grouped_units.append(buffer)
                buffer = []
                buffer_chars = 0

            buffer.append(unit)
            buffer_chars += len(unit.text) + (2 if len(buffer) > 1 else 0)

        if buffer:
            grouped_units.append(buffer)

        grouped_units = _merge_short_tail_chunks(
            grouped_units=grouped_units,
            min_chunk_chars=self.min_chunk_chars,
        )

        chunks: list[ChunkRecord] = []
        for index, chunk_units in enumerate(grouped_units, start=1):
            chunks.append(
                _make_chunk_record(
                    document=document,
                    strategy=self.strategy_name,
                    chunk_index=index,
                    text="\n\n".join(unit.text for unit in chunk_units),
                    section_headings=[unit.section_heading for unit in chunk_units],
                    page_numbers=[unit.page for unit in chunk_units],
                    metadata={
                        "section_count": len(chunk_units),
                        "start_section_order": chunk_units[0].section_order,
                        "end_section_order": chunk_units[-1].section_order,
                        "merge_rule": "min_chunk_chars",
                    },
                )
            )
        return chunks


def _flatten_sentence_spans(document: ParsedDocument) -> list[SentenceSpan]:
    spans: list[SentenceSpan] = []
    sentence_index = 0
    for section in document.sections:
        for sentence in split_sentences(section.text):
            spans.append(
                SentenceSpan(
                    text=sentence,
                    section_heading=section.heading,
                    section_order=section.order,
                    page=section.page,
                    sentence_index=sentence_index,
                )
            )
            sentence_index += 1
    return spans


def _split_large_section(section: ParsedSection, max_chars: int) -> list[SectionUnit]:
    text = section.text.strip()
    if len(text) <= max_chars:
        return [
            SectionUnit(
                text=text,
                section_heading=section.heading,
                section_order=section.order,
                page=section.page,
            )
        ]

    sentences = split_sentences(text)
    if not sentences:
        return [
            SectionUnit(
                text=text,
                section_heading=section.heading,
                section_order=section.order,
                page=section.page,
            )
        ]

    units: list[SectionUnit] = []
    buffer: list[str] = []
    buffer_chars = 0
    for sentence in sentences:
        projected = buffer_chars + len(sentence) + (1 if buffer else 0)
        if buffer and projected > max_chars:
            units.append(
                SectionUnit(
                    text="\n".join(buffer),
                    section_heading=section.heading,
                    section_order=section.order,
                    page=section.page,
                )
            )
            buffer = []
            buffer_chars = 0

        buffer.append(sentence)
        buffer_chars += len(sentence) + (1 if len(buffer) > 1 else 0)

    if buffer:
        units.append(
            SectionUnit(
                text="\n".join(buffer),
                section_heading=section.heading,
                section_order=section.order,
                page=section.page,
            )
        )
    return units


def _merge_short_tail_chunks(
    grouped_units: list[list[SectionUnit]],
    min_chunk_chars: int,
) -> list[list[SectionUnit]]:
    if len(grouped_units) < 2:
        return grouped_units

    merged = [list(group) for group in grouped_units]
    while len(merged) >= 2:
        tail_chars = len("\n\n".join(unit.text for unit in merged[-1]))
        if tail_chars >= min_chunk_chars:
            break
        merged[-2].extend(merged[-1])
        merged.pop()
    return merged


def _make_chunk_record(
    document: ParsedDocument,
    strategy: str,
    chunk_index: int,
    text: str,
    section_headings: list[str],
    page_numbers: list[int | None],
    metadata: dict[str, object],
) -> ChunkRecord:
    normalized_text = text.strip()
    return ChunkRecord(
        chunk_id=f"{document.source_id}-{strategy}-{chunk_index:03d}",
        source_id=document.source_id,
        document_title=document.title,
        source_ref=document.source_ref,
        published_at=document.published_at,
        format=document.format,
        authority_type=document.authority_type,
        strategy=strategy,
        chunk_index=chunk_index,
        text=normalized_text,
        char_count=len(normalized_text),
        section_headings=ordered_unique(section_headings),
        page_numbers=ordered_unique_int(page_numbers),
        metadata=metadata,
    )
