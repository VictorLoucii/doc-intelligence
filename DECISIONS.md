# N-ERGY Document Intelligence System — Decision Log
## Architectural & Engineering Decisions for Future Reference

> **Purpose:** Every significant architectural or engineering decision made during
> the build is recorded here with its rationale. This document directly feeds the
> README's "Key design decisions" and "Tradeoffs you made" sections.

---

## Decision 1: Accuracy Over Latency — Two-Stage Retrieval

**Date:** July 2026
**Status:** Active
**Decision:** We optimize explicitly for ACCURACY, not latency. This means implementing
a Two-Stage Retrieval Pipeline: Bi-Encoder vector search (fast approximate) followed
by a Cross-Encoder Reranker (slow but precise).

**Reason:**
- Document Q&A is not a real-time chatbot. Users uploading PDFs and asking questions
  expect correct, well-cited answers — not fast wrong ones.
- The assignment explicitly asks us to choose one optimization target and explain why.
  Accuracy is more compelling to evaluators because it demonstrates deeper engineering
  (reranking, citation grounding, relevance thresholding) vs. latency optimization
  which is primarily caching and smaller models.
- The 4× A10 GPUs make cross-encoder reranking viable. Without GPUs, reranking 50
  candidates would take ~10s on CPU. On A10, it takes ~1–2s.

**Tradeoff sacrificed:** Response time is 2–4 seconds instead of sub-second. This is
acceptable for the use case — document research is not instant messaging.

---

## Decision 2: Chunk Size 1000 Tokens with 200-Token Overlap

**Date:** July 2026
**Status:** Active
**Decision:** Use `RecursiveCharacterTextSplitter` with `chunk_size=1000` and
`chunk_overlap=200`.

**Reason:**
- Accuracy-first chunking requires preserving full paragraphs and multi-sentence
  arguments within a single chunk.
- 256-token chunks (common in tutorials) fragment sentences and lose context —
  the embedding captures an incomplete thought, degrading retrieval quality.
- 512-token chunks are the "safe default" but still split complex paragraphs
  that span 600–800 tokens.
- 1000 tokens preserves complete arguments. The 200-token overlap ensures no
  information falls between chunk boundaries — a key sentence at position
  999–1001 appears in both adjacent chunks.
- The cross-encoder reranker handles longer chunks well. Its input truncates
  at ~512 tokens, but the bi-encoder embedding still captured the full chunk
  semantics for the first-stage retrieval.

**Tradeoff:** Fewer total chunks means slightly less granular retrieval. Embedding
generation is ~3× slower than 256-token chunks. Both are acceptable for 50 PDFs.

---

## Decision 3: Anti-Summary Mandate — Verbatim Citations Only

**Date:** July 2026
**Status:** Active
**Decision:** The LLM answer generation prompt explicitly FORBIDS summarizing
retrieved chunks. Every citation must include the exact verbatim text from the
source document.

**Reason:**
- The assignment requires "cited sources (exact chunks or references)." Summaries
  are not citations — they are the LLM's interpretation, which may hallucinate or
  distort the source material.
- LLMs naturally summarize and paraphrase. Without explicit anti-summary instructions,
  the model will compress retrieved text and the "citation" becomes unreliable.
  The user cannot verify a paraphrased citation against the source document.
- Verbatim citations create a verifiable trust chain: user reads the answer → reads
  the cited text → can locate the exact text in the original PDF. This is the
  entire point of a document intelligence system.

**Implementation:** The LLM system prompt includes explicit rules: "You MUST quote
the exact text from the provided chunks. Do NOT paraphrase, summarize, or rephrase.
Include the document name, page number, and chunk index for every claim."

---

## Decision 4: FAISS Over ChromaDB / Weaviate / Pinecone

**Date:** July 2026
**Status:** Active
**Decision:** Use FAISS (Facebook AI Similarity Search) as the vector store.

**Reason:**
- FAISS is zero-dependency: no Docker container, no external server process, no
  API key, no network calls. It runs as an in-process Python library.
