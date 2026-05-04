"""Админ-роутер LLM: журнал трейсов чата (`/admin/traces`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import CurrentAdmin, DbSession, PageLimit, PageOffset
from app.exceptions import NotFoundError
from app.llm.schemas import TraceDetail, TraceSummary
from app.llm.service import get_trace, list_traces

router = APIRouter()


@router.get("/traces", response_model=list[TraceSummary])
async def list_llm_traces(
    admin: CurrentAdmin,
    db: DbSession,
    user_id: Annotated[uuid.UUID | None, Query(description="Фильтр по пользователю")] = None,
    date_from: Annotated[
        datetime | None, Query(description="С какого момента (включительно)")
    ] = None,
    date_to: Annotated[
        datetime | None, Query(description="По какой момент (включительно)")
    ] = None,
    offset: PageOffset = 0,
    limit: PageLimit = 50,
) -> list[TraceSummary]:
    """Лента LLM-трейсов с фильтрами и пагинацией."""
    return await list_traces(
        db,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )


@router.get("/traces/{trace_id}", response_model=TraceDetail)
async def get_llm_trace(trace_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> TraceDetail:
    """Полная запись трейса по id."""
    trace = await get_trace(trace_id, db)
    if trace is None:
        raise NotFoundError("Trace", str(trace_id))
    return trace
