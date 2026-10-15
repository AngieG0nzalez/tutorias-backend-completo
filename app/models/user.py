from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func,Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tutor = relationship(
        "Tutor",
        back_populates="user",
        uselist=False,
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="user",
    )

    sent_messages = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
    )

    received_messages = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver",
    )

    reviews = relationship(
        "Review",
        back_populates="user",
    )

    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    reviewed_registration_requests = relationship(
        "RegistrationRequest",
        foreign_keys="RegistrationRequest.reviewed_by",
        back_populates="reviewer",
    )

    exercise_attempts = relationship(
        "ExerciseAttempt",
        back_populates="user",
    )

    student_progress = relationship(
        "StudentProgress",
        back_populates="user",
    )

    # Dentro de class User:
    session_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
   