- For 50 PDFs (~25,000 chunks), in-memory FAISS is perfectly adequate. The entire
  index fits in ~100MB RAM. There is zero benefit from a distributed vector database
  at this scale.
- FAISS supports GPU acceleration via `faiss-gpu`, which we can leverage on the A10s
  if search latency becomes a concern.
- ChromaDB adds Docker overhead and a separate server process. Pinecone requires an
  API key and internet connectivity. Weaviate is a heavyweight system designed for
  multi-tenant production deployments. All are overkill for this scope.

**Scale mitigation:** At 10k+ documents, FAISS in-memory would consume ~20GB RAM.
Migration path: switch to `IndexIVFPQ` (4–8× memory reduction via product
quantization) or migrate to Milvus/Qdrant with disk-backed indices and sharding.

---

## Decision 5: BGE-Large Over MiniLM for Embeddings

**Date:** July 2026
**Status:** Active
**Decision:** Use `BAAI/bge-large-en-v1.5` (1024-dim) as the bi-encoder embedding
model instead of `all-MiniLM-L6-v2` (384-dim).

**Reason:**
- BGE-Large is the top-ranked open-source embedding model on the MTEB benchmark
  for retrieval tasks. Higher embedding quality directly translates to better
  first-stage recall.
- 1024-dimensional embeddings capture more semantic nuance than 384-dim. For an
  accuracy-first system, this difference matters.
- The model fits comfortably on one A10 GPU (24GB VRAM). BGE-Large uses ~1.5GB
  VRAM. We have 4 GPUs, so dedicating one to embeddings is trivial.
- MiniLM would be the correct choice if we were optimizing for latency — it's 6×
  faster and uses 3× less memory. But we're not.

**Tradeoff:** Embedding generation is ~3× slower than MiniLM. For 50 PDFs with
~25,000 chunks, total embedding time is ~30–60 seconds vs. ~10–20 seconds.
Acceptable for a one-time ingestion operation.

---

## Decision 6: PyMuPDF (fitz) Over pdfplumber / PyPDF2

**Date:** July 2026
**Status:** Active
**Decision:** Use PyMuPDF for all PDF text extraction.

**Reason:**
- PyMuPDF is 10–100× faster than PyPDF2 for text extraction. A 100-page PDF takes
  <1 second with PyMuPDF vs. 5–30 seconds with PyPDF2.
- It handles complex layouts, multi-column PDFs, and embedded tables better than
  pdfplumber (which is optimized for table extraction specifically).
- It provides page-level text extraction with proper reading order, which we need
  for page-number attribution in citations.
- Single C-extension dependency. Installs cleanly on Linux EC2 via pip.

---

## Decision 7: FastAPI Over Flask / Django

**Date:** July 2026
**Status:** Active
**Decision:** Use FastAPI as the backend framework.

**Reason:**
- Async-native: handles concurrent file uploads and embedding generation without
  blocking the event loop.
- Auto-generates interactive OpenAPI documentation at `/docs` — free API
  documentation for the README and evaluator to explore.
- Pydantic v2 integration is native — request/response validation uses the same
  models defined in `schemas.py` with zero adapter code.
- Type hints throughout the framework — Claude Code generates fewer bugs when
  working with strongly-typed frameworks.
- Flask would work but requires manual OpenAPI generation and lacks native Pydantic
  support. Django is a full MVC framework — extreme overkill for an API backend.

---

## Decision 8: Plain HTML + Vanilla JS — Not React / Next.js / Streamlit

**Date:** July 2026
**Status:** Active
**Decision:** The frontend will be plain HTML + vanilla JavaScript + minimal CSS.
Not React, Next.js, Vue, or Streamlit.

**Reason:**
- The assignment explicitly states: "We are not evaluating design — we are evaluating
  whether you can wire a frontend to a backend cleanly."
- A React/Next.js SPA would consume 2+ hours of the 8-hour budget on npm setup,
  webpack configuration, component architecture, and build tooling — zero ROI for
  the evaluation criteria.
