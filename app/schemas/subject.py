from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    grade: int = Field(ge=9, le=11)

    model_config = ConfigDict(extra="forbid")


class SubjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    description: str | None = None
    grade: int | None = Field(default=None, ge=9, le=11)

    model_config = ConfigDict(extra="forbid")


class SubjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    grade: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
