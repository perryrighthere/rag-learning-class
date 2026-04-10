from __future__ import annotations

from langchain_core.documents import Document as LangChainDocument

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover
    RecursiveCharacterTextSplitter = None

from .chunking import ordered_unique, ordered_unique_int
from .models import ChunkRecord, ParsedDocument


class LangChainRecursiveChunker:
    strategy_name = "langchain-recursive"

    def __init__(self, chunk_size: int = 90, chunk_overlap: int = 20) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, document: ParsedDocument) -> list[ChunkRecord]:
        if RecursiveCharacterTextSplitter is None:
            raise RuntimeError(
                "langchain-text-splitters is not installed. Install requirements to use the LangChain baseline."
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        )

        section_documents = [
            LangChainDocument(
                page_content=section.text,
                metadata={
                    "source_id": document.source_id,
                    "document_title": document.title,
                    "source_ref": document.source_ref,
                    "published_at": document.published_at,
                    "format": document.format,
                    "authority_type": document.authority_type,
                    "section_heading": section.heading,
                    "section_order": section.order,
                    "page": section.page,
                },
            )
            for section in document.sections
            if section.text.strip()
        ]
        if not section_documents and document.clean_text.strip():
            section_documents = [
                LangChainDocument(
                    page_content=document.clean_text.strip(),
                    metadata={
                        "source_id": document.source_id,
                        "document_title": document.title,
                        "source_ref": document.source_ref,
                        "published_at": document.published_at,
                        "format": document.format,
                        "authority_type": document.authority_type,
                        "section_heading": "正文",
                        "section_order": 1,
                        "page": None,
                    },
                )
            ]

        split_documents = splitter.split_documents(section_documents)
        chunks: list[ChunkRecord] = []
        for index, item in enumerate(split_documents, start=1):
            metadata = dict(item.metadata)
            text = item.page_content.strip()
            page = metadata.get("page")
            section_heading = str(metadata.get("section_heading", "正文"))
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{document.source_id}-{self.strategy_name}-{index:03d}",
                    source_id=document.source_id,
                    document_title=document.title,
                    source_ref=document.source_ref,
                    published_at=document.published_at,
                    format=document.format,
                    authority_type=document.authority_type,
                    strategy=self.strategy_name,
                    chunk_index=index,
                    text=text,
                    char_count=len(text),
                    section_headings=ordered_unique([section_heading]),
                    page_numbers=ordered_unique_int([page if isinstance(page, int) else None]),
                    metadata={
                        "section_order": metadata.get("section_order"),
                        "splitter": "RecursiveCharacterTextSplitter",
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                    },
                )
            )
        return chunks
