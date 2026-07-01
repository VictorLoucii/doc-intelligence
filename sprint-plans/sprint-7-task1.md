# Sprint 7 — Task 1: Insight Engine Service

**Goal:** Implement `backend/services/insight_engine.py`.

**Function:** `generate_insights(chunks: list[Chunk], top_n: int = 3) -> list[InsightSuggestion]`

**Logic:**
1. Require chunks spanning ≥2 distinct `document_id`s. If fewer, return `[]` and `logging.info(...)`.
2. Call the existing Anthropic client (see `answer_generator.py` pattern: `anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)`) to synthesize, per insight: an `insight_text` (a cross-document theme/connection) and a `suggested_next_question`. This is commentary, not a citation — do not reuse the anti-summary SYSTEM_PROMPT verbatim, but do NOT fabricate connections not supported by the chunks either.
3. `supporting_chunks`: build `Citation` objects directly from the source `Chunk` fields (verbatim `chunk_text`), never parsed from LLM output — same rule as Decision 15.
4. Return `list[InsightSuggestion]` (Section 5 schema, `extra="forbid"`), max `top_n` items.

**Do NOT** build the `/insights` endpoint or any frontend UI — that's Task 2/3.

**Verify:** Add a test to `eval.py` (e.g. `test_insight_engine`) asserting: schema validation passes, `supporting_chunks` is non-empty, each `chunk_text` matches its source `Chunk.text` verbatim, and <2-document input returns `[]`. Run `python eval.py` — must stay at 100%.

**Docs:** Add a new entry to `DECISIONS.md` (Decision 18) recording the chosen approach (LLM-synthesized themes vs. clustering) — DESIGN.md has no prior spec for this logic.

**Commit:** Only after eval is green. Message format: `"S7 T1: [Feature Name]"`.