- Streamlit was considered (30 minutes to a working UI) but rejected because:
  (a) it introduces an additional server process, (b) file upload handling is less
  transparent, and (c) plain HTML demonstrates raw API integration without framework
  abstraction — more impressive to evaluators.
- Plain HTML: ~45 minutes to a fully functional upload + question + answer display
  with citation cards. FastAPI serves static files directly. No build step.

**Budget rule:** Maximum 60 minutes on frontend. If over budget, cut CSS polish first.

---

## Decision 9: Eval-Driven Development (EDD) via eval.py

**Date:** July 2026
**Status:** Active
**Decision:** All development is gated by a local `eval.py` script. No component
is considered "done" until its corresponding eval test passes with 100% Logic Score.

**Reason:**
- With an 8-hour time constraint and Claude Code (in Goal Mode) doing most of the
  coding, the #1 risk is **silent regressions** — Claude "fixes" one component and
  unknowingly breaks another.
- The eval script provides a continuous ground truth. If the Logic Score drops below
  100% after any change, that change introduced a regression and must be fixed before
  moving to the next sprint task.
- EDD replaces the need for comprehensive `pytest` test suites, which would take
  2+ hours to write properly. `eval.py` is a single script with targeted checks:
  PDF ingestion, chunking correctness, embedding generation, retrieval accuracy,
  reranking improvement, citation verbatim match, and API endpoint responses.

**Enforcement:** CLAUDE.md Rule 5.1 makes this non-negotiable. Claude Code must
run `python eval.py` before declaring any task complete.

---

## Decision 10: Programmatic LLM Bypasses for Direct Lookups

**Date:** July 2026
**Status:** Active
**Decision:** Certain query types bypass the LLM entirely and return structured
data directly from the metadata store.

**Reason:**
- "How many documents are uploaded?" → Direct count from metadata. No LLM needed.
  Using an LLM for this wastes latency and introduces hallucination risk.
- "What documents contain [keyword]?" → Full-text search across chunk text.
  No embedding or reranking needed.
- "Show me page 5 of document X" → Direct page retrieval from PDF. No LLM needed.
- These bypasses simultaneously eliminate unnecessary latency AND eliminate
  hallucination risk for factual queries. It is strictly better to return a
  deterministic count than to ask an LLM to "count" documents.

**Implementation:** A lightweight intent classifier (regex patterns + keyword
matching) checks each query before sending it through the full retrieval pipeline.
Deterministic queries get deterministic answers. All other queries go through the
two-stage retrieval pipeline.

---

## Decision 11: GPU Allocation Strategy — 4× A10 Distribution

**Date:** July 2026
**Status:** Active
**Decision:** Allocate GPUs with explicit `torch.device('cuda:N')` assignments:

| GPU | Assignment | VRAM Usage | Reason |
|-----|-----------|------------|--------|
| GPU 0 | Embedding model (`BAAI/bge-large-en-v1.5`) | ~1.5 GB | Always loaded for both ingestion and query embedding |
| GPU 1 | Cross-encoder reranker (`ms-marco-MiniLM-L-12-v2`) | ~0.5 GB | Always loaded for query-time reranking |
| GPU 2 | Local LLM (if no Claude API) | ~14 GB (7B model) | Fallback: Mistral-7B via vLLM |
| GPU 3 | Reserved / idle | 0 GB | Spare capacity for batch operations or future use |

**Reason:**
- Embedding and reranking must never compete for the same GPU's VRAM. Separate
  GPU assignments eliminate memory contention and OOM crashes.
- PyTorch's default behavior is to use `cuda:0` for everything. Without explicit
  device assignments, loading BGE-Large + cross-encoder + a local LLM on the same
  GPU would exceed 24GB VRAM and crash.
- If Claude API is available for answer generation, GPUs 2–3 remain idle. This is
  fine for an 8-hour scope — over-provisioning is not a problem, under-provisioning is.

---

