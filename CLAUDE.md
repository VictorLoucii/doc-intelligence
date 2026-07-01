# CLAUDE.md

Behavioral guidelines for Claude Code during the N-ERGY Document Intelligence System build. These rules reduce common LLM coding mistakes and enforce the accuracy-first architecture defined in DESIGN.md.

**Context:** 8-hour timed take-home assignment. Every wasted token and every unnecessary abstraction costs us time we cannot recover.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- **8-HOUR RULE:** If a feature would take more than 30 minutes and isn't in the sprint plan (DESIGN.md Section 10), skip it. We do not have time for scope creep.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the current sprint task.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add PDF ingestion" → "Write eval test for PDF ingestion, then make it pass"
- "Fix the retrieval bug" → "Write a test that reproduces it, then make it pass"
- "Add reranker" → "Ensure eval.py retrieval score stays at 100% after integration"
- "Build the frontend" → "Upload a PDF via browser, ask a question, see answer with citations"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 5. N-ERGY Project-Specific Rules

**These rules are non-negotiable. They exist because of specific engineering decisions documented in DESIGN.md and DECISIONS.md.**

### 5.1 Eval-Driven Development (EDD) is Mandatory

- **BEFORE declaring any task complete**, run: `python eval.py`
- If the Logic Score drops below 100%, your change is **BROKEN**. Fix it before moving on.
- The eval script tests:
  - PDF ingestion (empty PDF returns error, valid PDF returns metadata)
  - Chunking correctness (chunk_size ~1000 tokens, overlap ~200, no empty chunks)
  - Embedding generation (correct dimensionality, GPU allocation)
  - Retrieval accuracy (known relevant chunks appear in top-50)
  - Reranking improvement (cross-encoder top-5 is strictly better than bi-encoder top-5)
  - Citation format (verbatim text, document name, page number, chunk index present)
  - API endpoint responses (correct HTTP status codes, Pydantic schema compliance)
- **NEVER** skip eval. **NEVER** say "I'll fix the tests later." Tests are the ground truth.
- If `eval.py` doesn't have a test for what you just built, **ADD ONE** before declaring done.

### 5.2 Pydantic Schemas Are the Data Contract

- ALL data structures use Pydantic v2 models defined in `backend/models/schemas.py`.
- **NEVER** pass raw `dict` objects between functions. Always validate through Pydantic.
- **NEVER** use `dict` as a type hint when a Pydantic model exists for that data structure.
- `extra = "forbid"` on ALL schemas. Unknown fields are bugs, not features.
- If you need a new data structure, define it as a Pydantic model **FIRST**, then use it.
- When modifying shared schemas, use optional fields with default values to avoid breaking existing callers.

### 5.3 The Anti-Summary Mandate is Sacred

- The LLM answer generation prompt **MUST** include explicit anti-summary instructions. See DESIGN.md Section 3.3 for the exact system prompt.
- Citations **MUST** be verbatim text from the retrieved chunks. No paraphrasing. No rewording. No "based on the document" hedging.
- Every citation **MUST** include all four fields: `document_name`, `page_number`, `chunk_index`, `chunk_text`.
- If you modify the answer generation prompt for any reason, verify that citations remain verbatim by running `eval.py`.
- **NEVER** add a "summarize the following" or "briefly describe" instruction to any LLM prompt in this system. The word "summarize" is banned from all prompts.

### 5.4 The Two-Stage Retrieval Pipeline is Non-Negotiable

- **Stage 1** (Bi-Encoder): Retrieves top-50 candidates from FAISS. This is the recall stage.
- **Stage 2** (Cross-Encoder): Reranks top-50 to top-5. This is the precision stage.
- **NEVER** remove the reranker to "simplify" or "speed up" the pipeline. The reranker is the primary accuracy mechanism. Without it, we're just a basic RAG demo.
- **NEVER** reduce top-50 candidates below 30. Recall degrades severely at lower values. The cross-encoder needs a wide candidate pool to find the best matches.
- If the reranker model fails to load on GPU, **FALL BACK** to CPU execution. Do **NOT** skip reranking entirely. Slow reranking is infinitely better than no reranking.

### 5.5 GPU Allocation Must Be Explicit

```
GPU 0: Embedding model (BAAI/bge-large-en-v1.5)       — ~1.5 GB VRAM
GPU 1: Cross-encoder reranker (ms-marco-MiniLM-L-12-v2) — ~0.5 GB VRAM
GPU 2: Local LLM (if no Claude API available)          — ~14 GB VRAM
GPU 3: Reserved / idle
```

- **ALWAYS** set `torch.device('cuda:0')`, `torch.device('cuda:1')`, etc. explicitly when loading models.
- **NEVER** let PyTorch auto-select the GPU with default `cuda`. Two models fighting for GPU 0 = OOM crash that wastes 30+ minutes of debugging time.
- In `backend/config.py`, define `EMBEDDING_GPU_ID`, `RERANKER_GPU_ID`, `LLM_GPU_ID` as environment variables.

### 5.6 No Secrets in Code or Config Files

- Never hardcode an API key, secret, password, or token anywhere in the codebase.
- Use environment variables read via `backend/config.py` (pydantic-settings).
- `.env` is for local development only and **MUST** be in `.gitignore`.
- `.env.example` shows variable names with placeholder values only.
- If you need a secret in a test, use a mock value or `unittest.mock.patch`.

