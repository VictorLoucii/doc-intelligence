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


def test_retrieval_finds_known_relevant_chunk():
    """End-to-end semantic retrieval: real embeddings + FAISS must surface the
    one chunk that actually answers the query, ranked first, among noise from
    earlier tests (DESIGN.md S2 verification: 'top-50 contains known relevant
    chunks').
    """
    from backend.models.schemas import Chunk
    from backend.services import embedding_service, vector_store as vs

    chunks = [
        Chunk(
            id="topic-invoice",
            document_id="topic-doc",
            document_name="topics.pdf",
            text="Invoice payment terms require full payment within 30 days of the invoice date.",
            page_number=1,
            chunk_index=0,
            token_count=15,
        ),
        Chunk(
            id="topic-solar",
            document_id="topic-doc",
            document_name="topics.pdf",
            text="Solar panel efficiency depends on the angle of installation and cell temperature.",
            page_number=1,
            chunk_index=1,
            token_count=14,
        ),
        Chunk(
            id="topic-vacation",
            document_id="topic-doc",
            document_name="topics.pdf",
            text="Employees accrue vacation policy days based on years of continuous service.",
            page_number=1,
            chunk_index=2,
            token_count=13,
        ),
    ]

    try:
        embeddings = embedding_service.embed_chunks(chunks)
        vs.add_chunks(chunks, embeddings)

        query_vec = embedding_service.embed_query("What are the payment terms for invoices?")
        results = vs.search(query_vec, top_k=50)

        result_ids = [chunk.id for chunk, _ in results]
        assert "topic-invoice" in result_ids, "Known relevant chunk missing from top-50"
        assert results[0][0].id == "topic-invoice", (
            f"Expected the invoice chunk to rank first, got {results[0][0].id}"
        )
    finally:
        vs.delete_document("topic-doc")


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
    """Cross-encoder must load on GPU 1 (DESIGN.md Section 5.5)."""
    import torch

    from backend.config import settings
    from backend.services.reranker import _device, _model

    assert settings.RERANKER_GPU_ID == 1, "Reranker must be configured for GPU 1"
    assert _device == torch.device("cuda:1"), f"Expected cuda:1, got {_device}"
    assert _model.device.type == "cuda" and _model.device.index == 1, (
        f"Model must be loaded on cuda:1, got {_model.device}"
    )


def test_reranker_reduces_candidates():
    """Reranker must reduce top-50 candidates to top-5, scores descending."""
    from backend.models.schemas import Chunk
    from backend.services.reranker import rerank

    query = "What are the payment terms for invoices?"
    # First 5 chunks are genuinely relevant (score above RELEVANCE_THRESHOLD after
    # sigmoid normalization); the rest are unrelated filler that the cross-encoder
    # correctly scores near 0.0, so they don't survive relevance-threshold filtering.
    relevant_texts = [
        "Invoice payment terms require full payment within 30 days of the invoice date.",
        "Payment for all invoices is due net 30 days from the invoice issue date.",
        "Customers must pay invoices within a 30-day payment term as specified in the contract.",
        "Late payment on invoices incurs a 1.5% monthly interest fee after the 30-day term.",
        "Invoices are payable within 30 days; early payment discounts of 2% apply within 10 days.",
    ]
    candidates = [
        (
            Chunk(
                id=f"rr-chunk-{i}",
                document_id="rr-doc",
                document_name="test.pdf",
                text=(
                    relevant_texts[i]
                    if i < len(relevant_texts)
                    else f"Unrelated filler text number {i} about office supplies and weather."
                ),
                page_number=1,
                chunk_index=i,
                token_count=15,
            ),
            1.0 - i * 0.01,
        )
        for i in range(50)
    ]

    results = rerank(query, candidates, top_k=5)

    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    scores = [score for _, score in results]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)), "Scores must be descending"
    assert results[0][0].id == "rr-chunk-0", "Known relevant chunk must rank first after reranking"


