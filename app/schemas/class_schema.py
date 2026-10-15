from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    tutor_id: int
    subject_id: int
    title: str
    description: str | None = None
    date_time: datetime
    duration_minutes: int = Field(gt=0)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: Literal[
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    ] = "scheduled"


class ClassUpdate(BaseModel):
    tutor_id: int | None = None
    subject_id: int | None = None
    title: str | None = None
    description: str | None = None
    date_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, ge=0)
    status: Literal[
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    ] | None = None


class ClassResponse(BaseModel):
    id: int
    tutor_id: int
    subject_id: int
    title: str
    description: str | None
    date_time: datetime
    duration_minutes: int
    price: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
