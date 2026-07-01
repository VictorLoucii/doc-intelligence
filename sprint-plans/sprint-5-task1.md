# Sprint 5 — Task 1: Documents Router (Upload, List, Delete)

**Scope:** `backend/routers/documents.py` only. No query/insights routing (Task 2), no frontend (Task 3), no eval.py (Task 4).

**Requirements (DESIGN.md §4 Layer 2, §7, §9; CLAUDE.md §5.2, §5.7, §5.9; Decision 12):**
- Module-level in-memory store: `_documents: dict[str, DocumentMetadata] = {}` keyed by document `id`. Build `existing_hashes` for dedup as `{d.sha256: d for d in _documents.values()}` — don't maintain a second synced dict.
- `POST /upload` — accepts `files: list[UploadFile]` (multipart). For each file: read bytes, call `pdf_processor.process_pdf(bytes, file.filename, existing_hashes)`. On success and not a duplicate: `embedding_service.embed_chunks(chunks)` → `vector_store.add_chunks(chunks, embeddings)`, then store `metadata` in `_documents`. Always return HTTP 200 with body `list[ProcessPDFResult]` (reuse the existing schema — no new model needed) so one bad file in the batch doesn't fail the others (CLAUDE.md §5.7).
- `GET /documents` — returns `list[DocumentMetadata]` from `_documents.values()`.
- `DELETE /documents/{document_id}` — pop from `_documents`; call `vector_store.delete_document(document_id)`. 404 if `document_id` not found.

**Out of scope:** `/query`, `/insights` (Task 2). No frontend wiring yet.

**Docs:** None yet — the in-memory `_documents` store and the "always-200, per-file result list" upload contract get logged in Task 4's DECISIONS.md entry.

**Verify:** No eval.py change this task (Section 6 tests stay stubs — that's Task 4's job). Sanity-check manually via `/docs` Swagger UI or `curl -F files=@sample.pdf localhost:8000/upload`. `python eval.py` must stay at 100% (no regressions).
