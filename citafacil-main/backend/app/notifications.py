"""Envío de mensajes por WhatsApp con Twilio.

- Si las 3 credenciales de Twilio están configuradas, envía mensajes REALES.
- Si no, funciona en 'modo demo': registra el mensaje en el log y no falla,
  para poder correr la app en local sin credenciales.
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger("citafacil.notifications")

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fmt_dt(dt: datetime) -> str:
    return f"{_DIAS[dt.weekday()]} {dt.day:02d}-{dt.month:02d} a las {dt.strftime('%H:%M')}"


def confirmation_message(business: str, customer_name: str, service_name: str, start_at: datetime) -> str:
    return (
        f"¡Hola {customer_name}! 👋 Tu reserva en {business} quedó registrada:\n"
        f"✂️ {service_name}\n"
        f"🗓️ {_fmt_dt(start_at)}\n\n"
        f"Te enviaremos un recordatorio antes. ¡Te esperamos!"
    )


def reminder_message(business: str, customer_name: str, service_name: str, start_at: datetime) -> str:
    return (
        f"Hola {customer_name}, te recordamos tu cita en {business}:\n"
        f"✂️ {service_name}\n"
        f"🗓️ {_fmt_dt(start_at)}\n\n"
        f"Si no puedes asistir, responde este mensaje. ¡Gracias!"
    )


def confirmation_email(
    business: str, customer_name: str, service_name: str, start_at: datetime
) -> tuple[str, str]:
    """Asunto y cuerpo del correo de confirmación."""
    subject = f"Confirmación de tu cita en {business}"
    body = (
        f"Hola {customer_name},\n\n"
        f"Tu cita en {business} quedó confirmada:\n"
        f"Servicio: {service_name}\n"
        f"Fecha y hora: {_fmt_dt(start_at)}\n"
        f"Profesional: {business}\n\n"
        "¡Te esperamos!"
    )
    return subject, body


def send_email(to_email: str, subject: str, body: str) -> dict:
    """Envía un correo por SMTP. En modo demo solo registra el mensaje."""
    if not settings.email_enabled:
        logger.info("[Email DEMO] Para %s | %s\n%s", to_email, subject, body)
        return {
            "ok": True,
            "mode": "demo",
            "detail": "SMTP no configurado; correo simulado.",
        }

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.set_content(body)

        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=15
            ) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=15
            ) as smtp:
                if settings.smtp_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)

        logger.info("Correo enviado a %s", to_email)
        return {"ok": True, "mode": "smtp"}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error enviando correo a %s: %s", to_email, exc)
        return {"ok": False, "mode": "smtp", "error": str(exc)}


def send_whatsapp(to_e164: str, body: str) -> dict:
    """Envía un WhatsApp. Devuelve un dict con el resultado.

    En modo demo no realiza llamadas de red; sólo registra el mensaje.
    """
    if not settings.twilio_enabled:
        logger.info("[WhatsApp DEMO] Para %s:\n%s", to_e164, body)
        return {"ok": True, "mode": "demo", "detail": "Twilio no configurado; mensaje simulado."}

    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        msg = client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=f"whatsapp:{to_e164}",
            body=body,
        )
        logger.info("WhatsApp enviado a %s (sid=%s)", to_e164, msg.sid)
        return {"ok": True, "mode": "twilio", "sid": msg.sid}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error enviando WhatsApp a %s: %s", to_e164, exc)
        return {"ok": False, "mode": "twilio", "error": str(exc)}
