from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegistrationRequestCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    requested_role: str

    grade: int | None = None

    @model_validator(mode="after")
    def validate_registration(self):
        if self.requested_role not in ("student", "tutor"):
            raise ValueError(
                "El rol solicitado debe ser student o tutor"
            )

        if self.requested_role == "student":
            if self.grade not in (9, 10, 11):
                raise ValueError(
                    "El estudiante debe pertenecer a grado 9, 10 u 11"
                )

        if self.requested_role == "tutor":
            if self.grade is not None:
                raise ValueError(
                    "Un tutor no debe tener grado"
                )

        return self


class RegistrationRequestResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    requested_role: str
    grade: int | None
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class RegistrationReviewResponse(BaseModel):
    id: int
    status: str
    message: str