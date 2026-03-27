from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from .manifest import resolve_source_path
from .models import SourcePreview, SourceRecord


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_markdown(text: str) -> str:
    cleaned_lines: list[str] = []
    in_code_block = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line:
            continue
        line = re.sub(r"^\s*#+\s*", "", line)
        line = re.sub(r"^\s*[-*]\s+", "", line)
        line = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", line)
        cleaned_lines.append(line)
    return _collapse_whitespace(" ".join(cleaned_lines))


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.ignored_tag_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.ignored_tag_depth > 0:
            self.ignored_tag_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.ignored_tag_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)


def _strip_html(text: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(text)
    parser.close()
    return _collapse_whitespace(" ".join(parser.parts))


def load_source_text(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".md":
        return _strip_markdown(raw_text)
    if suffix in {".html", ".htm"}:
        return _strip_html(raw_text)
    return _collapse_whitespace(raw_text)


def load_source_preview(path: Path, max_chars: int = 160) -> str:
    text = load_source_text(path)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def build_source_previews(
    records: list[SourceRecord],
    scope_dir: Path,
    limit: int = 4,
) -> list[SourcePreview]:
    previews: list[SourcePreview] = []
    for record in records[:limit]:
        path = resolve_source_path(scope_dir, record)
        if not path.exists():
            excerpt = "[missing file]"
        else:
            excerpt = load_source_preview(path)
        previews.append(
            SourcePreview(
                source_id=record.source_id,
                title=record.title,
                excerpt=excerpt,
            )
        )
    return previews
