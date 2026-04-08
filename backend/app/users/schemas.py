from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import CareerGoal, TechparkStatus, UserRole, WorkloadPref


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    semester: int | None
    career_goal: CareerGoal | None
    technopark_status: TechparkStatus | None
    workload_pref: WorkloadPref | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    semester: int | None = Field(default=None, ge=1, le=8)
    career_goal: CareerGoal | None = None
    technopark_status: TechparkStatus | None = None
    workload_pref: WorkloadPref | None = None
