"""
email_utils.py — Envío de correos del sistema (recuperación de contraseña).

Comportamiento:
  - Si hay variables SMTP configuradas en .env → envía un correo real.
  - Si NO hay configuración SMTP → imprime el correo en la consola del servidor
    y devuelve False. Así puedes probar la recuperación de contraseña sin tener
    un servidor de correo (útil para desarrollo / entregas de la universidad).

Variables de entorno necesarias para envío real (en backend/.env):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=tucorreo@gmail.com
    SMTP_PASSWORD=clave_de_aplicacion   (no tu clave normal de Gmail)
    SMTP_FROM=Talmocur <tucorreo@gmail.com>
"""

import os
import smtplib
from email.message import EmailMessage


def _hay_config_smtp() -> bool:
    """True solo si están las variables mínimas para enviar correo real."""
    return all(os.getenv(v) for v in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def enviar_correo(destinatario: str, asunto: str, cuerpo_texto: str) -> bool:
    """Envía un correo. Devuelve True si se envió por SMTP, False si fue por consola.

    Nunca lanza excepción hacia arriba: si el envío falla, lo registra y devuelve
    False para que la lógica de la app no se rompa por un problema de correo.
    """
    if not _hay_config_smtp():
        # ── Modo desarrollo: mostrar el correo en consola ──
        print("\n" + "=" * 60)
        print("[CORREO SIMULADO — no hay SMTP configurado]")
        print(f"Para:    {destinatario}")
        print(f"Asunto:  {asunto}")
        print("-" * 60)
        print(cuerpo_texto)
        print("=" * 60 + "\n")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER"))
        msg["To"] = destinatario
        msg.set_content(cuerpo_texto)

        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))

        with smtplib.SMTP(host, port) as servidor:
            servidor.starttls()
            servidor.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            servidor.send_message(msg)
        return True
    except Exception as e:
        # Si el correo falla, no rompemos la app: dejamos rastro y seguimos.
        print(f"[email_utils] Error enviando correo a {destinatario}: {e}")
        return False
