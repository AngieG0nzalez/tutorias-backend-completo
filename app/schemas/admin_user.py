
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    specialty: str | None = None
    bio: str | None = None
    experience_years: int | None = None
    warning: str | None = None


class AdminUserStatusResponse(BaseModel):
    id: int
    is_active: bool
    message: str



class AdminUserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    grade: int | None = Field(default=None, ge=9, le=11)
    specialty: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    tutor_is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("El nombre no puede estar vacío")
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return value

    @field_validator("grade", "experience_years", "tutor_is_active", mode="before")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("El valor no puede ser nulo")
        return value

    @model_validator(mode="after")
    def validate_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("Debes indicar al menos un campo para actualizar")
        return self
