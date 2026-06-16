import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "email",
    "profile",
]


def get_google_client_config() -> dict:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google client ID or secret is not configured.")
    return {
        "installed": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def create_flow(redirect_uri: str = GOOGLE_REDIRECT_URI) -> Flow:
    config = get_google_client_config()
    flow = Flow.from_client_config(config, scopes=GOOGLE_SCOPES, redirect_uri=redirect_uri)
    return flow


def get_authorization_url(redirect_uri: str = GOOGLE_REDIRECT_URI) -> tuple[str, str]:
    flow = create_flow(redirect_uri)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url, state


def exchange_code_for_credentials(code: str, redirect_uri: str = GOOGLE_REDIRECT_URI) -> Credentials:
    flow = create_flow(redirect_uri)
    flow.fetch_token(code=code)
    return flow.credentials


def refresh_credentials(credentials: Credentials) -> Credentials:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


def credentials_to_dict(credentials: Credentials) -> dict:
    if not credentials:
        return {}
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def credentials_from_dict(info: dict) -> Credentials | None:
    if not info:
        return None
    return Credentials(**info)


def build_gmail_service(credentials: Credentials):
    credentials = refresh_credentials(credentials)
    return build("gmail", "v1", credentials=credentials)


def build_calendar_service(credentials: Credentials):
    credentials = refresh_credentials(credentials)
    return build("calendar", "v3", credentials=credentials)


def create_gmail_message(sender: str, recipients: list[str], subject: str, body_text: str) -> dict:
    if isinstance(recipients, str):
        recipients = [recipients]
    message = MIMEText(body_text)
    message["to"] = ", ".join(recipients)
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_gmail_message(service, user_id: str, message: dict) -> dict:
    return service.users().messages().send(userId=user_id, body=message).execute()
