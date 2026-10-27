
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.services.grade_access import ensure_student_can_practice_topic
from app.services.progress_service import recalculate_student_progress

from app.database.connection import get_db
from app.dependencies.auth import require_student
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.exercise_option import ExerciseOption
from app.models.topic import Topic
from app.models.user import User
from app.schemas.attempt import (
    AttemptCreate,
    AttemptResponse,
    AttemptSummaryResponse,
)


router = APIRouter(
    prefix="/attempts",
    tags=["Exercise Attempts"],
)


@router.post(
    "",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attempt(
    data: AttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    # Bloqueamos la fila del ejercicio para serializar
    # los intentos simultáneos de un mismo ejercicio.
    exercise = db.scalar(
        select(Exercise)
        .where(Exercise.id == data.exercise_id)
        .with_for_update()
    )

    if exercise is None or not exercise.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado o inactivo",
        )

    topic = db.scalar(
        select(Topic)
        .where(Topic.id == exercise.topic_id)
        .with_for_update()
    )

    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no disponible",
        )

    ensure_student_can_practice_topic(db, current_user, topic)

    # La opción debe pertenecer al ejercicio enviado.
    option = db.scalar(
        select(ExerciseOption).where(
            ExerciseOption.id == data.selected_option_id,
            ExerciseOption.exercise_id == exercise.id,
        )
    )

    if option is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La opción no pertenece al ejercicio",
        )

    # El servidor calcula el resultado.
    is_correct = option.is_correct

    # Numeración independiente para cada estudiante
    # y ejercicio.
    previous_attempts = db.scalar(
        select(func.count(ExerciseAttempt.id)).where(
            ExerciseAttempt.user_id == current_user.id,
            ExerciseAttempt.exercise_id == exercise.id,
        )
    ) or 0

    attempt = ExerciseAttempt(
        user_id=current_user.id,
        exercise_id=exercise.id,
        selected_option_id=option.id,
        is_correct=is_correct,
        attempt_number=previous_attempts + 1,
        response_time_seconds=data.response_time_seconds,
    )


    try:
        db.add(attempt)

        # Insertamos el intento en la transacción,
        # sin confirmar todavía los cambios.
        db.flush()

        # Actualizamos el progreso del estudiante
        # usando el intento recién registrado.
        recalculate_student_progress(
            db=db,
            user_id=current_user.id,
            topic_id=exercise.topic_id,
        )

        # Confirmamos intento y progreso juntos.
        db.commit()
        db.refresh(attempt)

    except Exception:
        db.rollback()
        raise

    return attempt



@router.get(
    "/me",
    response_model=list[AttemptResponse],
)
def get_my_attempts(
    exercise_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Paginación inválida",
        )

    query = select(ExerciseAttempt).where(
        ExerciseAttempt.user_id == current_user.id,
    )

    if exercise_id is not None:
        query = query.where(
            ExerciseAttempt.exercise_id == exercise_id,
        )

    query = (
        query.order_by(
            ExerciseAttempt.created_at.desc(),
            ExerciseAttempt.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(query).all()


@router.get(
    "/me/summary",
    response_model=AttemptSummaryResponse,
)
def get_my_attempts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    total = db.scalar(
        select(func.count(ExerciseAttempt.id)).where(
            ExerciseAttempt.user_id == current_user.id,
        )
    ) or 0

    correct = db.scalar(
        select(func.count(ExerciseAttempt.id)).where(
            ExerciseAttempt.user_id == current_user.id,
            ExerciseAttempt.is_correct.is_(True),
        )
    ) or 0

    unique_exercises = db.scalar(
        select(
            func.count(
                func.distinct(ExerciseAttempt.exercise_id)
            )
        ).where(
            ExerciseAttempt.user_id == current_user.id,
        )
    ) or 0

    accuracy = round(
        (correct / total) * 100,
        2,
    ) if total > 0 else 0.0

    return AttemptSummaryResponse(
        total_attempts=total,
        correct_attempts=correct,
        incorrect_attempts=total - correct,
        accuracy_percentage=accuracy,
        unique_exercises_attempted=unique_exercises,
    )
