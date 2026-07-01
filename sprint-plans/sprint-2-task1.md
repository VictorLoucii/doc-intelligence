# Sprint 2 — Task 1: Embedding Service

**Scope:** `backend/services/embedding_service.py` only. No FAISS, no vector store, no ingestion wiring.

**Requirements (DESIGN.md §3.1, §4 Layer 1; CLAUDE.md §5.5):**
- Load `BAAI/bge-large-en-v1.5` via `sentence-transformers`, device pinned to `torch.device(f'cuda:{settings.EMBEDDING_GPU_ID}')` — read `EMBEDDING_GPU_ID` from `backend/config.py` (already `0`). Never bare `cuda`.
- Load the model once at module/service level, not per call.

**Two functions:**
- `embed_query(text: str) -> np.ndarray` — single query, returns a 1024-dim vector.
- `embed_chunks(chunks: list[Chunk]) -> np.ndarray` — batch-embeds `chunk.text` for a list of `Chunk` (schemas.py), returns shape `(N, 1024)`. Batch internally (e.g. `encode(..., batch_size=32)`) — don't loop one-by-one.
- Both must return float32, L2-normalized vectors (cosine via dot product downstream in FAISS `IndexFlatIP`).

**Out of scope:** FAISS indexing, query/ingestion pipeline wiring, reranker — Task 2/3.

**Verify:** `test_embedding_dimensionality`, `test_embedding_gpu_allocation` in `eval.py` (currently stubs) — upgrade them to call `embed_query`/`embed_chunks` for real and assert `cuda:0` + shape `(1024,)`/`(N,1024)`.
