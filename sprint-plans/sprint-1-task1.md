# Sprint 1 — Task 1: PDF Extraction & Validation

**Scope:** `backend/services/pdf_processor.py` — extraction stage only. No chunking, no metadata assembly, no router wiring.

**Function:** implement a single function that accepts a file path (or bytes) and returns per-page extracted text plus raw validation facts. Do not construct `DocumentMetadata` yet (that's Task 3).

**Requirements (DESIGN.md §4, §7):**
- Use PyMuPDF (`fitz`) exclusively. Wrap `fitz.open()` in try/except.
- Extract text page-by-page via `page.get_text()`, preserving page number (1-indexed) per page's text — downstream chunking needs page attribution.
- Compute SHA-256 hash of the raw file bytes (Decision 12) — return it, do not check it against a store here.
- Detect and handle, per the exact table in DESIGN.md §7:
  - **Empty PDF**: all pages have `len(text.strip()) == 0` → return a structured error, do not raise.
  - **Scanned/image-only PDF**: empty text but file size > 10KB → structured warning, not a hard error.
  - **Corrupted PDF**: `fitz.FileDataError` → catch, `logging.error(..., exc_info=True)`, return structured error.
  - **Password-protected PDF**: `fitz.open()` encryption error → catch, return structured error.
- Never raise an uncaught exception — always return a result object indicating success/error type, so the caller (a later task) can skip this file and continue processing others.
- No dependency on `chunking`, `embedding_service`, or FastAPI routers in this task.

**Out of scope for this task:** chunking, `DocumentMetadata` construction, dedup lookup against a store, eval.py wiring (comes with Task 3's orchestration function, or add a minimal extraction-only eval check now if you prefer — your call).
