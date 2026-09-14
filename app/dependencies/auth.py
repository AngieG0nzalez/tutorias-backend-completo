import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import ALGORITHM, SECRET_KEY
from app.database.connection import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=401,
        detail="Token inválido o expirado",
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_error

    except jwt.InvalidTokenError:
        raise credentials_error

    user = db.get(
        User,
        int(user_id),
    )

    if not user:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Usuario inactivo",
        )

    return user
