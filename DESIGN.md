# DESIGN.md — N-ERGY Document Intelligence System
## Architecture Bible · Single Source of Truth

> **Optimization Target:** ACCURACY
> **Environment:** AWS EC2 · 4× NVIDIA A10 (24GB VRAM each) · Claude Code CLI
> **Time Constraint:** 8 hours
> **Last Updated:** July 2026

---

## 1. The Problem in One Paragraph

N-ERGY needs a document intelligence system that lets users upload PDFs, ask natural language questions, and receive high-accuracy answers with exact citations from the source documents. The system must handle 1–50 PDFs with production-quality retrieval, not toy-demo keyword matching. We explicitly optimize for **ACCURACY**: every answer must be grounded in retrieved evidence, every citation must be verbatim text from the source document, and the system must gracefully handle edge cases like empty PDFs, irrelevant queries, and ambiguous questions. A bonus insight engine suggests follow-up questions and cross-document connections.

---

## 2. Why ACCURACY Over Latency (The Core Tradeoff)

The assignment requires choosing ONE optimization target. We choose **accuracy** because document Q&A is fundamentally a precision task — users uploading PDFs and asking questions expect correct, well-cited answers. They are not chatting in real-time; they are performing research. A fast wrong answer is worse than a slow correct one.

### 2.1 What Accuracy-First Means Architecturally

1. **Two-Stage Retrieval:** Bi-Encoder approximate search (fast, imprecise) → Cross-Encoder Reranker (slow, precise). The reranker sees query and document together, producing dramatically better relevance scores.
2. **Larger Chunks (1000 tokens):** Preserves full paragraphs and multi-sentence arguments. Smaller chunks fragment context.
3. **More Candidates per Query:** Retrieve top-50 from vector search, rerank to top-5. Wide recall funnel prevents relevant chunks from being missed.
4. **Strict Citation Grounding:** The LLM is explicitly forbidden from summarizing. Every citation is verbatim text with document name, page number, and chunk index.

### 2.2 What We Sacrifice

Response time is **2–4 seconds** instead of sub-second. This is acceptable because:
- Users are performing document research, not instant messaging.
- The 4× A10 GPUs make cross-encoder reranking fast (~1–2s for 50 candidates on GPU vs. ~10s on CPU).
- A loading spinner during retrieval is expected UX for document Q&A.

### 2.3 Comparison Table

| Dimension | Latency-Optimized | Accuracy-Optimized (Our Choice) |
|-----------|-------------------|--------------------------------|
| **Retrieval** | Single-stage bi-encoder only | Two-stage: bi-encoder + cross-encoder reranker |
| **Chunk Size** | 256 tokens (faster embedding) | 1000 tokens (preserves context) |
| **Candidates Retrieved** | Top-5 direct | Top-50 → rerank to top-5 |
| **Embedding Model** | MiniLM (384-dim, fast) | BGE-Large (1024-dim, accurate) |
| **Response Time** | < 1 second | 2–4 seconds |
| **Citation Quality** | Approximate, may paraphrase | Verbatim text, exact source location |
| **GPU Utilization** | Minimal | Full — embeddings + reranker on GPU |
| **Edge Case Handling** | Best-effort | Explicit "no relevant info" when confidence low |

---

## 3. System Architecture

### 3.1 High-Level Data Flow

```
                              ┌─────────────────────────────────────────────┐
                              │          INGESTION PIPELINE                 │
                              │                                             │
[ User Browser ]              │  PDF Upload                                 │
      │                       │      │                                      │
      │  Upload PDFs          │      ▼                                      │
      ├──────────────────────►│  PyMuPDF Text Extraction (per page)         │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  SHA-256 Dedup Check                        │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  Recursive Chunking (1000 tok, 200 overlap) │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  BGE-Large Embedding (GPU 0)                │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  FAISS Index (in-memory)                    │
      │                       └─────────────────────────────────────────────┘
      │
      │                       ┌─────────────────────────────────────────────┐
      │                       │           QUERY PIPELINE                    │
      │                       │                                             │
      │  Ask Question         │  User Query                                 │
      ├──────────────────────►│      │                                      │
      │                       │      ▼                                      │
      │                       │  BGE-Large Embed Query (GPU 0)              │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  FAISS ANN Search → Top-50 Candidates       │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  Cross-Encoder Reranker (GPU 1) → Top-5     │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  Relevance Threshold Check (score ≥ 0.3)    │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │                       │  LLM Answer Gen + Verbatim Citations        │
      │                       │      │                                      │
      │                       │      ▼                                      │
      │◄──────────────────────│  QueryResponse (answer + citations[])       │
      │                       └─────────────────────────────────────────────┘
```

