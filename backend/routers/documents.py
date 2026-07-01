"""POST /upload, GET /documents, DELETE /documents/{id}. Logic added in S5."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import DocumentMetadata, ProcessPDFResult
from backend.services import embedding_service, pdf_processor, vector_store

logger = logging.getLogger(__name__)

router = APIRouter()

_documents: dict[str, DocumentMetadata] = {}


@router.post("/upload", response_model=list[ProcessPDFResult])
async def upload_documents(files: list[UploadFile] = File(...)) -> list[ProcessPDFResult]:
    """Ingest one or more PDFs. One bad file must not fail the rest (CLAUDE.md 5.7)."""
    results: list[ProcessPDFResult] = []

    for file in files:
        file_bytes = await file.read()
        existing_hashes = {d.sha256: d for d in _documents.values()}
        result = pdf_processor.process_pdf(file_bytes, file.filename, existing_hashes)

        if result.success and not result.is_duplicate:
            if result.chunks:
                embeddings = embedding_service.embed_chunks(result.chunks)
                vector_store.add_chunks(result.chunks, embeddings)
            _documents[result.metadata.id] = result.metadata

        results.append(result)

    return results


@router.get("/documents", response_model=list[DocumentMetadata])
async def list_documents() -> list[DocumentMetadata]:
    return list(_documents.values())


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: str) -> None:
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    del _documents[document_id]
    vector_store.delete_document(document_id)
