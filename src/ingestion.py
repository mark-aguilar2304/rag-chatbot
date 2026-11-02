"""Extract text from one reference document while keeping page/section context."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".docx"}


class DocumentError(RuntimeError):
    """The reference document is missing, unsupported, or has no usable text."""


@dataclass(frozen=True)
class Block:
    text: str
    page: int | None = None
    section: str | None = None


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_document(path: str | Path) -> list[Block]:
    """Load a PDF, DOCX, TXT, or Markdown file into clean text blocks."""
    path = Path(path)
    if not path.is_file():
        raise DocumentError(f"Reference document not found: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        formats = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise DocumentError(f"Unsupported file type '{suffix}'. Supported types: {formats}.")

    try:
        if suffix == ".pdf":
            blocks = _load_pdf(path)
        elif suffix == ".docx":
            blocks = _load_docx(path)
        elif suffix in {".md", ".markdown"}:
            blocks = _load_markdown(path.read_text(encoding="utf-8-sig"))
        else:
            blocks = _text_blocks(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise DocumentError(f"{path.name} is not UTF-8 text. Save it as UTF-8 and try again.") from exc
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"Could not read {path.name}: {exc}") from exc

    blocks = [block for block in blocks if block.text.strip()]
    if not blocks:
        raise DocumentError(
            f"No extractable text found in {path.name}. If this is a scanned PDF, run OCR first."
        )
    return blocks


def normalize_text(text: str) -> str:
    """Join broken lines, keep paragraph breaks, and separate list items."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Some PDF fonts extract apostrophes as U+FFFD; keep the apostrophe, drop other artifacts.
    text = re.sub(r"(?<=[A-Za-z])\ufffd(?=[A-Za-z])", "'", text)
    text = text.replace("\ufffd", "")
    text = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "", text)

    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if re.match(r"^(?:[-*•]|\d+[.)])\s+", line) and current:
            paragraphs.append(" ".join(current))
            current = []
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs).strip()


def _text_blocks(text: str) -> list[Block]:
    cleaned = normalize_text(text)
    return [Block(cleaned)] if cleaned else []


def _clean_heading(text: str) -> str:
    return re.sub(r"[*_`]", "", text).strip().strip("#").strip()


def _load_markdown(text: str) -> list[Block]:
    blocks: list[Block] = []
    section: str | None = None
    lines: list[str] = []

    def flush() -> None:
        cleaned = normalize_text("\n".join(lines))
        if cleaned:
            blocks.append(Block(cleaned, section=section))
        lines.clear()

    for line in text.replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            flush()
            section = _clean_heading(heading.group(1))
        else:
            lines.append(line)
    flush()
    return blocks


def _load_pdf(path: Path) -> list[Block]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            unlocked = reader.decrypt("")
        except Exception as exc:
            raise DocumentError(f"{path.name} is password-protected. Remove the password first.") from exc
        if not unlocked:
            raise DocumentError(f"{path.name} is password-protected. Remove the password first.")

    blocks: list[Block] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            cleaned = normalize_text(page.extract_text() or "")
        except Exception:
            cleaned = ""
        if cleaned:
            blocks.append(Block(cleaned, page=page_number))
    return blocks


def _load_docx(path: Path) -> list[Block]:
    document = Document(str(path))
    blocks: list[Block] = []
    section: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        cleaned = normalize_text("\n".join(buffer))
        if cleaned:
            blocks.append(Block(cleaned, section=section))
        buffer.clear()

    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()
            style = (paragraph.style.name or "").lower() if paragraph.style else ""
            if style.startswith("heading") or style == "title":
                flush()
                section = text or section
            elif text:
                buffer.append(text)
        elif child.tag.endswith("}tbl"):
            flush()
            table = Table(child, document)
            rows = [
                " | ".join(cell.text.strip() for cell in row.cells)
                for row in table.rows
                if any(cell.text.strip() for cell in row.cells)
            ]
            if rows:
                blocks.append(Block("\n\n".join(rows), section=section))
    flush()
    return blocks
