# Sprint 6 — Task 1: Real Eval Test — Password-Protected PDF + Doc Sync

**Scope:** `eval.py` (replace `test_edge_case_password_protected_pdf` stub) + `DESIGN.md` Section 7 only. No malformed-query or dedup tests (Tasks 2–3). No new backend logic — `pdf_processor.extract_pdf_text()` already detects `doc.needs_pass` and returns `ExtractionErrorType.PASSWORD_PROTECTED` (built in S1).

**Requirements:**
- Replace the fake stub body of `test_edge_case_password_protected_pdf` in eval.py Section 7 with a real test:
  - Build an in-memory encrypted PDF with `fitz` (`doc.save(buffer, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=..., user_pw=...)`).
  - Call `pdf_processor.process_pdf(data, filename="locked.pdf")`.
  - Assert `success is False`, `error_type == ExtractionErrorType.PASSWORD_PROTECTED`, `metadata is None`.
- **Documentation Hygiene (required):** DESIGN.md Section 7's table lists HTTP 422 for password-protected PDFs, but Decision 16 (DECISIONS.md) established that `/upload` always returns 200 with per-file `ProcessPDFResult.error_type` — the current, correct behavior. Add one footnote line under the Section 7 table: PDF-processing error codes for `/upload` surface in the response body (HTTP 200), not the top-level status, per Decision 16. Do not change `documents.py` or `DECISIONS.md`.

**Out of scope:** malformed-query test, duplicate-upload test (Tasks 2–3).

**Verify:** `python eval.py -k password` passes on real assertions (not the stub). Full `python eval.py` stays at 100% Logic Score.
