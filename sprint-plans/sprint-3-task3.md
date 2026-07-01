# Sprint 3 — Task 3 (final): End-to-End Reranking Precision Test

**Scope:** `eval.py` only. No new production code in `reranker.py`/`vector_store.py` — this proves the S3 acceptance criterion (DESIGN.md §10: "reranking improves precision over bi-encoder alone"), it doesn't add features.

**Build a labeled fixture (8–12 `Chunk`s):**
- 5 genuinely relevant to a test query (reuse/extend the 5-relevant fixture from T1's fixed test if convenient).
- 3–5 "near-miss" decoys: semantically similar surface wording to the query but a different actual topic — designed to fool bi-encoder cosine similarity, which cross-encoder attention should correctly demote.

**Test `test_reranker_improves_precision`:**
- `embed_chunks` + `vector_store.add_chunks` the fixture.
- Bi-encoder precision@5: `vector_store.search(query_embedding, top_k=5)` directly — compute fraction of the 5 that are truly relevant.
- Reranker precision@5: `vector_store.search(..., top_k=50)` → `reranker.rerank(query, candidates, top_k=5)` — same fraction.
- Assert reranker precision@5 >= bi-encoder precision@5 (strictly greater on this fixture, since decoys are crafted to fool bi-encoder only).

**Note:** `vector_store` is module-level state — earlier tests' vectors are already in the index (same caveat as S2 T3). Real cosine/cross-encoder scores dominate noise; no reset needed.

**Verify:** `python eval.py` — 100%, Sprint 3 fully closed.
