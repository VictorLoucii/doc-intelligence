# Sprint 1 — Task 2: Chunking

**Scope:** `backend/services/pdf_processor.py` — chunking stage only. Consumes Task 1's output directly.

**Function signature:**
```python
def chunk_pages(pages: list[PageText], document_id: str, document_name: str) -> list[Chunk]
```
`pages` is the `PDFExtractionResult.pages` list from Task 1 (already page-attributed, non-empty). `document_id`/`document_name` are supplied by the caller (Task 3) — this function has no knowledge of `DocumentMetadata`.

**Exact output — populate every `Chunk` field (backend/models/schemas.py):**
- `id`: new UUID4 string per chunk
- `document_id`, `document_name`: passed through unchanged
- `text`: the chunk's text (never empty/whitespace-only — drop such chunks)
- `page_number`: the page the chunk's text originated from (see below)
- `chunk_index`: 0-indexed, sequential across the whole document
- `token_count`: actual token count of `text`

**Chunking logic (DESIGN.md §6):**
- Use `langchain_text_splitters.RecursiveCharacterTextSplitter` with `chunk_size=1000`, `chunk_overlap=200`, separators `["\n\n", "\n", ". ", " "]`.
- Length function must count **tokens, not characters** — use `transformers.AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")` (already pinned in requirements.txt) as the length function, matching the embedding model chunks will feed in S2.
- Concatenate page texts, but track each chunk's originating page: if a chunk spans a page boundary, attribute it to the page where the chunk **starts**.
- No empty chunks (Rule 5.1 eval check).

**Out of scope:** `DocumentMetadata`, dedup, orchestration wiring, embedding — Task 3.
