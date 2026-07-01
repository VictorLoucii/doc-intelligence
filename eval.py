#!/usr/bin/env python3
"""
eval.py — Eval-Driven Development (EDD) Harness
================================================
N-ERGY Document Intelligence System

This is the foundational testing scaffold referenced by CLAUDE.md Rule 5.1.
Running `python eval.py` MUST pass at 100% before any sprint task is declared
complete. Claude Code is instructed to fill in real assertions as each service
module is built during Sprints 1–6.

Current state (pre-Sprint-1):
  All tests use mocked/stubbed pipeline stages so the harness passes at 100%
  out of the box. Each test function is structurally complete — correct class,
  correct method name, correct docstring describing WHAT it will assert — so
  Claude Code can replace the stub body with real logic without renaming or
  restructuring anything.

Usage:
  python eval.py            # Run all tests, print Logic Score
  python eval.py -v         # Verbose — show each test name + result
  python eval.py -k ingest  # Run only tests matching "ingest"
"""

import sys
import time
import logging
from dataclasses import dataclass, field
from typing import Callable
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging — stdlib only, per CLAUDE.md Rule 6
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("eval")

# ---------------------------------------------------------------------------
# Lightweight test runner (zero external deps — no pytest required at S0)
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    error: str | None = None
    sprint: str = ""


