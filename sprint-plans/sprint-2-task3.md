# Sprint 2 — Task 3 (final): End-to-End Retrieval Accuracy Test

**Scope:** `eval.py` only. No new production code in `embedding_service.py` or `vector_store.py` — router/ingestion wiring (`/upload`, `/query`) is Sprint 5's job, out of scope here.

**Why this task exists:** DESIGN.md §10's S2 verification line is "retrieval tests pass — verify top-50 contains known relevant chunks." The current `test_vector_store_add_and_search` only proves FAISS mechanics with random vectors — it does not prove semantic retrieval actually works with the real embedding model. CLAUDE.md §5.1 requires adding a test for exactly this gap before declaring S2 done.

**Add one new test, `test_retrieval_finds_known_relevant_chunk`:**
- Build 3–5 `Chunk` fixtures by hand (short, clearly distinct topics — e.g. one about "invoice payment terms," one about "solar panel efficiency," one about "employee vacation policy").
- Call `embedding_service.embed_chunks(chunks)`, then `vector_store.add_chunks(chunks, embeddings)`.
- Call `embedding_service.embed_query(...)` with a question whose answer clearly matches exactly one fixture chunk (e.g. "What are the payment terms for invoices?").
- Call `vector_store.search(query_embedding, top_k=50)`.
- Assert the matching chunk's `id` is present in the returned results — and, since it's the only real semantic match among random noise from earlier tests, assert it ranks first (`results[0]`) by score.

**Note:** `vector_store` holds module-level state — earlier tests (`test_vector_store_add_and_search`) will have already added 100 random vectors before this test runs. Don't add a `reset()`/clear function for this — real semantic cosine scores (~0.7–0.9) will dominate random-vector noise (~0), so no test isolation hack is needed.

**Verify:** `python eval.py` — 100%, Sprint 2 fully closed.
