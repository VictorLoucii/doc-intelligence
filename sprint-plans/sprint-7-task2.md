# Sprint 7 — Task 2: Wire `POST /insights`

**Goal:** Expose `insight_engine.generate_insights()` (built in Task 1) via the API.

**1. New accessor in `backend/services/vector_store.py`:**
`all_chunks() -> list[Chunk]` — returns every chunk currently indexed, across all documents. Read-only; does not modify `_index`/`_chunks_by_id`. Extends the narrow-accessor pattern from Decision 17 (routers must not read private state directly).

**2. Endpoint in `backend/routers/query.py`:**
`POST /insights`, no request body, `response_model=list[InsightSuggestion]`.
- If `vector_store.is_empty()` → `HTTPException(400, "Please upload at least one document before asking questions.")` (same message as `/query`, for consistency).
- Else: `chunks = vector_store.all_chunks()`, `return insight_engine.generate_insights(chunks)`.
- `generate_insights()` already returns `[]` for <2 documents — do not duplicate that check in the router.

**Do NOT** touch `/query`, `/upload`, or any frontend file.

**Verify:** Add eval test(s) for: empty store → 400; single document uploaded → 200 with `[]`; ≥2 documents (mock the Anthropic call as Task 1's test does) → 200 with valid `InsightSuggestion` list. Run `python eval.py` — must stay at 100%.

**Docs:** If `all_chunks()` extends the accessor surface described in Decision 17, add one sentence there noting it (not a new decision — it's the same pattern, just one more accessor).

**Commit:** Only after eval is green. Message format: `"S7 T2: [Feature Name]"`.
