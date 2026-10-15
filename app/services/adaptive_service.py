
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.student_progress import StudentProgress


DIFFICULTY_BY_LEVEL = {
    "new": "easy",
    "low": "easy",
    "medium": "medium",
    "high": "hard",
}

FALLBACK_DIFFICULTIES = {
    "easy": ["easy", "medium", "hard"],
    "medium": ["medium", "easy", "hard"],
    "hard": ["hard", "medium", "easy"],
}


def recommend_next_exercise(
    db: Session,
    user_id: int,
    topic_id: int,
):
    # 1. Consultar el progreso del estudiante.
    progress = db.scalar(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.topic_id == topic_id,
        )
    )

    level = progress.level if progress else "new"
    preferred_difficulty = DIFFICULTY_BY_LEVEL.get(
        level,
        "easy",
    )

    # 2. Contar los intentos del estudiante por ejercicio.
    attempts_count = (
        select(
            ExerciseAttempt.exercise_id.label("exercise_id"),
            func.count(ExerciseAttempt.id).label("total"),
        )
        .where(ExerciseAttempt.user_id == user_id)
        .group_by(ExerciseAttempt.exercise_id)
        .subquery()
    )

    # 3. Buscar ejercicios activos del tema.
    # Se ordenan por cantidad de intentos y luego por ID.
    # Así se priorizan los menos practicados.
    for difficulty in FALLBACK_DIFFICULTIES[preferred_difficulty]:
        query = (
            select(Exercise)
            .outerjoin(
                attempts_count,
                Exercise.id == attempts_count.c.exercise_id,
            )
            .options(selectinload(Exercise.options))
            .where(
                Exercise.topic_id == topic_id,
                Exercise.is_active.is_(True),
                Exercise.difficulty == difficulty,
            )
            .order_by(
                func.coalesce(attempts_count.c.total, 0),
                Exercise.id,
            )
            .limit(1)
        )

        exercise = db.scalar(query)

        if exercise is not None:
            return {
                "exercise": exercise,
                "level": level,
                "recommended_difficulty": preferred_difficulty,
                "selected_difficulty": difficulty,
            }

    return None
