import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.account_security import AccountToken
from app.models.user import User
from app.schemas.account import (MessageResponse, ChangePasswordRequest, ForgotPasswordRequest,
    ResetPasswordRequest, ChangeEmailRequest, ConfirmEmailRequest, AdminResetRequest, AdminResetResponse)
from app.services.email_templates import email_change_email, password_reset_email
from app.services.account_security import (TOKEN_MINUTES, EMAIL_TOKEN_MINUTES, now_utc, issue_token,
    get_token_locked, revoke_all_tokens, audit, smtp_ready, send_email, frontend_link)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Account Management"])

@router.patch("/account/password", response_model=MessageResponse)
def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.scalar(select(User).where(User.id == current_user.id).with_for_update())
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Contraseña actual incorrecta")
    user.password_hash = hash_password(data.new_password)
    user.session_version += 1
    revoke_all_tokens(db, user.id)
    audit(db, user.id, "password_changed", actor_user_id=user.id)
    db.commit()
    return MessageResponse(message="Contraseña actualizada. Inicia sesión de nuevo")

@router.post("/auth/forgot-password", response_model=MessageResponse, status_code=202)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    if not smtp_ready():
        raise HTTPException(503, "Servicio de correo no configurado")
    # Respuesta idéntica para correos existentes o inexistentes.
    message = MessageResponse(message="Si el correo está registrado, recibirás instrucciones")
    email = str(data.email).strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email, User.is_active.is_(True)))
    if user is None:
        return message
    # Máximo 3 solicitudes en una hora por cuenta. Añadir limitación por IP en proxy/API gateway.
    recent = db.scalar(select(func.count(AccountToken.id)).where(
        AccountToken.user_id == user.id,
        AccountToken.purpose == "password_reset",
        AccountToken.created_at >= now_utc() - timedelta(hours=1),
    )) or 0
    if recent >= 3:
        return message
    raw = issue_token(db, user.id, "password_reset")
    db.commit()
    try:
        link = frontend_link("reset-password", raw)
        text, html = password_reset_email(link, TOKEN_MINUTES)
        send_email(user.email, "Nexo: recupera tu contraseña", text, html)
    except Exception:
        logger.exception("No fue posible enviar el correo de recuperación")
    return message

@router.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    token = get_token_locked(db, data.token, ("password_reset", "admin_reset"))
    if token is None:
        raise HTTPException(400, "Enlace o código inválido o vencido")
    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    if user is None or not user.is_active:
        raise HTTPException(400, "Enlace o código inválido o vencido")
    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(422, "La contraseña nueva debe ser diferente")
    user.password_hash = hash_password(data.new_password)
    user.session_version += 1
    audit(db, user.id, "password_reset", reason=token.purpose)
    revoke_all_tokens(db, user.id)
    db.commit()
    return MessageResponse(message="Contraseña restablecida. Inicia sesión nuevamente")

@router.post("/account/email-change", response_model=MessageResponse, status_code=202)
def request_email_change(data: ChangeEmailRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not smtp_ready():
        raise HTTPException(503, "Servicio de correo no configurado")
    email = str(data.new_email).strip().lower()
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(400, "Contraseña actual incorrecta")
    if email == current_user.email.lower():
        raise HTTPException(409, "Este ya es tu correo")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(409, "Correo no disponible")
    recent = db.scalar(select(func.count(AccountToken.id)).where(
        AccountToken.user_id == current_user.id,
        AccountToken.purpose == "email_change",
        AccountToken.created_at >= now_utc() - timedelta(hours=1),
    )) or 0
    if recent >= 3:
        raise HTTPException(429, "Demasiadas solicitudes; intenta más tarde")
    raw = issue_token(db, current_user.id, "email_change", target_email=email)
    db.commit()
    try:
        link = frontend_link("confirm-email", raw)
        text, html = email_change_email(link, EMAIL_TOKEN_MINUTES)
        send_email(email, "Nexo: confirma tu correo", text, html)
    except Exception:
        logger.exception("No fue posible enviar el correo de confirmación")
    return MessageResponse(message="Revisa el nuevo correo para confirmar el cambio")

@router.post("/account/email-confirm", response_model=MessageResponse)
def confirm_email(data: ConfirmEmailRequest, db: Session = Depends(get_db)):
    token = get_token_locked(db, data.token, ("email_change",))
    if token is None:
        raise HTTPException(400, "Enlace inválido o vencido")
    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    if user is None or not user.is_active:
        raise HTTPException(400, "Enlace inválido o vencido")
    if db.scalar(select(User.id).where(func.lower(User.email) == token.target_email, User.id != user.id)):
        raise HTTPException(409, "Correo no disponible")
    old_email = user.email
    user.email = token.target_email
    user.session_version += 1
    revoke_all_tokens(db, user.id)
    audit(db, user.id, "email_changed", actor_user_id=user.id, reason="Correo anterior: " + old_email)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Correo no disponible")
    return MessageResponse(message="Correo confirmado. Inicia sesión nuevamente")

@router.post("/admin/users/{user_id}/recovery-token", response_model=AdminResetResponse)
def admin_recovery_token(user_id: int, data: AdminResetRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    # Verificación humana obligatoria fuera del sistema: la casilla no sustituye la verificación.
    if not data.identity_verified:
        raise HTTPException(422, "Debes verificar la identidad antes de continuar")
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(404, "Usuario no encontrado")
    if not user.is_active or user.role == "admin":
        raise HTTPException(403, "No se puede restablecer esta cuenta por este procedimiento")
    recent = db.scalar(select(func.count(AccountToken.id)).where(
        AccountToken.user_id == user.id,
        AccountToken.purpose == "admin_reset",
        AccountToken.created_at >= now_utc() - timedelta(hours=1),
    )) or 0
    if recent >= 2:
        raise HTTPException(429, "Demasiadas recuperaciones administrativas")
    raw = issue_token(db, user.id, "admin_reset")
    audit(db, user.id, "admin_reset_issued", actor_user_id=admin.id, reason=data.reason)
    db.commit()
    # Solo se muestra una vez al administrador; no guardar ni registrar el código.
    return AdminResetResponse(message="Código temporal generado. Entrégalo solo tras verificar la identidad", one_time_token=raw, expires_in_minutes=TOKEN_MINUTES)
