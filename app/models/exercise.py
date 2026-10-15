from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.database.base import Base


class Exercise(Base):

    __tablename__ = "exercises"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )


    topic_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "topics.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )


    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    topic = relationship(
        "Topic",
        back_populates="exercises",
    )


    options = relationship(
        "ExerciseOption",
        back_populates="exercise",
        order_by="ExerciseOption.order_number",
    )

    attempts = relationship(
        "ExerciseAttempt",
        back_populates="exercise",
    )