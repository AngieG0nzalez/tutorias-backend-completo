from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ExerciseOptionResponse(BaseModel):

    id: int

    option_text: str

    order_number: int


    model_config = ConfigDict(
        from_attributes=True,
    )


class ExerciseResponse(BaseModel):

    id: int

    topic_id: int

    statement: str

    difficulty: str

    is_ai_generated: bool

    options: list[ExerciseOptionResponse]


    model_config = ConfigDict(
        from_attributes=True,
    )


class TutorExerciseOptionResponse(ExerciseOptionResponse):

    is_correct: bool


class TutorExerciseResponse(BaseModel):

    id: int

    topic_id: int

    statement: str

    difficulty: str

    explanation: str | None

    is_ai_generated: bool

    options: list[TutorExerciseOptionResponse]


    model_config = ConfigDict(
        from_attributes=True,
    )


class ExerciseOptionCreate(BaseModel):

    option_text: str = Field(min_length=1, max_length=300)

    is_correct: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("option_text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("La opción no puede estar vacía")
        return value


class ExerciseCreate(BaseModel):

    statement: str = Field(min_length=5, max_length=1000)

    difficulty: Literal["easy", "medium", "hard"] = "medium"

    explanation: str | None = Field(default=None, max_length=1000)

    options: list[ExerciseOptionCreate] = Field(min_length=4, max_length=4)

    model_config = ConfigDict(extra="forbid")

    @field_validator("statement")
    @classmethod
    def clean_statement(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 5:
            raise ValueError("El enunciado debe tener al menos 5 caracteres")
        return value

    @model_validator(mode="after")
    def validate_options(self):
        if sum(1 for o in self.options if o.is_correct) != 1:
            raise ValueError("Debe haber exactamente una opción correcta")
        texts = [o.option_text.casefold() for o in self.options]
        if len(set(texts)) != len(texts):
            raise ValueError("Las opciones no pueden repetirse")
        return self
