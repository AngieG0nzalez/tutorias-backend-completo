from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    grade: int | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
