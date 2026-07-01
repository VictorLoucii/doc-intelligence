# Sprint 8 — Task 1: Sync README.md with Final Implementation

**Goal:** `README.md` was written as an early scaffold (initial commit) and is now stale. Bring it in line with what's actually built — do not change application code.

**1. Decisions table (Section 4):** Add rows for Decisions 13–18 from `DECISIONS.md` (No Celery/Redis is already row 12 — verify it matches, then add 13: sigmoid-normalize cross-encoder scores, 14: build citations from `Chunk` objects not LLM output, 15: `/upload` always 200, 16: vector_store accessor pattern, 17→ renumber as needed, 18: LLM-synthesized cross-document insights). Match the existing table's `# | Decision | Rationale | Trade-off` format exactly.

**2. API Reference (Section 8):** Add a `POST /insights` entry alongside the existing `/query` and `/upload` docs — no request body, `response_model=list[InsightSuggestion]`, 400 on empty store, `[]` on <2 documents.

**3. Sprint Roadmap (Section 9):** Mark S6 (Edge Cases) and S7 (Insight Engine) as complete.

**4. Verification section (Section 11):** Update "30 TESTS PASSED" → current count from `python eval.py` output (39 as of now, but re-check — don't hardcode a stale number).

**Do NOT** touch any file under `backend/` or `frontend/`, and do not add new sections beyond what's listed above.

**Verify:** `python eval.py` — must stay at 100% (README changes shouldn't affect it, this just confirms no accidental edits elsewhere).

**Commit:** `"S8 T1: sync README with final implementation"`.