### 3.2 The Two-Stage Retrieval Pipeline (The Accuracy Engine)

**Stage 1: Bi-Encoder (Approximate Retrieval)**
- Model: `BAAI/bge-large-en-v1.5` (1024-dimensional embeddings)
- Hardware: GPU 0
- Operation: Query and documents encoded **independently** into dense vectors. FAISS cosine similarity finds top-50 nearest neighbors.
- Speed: ~10ms for query encoding + ~5ms for FAISS search = ~15ms total
- Limitation: Because query and document are encoded separately, the bi-encoder cannot capture fine-grained query-document interaction. It's fast but imprecise.

**Stage 2: Cross-Encoder (Precision Reranking)**
- Model: `cross-encoder/ms-marco-MiniLM-L-12-v2`
- Hardware: GPU 1
- Operation: Each (query, candidate_chunk) pair is fed together through the model. The cross-encoder sees both simultaneously, producing a precise relevance score.
- Speed: ~20–40ms per pair × 50 pairs = ~1–2 seconds on GPU
- Output: Top-5 chunks sorted by cross-encoder score

**Why Two Stages:**
Bi-encoders are fast but imprecise (they encode query and doc independently — no attention between them). Cross-encoders are slow but accurate (they see query + doc together via full cross-attention). The combination gives us both: the bi-encoder's speed to narrow the search space from thousands of chunks to 50, then the cross-encoder's precision to pick the best 5.

### 3.3 The Anti-Summary Mandate

Every answer returned to the user must include:
1. The **exact verbatim chunk text** that supports the answer (no paraphrasing)
2. The **source PDF filename**
3. The **page number(s)** within the PDF
4. The **chunk index** within the document

The LLM system prompt explicitly forbids summarizing:

```
SYSTEM PROMPT (CITATION RULES):
You are a document intelligence assistant. Answer questions using ONLY the provided
document chunks. Follow these rules strictly:

1. VERBATIM CITATIONS: You MUST quote the exact text from the provided chunks.
   Do NOT paraphrase, summarize, or rephrase any cited text.
2. SOURCE ATTRIBUTION: For every claim, include [Source: {filename}, Page {N},
   Chunk {M}] immediately after the quoted text.
3. NO FABRICATION: If the provided chunks do not contain enough information to
   answer the question, say: "The uploaded documents do not contain sufficient
   information to answer this question."
4. MULTI-SOURCE: If multiple chunks support the answer, cite all of them.
5. NO SUMMARY: Do not begin your answer with "Based on the documents..." or
   "The documents suggest...". Go directly to the evidence.
```

---

## 4. The Tech Stack

### Layer 1 — AI & Retrieval

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Embedding Model** | `BAAI/bge-large-en-v1.5` via `sentence-transformers` | Top-ranked open embedding model on MTEB benchmark. 1024-dim vectors capture fine semantic nuance. Runs on A10 GPU 0. |
| **Cross-Encoder Reranker** | `cross-encoder/ms-marco-MiniLM-L-12-v2` | MS MARCO-trained for passage relevance. Runs on A10 GPU 1. Adds ~1–2s but dramatically improves precision. |
| **Vector Store** | FAISS (IndexFlatIP or IndexIVFFlat) | In-memory, zero external dependencies. GPU-accelerable. Adequate for 50 PDFs (~25k chunks). No Docker/server overhead. |
| **LLM (Answer Generation)** | Claude API via `anthropic` SDK (primary), local Mistral-7B via `vllm` (fallback) | If Claude API key is available on the EC2, use it. If not, serve Mistral-7B on GPUs 2–3 via vLLM. |
| **PDF Extraction** | PyMuPDF (`fitz`) | 10–100× faster than PyPDF2. Handles complex layouts, multi-column PDFs, embedded tables. Page-level extraction with reading order. |
| **Chunking** | `langchain.text_splitter.RecursiveCharacterTextSplitter` | `chunk_size=1000`, `chunk_overlap=200`. Splits at paragraph → sentence → word boundaries, preserving semantic coherence. |

