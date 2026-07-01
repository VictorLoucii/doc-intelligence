"""
Pydantic v2 data models for the N-ERGY Document Intelligence System.
Single source of truth for all data structures passed between layers.
See DESIGN.md Section 5.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="UUID for the document")
    filename: str
    sha256: str = Field(..., description="Content hash for deduplication")
    upload_time: datetime
    page_count: int
    chunk_count: int
    status: ProcessingStatus
    file_size_bytes: int


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="UUID for the chunk")
    document_id: str
    document_name: str
    text: str
    page_number: int
    chunk_index: int
    token_count: int


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_name: str
    page_number: int
    chunk_index: int
    chunk_text: str = Field(..., description="VERBATIM text from source — never summarized")
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    citations: list[Citation]
    query: str
    documents_searched: int
    chunks_evaluated: int
    processing_time_ms: float


class InsightSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insight_text: str
    supporting_chunks: list[Citation]
    suggested_next_question: str
