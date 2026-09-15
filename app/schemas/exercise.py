from pydantic import (
    BaseModel,
    ConfigDict,
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