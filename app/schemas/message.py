from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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

class MessageContact(BaseModel):
    user_id: int
    name: str

class MessageCreate(BaseModel):
    receiver_id: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=5000)
    model_config = ConfigDict(extra="forbid")