def test_reranker_improves_precision():
    """Reranked top-5 must be strictly more relevant than bi-encoder top-5.

    Sprint 3 implementation:
      - Use a known query with labeled relevant chunks
      - Get bi-encoder top-5 (from FAISS)
      - Get reranker top-5 (from cross-encoder on FAISS top-50)
      - Assert reranker precision@5 >= bi-encoder precision@5
    """
    from backend.models.schemas import Chunk
    from backend.services import embedding_service, vector_store as vs
    from backend.services.reranker import rerank

    query = "What are the payment terms for invoices?"

    # 5 genuinely relevant chunks.
    relevant_texts = [
        "Invoice payment terms require full payment within 30 days of the invoice date.",
        "Payment for all invoices is due net 30 days from the invoice issue date.",
        "Customers must pay invoices within a 30-day payment term as specified in the contract.",
        "Late payment on invoices incurs a 1.5% monthly interest fee after the 30-day term.",
        "Invoices are payable within 30 days; early payment discounts of 2% apply within 10 days.",
    ]
    # Near-miss decoys: share surface wording ("invoice", "payment", "30-day", "terms")
    # with the query but answer a different actual question, so bi-encoder cosine
    # similarity is fooled while cross-encoder attention should correctly demote them.
    decoy_texts = [
        "The vendor invoice must include a purchase order number and delivery terms for the shipped goods.",
        "Employees must submit expense reports within 30 days of the travel date to receive reimbursement.",
        "The service agreement terms require a 30-day notice period before contract termination.",
        "Software license payment is due annually, with renewal terms set every 12 months.",
    ]

    chunks = [
        Chunk(
            id=f"prec-rel-{i}",
            document_id="prec-doc",
            document_name="test.pdf",
            text=text,
            page_number=1,
            chunk_index=i,
            token_count=15,
        )
        for i, text in enumerate(relevant_texts)
    ] + [
        Chunk(
            id=f"prec-decoy-{i}",
            document_id="prec-doc",
            document_name="test.pdf",
            text=text,
            page_number=1,
            chunk_index=100 + i,
            token_count=15,
        )
        for i, text in enumerate(decoy_texts)
    ]
    relevant_ids = {chunk.id for chunk in chunks[: len(relevant_texts)]}

    try:
        embeddings = embedding_service.embed_chunks(chunks)
        vs.add_chunks(chunks, embeddings)

        query_vec = embedding_service.embed_query(query)

        biencoder_top5 = vs.search(query_vec, top_k=5)
        biencoder_precision_at_5 = sum(1 for chunk, _ in biencoder_top5 if chunk.id in relevant_ids) / 5

        candidates_top50 = vs.search(query_vec, top_k=50)
        reranker_top5 = rerank(query, candidates_top50, top_k=5)
        reranker_precision_at_5 = sum(1 for chunk, _ in reranker_top5 if chunk.id in relevant_ids) / 5

        assert reranker_precision_at_5 >= biencoder_precision_at_5, (
            f"Reranker precision ({reranker_precision_at_5}) must beat "
            f"bi-encoder precision ({biencoder_precision_at_5})"
        )
        assert reranker_precision_at_5 > biencoder_precision_at_5, (
            "Decoys are crafted to fool the bi-encoder only — reranker precision "
            "must be strictly greater on this fixture"
        )
    finally:
        vs.delete_document("prec-doc")  # keep the module-level index clean for other tests


