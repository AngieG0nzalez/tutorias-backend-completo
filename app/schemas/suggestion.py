import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["content", "usability", "bug", "other"]
SuggestionStatus = Literal["new", "in_review", "resolved", "rejected"]

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _no_control(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("El texto contiene caracteres no permitidos")
    return value


class SuggestionCreate(BaseModel):
    category: Category
    subject: str = Field(min_length=3, max_length=150)
    message: str = Field(min_length=10, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("subject")
    @classmethod
    def clean_subject(cls, value: str) -> str:
        value = " ".join(_no_control(value).split())
        if len(value) < 3:
            raise ValueError("El asunto debe tener al menos 3 caracteres")
        return value

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        value = _no_control(value).strip()
        if len(value) < 10:
            raise ValueError("El mensaje debe tener al menos 10 caracteres")
        return value


class SuggestionAdminUpdate(BaseModel):
    status: SuggestionStatus | None = None
    admin_note: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("status", mode="before")
    @classmethod
    def status_not_null(cls, value):
        if value is None:
            raise ValueError("El estado no puede ser nulo")
        return value

    @field_validator("admin_note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = _no_control(value).strip()
        return value or None


class SuggestionResponse(BaseModel):
    id: int
    category: str
    subject: str
    message: str
    status: str
    admin_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminSuggestionResponse(SuggestionResponse):
    author_name: str
    author_role: str


class SuggestionList(BaseModel):
    items: list[SuggestionResponse]
    total: int
    limit: int
    offset: int


class AdminSuggestionList(BaseModel):
    items: list[AdminSuggestionResponse]
    total: int
    limit: int
    offset: int
