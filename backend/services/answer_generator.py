"""LLM answer generation + verbatim citation builder. Logic added in S4."""

import logging

import anthropic

from backend.config import settings
from backend.models.schemas import Chunk, Citation

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

_MAX_TOKENS = 1024

_NO_CONTEXT_ANSWER = "The uploaded documents do not contain sufficient information to answer this question."

SYSTEM_PROMPT = """You are a document intelligence assistant. Answer questions using ONLY the provided
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
   "The documents suggest...". Go directly to the evidence."""


def generate_answer(query: str, chunks: list[tuple[Chunk, float]]) -> str:
    """Generate an answer to `query` grounded in `chunks`, or the no-context fallback if empty."""
    if not chunks:
        return _NO_CONTEXT_ANSWER

    context = "\n\n".join(
        f"[Source: {chunk.document_name}, Page {chunk.page_number}, Chunk {chunk.chunk_index}]\n{chunk.text}"
        for chunk, _ in chunks
    )
    user_message = f"{context}\n\nQuestion: {query}"

    response = _client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def build_citations(chunks: list[tuple[Chunk, float]]) -> list[Citation]:
    """Build verbatim Citations directly from `Chunk` objects — never from `generate_answer()`'s output."""
    return [
        Citation(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            chunk_text=chunk.text,
            relevance_score=score,
        )
        for chunk, score in chunks
    ]
