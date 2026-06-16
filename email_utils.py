import os
import smtplib
from email.message import EmailMessage

try:
    from google_utils import build_gmail_service, create_gmail_message, Credentials
except ImportError:  # pragma: no cover
    build_gmail_service = None
    create_gmail_message = None
    Credentials = None


def get_smtp_settings():
    return {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "username": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "use_ssl": os.getenv("SMTP_USE_SSL", "true").lower() in ("1", "true", "yes"),
        "sender": os.getenv("SMTP_SENDER", os.getenv("SMTP_USER", "")),
    }


def send_email(subject: str, body: str, recipients: list[str], sender: str | None = None) -> tuple[bool, str]:
    settings = get_smtp_settings()
    sender_address = sender or settings["sender"]
    if not sender_address:
        return False, "SMTP sender address is not configured."
    if not settings["username"] or not settings["password"]:
        return False, "SMTP credentials are not configured."

    message = EmailMessage()
    message["From"] = sender_address
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    try:
        if settings["use_ssl"]:
            with smtplib.SMTP_SSL(settings["server"], settings["port"]) as smtp:
                smtp.login(settings["username"], settings["password"])
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings["server"], settings["port"]) as smtp:
                smtp.starttls()
                smtp.login(settings["username"], settings["password"])
                smtp.send_message(message)
        return True, "Email sent successfully."
    except Exception as exc:
        return False, f"Email sending failed: {exc}"


def send_email_via_google(subject: str, body: str, recipients: list[str], sender: str, credentials) -> tuple[bool, str]:
    if build_gmail_service is None or create_gmail_message is None:
        return False, "Google API client is not installed. Install google-api-python-client and google-auth libraries."
    if credentials is None:
        return False, "Google credentials are not available. Authorize the app with Google first."

    try:
        service = build_gmail_service(credentials)
        message = create_gmail_message(sender, recipients, subject, body)
        service.users().messages().send(userId="me", body=message).execute()
        return True, "Email sent successfully via Gmail OAuth."
    except Exception as exc:
        return False, f"Google email sending failed: {exc}"
