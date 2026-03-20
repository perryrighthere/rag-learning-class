from __future__ import annotations

from pathlib import Path

from .models import Document


def _read_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("#"):
            return line.lstrip("#").strip()
    return fallback


def _read_body(text: str) -> str:
    body_lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return "\n".join(body_lines).strip()


def load_markdown_documents(corpus_dir: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        documents.append(
            Document(
                path=str(path),
                title=_read_title(text, path.stem),
                text=_read_body(text),
            )
        )
    if not documents:
        raise FileNotFoundError(f"No markdown documents found in {corpus_dir}")
    return documents
