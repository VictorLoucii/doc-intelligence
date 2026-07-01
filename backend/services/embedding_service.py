"""Bi-encoder embedding service (BAAI/bge-large-en-v1.5, GPU 0). Logic added in S2."""

import logging

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.models.schemas import Chunk

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIM = 1024
_EMBEDDING_BATCH_SIZE = 32

_device = torch.device(f"cuda:{settings.EMBEDDING_GPU_ID}")
_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=str(_device))


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string into a 1024-dim, L2-normalized float32 vector."""
    embedding = _model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embedding.astype(np.float32)


def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """Batch-embed chunk text into an (N, 1024) L2-normalized float32 matrix."""
    texts = [chunk.text for chunk in chunks]
    embeddings = _model.encode(
        texts,
        batch_size=_EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.astype(np.float32)
