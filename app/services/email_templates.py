from html import escape

NAVY = "#152238"
AMBER = "#D99A3D"
BG = "#F2F4F8"
BORDER = "#DDE2EC"
TEXT = "#3B4A63"

LOGO_CID = "nexo-logo"


def _render(
    preheader: str,
    title: str,
    greeting: str,
    paragraphs: list[str],
    button_label: str,
    link: str,
    notes: list[str],
) -> tuple[str, str]:
    body_html = "".join(
        f'<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">{escape(p)}</p>'
        for p in paragraphs
    )
    notes_html = "".join(
        f'<li style="margin:0 0 6px;">{escape(n)}</li>' for n in notes
    )
    safe_link = escape(link, quote=True)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:{BG};font-family:Arial,Helvetica,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 12px;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border:1px solid {BORDER};border-radius:16px;overflow:hidden;">
<tr><td align="center" style="background:{NAVY};padding:28px 24px;">
<img src="cid:{LOGO_CID}" width="72" height="72" alt="Nexo" style="display:block;border:0;margin:0 auto 12px;">
<div style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:2px;">NEXO</div>
<div style="color:{AMBER};font-size:12px;letter-spacing:1px;margin-top:4px;">TUTORÍAS DE MATEMÁTICAS</div>
</td></tr>
<tr><td style="padding:36px 36px 12px;">
<h1 style="margin:0 0 20px;font-size:24px;color:{NAVY};">{escape(title)}</h1>
<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">{escape(greeting)}</p>
{body_html}
</td></tr>
<tr><td align="center" style="padding:8px 36px 24px;">
<a href="{safe_link}" style="display:inline-block;background:{AMBER};color:{NAVY};font-weight:bold;font-size:16px;text-decoration:none;padding:14px 32px;border-radius:10px;">{escape(button_label)}</a>
</td></tr>
<tr><td style="padding:0 36px 24px;">
<p style="margin:0 0 8px;font-size:13px;color:{TEXT};">Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
<p style="margin:0;font-size:13px;word-break:break-all;"><a href="{safe_link}" style="color:{NAVY};">{safe_link}</a></p>
</td></tr>
<tr><td style="padding:0 36px 32px;">
<div style="background:{BG};border-left:4px solid {AMBER};border-radius:8px;padding:14px 18px;">
<ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.5;color:{TEXT};">{notes_html}</ul>
</div>
</td></tr>
<tr><td align="center" style="background:{BG};padding:20px 24px;border-top:1px solid {BORDER};">
<p style="margin:0;font-size:12px;color:{TEXT};">Nexo · Plataforma de tutorías de matemáticas</p>
<p style="margin:6px 0 0;font-size:12px;color:#7A869A;">Este es un mensaje automático, por favor no respondas a este correo.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    text = "\n\n".join(
        [title, greeting, *paragraphs, f"{button_label}: {link}", "\n".join(f"- {n}" for n in notes), "Nexo · Plataforma de tutorías de matemáticas"]
    )
    return text, html


def password_reset_email(link: str, minutes: int) -> tuple[str, str]:
    return _render(
        preheader="Restablece tu contraseña de Nexo",
        title="Recupera tu contraseña",
        greeting="¡Hola!",
        paragraphs=[
            "Recibimos una solicitud para restablecer la contraseña de tu cuenta en Nexo.",
            "Haz clic en el botón para elegir una nueva contraseña y volver a tus clases y ejercicios.",
        ],
        button_label="Restablecer contraseña",
        link=link,
        notes=[
            f"El enlace es válido por {minutes} minutos y solo puede usarse una vez.",
            "Si no solicitaste este cambio, ignora este correo: tu contraseña actual no se modificará.",
            "Por tu seguridad, al cambiar la contraseña se cerrarán tus sesiones activas.",
        ],
    )


def email_change_email(link: str, minutes: int) -> tuple[str, str]:
    return _render(
        preheader="Confirma tu nuevo correo en Nexo",
        title="Confirma tu nuevo correo",
        greeting="¡Hola!",
        paragraphs=[
            "Solicitaste usar esta dirección como el correo de tu cuenta en Nexo.",
            "Confirma el cambio con el siguiente botón para empezar a usar este correo al iniciar sesión.",
        ],
        button_label="Confirmar correo",
        link=link,
        notes=[
            f"El enlace es válido por {minutes} minutos.",
            "Si no fuiste tú, ignora este mensaje y tu correo actual seguirá igual.",
            "Al confirmar, se cerrarán tus sesiones activas y deberás iniciar sesión de nuevo.",
        ],
    )
