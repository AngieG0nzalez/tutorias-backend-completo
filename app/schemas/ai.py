from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExplanationRequest(BaseModel):
    attempt_id: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class ExplanationResponse(BaseModel):
    attempt_id: int
    exercise_id: int
    explanation: str = Field(min_length=1, max_length=6000)
    source: Literal["ollama", "curated"]
    model: str | None = None
    is_fallback: bool


class DraftRequest(BaseModel):
    topic_id: int = Field(gt=0)
    difficulty: Literal["easy", "medium", "hard"]
    objective: str | None = Field(default=None, max_length=200)

    model_config = ConfigDict(extra="forbid")


class DraftOption(BaseModel):
    option_text: str
    is_correct: bool


class DraftResponse(BaseModel):
    topic_id: int
    grade: int
    difficulty: Literal["easy", "medium", "hard"]
    statement: str
    explanation: str | None
    options: list[DraftOption]
    is_ai_generated: Literal[True] = True
    persisted: Literal[False] = False
    warning: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1500)

    model_config = ConfigDict(extra="forbid")


class ChatRequest(BaseModel):
    # El cliente envía el historial reciente; el servidor no guarda conversaciones.
    messages: list[ChatMessage] = Field(min_length=1, max_length=12)

    model_config = ConfigDict(extra="forbid")


class ChatResponse(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    model: str | None = None
