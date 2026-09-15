from pydantic import BaseModel, ConfigDict


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