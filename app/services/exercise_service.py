"""Reglas únicas de preguntas, compartidas por /topics y /content."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.models.exercise_option import ExerciseOption


def normalized_statement(text: str) -> str:
    return " ".join(text.split()).casefold()


def duplicate_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Ya existe una pregunta activa con ese enunciado en este tema",
    )


def find_duplicate(
    db: Session,
    topic_id: int,
    statement: str,
    exclude_id: int | None = None,
) -> Exercise | None:
    key = normalized_statement(statement)
    rows = db.scalars(
        select(Exercise).where(
            Exercise.topic_id == topic_id,
            Exercise.is_active.is_(True),
        )
    ).all()
    for row in rows:
        if row.id != exclude_id and normalized_statement(row.statement) == key:
            return row
    return None


def build_options(options) -> list[ExerciseOption]:
    return [
        ExerciseOption(
            option_text=o.option_text,
            is_correct=o.is_correct,
            order_number=index,
        )
        for index, o in enumerate(options, start=1)
    ]


def create_exercise(db: Session, topic_id: int, data) -> Exercise:
    """Crea una pregunta activa; el llamador debe haber bloqueado el tema."""
    if find_duplicate(db, topic_id, data.statement) is not None:
        raise duplicate_conflict()
    exercise = Exercise(
        topic_id=topic_id,
        statement=data.statement,
        difficulty=data.difficulty,
        explanation=(data.explanation or "").strip() or None,
        is_ai_generated=False,
        is_active=True,
    )
    exercise.options = build_options(data.options)
    db.add(exercise)
    return exercise
