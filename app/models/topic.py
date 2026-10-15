from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base


class Topic(Base):

    __tablename__ = "topics"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )


    subject_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )


    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    order_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )


    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


    subject = relationship(
        "Subject",
    )


    exercises = relationship(
        "Exercise",
        back_populates="topic",
    )

    student_progress = relationship(
        "StudentProgress",
        back_populates="topic",
    )