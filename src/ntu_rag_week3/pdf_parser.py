from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None


@dataclass(frozen=True)
class PdfPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class PdfParseRequest:
    pdf_path: Path
    mineru_api_url: str | None = None
    fallback_parser: str = "auto"


@dataclass(frozen=True)
class PdfParseResult:
    pdf_path: str
    parser_used: str
    pages: list[PdfPage]
    text: str | None = None
    mineru_response: object | None = None


class PdfParserService:
    def parse(self, parse_request: PdfParseRequest) -> PdfParseResult:
        pdf_path = Path(parse_request.pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if parse_request.mineru_api_url:
            return PdfParseResult(
                pdf_path=str(pdf_path),
                parser_used="mineru-api",
                pages=[],
                text=None,
                mineru_response=_post_mineru_file_parse(
                    parse_request.mineru_api_url,
                    pdf_path,
                ),
            )

        parser_name = _choose_local_parser(parse_request.fallback_parser)
        if parser_name == "pypdf":
            pages = _parse_with_pypdf(pdf_path)
        else:
            pages = _parse_with_pymupdf(pdf_path)

        text = "\n\n".join(page.text for page in pages if page.text).strip() or None
        return PdfParseResult(
            pdf_path=str(pdf_path),
            parser_used=parser_name,
            pages=pages,
            text=text,
            mineru_response=None,
        )


def _choose_local_parser(fallback_parser: str) -> str:
    if fallback_parser not in {"auto", "pypdf", "pymupdf"}:
        raise ValueError(f"Unsupported fallback parser: {fallback_parser}")

    if fallback_parser == "pypdf":
        if PdfReader is None:
            raise RuntimeError("pypdf is not installed.")
        return "pypdf"

    if fallback_parser == "pymupdf":
        if fitz is None:
            raise RuntimeError("pymupdf is not installed.")
        return "pymupdf"

    if PdfReader is not None:
        return "pypdf"
    if fitz is not None:
        return "pymupdf"
    raise RuntimeError("Neither pypdf nor pymupdf is installed.")


def _parse_with_pypdf(pdf_path: Path) -> list[PdfPage]:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed.")

    reader = PdfReader(str(pdf_path))
    pages: list[PdfPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append(PdfPage(page_number=index, text=text))
    return pages


def _parse_with_pymupdf(pdf_path: Path) -> list[PdfPage]:
    if fitz is None:
        raise RuntimeError("pymupdf is not installed.")

    document = fitz.open(pdf_path)
    try:
        pages: list[PdfPage] = []
        for index, page in enumerate(document, start=1):
            pages.append(PdfPage(page_number=index, text=page.get_text("text").strip()))
        return pages
    finally:
        document.close()


def _build_multipart_form_data(
    file_path: Path,
    fields: list[tuple[str, str]],
) -> tuple[bytes, str]:
    boundary = f"----Week3PdfParser{uuid.uuid4().hex}"
    parts: list[bytes] = []

    for name, value in fields:
        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/pdf"
    parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="files"; '
                f'filename="{file_path.name}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(parts), boundary


def _post_mineru_file_parse(mineru_api_url: str, pdf_path: Path) -> object:
    body, boundary = _build_multipart_form_data(
        pdf_path,
        fields=[
            ("lang_list", "ch"),
            ("backend", "pipeline"),
            ("parse_method", "auto"),
            ("return_md", "false"),
            ("return_middle_json", "false"),
            ("return_model_output", "false"),
            ("return_content_list", "true"),
            ("return_images", "false"),
            ("response_format_zip", "false"),
        ],
    )
    api_request = request.Request(
        mineru_api_url.rstrip("/") + "/file_parse",
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with request.urlopen(api_request, timeout=300) as response:
            payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"MinerU API returned HTTP {exc.code}: {details.strip() or exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"MinerU API request failed: {exc.reason}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("MinerU API did not return JSON.") from exc