def test_reranker_relevance_threshold():
    """Chunks with cross-encoder score < RELEVANCE_THRESHOLD must be filtered out."""
    from backend.config import settings
    from backend.models.schemas import Chunk
    from backend.services.reranker import rerank

    query = "What are the payment terms for invoices?"
    candidates = [
        (
            Chunk(
                id="rr-thresh-relevant",
                document_id="rr-doc",
                document_name="test.pdf",
                text="Invoice payment terms require full payment within 30 days of the invoice date.",
                page_number=1,
                chunk_index=0,
                token_count=15,
            ),
            1.0,
        ),
        (
            Chunk(
                id="rr-thresh-irrelevant",
                document_id="rr-doc",
                document_name="test.pdf",
                text="Unrelated filler text about office supplies and weather.",
                page_number=1,
                chunk_index=1,
                token_count=15,
            ),
            0.9,
        ),
    ]

    results = rerank(query, candidates, top_k=5)

    assert len(results) == 1, f"Expected only the relevant chunk to survive, got {len(results)}"
    assert results[0][0].id == "rr-thresh-relevant"
    assert all(score >= settings.RELEVANCE_THRESHOLD for _, score in results), (
        "All returned scores must be >= RELEVANCE_THRESHOLD"
    )
    assert all(0.3 <= score <= 1.0 for _, score in results), "All returned scores must be within [0.3, 1.0]"


# ===========================================================================
#  SECTION 5 — ANSWER GENERATION & CITATIONS (Sprint S4)
#  Tests for LLM prompt compliance, anti-summary mandate, and citation format.
# ===========================================================================

def test_citation_format_complete():
    """Every citation must have all 4 required fields: document_name, page_number,
    chunk_index, chunk_text (CLAUDE.md Rule 5.3).
    """
    from backend.models.schemas import Chunk
    from backend.services.answer_generator import build_citations

    chunks = [
        (
            Chunk(
                id="cite-1",
                document_id="cite-doc",
                document_name="report.pdf",
                text="Exact text from the source document.",
                page_number=7,
                chunk_index=14,
                token_count=8,
            ),
            0.88,
        ),
        (
            Chunk(
                id="cite-2",
                document_id="cite-doc",
                document_name="report.pdf",
                text="A second verbatim passage.",
                page_number=8,
                chunk_index=15,
                token_count=5,
            ),
            0.5,
        ),
    ]

    citations = build_citations(chunks)

    assert len(citations) == len(chunks)
    for citation in citations:
        assert citation.document_name, "document_name must not be empty"
        assert citation.page_number >= 0, "page_number must be non-negative"
        assert citation.chunk_index >= 0, "chunk_index must be non-negative"
        assert citation.chunk_text, "chunk_text must not be empty"
        assert 0 <= citation.relevance_score <= 1, "relevance_score must be within [0, 1]"


def test_citation_text_is_verbatim():
    """Citation chunk_text must exactly match the source chunk — no paraphrasing."""
    from backend.models.schemas import Chunk
    from backend.services.answer_generator import build_citations

    chunks = [
        (
            Chunk(
                id="verb-1",
                document_id="verb-doc",
                document_name="test.pdf",
                text="The company reported $1.2M revenue in Q3 2025.",
                page_number=1,
                chunk_index=0,
                token_count=10,
            ),
            0.9,
        ),
        (
            Chunk(
                id="verb-2",
                document_id="verb-doc",
                document_name="test.pdf",
                text="Operating expenses decreased by 15% year-over-year.",
                page_number=2,
                chunk_index=1,
                token_count=8,
            ),
            0.7,
        ),
    ]

    citations = build_citations(chunks)

    for citation, (chunk, _) in zip(citations, chunks):
        assert citation.chunk_text == chunk.text, "Citation text must be identical to source chunk text"


def test_anti_summary_mandate_in_prompt():
    """The LLM system prompt must NOT use 'summarize' outside the anti-summary
    prohibition clause, and MUST instruct verbatim citation (CLAUDE.md Rule 5.3).
    """
    from backend.services.answer_generator import SYSTEM_PROMPT

    prompt_lower = SYSTEM_PROMPT.lower()

    prohibition_clause = "do not paraphrase, summarize, or rephrase"
    assert prohibition_clause in prompt_lower, "Anti-summary prohibition clause not found verbatim"

    # 'summarize' may ONLY appear inside the prohibition clause, nowhere else
    remainder = prompt_lower.replace(prohibition_clause, "")
    assert "summarize" not in remainder, "'summarize' must not appear outside the prohibition clause"

    assert "verbatim" in prompt_lower, "System prompt must instruct verbatim citation"
    assert "quote the exact text" in prompt_lower, "System prompt must instruct quoting exact text"


