"""POST /query, POST /insights. Logic added in S5."""

import logging
import time

from fastapi import APIRouter, HTTPException

from backend.models.schemas import QueryRequest, QueryResponse
from backend.services import answer_generator, embedding_service, reranker, vector_store

logger = logging.getLogger(__name__)

router = APIRouter()

_RETRIEVAL_TOP_K = 50


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    if vector_store.is_empty():
        raise HTTPException(status_code=400, detail="Please upload at least one document before asking questions.")

    start = time.perf_counter()

    query_embedding = embedding_service.embed_query(request.question)
    candidates = vector_store.search(query_embedding, top_k=_RETRIEVAL_TOP_K)
    reranked = reranker.rerank(request.question, candidates, top_k=request.top_k)

    answer = answer_generator.generate_answer(request.question, reranked)
    citations = answer_generator.build_citations(reranked)

    processing_time_ms = (time.perf_counter() - start) * 1000

    return QueryResponse(
        answer=answer,
        citations=citations,
        query=request.question,
        documents_searched=vector_store.document_count(),
        chunks_evaluated=len(candidates),
        processing_time_ms=processing_time_ms,
    )