### Layer 2 — Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **API Framework** | FastAPI | Async-native for file upload handling. Auto-generates OpenAPI docs at `/docs`. Native Pydantic v2 integration. |
| **Data Validation** | Pydantic v2 | Strict schemas for all API request/response models. `extra = "forbid"` prevents unknown fields. Type-safe throughout. |
| **Configuration** | `pydantic-settings` + env vars | All config (API keys, GPU indices, model names) from environment variables via `backend/config.py`. Zero hardcoded secrets. |
| **Logging** | Python `logging` (stdlib) | Structured logging with level, timestamp, module. No bare `print()` statements. |

### Layer 3 — Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **UI** | Plain HTML + vanilla JS + CSS | Assignment says "function over form — not evaluating design." Zero npm/webpack/build overhead. FastAPI serves static files. |
| **File Upload** | HTML5 `<input type="file" multiple>` + Fetch API | Native browser API. Drag-and-drop optional. Sends multipart/form-data to FastAPI. |
| **Response Display** | DOM manipulation + template literals | Renders answer text + citation cards with source document, page, chunk text. Collapsible citation blocks. |

---

## 5. Data Models (Pydantic Schemas)

All defined in `backend/models/schemas.py`:

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="UUID for the document")
    filename: str
    sha256: str = Field(..., description="Content hash for deduplication")
    upload_time: datetime
    page_count: int
    chunk_count: int
    status: ProcessingStatus
    file_size_bytes: int

class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="UUID for the chunk")
    document_id: str
    document_name: str
    text: str
    page_number: int
    chunk_index: int
    token_count: int

class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_name: str
    page_number: int
    chunk_index: int
    chunk_text: str = Field(..., description="VERBATIM text from source — never summarized")
    relevance_score: float = Field(..., ge=0.0, le=1.0)

class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    citations: list[Citation]
    query: str
    documents_searched: int
    chunks_evaluated: int
    processing_time_ms: float

class InsightSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    insight_text: str
    supporting_chunks: list[Citation]
    suggested_next_question: str