def test_irrelevant_query_returns_no_citations():
    """generate_answer(query, []) must return the fallback string; build_citations([]) must return []."""
    from backend.services.answer_generator import _NO_CONTEXT_ANSWER, build_citations, generate_answer

    answer = generate_answer("What is the meaning of life?", [])
    citations = build_citations([])

    assert answer == _NO_CONTEXT_ANSWER
    assert citations == []


def test_generate_answer_api_wiring():
    """generate_answer() must call the Anthropic client with the configured model,
    the SYSTEM_PROMPT, and a user message containing [Source: ...] formatting.
    """
    from unittest.mock import MagicMock, patch

    from backend.config import settings
    from backend.models.schemas import Chunk
    from backend.services.answer_generator import SYSTEM_PROMPT, generate_answer

    chunks = [
        (
            Chunk(
                id="wire-1",
                document_id="wire-doc",
                document_name="policy.pdf",
                text="Refunds are processed within 14 business days.",
                page_number=3,
                chunk_index=2,
                token_count=9,
            ),
            0.95,
        ),
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="The refund policy states...")]

    with patch(
        "backend.services.answer_generator._client.messages.create", return_value=mock_response
    ) as mock_create:
        answer = generate_answer("What is the refund policy?", chunks)

    assert answer == "The refund policy states..."
    mock_create.assert_called_once()
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == settings.ANTHROPIC_MODEL
    assert kwargs["system"] == SYSTEM_PROMPT
    user_content = kwargs["messages"][0]["content"]
    assert "[Source: policy.pdf, Page 3, Chunk 2]" in user_content, (
        "User message must include [Source: ...] formatting"
    )


# ===========================================================================
#  SECTION 6 — API ENDPOINTS (Sprint S5)
#  Tests for FastAPI router responses, HTTP status codes, and schema compliance.
# ===========================================================================

def _make_pdf_bytes(sentence: str = "Real extractable sentence for eval.py. ", repeats: int = 20) -> bytes:
    """Build an in-memory single-page PDF with extractable text (shared by S5 API tests)."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), sentence * repeats)
    data = doc.tobytes()
    doc.close()
    return data


def test_api_upload_endpoint_exists():
    """POST /upload must accept multipart file upload and return ProcessPDFResult JSON."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    document_id = None
    try:
        response = client.post(
            "/upload", files={"files": ("upload_test.pdf", _make_pdf_bytes(), "application/pdf")}
        )
        assert response.status_code == 200
        body = response.json()
        assert body[0]["success"] is True
        assert body[0]["metadata"]["page_count"] > 0
        document_id = body[0]["metadata"]["id"]
    finally:
        if document_id:
            client.delete(f"/documents/{document_id}")


def test_api_query_endpoint_exists():
    """POST /query must accept QueryRequest JSON and return a QueryResponse-shaped body."""
    from unittest.mock import MagicMock, patch

    from fastapi.testclient import TestClient

    from backend.main import app
    from backend.models.schemas import QueryResponse

    client = TestClient(app)
    document_id = None
    try:
        upload_response = client.post(
            "/upload", files={"files": ("query_test.pdf", _make_pdf_bytes(), "application/pdf")}
        )
        document_id = upload_response.json()[0]["metadata"]["id"]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="The document says so.")]
        with patch(
            "backend.services.answer_generator._client.messages.create", return_value=mock_response
        ):
            response = client.post("/query", json={"question": "What does the document say?", "top_k": 5})

        assert response.status_code == 200
        QueryResponse.model_validate(response.json())
    finally:
        if document_id:
            client.delete(f"/documents/{document_id}")


