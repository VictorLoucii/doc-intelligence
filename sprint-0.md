# Sprint 0 — Scaffold Checklist

**Window:** 0:00–0:45 · **Deliverable:** project structure, `requirements.txt`, `config.py`, Pydantic schemas, `.gitignore` in place
**Verify:** `python -c "from backend.models.schemas import *; print('OK')"`

## Directories

- [ ] `backend/`
- [ ] `backend/models/`
- [ ] `backend/services/`
- [ ] `backend/routers/`
- [ ] `backend/utils/`
- [ ] `frontend/`
- [ ] `tests/`
- [ ] `uploads/` (gitignored, not committed empty — add `.gitkeep` if needed)

## Files

- [ ] `backend/__init__.py`
- [ ] `backend/main.py` — FastAPI app skeleton (mounts routers, serves frontend) — stub only, no logic yet
- [ ] `backend/config.py` — `pydantic-settings` config: `EMBEDDING_GPU_ID`, `RERANKER_GPU_ID`, `LLM_GPU_ID`, API keys, log level (DESIGN.md §5.5, CLAUDE.md §5.5/§5.6)
- [ ] `backend/models/__init__.py`
- [ ] `backend/models/schemas.py` — all Pydantic v2 models from DESIGN.md §5, each with `model_config = ConfigDict(extra="forbid")`:
  - [ ] `ProcessingStatus(str, Enum)` — `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
  - [ ] `DocumentMetadata` — `id`, `filename`, `sha256`, `upload_time`, `page_count`, `chunk_count`, `status`, `file_size_bytes`
  - [ ] `Chunk` — `id`, `document_id`, `document_name`, `text`, `page_number`, `chunk_index`, `token_count`
  - [ ] `QueryRequest` — `question: str = Field(..., min_length=1, max_length=2000)`, `top_k: int = Field(default=5, ge=1, le=20)`
  - [ ] `Citation` — `document_name`, `page_number`, `chunk_index`, `chunk_text`, `relevance_score: float = Field(..., ge=0.0, le=1.0)`
  - [ ] `QueryResponse` — `answer`, `citations: list[Citation]`, `query`, `documents_searched`, `chunks_evaluated`, `processing_time_ms`
  - [ ] `InsightSuggestion` — `insight_text`, `supporting_chunks: list[Citation]`, `suggested_next_question`
- [ ] `backend/services/__init__.py` (package marker only)
- [ ] `backend/services/pdf_processor.py` (empty stub — logic in S1)
- [ ] `backend/services/embedding_service.py` (empty stub — logic in S2)
- [ ] `backend/services/vector_store.py` (empty stub — logic in S2)
- [ ] `backend/services/reranker.py` (empty stub — logic in S3)
- [ ] `backend/services/answer_generator.py` (empty stub — logic in S4)
- [ ] `backend/services/insight_engine.py` (empty stub — logic in S7, bonus)
- [ ] `backend/routers/__init__.py` (package marker only)
- [ ] `backend/routers/documents.py` (empty stub — logic in S5)
- [ ] `backend/routers/query.py` (empty stub — logic in S5)
- [ ] `backend/utils/__init__.py` (package marker only)
- [ ] `backend/utils/text_utils.py` (empty stub — logic in S1)
- [ ] `frontend/index.html` (placeholder, built out in S5)
- [ ] `frontend/style.css` (placeholder, built out in S5)
- [ ] `frontend/app.js` (placeholder, built out in S5)
- [ ] `tests/__init__.py`
- [ ] `tests/test_pdf_processor.py` (empty stub)
- [ ] `tests/test_retrieval.py` (empty stub)
- [ ] `tests/test_reranker.py` (empty stub)
- [ ] `tests/test_api.py` (empty stub)
- [ ] `tests/test_edge_cases.py` (empty stub)
- [ ] `.env.example` — variable names only, placeholder values, no real secrets
- [ ] `.gitignore` — excludes `.env`, `uploads/`, `__pycache__/`, `*.pyc`, `.venv/`, etc.

## Existing files (already present — do not recreate)

- [x] `CLAUDE.md`
- [x] `DESIGN.md`
- [x] `DECISIONS.md`
- [x] `README.md`
- [x] `eval.py`
- [x] `requirements.txt`

## Out of scope for Sprint 0

- No PDF processing, embedding, retrieval, reranking, or answer-generation logic (S1–S4).
- No FastAPI route bodies beyond app instantiation (S5).
- No frontend behavior beyond placeholder files (S5).
- No `eval.py` edits — only run it to confirm the schema import check passes.

## Definition of Done

- [ ] `python -c "from backend.models.schemas import *; print('OK')"` succeeds
- [ ] `git status` shows only S0-relevant new/changed files staged
- [ ] Commit message: `"S0 T1: scaffold project structure + schemas + config"`
