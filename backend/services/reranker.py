"""Cross-encoder reranker (ms-marco-MiniLM-L-12-v2, GPU 1). Logic added in S3."""

import logging

import torch
from sentence_transformers import CrossEncoder

from backend.config import settings
from backend.models.schemas import Chunk

logger = logging.getLogger(__name__)

RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-12-v2"

_device = torch.device(f"cuda:{settings.RERANKER_GPU_ID}")
try:
    _model = CrossEncoder(RERANKER_MODEL_NAME, device=str(_device))
except Exception:
    logger.error("Reranker failed to load on %s, falling back to CPU", _device, exc_info=True)
    _device = torch.device("cpu")
    _model = CrossEncoder(RERANKER_MODEL_NAME, device=str(_device))


def rerank(query: str, candidates: list[tuple[Chunk, float]], top_k: int = 5) -> list[tuple[Chunk, float]]:
    """Score each (query, chunk.text) pair with the cross-encoder; return top_k (Chunk, score) descending."""
    if not candidates:
        return []

    pairs = [(query, chunk.text) for chunk, _ in candidates]
    raw_scores = _model.predict(pairs)
    scores = torch.sigmoid(torch.tensor(raw_scores))

    reranked = sorted(zip((chunk for chunk, _ in candidates), scores), key=lambda item: item[1], reverse=True)
    top = [(chunk, float(score)) for chunk, score in reranked[:top_k]]
    return [(chunk, score) for chunk, score in top if score >= settings.RELEVANCE_THRESHOLD]
