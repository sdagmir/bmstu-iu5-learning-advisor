"""Админ-роутер LLM: журнал трейсов чата (`/admin/traces`)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import CurrentAdmin, DbSession, PageLimit, PageOffset
from app.exceptions import NotFoundError
from app.llm.schemas import TraceDetail, TraceSummary
from app.llm.service import get_trace, list_traces

logger = logging.getLogger(__name__)

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
    """Лента LLM-трейсов с фильтрами и пагинацией.

    Доступ к чужим диалогам — privileged. Каждый запрос фиксируется в audit
    log приложения с email админа и применёнными фильтрами.
    """
    logger.info(
        "audit: list_traces by admin=%s filter=user_id=%s date_from=%s date_to=%s",
        admin.email,
        user_id,
        date_from,
        date_to,
    )
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
    """Полная запись трейса по id.

    Audit log: каждое чтение чужого диалога фиксируется в логи приложения
    с email админа, который смотрел, и user_id владельца диалога.
    """
    trace = await get_trace(trace_id, db)
    if trace is None:
        raise NotFoundError("Trace", str(trace_id))
    logger.info(
        "audit: get_trace by admin=%s trace_id=%s owner_user_id=%s",
        admin.email,
        trace_id,
        trace.user_id,
    )
    return trace
