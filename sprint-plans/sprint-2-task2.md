# Sprint 2 — Task 2: FAISS Vector Store

**Scope:** `backend/services/vector_store.py` only. Consumes Task 1's `embed_chunks`/`embed_query` output. No ingestion wiring, no reranker.

**Requirements (DESIGN.md §3.2 Stage 1, §4 Layer 1; Decision 4):**
- `IndexFlatIP` (exact cosine, since Task 1 already L2-normalizes), `dim=1024`. In-memory only — no disk persistence, no Docker.
- Maintain a parallel `dict[int, Chunk]` (or list) mapping FAISS internal row IDs → `Chunk` objects, since FAISS itself only stores vectors. Use `IndexIDMap` (or equivalent) if you need stable IDs across deletes.

**Three functions:**
- `add_chunks(chunks: list[Chunk], embeddings: np.ndarray) -> None` — appends vectors + chunk metadata to the index. Append-only (CLAUDE.md §5.9) — never called from the query path.
- `search(query_embedding: np.ndarray, top_k: int = 50) -> list[tuple[Chunk, float]]` — returns up to `top_k` `(Chunk, score)` pairs, descending by score. If the index is empty, return `[]` — do not raise (caller/router turns this into the 400 from DESIGN.md §7).
- `delete_document(document_id: str) -> None` — removes all chunks for a document (rebuild index from remaining chunks; FAISS `IndexFlatIP` doesn't support in-place removal).

**Out of scope:** reranker, ingestion/query router wiring, embedding generation — Task 1 (done) / Task 3.

**Verify:** upgrade `test_vector_store_add_and_search` and `test_vector_store_empty_returns_error` in `eval.py` to call the real `add_chunks`/`search` — assert top_k=50 returns exactly 50 descending-score results, and an empty store returns `[]` without raising.
