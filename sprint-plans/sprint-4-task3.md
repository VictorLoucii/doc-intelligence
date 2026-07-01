# Sprint 4 — Task 3 (final): Eval Upgrade — Answer Generation & Citations

**Scope:** `eval.py` only. No new production code in `answer_generator.py` — this proves S4's acceptance criteria (DESIGN.md §10: "citation format correct, text is verbatim from source"), not new features. Sprint 4 closed after this.

**Upgrade the 4 existing S4 stubs (lines ~853–935) to real logic**, importing locally inside each function like the S3 tests do:
- `test_citation_format_complete` — build 2–3 fixture `Chunk`s, call `build_citations()`, assert every `Citation` has non-empty `document_name`, `page_number >= 0`, `chunk_index >= 0`, non-empty `chunk_text`, `0 <= relevance_score <= 1`. (Adapt from the old docstring's "parse QueryResponse" framing — `QueryResponse` doesn't exist yet, that's S5.)
- `test_citation_text_is_verbatim` — assert `citation.chunk_text == chunk.text` exactly (identity, not substring) for each fixture chunk.
- `test_anti_summary_mandate_in_prompt` — import real `SYSTEM_PROMPT`; assert "summarize" appears only inside the "Do NOT paraphrase, summarize, or rephrase" clause, nowhere else; assert "verbatim" and "quote the exact text" both present (case-insensitive).
- `test_irrelevant_query_returns_no_citations` — `generate_answer(query, [])` returns the exact fallback string; `build_citations([])` returns `[]`.

**Add one new test** (CLAUDE.md §5.1 — untested logic from Task 1 must get a test now): `test_generate_answer_api_wiring` — `unittest.mock.patch` the module-level `_client.messages.create` in `answer_generator`, call `generate_answer(query, chunks)` with 1–2 fixture chunks, assert the mock was called with `model=settings.ANTHROPIC_MODEL`, `system=SYSTEM_PROMPT`, and a user message containing `[Source: ...]` formatting. Register it in the S4 block of the test list at the bottom of the file.

**Verify:** `python eval.py` — 100%, Sprint 4 fully closed.