## Decision 12: SHA-256 Deduplication at Upload

**Date:** July 2026
**Status:** Active
**Decision:** Compute SHA-256 hash of every uploaded PDF. If the hash already
exists in the metadata store, skip re-processing and return the existing document
metadata.

**Reason:**
- Prevents duplicate embeddings from polluting the vector store. Duplicate chunks
  would artificially boost their retrieval scores and displace genuinely different
  relevant chunks.
- Prevents wasted GPU compute on re-embedding identical documents. For a 100-page
  PDF, this saves ~10 seconds of embedding time.
- SHA-256 is deterministic, collision-resistant, and has zero false positives
  for practical purposes.
- The implementation is 5 lines of code — near-zero engineering cost for significant
  correctness benefit.

---

## Decision 13: No Celery, No Redis — Direct Synchronous Execution

**Date:** July 2026
**Status:** Active
**Decision:** All PDF processing runs synchronously within the FastAPI request
lifecycle. No Celery task queue. No Redis broker. No background workers.

**Reason:**
- 50 PDFs × ~1 second/PDF (extraction + chunking) + ~30–60 seconds (batch embedding)
  = ~90 seconds worst case for full corpus ingestion. A loading spinner and progress
  indicator on the frontend is perfectly acceptable UX.
- Adding Celery + Redis would cost 1–2 hours of the 8-hour budget:
  - Redis installation and configuration
  - Celery worker setup and management
  - Task state tracking and result polling
  - Error handling for async task failures
  - Frontend polling/WebSocket for task completion
- This engineering cost produces zero accuracy improvement. It is the wrong investment
  for an accuracy-first system with a time constraint.

**Scale mitigation:** At 10k+ documents, synchronous processing is untenable.
Migration path: add Celery workers with Redis broker, batch embedding generation
across multiple GPU workers, and async upload with a status polling endpoint
(`GET /upload-status/{job_id}`).

---

## Decision 14: Sigmoid-Normalize Cross-Encoder Logits Before Thresholding

**Date:** July 2026
**Status:** Active
**Decision:** Apply `torch.sigmoid` to raw `CrossEncoder.predict()` scores before
sorting, slicing, or thresholding in `rerank()`.

**Reason:**
- `ms-marco-MiniLM-L-12-v2` returns raw, unbounded logits, not a [0,1] probability.
  Empirically verified: a clearly relevant pair scored ~7.4, clearly irrelevant
  pairs scored ~-11.2 to -11.3 — well outside [0,1].
- DESIGN.md Section 7's "score ≥ 0.3" threshold and `schemas.Citation.relevance_score`
  (`ge=0.0, le=1.0`) both assume a normalized score. Using raw logits directly would
  make the threshold meaningless and violate the Pydantic schema constraint.
- Sigmoid preserves rank order (monotonic), so it does not change which chunks are
  top-k — it only rescales scores into a valid, interpretable [0,1] range.

**Tradeoff:** Sigmoid-normalized scores are not true calibrated probabilities
(the model wasn't trained with a probabilistic loss), but they are monotonic and
bounded, which is sufficient for thresholding and citation display.

---

## Decision 15: Build Citations from `Chunk` Objects, Never Parsed from LLM Output

**Date:** July 2026
**Status:** Active
**Decision:** `build_citations()` constructs each `Citation` directly from the
`(Chunk, score)` pairs returned by the reranker — `chunk_text` is `chunk.text`,
copied verbatim. It never parses or extracts quoted text out of `generate_answer()`'s
LLM output.

**Reason:**
- Parsing quotes out of LLM-generated text risks the model paraphrasing mid-generation
  despite the system prompt's verbatim instruction (CLAUDE.md Section 5.3) — a prompt
  is a request, not a guarantee.
- Building citations from `Chunk` fields makes the verbatim guarantee structural
  (the text is never touched by the LLM) rather than dependent on the model reliably
  following instructions.

---

*Last updated: July 2026*
*Update this file whenever a new significant decision is made during the build.*
