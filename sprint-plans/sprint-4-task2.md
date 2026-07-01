# Sprint 4 — Task 2: Verbatim Citation Builder

**Scope:** `backend/services/answer_generator.py` (add one function) + `DECISIONS.md` (new entry). No eval.py changes (Task 3). No `QueryResponse` assembly — that's the S5 query router's job (`documents_searched`/`chunks_evaluated`/`processing_time_ms` aren't available in this module).

**Requirements (DESIGN.md §3.3, §5 Citation schema; CLAUDE.md §5.2, §5.3):**
- `build_citations(chunks: list[tuple[Chunk, float]]) -> list[Citation]` — one `Citation` per `(chunk, score)` pair:
  - `document_name=chunk.document_name`, `page_number=chunk.page_number`, `chunk_index=chunk.chunk_index`
  - `chunk_text=chunk.text` — copied verbatim, untouched. Never derive this from `generate_answer()`'s output.
  - `relevance_score=score` (already sigmoid-normalized in [0,1] by `reranker.rerank`, per Decision 14)
- Empty `chunks` → return `[]`. This is the correct "irrelevant query" citation state (DESIGN.md §7), independent of whatever `generate_answer` returns for the same input.

**Out of scope:** `QueryResponse` assembly and its timing/count fields — Sprint 5's query router computes and wires those.

**Docs (required):** Add `## Decision 15` to DECISIONS.md — citations are built directly from `Chunk` objects returned by the reranker, never parsed out of the LLM's generated answer text. Reason: parsing quotes from LLM output risks the model paraphrasing mid-generation despite the system prompt, silently breaking the verbatim guarantee; building from `Chunk` fields makes verbatim correctness structural, not prompt-dependent. ~10 lines, match existing decision format.

**Verify:** No eval.py change this task. Sanity-check manually: call `build_citations` on 2–3 fixture chunks, confirm 1:1 mapping and exact text match, and `[] -> []`. `python eval.py` stays at 100%.
