# Sprint 5 — Task 3: Frontend (Upload, Question, Answer Display)

**Scope:** `frontend/index.html`, `frontend/app.js`, `frontend/style.css` only. No backend changes. No eval.py.

**Requirements (CLAUDE.md §5.10, Decision 8; DESIGN.md §4 Layer 3):**
Plain HTML + vanilla JS, minimal CSS. **Max 60 minutes.** Exactly the three required features:
1. **Upload:** `<input type="file" name="files" multiple>` + submit button → `fetch('/upload', {method: 'POST', body: new FormData(formEl)})`. Response is `list[ProcessPDFResult]` — render each file's `success`/`is_duplicate`/`error_message` so a partial-batch failure is visible (backend never fails the whole batch, CLAUDE.md §5.7).
2. **Question input:** text box + submit → `fetch('/query', {method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({question})})`. On HTTP 400 (query before upload), show the error `detail` text.
3. **Answer display:** render `response.answer`, then one card per item in `response.citations` showing `document_name`, `page_number`, `chunk_index`, `chunk_text` (verbatim, no truncation/reformatting), `relevance_score`.

**Optional 4th (only if time remains):** `GET /documents` on page load → simple `<ul>` list. Skip without hesitation if over budget.

**Explicitly forbidden:** CSS animations, gradients, dark mode, responsive breakpoints (CLAUDE.md §5.10 — zero evaluation value, cut immediately if tempted).

**Out of scope:** No new backend routes/schemas. No eval.py changes (browser UI isn't covered by `eval.py`; that's Task 4's job to note explicitly).

**Docs:** None.

**Verify (per CLAUDE.md §4's stated success criterion for this task):** Start the server (`uvicorn backend.main:app --reload`), open `localhost:8000` in a browser, upload a real PDF, ask a question about its content, and confirm the answer renders with at least one citation card showing verbatim source text. `python eval.py` stays at 100% (no backend touched, so this should be a no-op check).
