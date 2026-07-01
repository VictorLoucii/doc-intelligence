"""PDF ingestion: extract text, chunk, build metadata. Logic added in S1."""

import hashlib
import logging
from pathlib import Path

import fitz

from backend.models.schemas import ExtractionErrorType, PageText, PDFExtractionResult

logger = logging.getLogger(__name__)

SCANNED_WARNING_MIN_BYTES = 10 * 1024


def extract_pdf_text(source: str | Path | bytes) -> PDFExtractionResult:
    """Extract per-page text and validation facts from a PDF (DESIGN.md Section 7).

    Accepts a file path or raw bytes. Never raises — always returns a
    PDFExtractionResult so the caller can skip a bad file and continue.
    """
    try:
        file_bytes = source if isinstance(source, bytes) else Path(source).read_bytes()
    except OSError as e:
        logger.error(f"Failed to read PDF source {source!r}: {e}", exc_info=True)
        return PDFExtractionResult(
            success=False,
            error_type=ExtractionErrorType.CORRUPTED,
            error_message=f"Could not read file: {e}",
        )

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    file_size_bytes = len(file_bytes)

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if doc.needs_pass:
            doc.close()
            return PDFExtractionResult(
                success=False,
                sha256=sha256,
                file_size_bytes=file_size_bytes,
                error_type=ExtractionErrorType.PASSWORD_PROTECTED,
                error_message="PDF is password-protected. Please upload an unlocked version.",
            )

        page_count = doc.page_count
        pages = [
            PageText(page_number=i + 1, text=doc.load_page(i).get_text())
            for i in range(page_count)
        ]
        doc.close()
    except fitz.FileDataError as e:
        logger.error(f"Corrupted PDF: {e}", exc_info=True)
        return PDFExtractionResult(
            success=False,
            sha256=sha256,
            file_size_bytes=file_size_bytes,
            error_type=ExtractionErrorType.CORRUPTED,
            error_message="PDF file is corrupted or unreadable.",
        )
    except Exception as e:
        logger.error(f"Unexpected error extracting PDF: {e}", exc_info=True)
        return PDFExtractionResult(
            success=False,
            sha256=sha256,
            file_size_bytes=file_size_bytes,
            error_type=ExtractionErrorType.CORRUPTED,
            error_message="PDF could not be processed.",
        )

    all_empty = all(len(p.text.strip()) == 0 for p in pages)

    if all_empty:
        if file_size_bytes > SCANNED_WARNING_MIN_BYTES:
            return PDFExtractionResult(
                success=True,
                pages=pages,
                sha256=sha256,
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                warning="PDF appears to be scanned. OCR not implemented.",
            )
        return PDFExtractionResult(
            success=False,
            pages=pages,
            sha256=sha256,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            error_type=ExtractionErrorType.EMPTY,
            error_message="PDF contains no extractable text.",
        )

    return PDFExtractionResult(
        success=True,
        pages=pages,
        sha256=sha256,
        file_size_bytes=file_size_bytes,
        page_count=page_count,
    )
