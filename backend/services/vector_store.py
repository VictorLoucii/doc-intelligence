"""FAISS vector store: add, search, delete. Logic added in S2.

In-memory only (Decision 4) — IndexFlatIP over L2-normalized embeddings from
embedding_service.py, wrapped in IndexIDMap2 for stable row IDs across deletes
(IndexIDMap2 supports reconstruct(), needed to rebuild the index on delete).
Append-only during queries (CLAUDE.md Section 5.9): add_chunks/delete_document
must never be called from the query path.
"""

import logging

import faiss
import numpy as np

from backend.models.schemas import Chunk

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1024

_index = faiss.IndexIDMap2(faiss.IndexFlatIP(EMBEDDING_DIM))
_chunks_by_id: dict[int, Chunk] = {}
_next_id = 0


def add_chunks(chunks: list[Chunk], embeddings: np.ndarray) -> None:
    """Append chunk vectors + metadata to the index. Never call from the query path."""
    global _next_id

    if not chunks:
        return

    ids = np.arange(_next_id, _next_id + len(chunks), dtype=np.int64)
    _index.add_with_ids(embeddings.astype(np.float32), ids)
    for row_id, chunk in zip(ids, chunks):
        _chunks_by_id[int(row_id)] = chunk
    _next_id += len(chunks)


def search(query_embedding: np.ndarray, top_k: int = 50) -> list[tuple[Chunk, float]]:
    """Return up to top_k (Chunk, score) pairs, descending by score. Empty index -> []."""
    if _index.ntotal == 0:
        return []

    k = min(top_k, _index.ntotal)
    query = query_embedding.astype(np.float32).reshape(1, -1)
    scores, ids = _index.search(query, k)

    results = []
    for score, row_id in zip(scores[0], ids[0]):
        if row_id == -1:
            continue
        results.append((_chunks_by_id[int(row_id)], float(score)))
    return results


def is_empty() -> bool:
    """True if the index has no vectors."""
    return _index.ntotal == 0


def all_chunks() -> list[Chunk]:
    """Return every chunk currently indexed, across all documents. Read-only (Decision 17)."""
    return list(_chunks_by_id.values())


def document_count() -> int:
    """Count of distinct documents represented in the index."""
    return len({chunk.document_id for chunk in _chunks_by_id.values()})


def delete_document(document_id: str) -> None:
    """Remove all chunks for a document by rebuilding the index from the rest."""
    global _index, _next_id

    remaining = [(chunk, row_id) for row_id, chunk in _chunks_by_id.items() if chunk.document_id != document_id]

    new_index = faiss.IndexIDMap2(faiss.IndexFlatIP(EMBEDDING_DIM))
    new_chunks_by_id: dict[int, Chunk] = {}

    if remaining:
        remaining_ids = np.array([row_id for _, row_id in remaining], dtype=np.int64)
        vectors = np.vstack([_index.reconstruct(int(row_id)) for row_id in remaining_ids])
        new_index.add_with_ids(vectors, remaining_ids)
        new_chunks_by_id = {row_id: chunk for chunk, row_id in remaining}

    _index = new_index
    _chunks_by_id.clear()
    _chunks_by_id.update(new_chunks_by_id)
