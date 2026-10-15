from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    tutor_id: int
    class_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    tutor_id: int
    class_id: int
    rating: int
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class ReviewCreate(BaseModel):
    tutor_id: int = Field(gt=0)
    class_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")