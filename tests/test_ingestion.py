from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter

from src.ingestion import DocumentError, load_document, normalize_text, sha256_file


def _write_pdf(path: Path, text: str) -> None:
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (
            3,
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        ),
        (
            4,
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
            + content
            + b"\nendstream",
        ),
        (5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in objects:
        offsets.append(len(data))
        data += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects) + 1}\n".encode()
    data += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        data += f"{offset:010d} 00000 n \n".encode()
    data += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(data))


def test_normalize_text_joins_wrapped_lines_and_dehyphenates() -> None:
    text = "This is a long-\nline about a policy.\n\n- First item\n- Second item"
    assert normalize_text(text) == (
        "This is a longline about a policy.\n\n- First item\n\n- Second item"
    )


def test_normalize_text_cleans_pdf_replacement_characters() -> None:
    assert normalize_text("Dean\ufffds award. Microsoft 365\ufffd") == "Dean's award. Microsoft 365"


def test_load_txt_returns_one_block(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("  Remote work is allowed.\n\nReport lost devices.  ", encoding="utf-8")
    blocks = load_document(path)
    assert len(blocks) == 1
    assert blocks[0].page is None
    assert blocks[0].section is None
    assert "Remote work is allowed." in blocks[0].text


def test_load_markdown_keeps_sections(tmp_path: Path) -> None:
    path = tmp_path / "policy.md"
    path.write_text(
        "# Policy\n\nIntro.\n\n## Eligibility\n\n90 days.\n\n## Travel\n\n$180 per night.\n",
        encoding="utf-8",
    )
    blocks = load_document(path)
    assert [block.section for block in blocks] == ["Policy", "Eligibility", "Travel"]
    assert all(block.page is None for block in blocks)


def test_load_docx_keeps_headings_and_tables(tmp_path: Path) -> None:
    path = tmp_path / "policy.docx"
    document = Document()
    document.add_heading("Equipment", level=1)
    document.add_paragraph("The stipend is $600.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Limit"
    table.cell(1, 0).text = "Hotel"
    table.cell(1, 1).text = "$180"
    document.save(path)

    blocks = load_document(path)
    combined = "\n".join(block.text for block in blocks)
    assert any(block.section == "Equipment" for block in blocks)
    assert "$600" in combined
    assert "Hotel | $180" in combined


def test_load_pdf_keeps_page_numbers(tmp_path: Path) -> None:
    path = tmp_path / "policy.pdf"
    _write_pdf(path, "Hello RAG PDF")
    blocks = load_document(path)
    assert len(blocks) == 1
    assert blocks[0].page == 1
    assert "Hello RAG PDF" in blocks[0].text


def test_blank_pdf_reports_ocr_needed(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as handle:
        writer.write(handle)

    with pytest.raises(DocumentError, match="OCR"):
        load_document(path)


def test_password_protected_pdf_reports_password(tmp_path: Path) -> None:
    path = tmp_path / "locked.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("secret")
    with open(path, "wb") as handle:
        writer.write(handle)

    with pytest.raises(DocumentError, match="password-protected"):
        load_document(path)


def test_empty_document_raises(tmp_path: Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("  \n\n ", encoding="utf-8")
    with pytest.raises(DocumentError, match="No extractable text"):
        load_document(path)


def test_unsupported_and_missing_documents_raise(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("a,b", encoding="utf-8")
    with pytest.raises(DocumentError, match="Unsupported"):
        load_document(path)
    with pytest.raises(DocumentError, match="not found"):
        load_document(tmp_path / "absent.pdf")


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_bytes(b"same bytes")
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64
