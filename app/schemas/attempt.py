
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttemptCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    selected_option_id: int = Field(gt=0)
    response_time_seconds: int | None = Field(
        default=None,
        ge=0,
        le=86400,
    )

    model_config = ConfigDict(extra="forbid")


class AttemptResponse(BaseModel):
    id: int
    user_id: int
    exercise_id: int
    selected_option_id: int | None
    is_correct: bool
    attempt_number: int
    response_time_seconds: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttemptSummaryResponse(BaseModel):
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    accuracy_percentage: float
    unique_exercises_attempted: int
