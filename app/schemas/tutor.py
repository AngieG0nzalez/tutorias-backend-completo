from datetime import datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TutorCreate(BaseModel):
    user_id: int
    bio: str | None = None
    specialty: str | None = Field(default=None, max_length=100)
    experience_years: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")


class TutorUpdate(BaseModel):
    bio: str | None = None
    specialty: str | None = Field(default=None, max_length=100)
    experience_years: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class TutorResponse(BaseModel):
    id: int
    user_id: int
    bio: str | None
    specialty: str | None
    experience_years: int
    rating: Decimal | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TutorDirectoryItem(BaseModel):
    user_id: int
    name: str
    specialty: str | None


class AdminTutorSubjectCreate(BaseModel):
    subject_id: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class AdminTutorSubjectResponse(BaseModel):
    subject_id: int
    name: str
    grade: int
    assigned_at: datetime | None = None
