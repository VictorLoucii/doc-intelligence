# Sprint 3 — Task 1: Reranker Core (Model Load + rerank())

**Scope:** `backend/services/reranker.py` only. No threshold filtering (Task 2), no end-to-end eval (Task 3).

**Requirements (DESIGN.md §3.2 Stage 2, §4 Layer 1; CLAUDE.md §5.4, §5.5):**
- Load `cross-encoder/ms-marco-MiniLM-L-12-v2` via `sentence_transformers.CrossEncoder`, device pinned to `cuda:{settings.RERANKER_GPU_ID}` (config.py, already `1`). Never bare `cuda`.
- Load once at module level, not per call.
- CPU fallback (CLAUDE.md §5.4): if GPU load raises, catch, log via `logging.error(..., exc_info=True)`, retry on CPU. Never skip reranking.

**One function:**
- `rerank(query: str, candidates: list[tuple[Chunk, float]], top_k: int = 5) -> list[tuple[Chunk, float]]` — scores each `(query, chunk.text)` pair with the cross-encoder, returns top_k `(Chunk, score)` sorted descending by score. Mirrors `vector_store.search`'s return shape — no new Pydantic model needed.

**Out of scope:** relevance threshold (<0.3 filtering) — Task 2. Full retrieval pipeline wiring — Sprint 5.

**Docs:** No DESIGN.md/DECISIONS.md updates required for this task — model choice, GPU 1, and CPU-fallback behavior are already fully specified in DESIGN.md §3.2/§4 and CLAUDE.md §5.4/§5.5. Implementation must match, not redefine.

**Verify:** `test_reranker_gpu_allocation`, `test_reranker_reduces_candidates` in `eval.py` — upgrade from stubs to call `rerank()` for real; assert model device is `cuda:1` and output is exactly 5 items, scores descending. `python eval.py` must stay at 100%.
