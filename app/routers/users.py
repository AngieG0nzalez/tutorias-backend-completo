from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(User).order_by(User.id)
    ).all()


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    for key, value in data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user
