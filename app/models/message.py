from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages",
    )

    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_messages",
    )