### 5.7 PDF Processing Must Be Resilient

- Every PDF processing function **MUST** handle:
  - Empty PDFs (0 extractable text pages) → Return error, do not index.
  - Corrupted PDFs (`fitz.FileDataError`) → Catch exception, log error, skip file, continue processing remaining PDFs.
  - Password-protected PDFs → Detect, return error, skip file.
- **NEVER** let a single bad PDF crash the entire ingestion pipeline. If 5 PDFs are uploaded and 1 is corrupted, the other 4 must still be processed successfully.
- **ALWAYS** wrap `fitz.open()` and `page.get_text()` in try/except blocks. Log the exception with `logging.error()`. Return a clear error message to the frontend.

### 5.8 Token Optimization — The /clear Mandate

During the build, follow these rules to minimize Claude Code API token burn:

- **After completing each sprint task**, type `/clear` in Claude Code CLI. This resets the context window and prevents cumulative token accumulation across unrelated tasks.
- **NEVER** ask Claude Code to "explore the codebase," "read DESIGN.md and explain it," or "look through all the files." That is exploratory work — use Antigravity for exploration (unlimited context, $0 cost). Reserve Claude Code strictly for writing code.
- If a section of DESIGN.md or DECISIONS.md is needed for context, copy **ONLY** the relevant section (10–30 lines) into the prompt — not the entire 300-line file.
- Use `/goal` mode for each sprint task: `/goal Implement sprint S2 (embedding service + vector store) per DESIGN.md Section 4 Layer 1. Ensure eval.py passes.`

### 5.9 The Vector Store is Append-Only During Queries

- During query processing (the `/query` endpoint), **NEVER** modify the FAISS vector store.
- Embeddings are added to the index **ONLY** during PDF ingestion (the `/upload` endpoint).
- Embeddings are removed from the index **ONLY** during explicit document deletion (the `DELETE /documents/{id}` endpoint).
- If a query somehow triggers a vector store write, that is a bug. Fix it.

### 5.10 Frontend Must Be Functional, Not Beautiful

- Do **NOT** spend more than 60 minutes on the frontend. The sprint plan allocates 1 hour.
- The assignment explicitly says: "Simple working UI — function over form" and "We are not evaluating design."
- The minimum viable frontend has exactly three features:
  1. File upload (select PDFs → upload to `/upload`)
  2. Question input (text box → send to `/query`)
  3. Answer display (answer text + citation cards with source, page, chunk text)
- A fourth feature (document list) is nice-to-have.
- CSS animations, color gradients, responsive breakpoints, dark mode = **zero evaluation marks**. Skip them entirely.
- If the frontend is over budget at 60 minutes, cut CSS polish. A working ugly UI scores 100%; a beautiful broken UI scores 0%.

---

## 6. Core Logic & Behaviour Rules

- Do not change application logic unless explicitly asked.
- **Backward Compatibility:** When modifying shared Pydantic schemas or utility functions, use optional fields with default values to avoid breaking existing callers.
- Do not guess or assume missing information. Only reason using files and context that are explicitly provided or requested.
- Follow the existing project structure and coding style. Do not refactor unrelated code.
- If an issue cannot be confirmed from the provided files, state that clearly.
- Use Python `logging` (stdlib) for all logging. Never use bare `print()` statements in production code. Configure log level via `backend/config.py`.
- Do not install or add new dependencies without checking `requirements.txt` first. If the needed functionality exists in a listed dependency, use it. If a new dependency is truly needed, add it to `requirements.txt` with a pinned version.
- Always `grep` the codebase for all references to a function, Pydantic field, or variable before renaming or deleting it. Broken imports waste 15+ minutes of debugging.
- Never hardcode API keys, passwords, credentials, or secrets. Always read them from environment variables via `backend/config.py`.
- Ensure proper error handling: Never leave `except` blocks empty. Always log the exception via `logging.error(f"...", exc_info=True)` and return a descriptive HTTP error response.
- Keep modules focused: aim for under **300 lines per file**. If a file grows beyond this, split into sub-modules before adding more logic.
- **Non-Destructive Editing:** Preserve all existing comments, docstrings, and unrelated functions. Do not delete logic unless explicitly instructed.
- **Dry-Run Before Declaring Done:** Run `python eval.py` before declaring a task complete. Fix all failures before finishing. This is Rule 5.1 — it is repeated here for emphasis because it is the most commonly violated rule.
- **Git Hygiene — Commit After Every Green Eval:** The commit trigger is `eval.py` passing at 100%. Once it passes, immediately stage, review, and commit before moving to the next task. Never run `git add .` — only stage files that directly implement the current sprint task. Always review `git diff --staged` before committing. Commit messages use format: `"S[X] T[Y]: [Feature Name]"` (e.g., `"S2 T1: add embedding service + FAISS vector store"`). The repository must be in a clean, committed state before starting the next sprint task.

---

**These guidelines are working if:**
- `eval.py` passes at 100% after every sprint.
- Diffs contain only the files and lines relevant to the current task.
- No rewrites due to overcomplication.
- Clarifying questions come before implementation rather than after mistakes.
- The 8-hour clock ends with a working, deployed, accuracy-first Document Intelligence System.
