from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str
    description: str | None = None
    grade: int = Field(ge=9, le=11)


class SubjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    grade: int | None = Field(default=None, ge=9, le=11)


class SubjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    grade: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
