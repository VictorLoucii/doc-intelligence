"""PDF ingestion: extract text, chunk, build metadata. Logic added in S1."""

import hashlib
import logging
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from backend.models.schemas import Chunk, ExtractionErrorType, PageText, PDFExtractionResult

logger = logging.getLogger(__name__)

SCANNED_WARNING_MIN_BYTES = 10 * 1024

TOKENIZER_MODEL = "BAAI/bge-large-en-v1.5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " "]


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


@lru_cache(maxsize=1)
def _get_tokenizer():
    return AutoTokenizer.from_pretrained(TOKENIZER_MODEL)


def _token_count(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def chunk_pages(pages: list[PageText], document_id: str, document_name: str) -> list[Chunk]:
    """Split extracted page text into token-bounded chunks (DESIGN.md Section 6).

    `pages` must be the non-empty, page-attributed output of extract_pdf_text().
    A chunk that spans a page boundary is attributed to the page it starts on.
    """
    tokenizer = _get_tokenizer()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=CHUNK_SEPARATORS,
        length_function=lambda text: _token_count(tokenizer, text),
    )

    full_text_parts = []
    page_offsets: list[tuple[int, int]] = []
    offset = 0
    for page in pages:
        page_offsets.append((offset, page.page_number))
        full_text_parts.append(page.text)
        offset += len(page.text)
        full_text_parts.append("\n\n")
        offset += 2
    full_text = "".join(full_text_parts)

    raw_chunks = splitter.split_text(full_text)

    chunks: list[Chunk] = []
    search_start = 0
    chunk_index = 0
    for text in raw_chunks:
        if not text.strip():
            continue

        pos = full_text.find(text, search_start)
        if pos == -1:
            pos = full_text.find(text)
        if pos == -1:
            pos = search_start
        search_start = pos

        page_number = page_offsets[0][1]
        for start_offset, page_num in page_offsets:
            if start_offset <= pos:
                page_number = page_num
            else:
                break

        chunks.append(
            Chunk(
                id=str(uuid4()),
                document_id=document_id,
                document_name=document_name,
                text=text,
                page_number=page_number,
                chunk_index=chunk_index,
                token_count=_token_count(tokenizer, text),
            )
        )
        chunk_index += 1

    return chunks
