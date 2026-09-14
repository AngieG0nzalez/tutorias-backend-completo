from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
