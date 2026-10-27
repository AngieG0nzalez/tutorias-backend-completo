from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.exercise import ExerciseOptionCreate


Difficulty = Literal["easy", "medium", "hard"]


def _clean(value: str) -> str:
    return " ".join(value.split())


def _validate_four_options(options: list[ExerciseOptionCreate]) -> None:
    if sum(1 for o in options if o.is_correct) != 1:
        raise ValueError("Debe haber exactamente una opción correcta")
    texts = [o.option_text.casefold() for o in options]
    if len(set(texts)) != len(texts):
        raise ValueError("Las opciones no pueden repetirse")


class ContentExerciseCreate(BaseModel):
    topic_id: int = Field(gt=0)
    statement: str = Field(min_length=5, max_length=1000)
    difficulty: Difficulty = "medium"
    explanation: str | None = Field(default=None, max_length=1000)
    options: list[ExerciseOptionCreate] = Field(min_length=4, max_length=4)

    model_config = ConfigDict(extra="forbid")

    @field_validator("statement")
    @classmethod
    def clean_statement(cls, value: str) -> str:
        value = _clean(value)
        if len(value) < 5:
            raise ValueError("El enunciado debe tener al menos 5 caracteres")
        return value

    @model_validator(mode="after")
    def validate_options(self):
        _validate_four_options(self.options)
        return self


class ContentExerciseUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=5, max_length=1000)
    difficulty: Difficulty | None = None
    explanation: str | None = Field(default=None, max_length=1000)
    options: list[ExerciseOptionCreate] | None = Field(
        default=None, min_length=4, max_length=4
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("statement", "difficulty", "options", mode="before")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("El valor no puede ser nulo")
        return value

    @field_validator("statement")
    @classmethod
    def clean_statement(cls, value: str) -> str:
        value = _clean(value)
        if len(value) < 5:
            raise ValueError("El enunciado debe tener al menos 5 caracteres")
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Debes indicar al menos un campo para actualizar")
        if self.options is not None:
            _validate_four_options(self.options)
        return self


class ContentExerciseStatus(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")


class ContentOptionResponse(BaseModel):
    id: int
    option_text: str
    order_number: int
    is_correct: bool


class ContentExerciseResponse(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    subject_id: int
    subject_name: str
    grade: int
    statement: str
    difficulty: str
    explanation: str | None
    is_ai_generated: bool
    is_active: bool
    attempts_count: int
    created_at: datetime | None = None
    options: list[ContentOptionResponse]
    warning: str | None = None


class ContentExerciseList(BaseModel):
    items: list[ContentExerciseResponse]
    total: int
    limit: int
    offset: int


class ContentTopicCatalog(BaseModel):
    id: int
    name: str
    order_number: int
    active_exercises: int
    inactive_exercises: int


class ContentSubjectCatalog(BaseModel):
    id: int
    name: str
    grade: int
    topics: list[ContentTopicCatalog]
