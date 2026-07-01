# Sprint 4 — Task 1: Answer Generation Core (Claude API + System Prompt)

**Scope:** `backend/services/answer_generator.py` only. No Citation objects (Task 2), no eval.py (Task 3).

**Requirements (DESIGN.md §3.3, §4; CLAUDE.md §5.3, §5.6):**
- Anthropic client via `settings.ANTHROPIC_API_KEY`. Add `ANTHROPIC_MODEL: str = "claude-sonnet-5"` to `Settings` (config.py) — no model is specified anywhere yet.
- `SYSTEM_PROMPT` constant: copy DESIGN.md §3.3's prompt verbatim. "summarize" may only appear inside rule 3's prohibition — never as an instruction elsewhere (CLAUDE.md §5.3).

**One function:**
- `generate_answer(query: str, chunks: list[tuple[Chunk, float]]) -> str`
  - Empty `chunks` → return `"The uploaded documents do not contain sufficient information to answer this question."` verbatim, no API call.
  - Otherwise, format each chunk as `[Source: {document_name}, Page {page_number}, Chunk {chunk_index}]\n{text}` in the user message, call Claude with `SYSTEM_PROMPT`, return raw response text.

**Out of scope:** `Citation`/`QueryResponse` assembly — Task 2. Do NOT parse citations out of LLM text; verbatim citations must come from `Chunk` fields directly, never from model output.

**Docs:** Add `ANTHROPIC_MODEL` to `.env.example`. No DESIGN.md/DECISIONS.md edit yet — the "citations built from Chunk, not parsed from LLM text" decision is logged in Task 2's DECISIONS.md entry.

**Verify:** No eval.py change this task. Sanity-check manually with a mocked `anthropic.Anthropic().messages.create`. `python eval.py` stays at 100% (no regressions).
