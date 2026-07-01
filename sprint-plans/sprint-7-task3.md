# Sprint 7 — Task 3: Frontend Hook + Documentation Sync (FINAL TASK)

**Goal:** Minimal UI for insights + close the documentation loop. Last task in Sprint 7.

**1. Frontend (`frontend/index.html` + `frontend/app.js`, match existing patterns exactly):**
- Add a `<section>` "Cross-Document Insights" with `<button id="insights-btn">Get Insights</button>` and `<div id="insights-results"></div>`.
- On click: `POST /insights` (no body). Non-2xx → show `errorBody.detail` (reuse the `queryError` pattern). Success → render one card per `InsightSuggestion` (`insight_text`, `suggested_next_question`) plus its `supporting_chunks`, reusing the existing `.citation-card` markup/class — don't invent new styling.
- No new CSS animations/polish (CLAUDE.md 5.10).

**2. Documentation Sync (`DESIGN.md`):**
Section 9's directory tree lists `POST /insights` but nowhere documents its contract. Add a short subsection (e.g. under Section 5) stating: no request body; `response_model=list[InsightSuggestion]`; empty vector store → 400; <2 documents indexed → 200 with `[]`.

**Do NOT** touch `/query`, `/upload`, `insight_engine.py`, or `vector_store.py` — those are already done.

**Verify:**
- `python eval.py` — must stay at 100% (no regressions).
- Start the server and smoke-test `POST /insights` with curl against an empty store (expect 400) as an automated check.
- Recommend the user do one manual browser pass (upload ≥2 PDFs → click "Get Insights" → see cards) before calling Sprint 7 done, per CLAUDE.md's frontend verification standard.

**Commit:** Message format: `"S7 T3: [Feature Name]"`. This closes Sprint 7 — confirm the working tree is clean before stopping.
