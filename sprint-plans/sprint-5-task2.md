# Sprint 5 — Task 2: Query Router

**Scope:** `backend/routers/query.py`, plus two small read-only additions to `backend/services/vector_store.py`: `is_empty() -> bool` (`_index.ntotal == 0`) and `document_count() -> int` (count of distinct `chunk.document_id` across `_chunks_by_id`). No `/insights` (deferred — `insight_engine.py` doesn't exist yet, that's bonus S7), no frontend, no eval.py.

**Requirements (DESIGN.md §3.1 query flow, §7 "query before upload"; CLAUDE.md §5.4, §5.9):**
- `POST /query`, body = `QueryRequest`. Steps in order:
  1. `vector_store.is_empty()` → if true, raise `HTTPException(400, "Please upload at least one document before asking questions.")` (verbatim, DESIGN §7).
  2. `embedding_service.embed_query(request.question)`.
  3. `vector_store.search(query_embedding, top_k=50)` — **always 50**, a stage-1 constant independent of `request.top_k` (CLAUDE.md §5.4 — never conflate recall width with the final result count).
  4. `reranker.rerank(request.question, candidates, top_k=request.top_k)` — already threshold-filters internally, so an all-irrelevant query naturally yields `[]` and flows into `generate_answer`'s "insufficient information" branch. No extra handling needed here.
  5. `answer_generator.generate_answer(...)` and `.build_citations(...)`.
  6. Return `QueryResponse(answer, citations, query=request.question, documents_searched=vector_store.document_count(), chunks_evaluated=len(candidates), processing_time_ms=...)`. Time the handler with `time.perf_counter()`.
- Never call `vector_store.add_chunks`/`delete_document` from this router (CLAUDE.md §5.9).

**Docs:** None yet — flag for Task 4: DESIGN.md §7 literally says "`vector_store.ntotal == 0`"; actual implementation wraps it in `is_empty()` instead of reaching into a private attribute from the router. Log that as a Task 4 doc-sync item.

**Verify:** No eval.py change. Manually test via `/docs` or curl: query before any upload → 400; query after upload → 200 with citations; a clearly off-topic question → 200 with empty citations and the "insufficient information" message. `python eval.py` stays at 100%.
