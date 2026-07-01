# Sprint 6 — Task 2: Real Eval Test — Malformed Query

**Scope:** `eval.py` only (replace `test_edge_case_malformed_query` stub). No PDF tests (Task 1, done), no dedup test (Task 3). No new backend logic — `QueryRequest.question` already has `min_length=1, max_length=2000` (S0), and FastAPI's default Pydantic validation already turns violations into HTTP 422 with no custom exception handler overriding it (`backend/main.py` has none).

**Requirements:**
- Replace the fake stub body of `test_edge_case_malformed_query` in eval.py Section 7 with a real test using `fastapi.testclient.TestClient` against `backend.main.app` (follow the pattern in `test_api_query_before_upload_returns_400`):
  - `POST /query` with `{"question": "", "top_k": 5}` → assert `response.status_code == 422`.
  - `POST /query` with `{"question": "x" * 2001, "top_k": 5}` → assert `response.status_code == 422`.
  - No document upload needed — validation happens before the `vector_store.is_empty()` check.
- No documentation changes needed this task — §7's "422" for malformed question already matches actual behavior (no Decision-16-style conflict here).

**Out of scope:** password-protected PDF test (Task 1, done), duplicate-upload test (Task 3).

**Verify:** `python eval.py -k malformed` passes on real assertions (not the stub). Full `python eval.py` stays at 100% Logic Score.
