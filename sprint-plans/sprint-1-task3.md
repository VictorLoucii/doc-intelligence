# Sprint 1 — Task 3: Orchestration + DocumentMetadata + Dedup

**Scope:** `backend/services/pdf_processor.py` (final S1 task) + `backend/models/schemas.py` + `eval.py`. Ties Task 1 (`extract_pdf_text`) and Task 2 (`chunk_pages`) together.

**1. Add schema first (Rule 5.2)** — `ProcessPDFResult` in `schemas.py`:
```python
success: bool
metadata: DocumentMetadata | None = None
chunks: list[Chunk] = Field(default_factory=list)
is_duplicate: bool = False
error_type: ExtractionErrorType | None = None
error_message: str | None = None
warning: str | None = None
```

**2. Implement:**
```python
def process_pdf(source, filename: str, existing_hashes: dict[str, DocumentMetadata] | None = None) -> ProcessPDFResult
```
- Call `extract_pdf_text(source)`. If `success=False`, return `ProcessPDFResult(success=False, error_type=..., error_message=...)` — never chunk.
- **Dedup (Decision 12):** if `existing_hashes` provided and `sha256` is a key, return `ProcessPDFResult(success=True, is_duplicate=True, metadata=existing_hashes[sha256])` — skip chunking entirely. `existing_hashes` is caller-owned (router state, S5); this function stays stateless.
- Otherwise call `chunk_pages(pages, document_id=uuid4, document_name=filename)`, build `DocumentMetadata` (`status=COMPLETED`, `upload_time=datetime.utcnow()`, counts from extraction/chunks), return both.
- Never raise. Batch/multi-file looping is a router concern (S5) — this handles one PDF.

**3. Upgrade eval.py stubs** (lines ~319–380: `test_ingestion_valid_pdf_returns_metadata`, `_empty_pdf_returns_error`, `_corrupted_pdf_does_not_crash`, `_sha256_dedup_skips_duplicate`) to call real `process_pdf()`. Drop the dedup test's vector-store assertion — no vector store exists until S2.

Run `python eval.py` — must be 100%.
