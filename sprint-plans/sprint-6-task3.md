# Sprint 6 — Task 3: Real Eval Test — Duplicate Upload Idempotency

**Scope:** `eval.py` only (replace `test_edge_case_duplicate_upload_idempotent` stub). This is the last Sprint 6 task — no further edge-case tasks after this. No new backend logic — SHA-256 dedup already works end-to-end (`pdf_processor.process_pdf` + `documents.py` upload router, Decision 12).

**Requirements:**
- Replace the fake stub body of `test_edge_case_duplicate_upload_idempotent` in eval.py Section 7 with a real test using `TestClient` against `backend.main.app` (follow the `finally`-cleanup pattern in `test_api_upload_endpoint_exists`):
  - `POST /upload` the same PDF bytes twice (reuse `_make_pdf_bytes()` helper already in eval.py).
  - Assert first response: `is_duplicate is False`, `metadata.chunk_count > 0`.
  - Assert second response: `is_duplicate is True`, same `metadata.id`/`sha256` as the first.
  - Assert the vector store did not grow: read `vector_store._index.ntotal` before the second upload and after, assert unchanged (mirrors existing precedent in `test_vector_store_empty_returns_error`, which already reads `_index.ntotal` directly in a test).
  - In a `finally`, delete the document via `DELETE /documents/{id}` to keep shared state clean for later test runs.
- No documentation changes needed — §7's dedup row already matches actual behavior.

**Out of scope:** any other stub or file. Sprint 6 ends after this task.

**Verify:** `python eval.py -k duplicate` passes on real assertions (not the stub). Full `python eval.py` stays at 100% Logic Score.
