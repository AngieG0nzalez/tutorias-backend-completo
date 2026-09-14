from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.message import Message
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)


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
    return db.scalars(
        select(Message)
        .where(
            or_(
                Message.sender_id == current_user.id,
                Message.receiver_id == current_user.id,
            )
        )
        .order_by(
            Message.created_at.desc(),
        )
    ).all()


@router.post(
    "",
    response_model=MessageResponse,
    status_code=201,
)
def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receiver = db.get(
        User,
        data.receiver_id,
    )

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Usuario receptor no encontrado",
        )

    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes enviarte un mensaje a ti mismo",
        )

    message = Message(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        content=data.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message