def test_api_documents_list_endpoint():
    """GET /documents must return the list of uploaded DocumentMetadata."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    document_ids = []
    try:
        for filename in ("list_test_1.pdf", "list_test_2.pdf"):
            response = client.post("/upload", files={"files": (filename, _make_pdf_bytes(), "application/pdf")})
            document_ids.append(response.json()[0]["metadata"]["id"])

        response = client.get("/documents")
        assert response.status_code == 200
        assert len(response.json()) == 2
    finally:
        for document_id in document_ids:
            client.delete(f"/documents/{document_id}")


def test_api_query_before_upload_returns_400():
    """Querying before any document upload must return HTTP 400.

    Must run before any other S5 test uploads — vector_store/documents._documents
    are process-wide singletons shared across the whole eval.py run.
    """
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    response = client.post("/query", json={"question": "Anything?", "top_k": 5})
    assert response.status_code == 400


# ===========================================================================
#  SECTION 7 — EDGE CASES (Sprint S6)
#  Tests for boundary conditions from DESIGN.md Section 7.
# ===========================================================================

def test_edge_case_password_protected_pdf():
    """Password-protected PDF must return error, not crash."""
    import fitz
    from backend.models.schemas import ExtractionErrorType
    from backend.services.pdf_processor import process_pdf

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "secret content")
    buffer = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner-secret",
        user_pw="user-secret",
    )
    doc.close()

    result = process_pdf(buffer, filename="locked.pdf")

    assert result.success is False
    assert result.metadata is None
    assert result.error_type == ExtractionErrorType.PASSWORD_PROTECTED


def test_edge_case_malformed_query():
    """Empty or too-long question must be rejected by Pydantic validation."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)

    response = client.post("/query", json={"question": "", "top_k": 5})
    assert response.status_code == 422

    response = client.post("/query", json={"question": "x" * 2001, "top_k": 5})
    assert response.status_code == 422


def test_edge_case_duplicate_upload_idempotent():
    """Uploading the same PDF bytes twice must be idempotent (Decision 12 SHA-256 dedup)."""
    from fastapi.testclient import TestClient

    from backend.main import app
    from backend.services import vector_store as vs

    client = TestClient(app)
    document_id = None
    try:
        pdf_bytes = _make_pdf_bytes()

        first = client.post("/upload", files={"files": ("dup_test.pdf", pdf_bytes, "application/pdf")})
        assert first.status_code == 200
        first_metadata = first.json()[0]
        assert first_metadata["is_duplicate"] is False
        assert first_metadata["metadata"]["chunk_count"] > 0
        document_id = first_metadata["metadata"]["id"]

        ntotal_before = vs._index.ntotal

        second = client.post("/upload", files={"files": ("dup_test.pdf", pdf_bytes, "application/pdf")})
        assert second.status_code == 200
        second_metadata = second.json()[0]
        assert second_metadata["is_duplicate"] is True
        assert second_metadata["metadata"]["id"] == first_metadata["metadata"]["id"]
        assert second_metadata["metadata"]["sha256"] == first_metadata["metadata"]["sha256"]

        assert vs._index.ntotal == ntotal_before, "Duplicate upload must not add vectors to the store"
    finally:
        if document_id:
            client.delete(f"/documents/{document_id}")


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
        ("retrieval_finds_known_relevant_chunk", test_retrieval_finds_known_relevant_chunk, "S2"),
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
        ("generate_answer_api_wiring", test_generate_answer_api_wiring, "S4"),

        # S5 — API Endpoints
        # api_query_before_upload_400 MUST run first: vector_store/documents._documents
        # are process-wide singletons, and this test asserts the pre-upload 400 state.
        ("api_query_before_upload_400", test_api_query_before_upload_returns_400, "S5"),
        ("api_upload_endpoint", test_api_upload_endpoint_exists, "S5"),
        ("api_query_endpoint", test_api_query_endpoint_exists, "S5"),
        ("api_documents_list", test_api_documents_list_endpoint, "S5"),

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
