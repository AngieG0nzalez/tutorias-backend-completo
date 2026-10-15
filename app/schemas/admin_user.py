
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AdminUserStatusUpdate(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")


class AdminUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    grade: int | None = None
    tutor_id: int | None = None
    tutor_is_active: bool | None = None


class AdminUserStatusResponse(BaseModel):
    id: int
    is_active: bool
    message: str