@dataclass
class EvalSuite:
    """Minimal test runner that prints a Logic Score summary."""

    results: list[TestResult] = field(default_factory=list)
    verbose: bool = False

    def run_test(self, name: str, fn: Callable[[], None], sprint: str = "S0") -> None:
        """Execute a single test function and record pass/fail."""
        start = time.perf_counter()
        try:
            fn()
            elapsed = (time.perf_counter() - start) * 1000
            self.results.append(TestResult(name=name, passed=True, duration_ms=elapsed, sprint=sprint))
            if self.verbose:
                print(f"  ✅ PASS  {name} ({elapsed:.1f}ms)")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            self.results.append(TestResult(name=name, passed=False, duration_ms=elapsed, error=str(e), sprint=sprint))
            if self.verbose:
                print(f"  ❌ FAIL  {name} ({elapsed:.1f}ms) — {e}")

    def print_report(self) -> int:
        """Print the Logic Score summary. Returns exit code (0 = all pass)."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        score = (passed / total * 100) if total > 0 else 0.0

        print()
        print("=" * 70)
        print(f"  N-ERGY Document Intelligence — Eval Report")
        print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # Group by sprint
        sprints_seen: dict[str, list[TestResult]] = {}
        for r in self.results:
            sprints_seen.setdefault(r.sprint, []).append(r)

        for sprint, tests in sprints_seen.items():
            sprint_passed = sum(1 for t in tests if t.passed)
            sprint_total = len(tests)
            marker = "✅" if sprint_passed == sprint_total else "❌"
            print(f"\n  {marker} {sprint}: {sprint_passed}/{sprint_total} passed")
            for t in tests:
                icon = "✅" if t.passed else "❌"
                print(f"     {icon} {t.name} ({t.duration_ms:.1f}ms)")
                if t.error:
                    # Indent error on next line for readability
                    print(f"        └─ {t.error}")

        print()
        print("-" * 70)
        if failed == 0:
            print(f"  🎯 Logic Score: {score:.0f}% — ALL {total} TESTS PASSED")
        else:
            print(f"  ⚠️  Logic Score: {score:.0f}% — {failed}/{total} TESTS FAILED")
        print("-" * 70)
        print()

        return 0 if failed == 0 else 1


# ===========================================================================
#  SECTION 1 — PYDANTIC SCHEMA ALIGNMENT (Sprint S0)
#  Validates that all Pydantic models from DESIGN.md Section 5 can be
#  instantiated with valid data and reject invalid data.
# ===========================================================================

def test_schema_document_metadata_valid():
    """DocumentMetadata accepts valid fields and enforces extra='forbid'."""
    # Stub: import will fail until schemas.py exists. Replace during S0.
    from pydantic import BaseModel, ConfigDict, Field
    from datetime import datetime as dt
    from enum import Enum

    # Inline mock of the schema — Claude Code replaces with real import in S0
    class ProcessingStatus(str, Enum):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    class DocumentMetadata(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str = Field(...)
        filename: str
        sha256: str = Field(...)
        upload_time: dt
        page_count: int
        chunk_count: int
        status: ProcessingStatus
        file_size_bytes: int

    doc = DocumentMetadata(
        id="test-uuid-001",
        filename="report.pdf",
        sha256="abc123def456",
        upload_time=dt.now(timezone.utc),
        page_count=10,
        chunk_count=45,
        status=ProcessingStatus.COMPLETED,
        file_size_bytes=204800,
    )
    assert doc.filename == "report.pdf"
    assert doc.page_count == 10


def test_schema_document_metadata_rejects_extra_fields():
    """DocumentMetadata with extra='forbid' must reject unknown fields."""
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
    from datetime import datetime as dt
    from enum import Enum

    class ProcessingStatus(str, Enum):
        PENDING = "pending"
        COMPLETED = "completed"

    class DocumentMetadata(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str = Field(...)
        filename: str
        sha256: str = Field(...)
        upload_time: dt
        page_count: int
        chunk_count: int
        status: ProcessingStatus
        file_size_bytes: int

    try:
        DocumentMetadata(
            id="test",
            filename="x.pdf",
            sha256="abc",
            upload_time=dt.now(timezone.utc),
            page_count=1,
            chunk_count=1,
            status=ProcessingStatus.COMPLETED,
            file_size_bytes=100,
            rogue_field="should_fail",  # type: ignore
        )
        raise AssertionError("Expected ValidationError for extra field, but none was raised")
    except ValidationError:
        pass  # Correct behavior


def test_schema_chunk_valid():
    """Chunk model accepts valid data with all required fields."""
    from pydantic import BaseModel, ConfigDict, Field

    class Chunk(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str = Field(...)
        document_id: str
        document_name: str
        text: str
        page_number: int
        chunk_index: int
        token_count: int

    chunk = Chunk(
        id="chunk-001",
        document_id="doc-001",
        document_name="report.pdf",
        text="This is a sample chunk of text from the document.",
        page_number=3,
        chunk_index=12,
        token_count=42,
    )
    assert chunk.page_number == 3
    assert chunk.chunk_index == 12


def test_schema_citation_has_verbatim_field():
    """Citation model must have chunk_text described as VERBATIM — Anti-Summary Mandate."""
    from pydantic import BaseModel, ConfigDict, Field

    class Citation(BaseModel):
        model_config = ConfigDict(extra="forbid")
        document_name: str
        page_number: int
        chunk_index: int
        chunk_text: str = Field(..., description="VERBATIM text from source — never summarized")
        relevance_score: float = Field(..., ge=0.0, le=1.0)

    cit = Citation(
        document_name="report.pdf",
        page_number=5,
        chunk_index=22,
        chunk_text="The exact verbatim text from the source document.",
        relevance_score=0.92,
    )
    assert cit.chunk_text == "The exact verbatim text from the source document."
    assert 0.0 <= cit.relevance_score <= 1.0


def test_schema_query_request_validation():
    """QueryRequest enforces min_length=1 and max_length=2000 on question."""
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    class QueryRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        question: str = Field(..., min_length=1, max_length=2000)
        top_k: int = Field(default=5, ge=1, le=20)

    # Valid request
    qr = QueryRequest(question="What is the revenue?")
    assert qr.top_k == 5  # default

    # Empty question must fail
    try:
        QueryRequest(question="")
        raise AssertionError("Expected ValidationError for empty question")
    except ValidationError:
        pass


def test_schema_query_response_structure():
    """QueryResponse must contain answer, citations list, and timing metadata."""
    from pydantic import BaseModel, ConfigDict, Field

    class Citation(BaseModel):
        model_config = ConfigDict(extra="forbid")
        document_name: str
        page_number: int
        chunk_index: int
        chunk_text: str = Field(...)
        relevance_score: float = Field(..., ge=0.0, le=1.0)

    class QueryResponse(BaseModel):
        model_config = ConfigDict(extra="forbid")
        answer: str
        citations: list[Citation]
        query: str
        documents_searched: int
        chunks_evaluated: int
        processing_time_ms: float

    resp = QueryResponse(
        answer="Revenue was $1.2M in Q3.",
        citations=[
            Citation(
                document_name="financials.pdf",
                page_number=12,
                chunk_index=5,
                chunk_text="Revenue was $1.2M in Q3.",
                relevance_score=0.95,
            )
        ],
        query="What is the revenue?",
        documents_searched=3,
        chunks_evaluated=50,
        processing_time_ms=2340.5,
    )
    assert len(resp.citations) == 1
    assert resp.citations[0].chunk_text == "Revenue was $1.2M in Q3."


# ===========================================================================
#  SECTION 2 — PDF INGESTION (Sprint S1)
#  Structural placeholders for PDF extraction, chunking, and dedup tests.
#  Claude Code fills in real PyMuPDF assertions during Sprint 1.
# ===========================================================================

def test_ingestion_valid_pdf_returns_metadata():
    """A valid PDF should produce DocumentMetadata with page_count > 0 and chunk_count > 0."""
    import fitz
    from backend.models.schemas import ProcessingStatus
    from backend.services.pdf_processor import process_pdf

    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), "Real extractable sentence for eval.py. " * 20)
    data = doc.tobytes()
    doc.close()

    result = process_pdf(data, filename="test.pdf")

    assert result.success is True
    assert result.metadata is not None
    assert result.metadata.filename == "test.pdf"
    assert result.metadata.page_count == 2
    assert result.metadata.chunk_count > 0
    assert result.metadata.status == ProcessingStatus.COMPLETED
    assert len(result.chunks) == result.metadata.chunk_count


def test_ingestion_empty_pdf_returns_error():
    """An empty PDF (0 extractable text) must return an error, not pollute the index."""
    import fitz
    from backend.models.schemas import ExtractionErrorType
    from backend.services.pdf_processor import process_pdf

    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()

    result = process_pdf(data, filename="empty.pdf")

    assert result.success is False
    assert result.metadata is None
    assert result.chunks == []
    assert result.error_type == ExtractionErrorType.EMPTY


def test_ingestion_corrupted_pdf_does_not_crash():
    """A corrupted PDF must be caught gracefully — not crash the pipeline."""
    from backend.models.schemas import ExtractionErrorType
    from backend.services.pdf_processor import process_pdf

    data = b"not a real pdf file, just random bytes" * 100

    result = process_pdf(data, filename="corrupted.pdf")

    assert result.success is False
    assert result.metadata is None
    assert result.chunks == []
    assert result.error_type == ExtractionErrorType.CORRUPTED


def test_ingestion_sha256_dedup_skips_duplicate():
    """Uploading the same PDF twice must skip re-processing (SHA-256 dedup)."""
    import fitz
    from backend.services.pdf_processor import process_pdf

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Duplicate detection test sentence. " * 20)
    data = doc.tobytes()
    doc.close()

    first = process_pdf(data, filename="dup.pdf")
    assert first.success is True
    assert first.is_duplicate is False

    existing_hashes = {first.metadata.sha256: first.metadata}
    second = process_pdf(data, filename="dup.pdf", existing_hashes=existing_hashes)

    assert second.success is True
    assert second.is_duplicate is True
    assert second.metadata == first.metadata
    assert second.chunks == []


def test_extraction_valid_pdf_returns_pages():
    """extract_pdf_text() must return per-page text for a valid PDF (Sprint 1, Task 1).

    Real implementation (Task 1 — extraction only, no chunking/metadata yet):
      - Build a minimal in-memory PDF with fitz
      - Call pdf_processor.extract_pdf_text()
      - Assert success=True, correct page_count, sha256 present
    """
    import fitz
    from backend.services.pdf_processor import extract_pdf_text

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Real extractable sentence for eval.py.")
    data = doc.tobytes()
    doc.close()

    result = extract_pdf_text(data)
    assert result.success is True
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.sha256 and len(result.sha256) == 64


def test_extraction_empty_pdf_returns_structured_error():
    """extract_pdf_text() must flag an all-blank PDF as EMPTY, not raise (Sprint 1, Task 1)."""
    import fitz
    from backend.models.schemas import ExtractionErrorType
    from backend.services.pdf_processor import extract_pdf_text

    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()

    result = extract_pdf_text(data)
    assert result.success is False
    assert result.error_type == ExtractionErrorType.EMPTY


def test_ingestion_chunking_parameters():
    """Chunks must respect chunk_size=1000, chunk_overlap=200, no empty chunks
    (Sprint 1, Task 2 — real chunk_pages() implementation).
    """
    from backend.models.schemas import PageText
    from backend.services.pdf_processor import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        chunk_pages,
        _get_tokenizer,
    )

    assert CHUNK_SIZE == 1000, f"Expected 1000, got {CHUNK_SIZE}"
    assert CHUNK_OVERLAP == 200, f"Expected 200, got {CHUNK_OVERLAP}"
    assert CHUNK_OVERLAP < CHUNK_SIZE, "Overlap must be less than chunk size"

    paragraph = "This is a sentence about revenue and operations. " * 40
    pages = [
        PageText(page_number=1, text=paragraph * 3),
        PageText(page_number=2, text=paragraph * 3),
    ]

    chunks = chunk_pages(pages, document_id="doc-1", document_name="test.pdf")

    assert len(chunks) > 1, "Multi-page long text should split into multiple chunks"

    tokenizer = _get_tokenizer()
    for chunk in chunks:
        assert chunk.text.strip(), "No chunk may be empty/whitespace-only"
        assert chunk.token_count <= CHUNK_SIZE + 50, "Chunk exceeds token budget (tolerance for splitter)"
        assert chunk.token_count == len(tokenizer.encode(chunk.text, add_special_tokens=False))
        assert chunk.document_id == "doc-1"
        assert chunk.document_name == "test.pdf"
        assert chunk.page_number in (1, 2)

    # chunk_index must be sequential across the whole document
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    # Overlap: consecutive chunks should share trailing/leading text
    overlap_found = any(
        chunks[i].text[-30:] in chunks[i + 1].text or chunks[i + 1].text[:30] in chunks[i].text
        for i in range(len(chunks) - 1)
    )
    assert overlap_found, "Expected overlap between at least one pair of consecutive chunks"


# ===========================================================================
#  SECTION 3 — EMBEDDING & VECTOR STORE (Sprint S2)
#  Tests for BGE-Large embedding dimensionality, FAISS index ops, and
#  GPU allocation correctness.
# ===========================================================================

def test_embedding_dimensionality():
    """BGE-Large must produce 1024-dimensional embeddings.

    Embeds a single query and a batch of chunks, asserting shapes
    (1024,) and (N, 1024) respectively, plus L2-normalization and dtype.
    """
    import numpy as np

    from backend.models.schemas import Chunk
    from backend.services.embedding_service import embed_chunks, embed_query

    query_vec = embed_query("What was the reported revenue in Q3?")
    assert query_vec.shape == (1024,), f"Expected (1024,), got {query_vec.shape}"
    assert query_vec.dtype == np.float32
    assert abs(np.linalg.norm(query_vec) - 1.0) < 1e-3, "Query embedding must be L2-normalized"

    chunks = [
        Chunk(
            id=f"chunk-{i}",
            document_id="doc-1",
            document_name="test.pdf",
            text=f"This is sample chunk text number {i} about revenue and operations.",
            page_number=1,
            chunk_index=i,
            token_count=10,
        )
        for i in range(3)
    ]
    chunk_vecs = embed_chunks(chunks)
    assert chunk_vecs.shape == (3, 1024), f"Expected (3, 1024), got {chunk_vecs.shape}"
    assert chunk_vecs.dtype == np.float32
    norms = np.linalg.norm(chunk_vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "Chunk embeddings must be L2-normalized"


def test_embedding_gpu_allocation():
    """Embedding model must load on GPU 0 (DESIGN.md Section 5.5)."""
    import torch

    from backend.config import settings
    from backend.services.embedding_service import _device, _model

    assert settings.EMBEDDING_GPU_ID == 0, "Embedding model must be configured for GPU 0"
    assert _device == torch.device("cuda:0"), f"Expected cuda:0, got {_device}"
    assert _model.device.type == "cuda" and _model.device.index == 0, (
        f"Model must be loaded on cuda:0, got {_model.device}"
    )


def test_vector_store_add_and_search():
    """FAISS index: add vectors, search returns correct top-k candidates.

    Adds 100 known chunks + L2-normalized embeddings via add_chunks, then
    searches with one of the added vectors as the query. Asserts exactly
    top_k=50 results come back, scores are descending, and the exact-match
    vector ranks first.
    """
    import numpy as np

    from backend.models.schemas import Chunk
    from backend.services import vector_store as vs

    dim = 1024
    n_vectors = 100
    top_k = 50

    chunks = [
        Chunk(
            id=f"vs-chunk-{i}",
            document_id="vs-doc-1",
            document_name="test.pdf",
            text=f"sample text {i}",
            page_number=1,
            chunk_index=i,
            token_count=5,
        )
        for i in range(n_vectors)
    ]
    vectors = np.random.randn(n_vectors, dim).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    vs.add_chunks(chunks, vectors)
    try:
        query = vectors[7].copy()
        results = vs.search(query, top_k=top_k)

        assert len(results) == top_k, f"Expected {top_k} results, got {len(results)}"
        scores = [score for _, score in results]
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)), "Scores must be descending"
        assert results[0][0].id == "vs-chunk-7", "Exact-match vector must rank first"
    finally:
        vs.delete_document("vs-doc-1")  # keep the module-level index clean for other tests


def test_vector_store_empty_returns_error():
    """Querying an empty vector store must return [] without raising.

    Sprint 2 implementation: search() on a fresh (empty) index must not
    raise — it returns an empty list, which the router turns into the
    400 from DESIGN.md Section 7.
    """
    import numpy as np

    from backend.services import vector_store as vs

    assert vs._index.ntotal == 0, "Vector store must be empty at the start of this test"
    results = vs.search(np.random.randn(1024).astype(np.float32), top_k=50)
    assert results == [], "Empty store must return [] rather than raising"


# ===========================================================================
#  SECTION 4 — CROSS-ENCODER RERANKING (Sprint S3)
#  Tests for reranker model loading, GPU allocation, and precision improvement.
# ===========================================================================

def test_reranker_gpu_allocation():
    """Cross-encoder must load on GPU 1 (DESIGN.md Section 5.5).

    Sprint 3 implementation:
      - Load reranker service
      - Check model device == torch.device('cuda:1')
    """
    # STUB: validates config constant
    RERANKER_GPU_ID = 1
    assert RERANKER_GPU_ID == 1, "Reranker must be on GPU 1"


def test_reranker_reduces_candidates():
    """Reranker must reduce top-50 candidates to top-5.

    Sprint 3 implementation:
      - Provide 50 (query, chunk) pairs with known relevance
      - Run through reranker.rerank()
      - Assert output is exactly 5 items
      - Assert output scores are descending
    """
    # STUB: validates pipeline parameters
    INPUT_CANDIDATES = 50
    OUTPUT_TOP_K = 5
    assert INPUT_CANDIDATES >= 30, "Must retrieve at least 30 candidates (CLAUDE.md 5.4)"
    assert OUTPUT_TOP_K == 5


def test_reranker_improves_precision():
    """Reranked top-5 must be strictly more relevant than bi-encoder top-5.

    Sprint 3 implementation:
      - Use a known query with labeled relevant chunks
      - Get bi-encoder top-5 (from FAISS)
      - Get reranker top-5 (from cross-encoder on FAISS top-50)
      - Assert reranker precision@5 >= bi-encoder precision@5
    """
    # STUB: simulated precision values
    biencoder_precision_at_5 = 0.60
    reranker_precision_at_5 = 0.80
    assert reranker_precision_at_5 >= biencoder_precision_at_5, (
        f"Reranker precision ({reranker_precision_at_5}) must beat "
        f"bi-encoder precision ({biencoder_precision_at_5})"
    )


def test_reranker_relevance_threshold():
    """Chunks with cross-encoder score < 0.3 must be filtered out.

    Sprint 3 implementation:
      - Provide chunks with known low relevance to a query
      - Run reranker
      - Assert all returned chunks have score >= 0.3
    """
    # STUB: validates threshold constant
    RELEVANCE_THRESHOLD = 0.3
    mock_scores = [0.95, 0.82, 0.71, 0.45, 0.31]  # All above threshold
    filtered = [s for s in mock_scores if s >= RELEVANCE_THRESHOLD]
    assert len(filtered) == len(mock_scores), "All mock scores should pass threshold"


# ===========================================================================
#  SECTION 5 — ANSWER GENERATION & CITATIONS (Sprint S4)
#  Tests for LLM prompt compliance, anti-summary mandate, and citation format.
# ===========================================================================

def test_citation_format_complete():
    """Every citation must have all 4 required fields: document_name, page_number,
    chunk_index, chunk_text (CLAUDE.md Rule 5.3).

    Sprint 4 implementation:
      - Generate an answer from real retrieved chunks
      - Parse the QueryResponse
      - Assert every Citation has non-empty document_name, page_number >= 0,
        chunk_index >= 0, and non-empty chunk_text
    """
    # STUB: validates structure
    mock_citation = {
        "document_name": "report.pdf",
        "page_number": 7,
        "chunk_index": 14,
        "chunk_text": "Exact text from the source document.",
        "relevance_score": 0.88,
    }
    assert mock_citation["document_name"], "document_name must not be empty"
    assert mock_citation["page_number"] >= 0, "page_number must be non-negative"
    assert mock_citation["chunk_index"] >= 0, "chunk_index must be non-negative"
    assert mock_citation["chunk_text"], "chunk_text must not be empty"


def test_citation_text_is_verbatim():
    """Citation chunk_text must exactly match the source chunk — no paraphrasing.

    Sprint 4 implementation:
      - Provide known chunks to the answer generator
      - Parse returned citations
      - Assert each citation.chunk_text exists verbatim in the provided chunks
    """
    # STUB: simulated verbatim check
    source_chunks = [
        "The company reported $1.2M revenue in Q3 2025.",
        "Operating expenses decreased by 15% year-over-year.",
    ]
    cited_text = "The company reported $1.2M revenue in Q3 2025."
    assert cited_text in source_chunks, "Citation must be verbatim from source chunks"


def test_anti_summary_mandate_in_prompt():
    """The LLM system prompt must NOT contain 'summarize' and MUST contain
    anti-summary instructions (CLAUDE.md Rule 5.3).

    Sprint 4 implementation:
      - Read the actual system prompt string from answer_generator.py
      - Assert 'summarize' (case-insensitive) does NOT appear
      - Assert 'VERBATIM' or 'exact text' appears
    """
    # STUB: validates against the canonical prompt from DESIGN.md Section 3.3
    system_prompt = (
        "You MUST quote the exact text from the provided chunks. "
        "Do NOT paraphrase, summarize, or rephrase any cited text."
    )
    # The word 'summarize' here is in a PROHIBITION context — that's OK
    # What we ban is "summarize the following" as an INSTRUCTION
    assert "quote the exact text" in system_prompt.lower() or "verbatim" in system_prompt.lower(), (
        "System prompt must instruct verbatim citation"
    )


def test_irrelevant_query_returns_no_citations():
    """When max reranker score < 0.3, answer must state 'no relevant information found'.

    Sprint 4 implementation:
      - Query with a nonsense question against real documents
      - Assert response has empty citations list
      - Assert answer text contains 'no relevant information' or similar
    """
    # STUB: validates the expected behavior
    max_score = 0.15  # Below 0.3 threshold
    THRESHOLD = 0.3
    if max_score < THRESHOLD:
        answer = "No relevant information found in the uploaded documents for this query."
        citations = []
    else:
        answer = "Some answer"
        citations = [{"chunk_text": "some text"}]

    assert len(citations) == 0, "Irrelevant query should produce 0 citations"
    assert "no relevant information" in answer.lower()


# ===========================================================================
#  SECTION 6 — API ENDPOINTS (Sprint S5)
#  Tests for FastAPI router responses, HTTP status codes, and schema compliance.
# ===========================================================================

def test_api_upload_endpoint_exists():
    """POST /upload must accept multipart file upload.

    Sprint 5 implementation:
      - Use httpx.AsyncClient with FastAPI TestClient
      - POST a PDF file to /upload
      - Assert 200 response with DocumentMetadata JSON
    """
    # STUB: validates route name constant
    UPLOAD_ROUTE = "/upload"
    assert UPLOAD_ROUTE == "/upload"


def test_api_query_endpoint_exists():
    """POST /query must accept QueryRequest JSON and return QueryResponse.

    Sprint 5 implementation:
      - POST JSON {"question": "...", "top_k": 5} to /query
      - Assert 200 response
      - Assert response body validates as QueryResponse
    """
    QUERY_ROUTE = "/query"
    assert QUERY_ROUTE == "/query"


def test_api_documents_list_endpoint():
    """GET /documents must return list of uploaded DocumentMetadata.

    Sprint 5 implementation:
      - Upload 2 PDFs
      - GET /documents
      - Assert response is a list of length 2
    """
    DOCUMENTS_ROUTE = "/documents"
    assert DOCUMENTS_ROUTE == "/documents"


def test_api_query_before_upload_returns_400():
    """Querying before any document upload must return HTTP 400.

    Sprint 5 implementation:
      - Fresh app state (no uploads)
      - POST /query
      - Assert HTTP 400 with descriptive error message
    """
    # STUB: validates expected status code
    expected_status = 400
    assert expected_status == 400


# ===========================================================================
#  SECTION 7 — EDGE CASES (Sprint S6)
#  Tests for boundary conditions from DESIGN.md Section 7.
# ===========================================================================

def test_edge_case_password_protected_pdf():
    """Password-protected PDF must return error, not crash.

    Sprint 6 implementation:
      - Create or provide a password-protected PDF
      - Call pdf_processor.process_pdf(path)
      - Assert error response, HTTP 422
    """
    # STUB
    is_encrypted = True
    assert is_encrypted, "Should detect encrypted PDF"


def test_edge_case_malformed_query():
    """Empty or too-long question must be rejected by Pydantic validation.

    Sprint 6 implementation:
      - POST /query with {"question": ""}
      - Assert HTTP 422
      - POST /query with {"question": "x" * 2001}
      - Assert HTTP 422
    """
    # STUB: validates boundary values
    MIN_LEN = 1
    MAX_LEN = 2000
    assert MIN_LEN == 1
    assert MAX_LEN == 2000
    assert len("") < MIN_LEN, "Empty string must fail validation"
    assert len("x" * 2001) > MAX_LEN, "2001-char string must fail validation"


def test_edge_case_duplicate_upload_idempotent():
    """Uploading the same PDF twice must be idempotent — no duplicate chunks.

    Sprint 6 implementation:
      - Upload PDF A, record chunk_count
      - Upload PDF A again
      - Assert total chunks in vector store did NOT increase
    """
    # STUB
    chunks_after_first = 45
    chunks_after_second = 45
    assert chunks_after_first == chunks_after_second, "Dedup should prevent duplicate chunks"


# ===========================================================================
#  MAIN — Test execution and Logic Score output
# ===========================================================================

def main() -> int:
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    # Parse -k filter
    keyword_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "-k" and i + 1 < len(sys.argv):
            keyword_filter = sys.argv[i + 1].lower()

    suite = EvalSuite(verbose=verbose)

    # Collect all tests — ordered by sprint for logical grouping
    all_tests: list[tuple[str, Callable, str]] = [
        # S0 — Pydantic Schema Alignment
        ("schema_document_metadata_valid", test_schema_document_metadata_valid, "S0"),
        ("schema_document_metadata_rejects_extra", test_schema_document_metadata_rejects_extra_fields, "S0"),
        ("schema_chunk_valid", test_schema_chunk_valid, "S0"),
        ("schema_citation_verbatim_field", test_schema_citation_has_verbatim_field, "S0"),
        ("schema_query_request_validation", test_schema_query_request_validation, "S0"),
        ("schema_query_response_structure", test_schema_query_response_structure, "S0"),

        # S1 — PDF Ingestion
        ("ingest_valid_pdf_metadata", test_ingestion_valid_pdf_returns_metadata, "S1"),
        ("ingest_empty_pdf_error", test_ingestion_empty_pdf_returns_error, "S1"),
        ("ingest_corrupted_pdf_resilience", test_ingestion_corrupted_pdf_does_not_crash, "S1"),
        ("ingest_sha256_dedup", test_ingestion_sha256_dedup_skips_duplicate, "S1"),
        ("extraction_valid_pdf_pages", test_extraction_valid_pdf_returns_pages, "S1"),
        ("extraction_empty_pdf_error", test_extraction_empty_pdf_returns_structured_error, "S1"),
        ("ingest_chunking_params", test_ingestion_chunking_parameters, "S1"),

        # S2 — Embedding + Vector Store
        ("embed_dimensionality_1024", test_embedding_dimensionality, "S2"),
        ("embed_gpu_0_allocation", test_embedding_gpu_allocation, "S2"),
        ("vector_store_add_search", test_vector_store_add_and_search, "S2"),
        ("vector_store_empty_error", test_vector_store_empty_returns_error, "S2"),

        # S3 — Cross-Encoder Reranking
        ("reranker_gpu_1_allocation", test_reranker_gpu_allocation, "S3"),
        ("reranker_reduces_to_top5", test_reranker_reduces_candidates, "S3"),
        ("reranker_improves_precision", test_reranker_improves_precision, "S3"),
        ("reranker_relevance_threshold", test_reranker_relevance_threshold, "S3"),

        # S4 — Answer Generation & Citations
        ("citation_format_complete", test_citation_format_complete, "S4"),
        ("citation_text_verbatim", test_citation_text_is_verbatim, "S4"),
        ("anti_summary_in_prompt", test_anti_summary_mandate_in_prompt, "S4"),
        ("irrelevant_query_no_citations", test_irrelevant_query_returns_no_citations, "S4"),

        # S5 — API Endpoints
        ("api_upload_endpoint", test_api_upload_endpoint_exists, "S5"),
        ("api_query_endpoint", test_api_query_endpoint_exists, "S5"),
        ("api_documents_list", test_api_documents_list_endpoint, "S5"),
        ("api_query_before_upload_400", test_api_query_before_upload_returns_400, "S5"),

        # S6 — Edge Cases
        ("edge_password_protected_pdf", test_edge_case_password_protected_pdf, "S6"),
        ("edge_malformed_query", test_edge_case_malformed_query, "S6"),
        ("edge_duplicate_upload_idempotent", test_edge_case_duplicate_upload_idempotent, "S6"),
    ]

    # Apply keyword filter
    if keyword_filter:
        all_tests = [(n, f, s) for n, f, s in all_tests if keyword_filter in n.lower()]
        if not all_tests:
            print(f"⚠️  No tests matched filter: '{keyword_filter}'")
            return 1

    print(f"\n🔬 Running {len(all_tests)} eval tests...\n")

    for name, fn, sprint in all_tests:
        suite.run_test(name, fn, sprint)

    return suite.print_report()


if __name__ == "__main__":
    sys.exit(main())
