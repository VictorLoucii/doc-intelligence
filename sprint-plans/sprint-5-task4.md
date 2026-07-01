# Sprint 5 — Task 4 (final): Real API Tests + Doc Sync

**Scope:** `eval.py` (S5 block only), `DECISIONS.md`, one-line `DESIGN.md` §7 edit. No new backend/frontend logic — if a real bug surfaces while wiring these tests, fix it minimally and call it out, don't silently patch.

**Critical ordering/isolation constraint:** `vector_store`/`documents._documents` are process-wide module singletons shared across the whole `eval.py` run (same discipline S2/S3 already follow — see `test_vector_store_empty_returns_error`'s "must be empty at the start of this test"). In the `all_tests` list, reorder the S5 block so `test_api_query_before_upload_returns_400` runs **first**, before any test uploads. Every other S5 test that uploads MUST clean up via `client.delete(f"/documents/{id}")` in a `finally:` block.

**Per test, using `fastapi.testclient.TestClient(app)` (lazy import inside each function) and the real-PDF pattern from `test_ingestion_valid_pdf_returns_metadata` (~line 325):**
1. `test_api_upload_endpoint_exists` — POST one PDF via `files={"files": (...)}`. Assert 200, `body[0]["success"] is True`, `metadata.page_count > 0`. Cleanup.
2. `test_api_query_endpoint_exists` — upload one PDF; mock `backend.services.answer_generator._client.messages.create` exactly as `test_generate_answer_api_wiring` does (~line 994) — never call the real Anthropic API here. POST `/query`, assert 200 and body validates as `QueryResponse`. Cleanup.
3. `test_api_documents_list_endpoint` — upload 2 PDFs, GET `/documents`, assert length 2. Cleanup both.
4. `test_api_query_before_upload_returns_400` — no setup, assert `status_code == 400`.

**Docs:** Add to `DECISIONS.md`: (a) `/upload` always returns 200 with `list[ProcessPDFResult]` so one bad file never fails the batch (Task 1); (b) `vector_store.is_empty()`/`document_count()` wrap private state instead of routers reading `_index.ntotal` directly (Task 2). Update `DESIGN.md` §7's "Query before any upload" row: `vector_store.ntotal == 0` → `vector_store.is_empty()`.

**Verify:** `python eval.py` → 34/34 at 100%. This is Sprint 5's last task — `git status` must be clean before Sprint 6 starts (CLAUDE.md §189).
