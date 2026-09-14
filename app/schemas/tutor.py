from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TutorCreate(BaseModel):
    user_id: int
    bio: str | None = None
    specialty: str | None = None
    experience_years: int = 0


class TutorUpdate(BaseModel):
    bio: str | None = None
    specialty: str | None = None
    experience_years: int | None = None
    is_active: bool | None = None


class TutorResponse(BaseModel):
    id: int
    user_id: int
    bio: str | None
    specialty: str | None
    experience_years: int
    rating: Decimal | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
