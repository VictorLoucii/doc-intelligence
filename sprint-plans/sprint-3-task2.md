# Sprint 3 — Task 2: Relevance Threshold Filtering

**Scope:** `backend/services/reranker.py` (extend `rerank()`) + `backend/config.py` (new setting). No routing/answer-gen changes.

**Finding driving this task:** `CrossEncoder.predict()` for `ms-marco-MiniLM-L-12-v2` returns raw, unbounded logits — not a [0,1] probability. DESIGN.md §7's "score ≥ 0.3" threshold and `schemas.Citation.relevance_score` (`ge=0.0, le=1.0`) both assume a normalized score. Verify the raw range empirically first (quick script/print), then confirm sigmoid is the right fix before wiring it in.

**Requirements:**
- Inside `rerank()`, apply `torch.sigmoid` to raw scores before sorting/slicing, so every returned score is in [0,1].
- Add `RELEVANCE_THRESHOLD: float = 0.3` to `Settings` in `config.py`, alongside `RERANKER_GPU_ID`.
- After building the top-`k` list, drop any `(chunk, score)` pair with `score < settings.RELEVANCE_THRESHOLD`. Fewer than `top_k` results (including zero) is correct — this is DESIGN.md §7's "irrelevant query" case, handled properly in S4.

**Out of scope:** user-facing "no relevant info" message — that's `answer_generator.py`, Sprint 4.

**Docs (required, not optional this time):** Add a new `## Decision 14` to DECISIONS.md — sigmoid-normalizing cross-encoder logits before thresholding/citation use. ~10 lines, match existing decision format (Date/Status/Decision/Reason/Tradeoff).

**Verify:** `test_reranker_relevance_threshold` in `eval.py` — upgrade to real chunks/query via the actual model; assert all returned scores are within [0.3, 1.0]. `python eval.py` at 100%.