```

---

## 6. Chunking Strategy (Why 1000 Tokens)

| Chunk Size | Pros | Cons | Verdict |
|------------|------|------|---------|
| **256 tokens** | Fast to embed. More chunks = finer granularity. | Fragments sentences. Loses paragraph context. Embedding captures partial ideas. | ❌ Bad for accuracy |
| **512 tokens** | Common default. Reasonable balance. | Still splits complex paragraphs. Multi-sentence arguments broken across chunks. | ⚠️ OK for latency optimization |
| **1000 tokens** | Preserves full paragraphs. Complete arguments in single chunks. Embedding captures full semantic meaning. | Slower to embed (~3× vs 256). Fewer chunks = slightly less granular. | ✅ Our choice — accuracy-first |
| **2000+ tokens** | Maximum context per chunk. | Dilutes embedding signal. Cross-encoder struggles with very long inputs (512 max). Chunks contain mixed topics. | ❌ Too large |

**Overlap: 200 tokens.** Ensures that information at chunk boundaries is captured in at least two chunks. Without overlap, a key sentence at position 999–1001 would be split across two chunks and potentially missed by both embeddings.

**Separator Hierarchy:** `RecursiveCharacterTextSplitter` splits at `\n\n` (paragraph) → `\n` (line) → `. ` (sentence) → ` ` (word). This preserves semantic boundaries at every level.

---

## 7. Edge Case Handling

| Edge Case | Detection | Response | HTTP Code |
|-----------|-----------|----------|-----------|
| **Empty PDF** (0 extractable text) | `len(page.get_text().strip()) == 0` for all pages | Return error: "PDF contains no extractable text." Skip indexing. | 400 |
| **Scanned/Image-only PDF** | All pages return empty text but file size > 10KB | Return warning: "PDF appears to be scanned. OCR not implemented." Log for future improvement. | 422 |
| **Corrupted PDF** | `fitz.open()` raises exception | Catch `fitz.FileDataError`. Log error. Skip file. Continue processing remaining PDFs. | 422 |
| **Password-protected PDF** | `fitz.open()` raises encryption error | Return error: "PDF is password-protected. Please upload an unlocked version." | 422 |
| **Irrelevant query** | Max cross-encoder score < 0.3 threshold | Return: "No relevant information found in the uploaded documents for this query." | 200 (with empty citations) |
| **Query before any upload** | `vector_store.is_empty()` | Return error: "Please upload at least one document before asking questions." | 400 |
| **Duplicate PDF upload** | SHA-256 hash already in metadata store | Skip re-processing. Return existing document metadata. | 200 (idempotent) |
| **Very long PDF** (500+ pages) | `doc.page_count > 500` | Process all pages. Log warning. No artificial limit. Chunking handles size naturally. | 200 |
| **Non-English PDF** | Not detected at upload | BGE model handles English well. Non-English recall may degrade. Document in README as limitation. | 200 |
| **Malformed question** (empty, too long) | Pydantic validation on `QueryRequest` | Return validation error with details. | 422 |

---

## 8. What Breaks at Scale (10,000+ Documents)

This section directly answers the assignment's README requirement: "What would break at scale (e.g., 10k+ documents)."

### 8.1 Silent Recall Degradation

**Problem:** FAISS HNSW's default `ef_search` parameter (16–64) works well for <10k vectors. At 10k+ documents (~5M chunks), the approximate nearest neighbor search starts silently missing relevant results. The recall@50 can drop from 95% to 70% without any visible error.

**Mitigation:** Tune `ef_search` (HNSW) or `n_probe` (IVF) parameters. Higher values = better recall but slower search. Monitor recall via a held-out eval set. Switch to IVF-PQ with `n_probe=64` for 10k+ doc corpus.

### 8.2 Memory Pressure

**Calculation:**
- 10,000 documents × ~500 chunks/doc = 5,000,000 chunks
- 5M chunks × 1024 dimensions × 4 bytes (float32) = **~20 GB** for embeddings alone
- Plus chunk text storage, metadata, FAISS overhead → **~30–40 GB** total

**Mitigation:**
- IVF-PQ quantization reduces embedding memory 4–8×
- Product quantization: 1024-dim → 128 sub-vectors × 8-bit codes = ~640 MB
- Move to Milvus or Qdrant with disk-backed indices for >50GB datasets

### 8.3 Ingestion Time Bottleneck

**Problem:** Sequential PDF processing (current architecture) at ~1 second/PDF = 10,000 seconds (~2.7 hours). Unacceptable.

**Mitigation:** Celery + Redis task queue with parallel workers. Batch embedding generation (process 32–64 chunks per GPU call instead of one-by-one). Async upload with status polling endpoint.

### 8.4 Vector Store Scaling

**Problem:** FAISS `IndexFlatIP` (exact search) becomes impractical at 5M+ vectors. Even `IndexIVFFlat` with `n_probe=10` takes >100ms per query.

**Mitigation:** Switch to FAISS `IndexIVFPQ` or migrate to a purpose-built vector database (Milvus, Qdrant, Weaviate) with disk-backed indices, sharding, and replication.

### 8.5 Reranker Throughput

**Problem:** Cross-encoder processes 50 candidates per query at ~1–2 seconds on GPU. At 100 concurrent users: 100 × 50 = 5,000 (query, chunk) pairs. Single A10 GPU becomes a bottleneck.

**Mitigation:** Horizontal scaling — load-balance reranker across multiple GPUs. Use distilled/smaller cross-encoder models. Implement request batching.

---

## 9. Directory Structure

```
doc-intelligence/
├── CLAUDE.md                   # Claude Code behavioral rules (Karpathy-based)
├── DESIGN.md                   # This file — Architecture Bible
├── DECISIONS.md                # Decision log with rationale
├── README.md                   # Assignment deliverable
├── requirements.txt            # Python dependencies (pinned)
├── eval.py                     # Eval-Driven Development script
├── .env.example                # Environment variable template
├── .gitignore                  # Excludes .env, uploads/, __pycache__, etc.
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app — mounts routes, serves frontend
│   ├── config.py               # pydantic-settings: env var config
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # ALL Pydantic models (Section 5)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py    # PDF ingestion: extract → chunk → metadata
│   │   ├── embedding_service.py # BGE-Large bi-encoder on GPU 0
│   │   ├── vector_store.py     # FAISS index: add, search, delete
│   │   ├── reranker.py         # Cross-encoder reranking on GPU 1
│   │   ├── answer_generator.py # LLM answer + verbatim citation builder
│   │   └── insight_engine.py   # Bonus: cross-document insight suggestions
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── documents.py        # POST /upload, GET /documents, DELETE /documents/{id}
│   │   └── query.py            # POST /query, POST /insights
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py       # Chunking helpers, text cleaning
├── frontend/
│   ├── index.html              # Single-page UI
│   ├── style.css               # Minimal functional styling
│   └── app.js                  # Fetch API calls to backend
├── tests/
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_retrieval.py
│   ├── test_reranker.py
│   ├── test_api.py
│   └── test_edge_cases.py
└── uploads/                    # Uploaded PDFs (gitignored)
```

---

## 10. Sprint Plan (8-Hour Allocation)

| Hour | Sprint | Deliverable | Verification |
|------|--------|-------------|-------------|
| **0:00–0:45** | S0: Scaffold | Project structure, `requirements.txt`, `config.py`, Pydantic schemas, `.gitignore`, CLAUDE.md/DESIGN.md/DECISIONS.md in place | `python -c "from backend.models.schemas import *; print('OK')"` |
| **0:45–1:45** | S1: PDF Ingestion | `pdf_processor.py`: PyMuPDF extract → chunk → metadata. Handle empty/corrupt PDFs. SHA-256 dedup. | `python eval.py` — ingestion tests pass |
| **1:45–3:00** | S2: Embedding + Vector Store | `embedding_service.py`: BGE-Large on GPU 0. `vector_store.py`: FAISS index build/search. | `python eval.py` — retrieval tests pass (verify top-50 contains known relevant chunks) |
| **3:00–4:00** | S3: Cross-Encoder Reranker | `reranker.py`: ms-marco on GPU 1. Rerank top-50 → top-5. Relevance threshold check. | `python eval.py` — reranking improves precision over bi-encoder alone |
| **4:00–5:15** | S4: Answer Generation | `answer_generator.py`: LLM prompt with anti-summary mandate. Verbatim citations with source/page/chunk. | `python eval.py` — citation format correct, text is verbatim from source |
| **5:15–6:15** | S5: FastAPI + Frontend | Routers: `/upload`, `/documents`, `/query`. Frontend: HTML upload + question + answer display. | Manual browser test: upload PDF → ask question → see answer with citations |
| **6:15–7:00** | S6: Edge Cases + Polish | Empty PDF handling, irrelevant query detection, error messages, logging. | `python eval.py` — all edge case tests pass |
| **7:00–7:30** | S7: Bonus — Insight Engine | `insight_engine.py`: Cross-document theme detection, suggested follow-up questions. | Best-effort. Skip if behind schedule. |
| **7:30–8:00** | S8: README + Final Push | Write README (architecture, decisions, tradeoffs, scale analysis). Final eval run. Git push. | `python eval.py` — 100% Logic Score. README covers all required sections. `git push` succeeds. |

---

## 11. Improvements With More Time

If this were a production system with unlimited development time:

1. **OCR Pipeline:** Tesseract/PaddleOCR integration for scanned/image-only PDFs.
2. **Table Extraction:** Specialized table parsing (Camelot, pdfplumber) to extract structured data from PDF tables.
3. **Multi-Modal:** Support for images, charts, and diagrams within PDFs via vision models.
4. **Conversation Memory:** Multi-turn Q&A with context from previous questions.
5. **Document Versioning:** Track document updates, re-embed only changed pages.
6. **Fine-Tuned Embedding Model:** Domain-specific fine-tuning of BGE-Large on the target document corpus.
7. **Streaming Answers:** SSE/WebSocket streaming for the LLM response (perceived latency reduction).
8. **User Authentication:** Multi-tenant document isolation.
9. **Caching Layer:** Redis cache for frequent queries (cache key = hash of query + document set).
10. **Monitoring:** Prometheus metrics for retrieval quality, latency percentiles, GPU utilization.

---

*N-ERGY Document Intelligence System — DESIGN.md*
*Do not modify this document without updating the "Last Updated" date.*
