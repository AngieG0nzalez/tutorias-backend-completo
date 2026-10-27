from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class TopicCreate(BaseModel):
    subject_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    order_number: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("El nombre debe tener entre 2 y 150 caracteres")
        return value


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    order_number: int | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("El nombre no puede estar vacío")
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("El nombre debe tener entre 2 y 150 caracteres")
        return value

    @field_validator("order_number", mode="before")
    @classmethod
    def validate_order(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("El orden no puede estar vacío")
        return value

    @model_validator(mode="after")
    def validate_non_empty_update(self):
        if not self.model_fields_set:
            raise ValueError("Debes indicar al menos un campo para actualizar")
        return self


class TopicResponse(BaseModel):

    id: int

    subject_id: int

    name: str

    description: str | None

    order_number: int

    is_active: bool


    model_config = ConfigDict(
        from_attributes=True,
    )