from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    receiver_id: int
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
