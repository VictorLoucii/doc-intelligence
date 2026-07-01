# N-ERGY Document Intelligence System

> **A production-grade, accuracy-first document Q&A engine that lets users upload PDFs, ask natural language questions, and receive answers grounded in verbatim, cited evidence from the source material.**

Built as an 8-hour engineering challenge on AWS EC2 (4× NVIDIA A10 GPUs). This system explicitly optimizes for **ACCURACY over latency** — every answer is traceable back to an exact chunk of text in the original document, with page number, chunk index, and the verbatim quote.

---

## Table of Contents

1. [Why Accuracy Over Latency](#1-why-accuracy-over-latency)
2. [System Architecture](#2-system-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Key Design Decisions & Trade-offs](#4-key-design-decisions--trade-offs)
5. [What Breaks at Scale (10,000+ Documents)](#5-what-breaks-at-scale-10000-documents)
6. [Project Structure](#6-project-structure)
7. [Installation & Launch](#7-installation--launch)
8. [API Reference](#8-api-reference)
9. [Sprint Roadmap](#9-sprint-roadmap)
10. [Improvements With More Time](#10-improvements-with-more-time)
11. [Project Status & Verification](#11-project-status--verification)

---

## 1. Why Accuracy Over Latency

The assignment asks us to choose one optimization target. We chose **accuracy** because document Q&A is fundamentally a precision task — users uploading PDFs and asking questions expect correct, well-cited answers. They are not chatting in real-time; they are performing research. A fast wrong answer is worse than a slow correct one.

**What accuracy-first means architecturally:**

| Dimension | Latency-Optimized | Accuracy-Optimized (Our Choice) |
|---|---|---|
| **Retrieval** | Single-stage bi-encoder only | Two-stage: bi-encoder + cross-encoder reranker |
| **Chunk Size** | 256 tokens (faster embedding) | 1000 tokens (preserves full paragraphs) |
| **Candidates Retrieved** | Top-5 direct | Top-50 → rerank to top-5 |
| **Embedding Model** | MiniLM (384-dim, fast) | BGE-Large (1024-dim, accurate) |
| **Response Time** | < 1 second | 2–4 seconds |
| **Citation Quality** | May paraphrase | Verbatim text, exact source location |
| **GPU Utilization** | Minimal | Full — embeddings on GPU 0, reranker on GPU 1 |

**What we sacrifice:** Response time is 2–4 seconds instead of sub-second. This is acceptable because the 4× A10 GPUs make cross-encoder reranking fast (~1–2s for 50 candidates on GPU vs. ~10s on CPU), and a loading spinner during document research is expected UX.

---

## 2. System Architecture

### The Two-Stage Retrieval Pipeline

The core accuracy engine uses two retrieval stages:

- **Stage 1 — Bi-Encoder (Recall):** `BAAI/bge-large-en-v1.5` encodes the query into a 1024-dim vector. FAISS finds the top-50 nearest neighbors via approximate cosine similarity. Fast (~15ms) but imprecise — query and document are encoded independently with no cross-attention.

- **Stage 2 — Cross-Encoder (Precision):** `cross-encoder/ms-marco-MiniLM-L-12-v2` takes each (query, candidate_chunk) pair and scores them jointly via full cross-attention. Dramatically more accurate. Reranks the 50 candidates down to the top-5. Chunks scoring below a 0.3 relevance threshold are filtered out entirely.

### Data Flow

```
INGESTION PIPELINE
==================

  User uploads PDFs
        │
        ▼
  PyMuPDF Text Extraction (per page)
        │
        ▼
  SHA-256 Deduplication Check ──── duplicate? ──→ Skip, return existing metadata
        │
        ▼ (new document)
  Recursive Chunking (1000 tokens, 200 overlap)
        │
        ▼
  BGE-Large Embedding Generation (GPU 0)
        │
        ▼
  FAISS Index (in-memory, IndexFlatIP)


QUERY PIPELINE
==============

  User submits question
        │
        ▼
  BGE-Large Embed Query (GPU 0)
        │
        ▼
  FAISS ANN Search → Top-50 Candidates
        │
        ▼
  Cross-Encoder Reranker (GPU 1) → Top-5
        │
        ▼
  Relevance Threshold Filter (score ≥ 0.3)
        │                              │
        ▼ (chunks pass)                ▼ (all below threshold)
  LLM Answer Generation         "No relevant information
  + Verbatim Citations            found in the uploaded
        │                          documents."
        ▼
  QueryResponse {
    answer: "...",
    citations: [
      { document_name, page_number,
        chunk_index, chunk_text (VERBATIM) }
    ]
  }
```

### The Anti-Summary Mandate

Every answer returned to the user includes the **exact verbatim text** from the source document — no paraphrasing, no summarizing, no rewording. The LLM system prompt explicitly forbids summarization. Each citation includes: document filename, page number, chunk index, and the exact quoted text. This creates a verifiable trust chain: the user can trace any claim back to the original PDF.

---

## 3. Tech Stack

### Layer 1 — AI & Retrieval

| Component | Technology | Why |
|---|---|---|
| Embedding Model | `BAAI/bge-large-en-v1.5` via `sentence-transformers` | Top MTEB benchmark model. 1024-dim vectors. Runs on GPU 0. |
| Cross-Encoder Reranker | `cross-encoder/ms-marco-MiniLM-L-12-v2` | MS MARCO-trained passage relevance scorer. Runs on GPU 1. |
| Vector Store | FAISS (`IndexFlatIP`) | In-memory, zero external dependencies, GPU-accelerable. Adequate for 50 PDFs (~25k chunks). |
| LLM (Answer Generation) | Claude API via `anthropic` SDK | Primary answer generator. Fallback: local Mistral-7B via vLLM on GPUs 2–3. |
| PDF Extraction | PyMuPDF (`fitz`) | 10–100× faster than PyPDF2. Handles complex layouts. Page-level extraction. |
| Chunking | `langchain-text-splitters` | `RecursiveCharacterTextSplitter` — 1000-token chunks, 200-token overlap. |

### Layer 2 — Backend

| Component | Technology | Why |
|---|---|---|
| API Framework | FastAPI | Async-native. Auto OpenAPI docs at `/docs`. Native Pydantic v2 integration. |
| Data Validation | Pydantic v2 | Strict schemas, `extra="forbid"` on all models. Type-safe throughout. |
| Configuration | `pydantic-settings` | All config from environment variables. Zero hardcoded secrets. |

### Layer 3 — Frontend

| Component | Technology | Why |
|---|---|---|
| UI | Plain HTML + vanilla JS + CSS | Assignment says "function over form." Zero build tooling overhead. |

### GPU Allocation

| GPU | Assignment | VRAM |
|---|---|---|
| GPU 0 | Embedding model (`bge-large-en-v1.5`) | ~1.5 GB |
| GPU 1 | Cross-encoder reranker (`ms-marco-MiniLM`) | ~0.5 GB |
| GPU 2 | Local LLM fallback (if no Claude API) | ~14 GB |
| GPU 3 | Reserved / idle | — |

All models use explicit `torch.device('cuda:N')` assignments to prevent memory contention.

---

## 4. Key Design Decisions & Trade-offs

| # | Decision | Rationale | Trade-off |
|---|---|---|---|
| 1 | **Accuracy over latency** — Two-stage retrieval | Document Q&A is research, not chat. Correct cited answers > fast wrong ones. A10 GPUs make reranking viable. | 2–4s response vs. sub-second |
| 2 | **1000-token chunks, 200-token overlap** | Preserves full paragraphs and multi-sentence arguments. 256 tokens fragments sentences. | Fewer total chunks, ~3× slower embedding vs. 256 |
| 3 | **Anti-Summary Mandate** — Verbatim citations only | Assignment requires "exact chunks or references." Summaries are LLM interpretation, not evidence. | Longer answers (full quoted text vs. compressed summary) |
| 4 | **FAISS over ChromaDB/Pinecone** | Zero-dependency, in-process library. No Docker, no API keys, no network. Adequate for 50 PDFs. | No built-in persistence (in-memory only at current scale) |
| 5 | **BGE-Large over MiniLM** | Top MTEB retrieval model. 1024-dim captures more nuance. | ~3× slower embedding than MiniLM-384 |
| 6 | **PyMuPDF over PyPDF2** | 10–100× faster. Better complex layout handling. | C-extension dependency |
| 7 | **FastAPI over Flask** | Async-native, auto OpenAPI, native Pydantic v2 integration | Slightly more opinionated than Flask |
| 8 | **Plain HTML over React** | Assignment doesn't evaluate design. React would cost 2+ hours with zero ROI. | No component reusability |
| 9 | **Eval-Driven Development** | `eval.py` gates every task. Prevents silent regressions from AI-assisted coding. | Slight overhead per sprint (~2 min to run) |
| 10 | **Programmatic LLM bypasses** | "How many documents?" = direct count. No LLM needed. Eliminates hallucination for factual queries. | Extra routing logic |
| 11 | **SHA-256 dedup at upload** | Prevents duplicate embeddings polluting vector store. Deterministic, zero false positives. | 5 lines of code, near-zero cost |
| 12 | **No Celery/Redis** — Synchronous processing | 50 PDFs × ~1s = ~50s total. Loading spinner acceptable. Celery+Redis = 1–2 hours of setup time. | Not viable at 10k+ documents |

---

## 5. What Breaks at Scale (10,000+ Documents)

### 5.1 Silent Recall Degradation

**Problem:** FAISS HNSW's default `ef_search` (16–64) works for <10k vectors. At 10k+ documents (~5M chunks), approximate nearest neighbor recall@50 silently drops from 95% to ~70% — no error, just worse answers.

**Mitigation:** Tune `ef_search` (HNSW) or `n_probe` (IVF) upward. Switch to `IndexIVFPQ` with `n_probe=64`. Monitor recall via a held-out evaluation set.

### 5.2 Memory Pressure

**Calculation:**
```
10,000 documents × ~500 chunks/doc     =   5,000,000 chunks
5M chunks × 1024 dims × 4 bytes (fp32) = ~20 GB (embeddings alone)
+ chunk text + metadata + FAISS overhead = ~30–40 GB total
```

**Mitigation:** IVF-PQ quantization reduces memory 4–8× (1024-dim → 128 sub-vectors × 8-bit codes = ~640 MB). For >50GB: migrate to Milvus or Qdrant with disk-backed indices.

### 5.3 Ingestion Time

**Problem:** Sequential PDF processing at ~1s/PDF → 10,000 PDFs = ~2.7 hours.

**Mitigation:** Celery + Redis async task queue with parallel workers. Batch embedding generation (32–64 chunks per GPU call). Async upload with status polling endpoint.

### 5.4 Vector Store Index Type

**Problem:** `IndexFlatIP` (exact brute-force search) is O(n) — impractical at 5M+ vectors.

**Mitigation:** Switch to `IndexIVFPQ` or migrate to a purpose-built vector database (Milvus, Qdrant) with disk-backed indices, sharding, and replication.

### 5.5 Reranker Throughput

**Problem:** 100 concurrent users × 50 candidates each = 5,000 cross-encoder inferences. Single A10 GPU becomes a bottleneck.

**Mitigation:** Horizontal GPU scaling, distilled cross-encoder models, request batching across concurrent queries.

---

## 6. Project Structure

```
doc-intelligence/
├── CLAUDE.md                      # Claude Code behavioral rules
├── DESIGN.md                      # Architecture Bible
├── DECISIONS.md                   # Decision log with rationale
├── README.md                      # This file
├── requirements.txt               # Pinned Python dependencies
├── eval.py                        # Eval-Driven Development harness
├── .env.example                   # Environment variable template
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # pydantic-settings config
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # All Pydantic v2 models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py       # PDF extract → chunk → metadata
│   │   ├── embedding_service.py   # BGE-Large on GPU 0
│   │   ├── vector_store.py        # FAISS index ops
│   │   ├── reranker.py            # Cross-encoder on GPU 1
│   │   ├── answer_generator.py    # LLM + verbatim citation builder
│   │   └── insight_engine.py      # Bonus: cross-doc insights
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── documents.py           # /upload, /documents, /documents/{id}
│   │   └── query.py               # /query, /insights
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py          # Chunking helpers
├── frontend/
│   ├── index.html                 # Single-page UI
│   ├── style.css
│   └── app.js                     # Fetch API calls
├── tests/
│   └── ...
└── uploads/                       # Uploaded PDFs (gitignored)
```

---

## 7. Installation & Launch

### Prerequisites

- Python 3.11+
- NVIDIA GPU with CUDA 12.1+ (for A10 GPU support)
- An Anthropic API key (optional — system falls back to local LLM)

### Setup

```bash
# Clone the repository
git clone https://github.com/<username>/doc-intelligence.git
cd doc-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install PyTorch with CUDA 12.1 support (REQUIRED for A10 GPUs)
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
#   ANTHROPIC_API_KEY=sk-ant-...
#   EMBEDDING_GPU_ID=0
#   RERANKER_GPU_ID=1
#   LLM_GPU_ID=2
```

### Launch

```bash
# Start the server
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# The application is now available at:
#   UI:       http://localhost:8000
#   API Docs: http://localhost:8000/docs
```

### Verify Installation

```bash
# Run the evaluation harness
python eval.py -v
# Expected: 🎯 Logic Score: 100% — ALL 30 TESTS PASSED
```

---

## 8. API Reference

| Method | Endpoint | Description | Request | Response |
|---|---|---|---|---|
| `POST` | `/upload` | Upload one or more PDFs | `multipart/form-data` (files) | `DocumentMetadata[]` |
| `GET` | `/documents` | List all uploaded documents | — | `DocumentMetadata[]` |
| `DELETE` | `/documents/{id}` | Remove a document and its embeddings | — | `204 No Content` |
| `POST` | `/query` | Ask a question about uploaded documents | `{"question": "...", "top_k": 5}` | `QueryResponse` |

### QueryResponse Schema

```json
{
  "answer": "The exact answer text...",
  "citations": [
    {
      "document_name": "report.pdf",
      "page_number": 7,
      "chunk_index": 14,
      "chunk_text": "The exact verbatim text from the source...",
      "relevance_score": 0.92
    }
  ],
  "query": "What was the revenue?",
  "documents_searched": 3,
  "chunks_evaluated": 50,
  "processing_time_ms": 2340.5
}
```

---

## 9. Sprint Roadmap

| Sprint | Hours | Deliverable | Verification |
|---|---|---|---|
| **S0** Scaffold | 0:00–0:45 | Project structure, `requirements.txt`, config, Pydantic schemas | `from backend.models.schemas import *` |
| **S1** PDF Ingestion | 0:45–1:45 | PyMuPDF extract → chunk → metadata. Empty/corrupt PDF handling. SHA-256 dedup. | `python eval.py` — ingestion tests pass |
| **S2** Embedding + Vector Store | 1:45–3:00 | BGE-Large on GPU 0. FAISS index build/search. | `python eval.py` — retrieval tests pass |
| **S3** Cross-Encoder Reranker | 3:00–4:00 | ms-marco on GPU 1. Rerank top-50 → top-5. Relevance threshold. | `python eval.py` — reranking beats bi-encoder |
| **S4** Answer Generation | 4:00–5:15 | LLM prompt with anti-summary mandate. Verbatim citations. | `python eval.py` — citations are verbatim |
| **S5** API + Frontend | 5:15–6:15 | FastAPI routers + HTML/JS upload, question, answer display. | Browser test: upload → ask → see citations |
| **S6** Edge Cases | 6:15–7:00 | Empty PDF, irrelevant query, error messages, logging. | `python eval.py` — all edge cases pass |

---

## 10. Improvements With More Time

If this were a production system with unlimited development time:

1. **OCR Pipeline** — Tesseract/PaddleOCR for scanned/image-only PDFs
2. **Table Extraction** — Camelot/pdfplumber for structured table data within PDFs
3. **Multi-Modal Support** — Vision models for charts, diagrams, and images embedded in PDFs
4. **Conversation Memory** — Multi-turn Q&A with context from previous questions
5. **Document Versioning** — Track updates, re-embed only changed pages
6. **Fine-Tuned Embeddings** — Domain-specific BGE-Large fine-tuning on the target corpus
7. **Streaming Answers** — SSE/WebSocket for perceived latency reduction during LLM generation
8. **User Authentication** — Multi-tenant document isolation and access control
9. **Query Caching** — Redis cache keyed on `hash(query + document_set)` for repeated questions
10. **Observability** — Prometheus metrics for retrieval quality, latency percentiles, and GPU utilization

---

## 11. Project Status & Verification

This repository represents the completed submission for the N-ERGY Document Intelligence System within the designated 8-hour engineering window. All implementation phases have been verified via the automated evaluation harness.

| Component | Status | Verification |
|---|---|---|
| FastAPI Core Backend | 🟩 **COMPLETE** | Pydantic v2 schema alignment — all models validate |
| Multi-PDF Processing Pipeline | 🟩 **COMPLETE** | PyMuPDF extraction, SHA-256 dedup, recursive chunking |
| Two-Stage Retrieval Engine | 🟩 **COMPLETE** | BGE-Large (GPU 0) + Cross-Encoder reranking (GPU 1) |
| Verbatim Citation System | 🟩 **COMPLETE** | Anti-summary mandate enforced in all LLM prompts |
| Browser-Based UI | 🟩 **COMPLETE** | Upload, question input, answer + citation display |
| Edge Case Handling | 🟩 **COMPLETE** | Empty/corrupt/encrypted PDFs, irrelevant queries |

### Automated Verification

The system state is verified under our Eval-Driven Development (EDD) constraint. Run the full regression suite:

```bash
python eval.py -v
```

Expected output:

```
🎯 Logic Score: 100% — ALL 30 TESTS PASSED
```

---

*Built with precision for the N-ERGY engineering team.*
