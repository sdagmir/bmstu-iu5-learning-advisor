"""Роутер RAG — загрузка/удаление документов, поиск, статистика."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser, DbSession
from app.rag.schemas import (
    DocumentChunk,
    DocumentUpload,
    DocumentUploadResult,
    RAGStats,
    SearchRequest,
)
from app.rag.service import rag_service

router = APIRouter()


@router.post("/documents", response_model=DocumentUploadResult, status_code=201)
async def upload_document(
    body: DocumentUpload, admin: CurrentAdmin, db: DbSession
) -> DocumentUploadResult:
    """Загрузка документа в базу знаний (админ)."""
    chunks = await rag_service.index_document(body.source, body.text)
    return DocumentUploadResult(source=body.source, chunks_count=chunks)


@router.delete("/documents/{source:path}", status_code=204)
async def delete_document(source: str, admin: CurrentAdmin, db: DbSession) -> None:
    """Удаление документа из базы знаний (админ). source может содержать /."""
    rag_service.delete_document(source)


@router.post("/search", response_model=list[DocumentChunk])
async def search(body: SearchRequest, user: CurrentUser, db: DbSession) -> list[DocumentChunk]:
    """Семантический поиск по базе знаний (студент/админ)."""
    return await rag_service.search(body.query, top_k=body.top_k)


@router.get("/stats", response_model=RAGStats)
async def stats(admin: CurrentAdmin, db: DbSession) -> RAGStats:
    """Статистика RAG-базы (админ)."""
    return RAGStats(total_chunks=rag_service.document_count())
