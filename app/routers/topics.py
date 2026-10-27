from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import (
    select,
)
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.database.connection import get_db
from app.dependencies.auth import require_tutor
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
from app.models.exercise import Exercise
from app.services.exercise_service import create_exercise
from app.models.exercise_option import ExerciseOption
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseResponse,
    TutorExerciseResponse,
)


router = APIRouter(
    prefix="/topics",
    tags=["Topics"],
)


def get_active_tutor_for_subject(
    db: Session,
    current_user: User,
    subject_id: int,
) -> Tutor:
    tutor = db.scalar(
        select(Tutor).where(Tutor.user_id == current_user.id)
    )
    if tutor is None or not tutor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere un perfil de tutor activo",
        )
    assigned = db.scalar(
        select(TutorSubject.id).where(
            TutorSubject.tutor_id == tutor.id,
            TutorSubject.subject_id == subject_id,
        )
    )
    if assigned is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes gestionar temas de materias asignadas",
        )
    return tutor


def normalized_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def ensure_unique_topic_name(
    db: Session,
    subject_id: int,
    name: str,
    exclude_topic_id: int | None = None,
) -> None:
    candidates = db.scalars(
        select(Topic).where(Topic.subject_id == subject_id)
    ).all()
    if any(
        item.id != exclude_topic_id
        and normalized_name(item.name) == normalized_name(name)
        for item in candidates
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un tema con ese nombre en la materia",
        )


@router.post(
    "",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    data: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    get_active_tutor_for_subject(db, current_user, data.subject_id)
    name = " ".join(data.name.split())
    ensure_unique_topic_name(db, data.subject_id, name)
    topic = Topic(
        subject_id=data.subject_id,
        name=name,
        description=data.description.strip() if data.description else None,
        order_number=data.order_number,
    )
    db.add(topic)
    try:
        db.commit()
        db.refresh(topic)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el tema",
        )
    return topic


@router.patch(
    "/{topic_id}",
    response_model=TopicResponse,
)
def update_topic(
    topic_id: int,
    data: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado",
        )
    get_active_tutor_for_subject(db, current_user, topic.subject_id)
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = " ".join(update_data["name"].split())
        ensure_unique_topic_name(
            db, topic.subject_id, update_data["name"], exclude_topic_id=topic.id
        )
    if "description" in update_data and update_data["description"] is not None:
        update_data["description"] = update_data["description"].strip() or None
    for key, value in update_data.items():
        setattr(topic, key, value)
    try:
        db.commit()
        db.refresh(topic)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible actualizar el tema",
        )
    return topic


@router.get(
    "",
    response_model=list[TopicResponse],
)
def get_topics(
    subject_id: int | None = None,
    db: Session = Depends(get_db),
):

    query = (
        select(Topic)
        .where(
            Topic.is_active.is_(True),
        )
        .order_by(
            Topic.order_number,
        )
    )


    if subject_id is not None:

        query = query.where(
            Topic.subject_id == subject_id,
        )


    topics = db.scalars(
        query,
    ).all()


    return topics

@router.get(
    "/{topic_id}/exercises",
    response_model=list[ExerciseResponse],
)
def get_topic_exercises(
    topic_id: int,
    db: Session = Depends(get_db),
):
    topic = db.get(Topic, topic_id)

    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado",
    )

    query = (
        select(Exercise)
        .options(
            selectinload(
                Exercise.options,
            ),
        )
        .where(
            Exercise.topic_id == topic_id,
            Exercise.is_active.is_(True),
        )
        .order_by(
            Exercise.id,
        )
    )


    exercises = db.scalars(
        query,
    ).all()


    return exercises


def get_manageable_topic(
    db: Session,
    current_user: User,
    topic_id: int,
    lock: bool = False,
) -> Topic:
    query = select(Topic).where(Topic.id == topic_id)
    if lock:
        # Misma serialización que /content/exercises: evita duplicados concurrentes.
        query = query.with_for_update()
    topic = db.scalar(query)
    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado",
        )
    get_active_tutor_for_subject(db, current_user, topic.subject_id)
    return topic


def load_active_exercises(db: Session, topic_id: int) -> list[Exercise]:
    return list(
        db.scalars(
            select(Exercise)
            .options(selectinload(Exercise.options))
            .where(
                Exercise.topic_id == topic_id,
                Exercise.is_active.is_(True),
            )
            .order_by(Exercise.id)
        ).all()
    )


@router.get(
    "/{topic_id}/exercises/manage",
    response_model=list[TutorExerciseResponse],
)
def get_topic_exercises_for_tutor(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    get_manageable_topic(db, current_user, topic_id)
    return load_active_exercises(db, topic_id)


@router.post(
    "/{topic_id}/exercises",
    response_model=TutorExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic_exercise(
    topic_id: int,
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    get_manageable_topic(db, current_user, topic_id, lock=True)
    exercise = create_exercise(db, topic_id, data)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete(
    "/{topic_id}/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_topic_exercise(
    topic_id: int,
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    get_manageable_topic(db, current_user, topic_id)
    exercise = db.get(Exercise, exercise_id)
    if (
        exercise is None
        or exercise.topic_id != topic_id
        or not exercise.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada",
        )
    # Eliminación lógica: conserva intentos y progreso históricos.
    exercise.is_active = False
    db.commit()
