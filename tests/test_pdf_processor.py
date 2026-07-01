"""Tests for backend/services/pdf_processor.py. Logic added in S1."""

import fitz

from backend.models.schemas import ExtractionErrorType
from backend.services.pdf_processor import extract_pdf_text


def _make_pdf_bytes(num_pages: int = 1, with_text: bool = True) -> bytes:
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page()
        if with_text:
            page.insert_text((72, 72), "Hello world, this is a real extractable sentence.")
        else:
            # Vector drawing with no text — mimics a scanned/image-only page.
            page.draw_rect(fitz.Rect(10, 10, 500, 700), color=(0, 0, 0), fill=(0.5, 0.5, 0.5))
    data = doc.tobytes()
    doc.close()
    return data


def test_valid_pdf_returns_text_per_page():
    data = _make_pdf_bytes(num_pages=2, with_text=True)
    result = extract_pdf_text(data)

    assert result.success is True
    assert result.error_type is None
    assert result.page_count == 2
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert "extractable sentence" in result.pages[0].text
    assert result.sha256 is not None and len(result.sha256) == 64


def test_empty_pdf_returns_error():
    data = _make_pdf_bytes(num_pages=1, with_text=False)
    result = extract_pdf_text(data)

    assert result.success is False
    assert result.error_type == ExtractionErrorType.EMPTY
    assert result.error_message


def test_scanned_pdf_returns_warning_not_error():
    # Enough blank vector-drawing pages to push file size above the 10KB threshold.
    data = _make_pdf_bytes(num_pages=60, with_text=False)
    assert len(data) > 10 * 1024

    result = extract_pdf_text(data)

    assert result.success is True
    assert result.error_type is None
    assert result.warning is not None


def test_corrupted_pdf_does_not_raise():
    data = b"not a real pdf" * 100
    result = extract_pdf_text(data)

    assert result.success is False
    assert result.error_type == ExtractionErrorType.CORRUPTED
    assert result.error_message


def test_password_protected_pdf_returns_error(tmp_path):
    doc = fitz.open()
    doc.new_page()
    enc_path = tmp_path / "encrypted.pdf"
    doc.save(
        str(enc_path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner123",
        user_pw="user123",
    )
    doc.close()

    result = extract_pdf_text(enc_path.read_bytes())

    assert result.success is False
    assert result.error_type == ExtractionErrorType.PASSWORD_PROTECTED
    assert result.error_message


def test_sha256_is_deterministic():
    data = _make_pdf_bytes(num_pages=1, with_text=True)
    first = extract_pdf_text(data)
    second = extract_pdf_text(data)

    assert first.sha256 == second.sha256


def test_accepts_file_path(tmp_path):
    data = _make_pdf_bytes(num_pages=1, with_text=True)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(data)

    result = extract_pdf_text(pdf_path)

    assert result.success is True
    assert result.page_count == 1
