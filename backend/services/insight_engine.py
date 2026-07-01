"""Bonus: cross-document insight suggestions. Logic added in S7."""

import json
import logging

import anthropic
from pydantic import ValidationError

from backend.config import settings
from backend.models.schemas import Chunk, Citation, InsightSuggestion

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

_MAX_TOKENS = 2048

_INSIGHT_SYSTEM_PROMPT = """You are a document intelligence assistant identifying cross-document
connections. You will be given numbered chunks pulled from multiple documents. Identify themes,
contradictions, or connections that span at least two different documents. Follow these rules:

1. GROUNDING: Every insight must be directly supported by the text of the chunks provided.
   Do NOT invent facts, numbers, or relationships that are not present in the chunks.
2. CROSS-DOCUMENT ONLY: Each insight's supporting_chunk_ids must include chunks from at least
   two distinct documents.
3. OUTPUT FORMAT: Respond with ONLY a JSON array, no other text before or after it. Each element
   must have exactly these keys: "insight_text" (string), "suggested_next_question" (string), and
   "supporting_chunk_ids" (array of the integer chunk numbers given below)."""


def _parse_json_array(raw_text: str) -> list:
    """Strip an optional markdown code fence, then parse a JSON array."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[len("json"):]
        text = text.strip()
    return json.loads(text)


def generate_insights(chunks: list[Chunk], top_n: int = 3) -> list[InsightSuggestion]:
    """Synthesize cross-document insights from `chunks`, or [] if fewer than 2 documents are represented."""
    distinct_document_ids = {chunk.document_id for chunk in chunks}
    if len(distinct_document_ids) < 2:
        logging.info(
            "generate_insights: only %d distinct document(s) present, need >=2 — returning []",
            len(distinct_document_ids),
        )
        return []

    numbered_chunks = "\n\n".join(
        f"[{i}] Document: {chunk.document_name}, Page {chunk.page_number}, Chunk {chunk.chunk_index}\n{chunk.text}"
        for i, chunk in enumerate(chunks)
    )
    user_message = (
        f"Here are {len(chunks)} chunks from {len(distinct_document_ids)} documents:\n\n"
        f"{numbered_chunks}\n\nIdentify up to {top_n} cross-document insights."
    )

    response = _client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_INSIGHT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    try:
        raw_insights = _parse_json_array(response.content[0].text)
    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"generate_insights: failed to parse LLM output as JSON: {e}", exc_info=True)
        return []

    insights: list[InsightSuggestion] = []
    for raw in raw_insights:
        try:
            chunk_ids = raw["supporting_chunk_ids"]
            supporting_chunks = [chunks[i] for i in chunk_ids if 0 <= i < len(chunks)]
        except (KeyError, TypeError) as e:
            logging.error(f"generate_insights: malformed insight entry, skipping: {raw} ({e})")
            continue

        if len({c.document_id for c in supporting_chunks}) < 2:
            logging.info(f"generate_insights: skipping insight without >=2-document support: {raw}")
            continue

        # Citation.chunk_text is built directly from Chunk.text — never from LLM output (Decision 15).
        citations = [
            Citation(
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.text,
                relevance_score=1.0,
            )
            for chunk in supporting_chunks
        ]

        try:
            insight = InsightSuggestion(
                insight_text=raw["insight_text"],
                supporting_chunks=citations,
                suggested_next_question=raw["suggested_next_question"],
            )
        except (KeyError, ValidationError) as e:
            logging.error(f"generate_insights: failed to build InsightSuggestion: {e}", exc_info=True)
            continue

        insights.append(insight)

    return insights[:top_n]
