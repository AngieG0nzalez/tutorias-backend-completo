import hashlib
import os
import re
import secrets
import smtplib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.parse import urlencode

import httpx

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.account_security import AccountToken, AccountAudit
from app.models.user import User

TOKEN_MINUTES = 15
EMAIL_TOKEN_MINUTES = 20

def now_utc():
    return datetime.now(timezone.utc)

def digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def issue_token(db: Session, user_id: int, purpose: str, target_email: str | None = None):
    token = secrets.token_urlsafe(32)
    db.add(AccountToken(
        user_id=user_id, token_hash=digest(token), purpose=purpose,
        target_email=target_email,
        expires_at=now_utc() + timedelta(minutes=EMAIL_TOKEN_MINUTES if purpose == "email_change" else TOKEN_MINUTES),
    ))
    return token

def get_token_locked(db: Session, raw_token: str, purposes: tuple[str, ...]):
    return db.scalar(select(AccountToken).where(
        AccountToken.token_hash == digest(raw_token),
        AccountToken.purpose.in_(purposes),
        AccountToken.consumed_at.is_(None),
        AccountToken.expires_at > now_utc(),
    ).with_for_update())

def revoke_all_tokens(db: Session, user_id: int):
    db.execute(update(AccountToken).where(
        AccountToken.user_id == user_id,
        AccountToken.consumed_at.is_(None),
    ).values(consumed_at=now_utc()))

def audit(db: Session, target_user_id: int, action: str, actor_user_id: int | None = None, reason: str | None = None):
    db.add(AccountAudit(actor_user_id=actor_user_id, target_user_id=target_user_id, action=action, reason=reason))

def brevo_api_key() -> str:
    """BREVO_API_KEY, o SMTP_PASSWORD si ya contiene una clave de API de Brevo (xkeysib-...)."""
    explicit = os.getenv("BREVO_API_KEY", "").strip()
    if explicit:
        return explicit
    legacy = os.getenv("SMTP_PASSWORD", "").strip()
    return legacy if legacy.startswith("xkeysib-") else ""

def brevo_api_ready():
    return bool(brevo_api_key()) and all(os.getenv(k) for k in ("SMTP_FROM", "FRONTEND_URL"))

def smtp_ready():
    # La API HTTPS de Brevo tiene prioridad: Render Free bloquea los puertos SMTP salientes.
    if brevo_api_ready():
        return True
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "FRONTEND_URL"))

def _send_via_brevo_api(to_email: str, subject: str, body: str, html: str | None):
    name, address = parseaddr(os.environ["SMTP_FROM"])
    payload = {
        "sender": {"email": address, **({"name": name} if name else {})},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }
    if html:
        # Sin adjuntos inline en la API: se omite el logo incrustado por cid.
        payload["htmlContent"] = re.sub(r"<img[^>]*cid:[^>]*>", "", html)
    response = httpx.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers={"api-key": brevo_api_key(), "accept": "application/json"},
        timeout=15,
    )
    if response.status_code >= 300:
        # Solo el código: nunca la clave ni el contenido del correo.
        raise RuntimeError(f"Brevo API respondió HTTP {response.status_code}")

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "nexo_logo.png"

def send_email(to_email: str, subject: str, body: str, html: str | None = None):
    if brevo_api_ready():
        return _send_via_brevo_api(to_email, subject, body, html)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = to_email
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")
        try:
            message.get_payload()[1].add_related(
                LOGO_PATH.read_bytes(), "image", "png", cid="<nexo-logo>", filename="nexo.png"
            )
        except OSError:
            pass
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=15) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)

def frontend_link(path: str, token: str):
    base = os.environ["FRONTEND_URL"].rstrip("/")
    return f"{base}/{path}?{urlencode({'token': token})}"
