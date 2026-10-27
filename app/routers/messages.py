from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageContact, MessageCreate, MessageResponse


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


@router.get(
    "",
    response_model=list[MessageResponse],
)
def get_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("student", "tutor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado",
        )

    return db.scalars(
        select(Message)
        .where(
            or_(
                Message.sender_id == current_user.id,
                Message.receiver_id == current_user.id,
            )
        )
        .order_by(Message.created_at.desc())
    ).all()


# Nombres de las personas con las que el usuario ya intercambió mensajes.
# No expone correo ni usuarios sin conversación con quien consulta.
@router.get(
    "/contacts",
    response_model=list[MessageContact],
)
def get_message_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("student", "tutor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no autorizado",
        )

    rows = db.execute(
        select(Message.sender_id, Message.receiver_id).where(
            or_(
                Message.sender_id == current_user.id,
                Message.receiver_id == current_user.id,
            )
        )
    ).all()

    other_ids = {
        r[1] if r[0] == current_user.id else r[0] for r in rows
    }

    if not other_ids:
        return []

    users = db.scalars(
        select(User).where(User.id.in_(other_ids)).order_by(User.name)
    ).all()

    return [MessageContact(user_id=u.id, name=u.name) for u in users]


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("student", "tutor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo estudiantes y tutores pueden enviar mensajes",
        )

    receiver = db.get(User, data.receiver_id)

    if receiver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario receptor no encontrado",
        )

    if not receiver.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario receptor está inactivo",
        )

    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes enviarte mensajes a ti mismo",
        )

    # Comunicación únicamente entre estudiantes y tutores.
    allowed_pairs = {
        ("student", "tutor"),
        ("tutor", "student"),
    }

    if (current_user.role, receiver.role) not in allowed_pairs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La comunicación debe ser entre estudiante y tutor",
        )

    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=data.content.strip(),
    )

    db.add(message)

    try:
        db.commit()
        db.refresh(message)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible enviar el mensaje",
        )

    return message
