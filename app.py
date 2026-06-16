import base64
import os
import streamlit as st
from streamlit import session_state as state
from sqlalchemy.orm import Session

try:
    from streamlit_audiorecorder import st_audiorecorder
except ImportError:
    st_audiorecorder = None

from auth_utils import create_access_token, hash_password, verify_access_token, verify_password
from ai_utils import draft_email, generate_ai_response, summarize_calendar
from db import SessionLocal, init_db
from email_utils import send_email, send_email_via_google
from google_oauth import authorize_google, get_google_credentials
from models import AppConfig, User
from speech_utils import synthesize_speech, transcribe_audio


def init_app():
    st.set_page_config(page_title="Gmail Calendar AI", page_icon="🤖", layout="wide")
    init_db()
    if "jwt_token" not in state:
        state.jwt_token = ""
    if "user_email" not in state:
        state.user_email = ""
    if "is_admin" not in state:
        state.is_admin = False


def get_current_user() -> User | None:
    token = state.jwt_token
    if not token:
        return None
    data = verify_access_token(token)
    if not data:
        return None
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == data.get("email")).first()
        return user


def get_config_entries(db: Session) -> dict[str, str]:
    rows = db.query(AppConfig).all()
    return {row.key: row.value for row in rows}


def set_config_entry(db: Session, key: str, value: str, description: str = ""):
    entry = db.query(AppConfig).filter(AppConfig.key == key).first()
    if entry:
        entry.value = value
        entry.description = description or entry.description
    else:
        entry = AppConfig(key=key, value=value, description=description)
        db.add(entry)
    db.commit()


def register_user(db: Session):
    st.header("Register")
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create account")
    if submitted:
        if not name or not email or not password or password != confirm:
            st.error("Please fill all fields and make sure passwords match.")
            return
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            st.error("Email already registered.")
            return
        user = User(email=email, name=name, password_hash=hash_password(password), is_admin=False)
        db.add(user)
        db.commit()
        st.success("Account created. Please sign in.")


def login_user(db: Session):
    st.header("Sign In")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            st.error("Invalid email or password.")
            return
        state.jwt_token = create_access_token({"email": user.email, "is_admin": user.is_admin})
        state.user_email = user.email
        state.is_admin = user.is_admin
        st.success(f"Welcome back, {user.name or user.email}!")


def main_app(db: Session, user: User):
    st.sidebar.title("Assistant")
    page = st.sidebar.radio("Navigation", ["Assistant", "Email Composer", "Calendar", "Admin"] if user.is_admin else ["Assistant", "Email Composer", "Calendar"])

    config = get_config_entries(db)
    provider = st.sidebar.selectbox("AI Provider", ["OpenAI", "Local", "Skilit", "Groq"], index=0 if config.get("ai_provider", "OpenAI") == "OpenAI" else 1)
    model_name = st.sidebar.text_input("Model name", config.get("ai_model", "gpt-4o-mini"))
    voice_enabled = st.sidebar.checkbox("Enable voice interaction", value=True)

    if page == "Assistant":
        st.header("Voice AI Assistant")
        st.write("Ask the assistant to manage emails, draft content, check your calendar, or send messages by voice or text.")
        if voice_enabled:
            st.info("Voice support requires browser microphone permission and a configured provider.")

        voice_input = None
        if voice_enabled and st_audiorecorder is not None:
            st.write("Record your request directly in the browser:")
            audio_bytes = st_audiorecorder(key="assistant_recorder")
            if audio_bytes is not None and audio_bytes != b"":
                voice_input = audio_bytes
        else:
            audio_file = st.file_uploader("Upload a voice request (WAV/MP3)", type=["wav", "mp3", "mpeg"], help="Upload a recorded request if browser recording is unavailable.")
            if audio_file is not None:
                voice_input = audio_file.read()

        if voice_input is not None:
            transcription = transcribe_audio(voice_input, provider.lower(), model_name if provider.lower() == "openai" else "whisper-1")
            st.markdown("**Transcribed request:**")
            st.write(transcription)
            text_prompt = transcription
        else:
            text_prompt = st.text_area("Tell the assistant what you need", height=180)

        if st.button("Submit request"):
            action = text_prompt.strip()
            if action:
                response = generate_ai_response(action, provider.lower(), model_name)
                st.success(response)
                speech_bytes, mime_type = synthesize_speech(response, provider.lower(), model_name)
                if speech_bytes:
                    b64_audio = base64.b64encode(speech_bytes).decode("utf-8")
                    st.markdown("### Assistant Voice Response")
                    st.audio(speech_bytes, format=mime_type)
                    st.markdown(
                        f"[Download response audio](data:{mime_type};base64,{b64_audio})"
                    )
                else:
                    st.warning("Unable to generate speech output for this request.")
            else:
                st.warning("Enter a request or use voice input.")

    if page == "Email Composer":
        st.header("Draft and send emails")
        st.subheader("Text or voice email drafting")
        email_audio = None
        if voice_enabled and st_audiorecorder is not None:
            st.write("Record email instructions directly in the browser:")
            recorder_bytes = st_audiorecorder(key="email_recorder")
            if recorder_bytes is not None and recorder_bytes != b"":
                email_audio = recorder_bytes
        else:
            uploaded_email_audio = st.file_uploader("Upload voice instructions for email", type=["wav", "mp3", "mpeg"], help="Upload a voice note describing the email.")
            if uploaded_email_audio is not None:
                email_audio = uploaded_email_audio.read()

        if email_audio is not None:
            email_transcription = transcribe_audio(email_audio, provider.lower(), model_name if provider.lower() == "openai" else "whisper-1")
            st.markdown("**Transcribed email instructions:**")
            st.write(email_transcription)
        else:
            email_transcription = ""

        with st.form("compose_form"):
            subject = st.text_input("Subject")
            body_context = st.text_area("Context / purpose", value=email_transcription)
            tone = st.selectbox("Tone", ["Professional", "Casual", "Friendly", "Formal"])
            recipients = st.text_input("Recipients (comma-separated)")
            draft_button = st.form_submit_button("Draft email")
            send_button = st.form_submit_button("Send email")
        if draft_button:
            if not subject or not body_context:
                st.error("Provide subject and context.")
            else:
                draft = draft_email(subject, body_context, tone, provider.lower(), model_name)
                st.text_area("Drafted Email", value=draft, height=220)
                speech_bytes, mime_type = synthesize_speech(draft, provider.lower(), model_name)
                if speech_bytes:
                    st.audio(speech_bytes, format=mime_type)
        if send_button:
            if not subject or not body_context or not recipients:
                st.error("Subject, context, and recipients are required.")
            else:
                draft = draft_email(subject, body_context, tone, provider.lower(), model_name)
                google_credentials = get_google_credentials()
                if google_credentials is not None:
                    success, message = send_email_via_google(subject, draft, [email.strip() for email in recipients.split(",")], sender=config.get("smtp_sender") or recipients.split(",")[0].strip(), credentials=google_credentials)
                else:
                    success, message = send_email(subject, draft, [email.strip() for email in recipients.split(",")], sender=config.get("smtp_sender"))
                if success:
                    st.success(message)
                else:
                    st.error(message)

    if page == "Calendar":
        st.header("Calendar Summary")
        st.write("Use the assistant to view schedule summaries for the day, week, or month.")
        period = st.selectbox("Period", ["Today", "This week", "This month"])
        items = [
            {"title": "Meeting with team", "when": "10:00 AM"},
            {"title": "Client call", "when": "2:00 PM"},
            {"title": "Review drafts", "when": "4:30 PM"},
        ]
        if st.button("Summarize calendar"):
            summary = summarize_calendar(items, period, provider.lower(), model_name)
            st.text_area("Calendar Summary", value=summary, height=220)
        st.markdown("**Example events**")
        for item in items:
            st.write(f"- {item['title']} at {item['when']}")

    if page == "Admin" and user.is_admin:
        st.header("Admin Configuration")
        st.write("Configure AI, Gmail OAuth, and email settings for the assistant.")
        with st.form("admin_form"):
            ai_provider = st.selectbox("AI Provider", ["OpenAI", "Local", "Skilit", "Groq"], index=["OpenAI", "Local", "Skilit", "Groq"].index(config.get("ai_provider", "OpenAI")))
            ai_model = st.text_input("AI Model", config.get("ai_model", "gpt-4o-mini"))
            smtp_server = st.text_input("SMTP Server", config.get("smtp_server", "smtp.gmail.com"))
            smtp_port = st.text_input("SMTP Port", config.get("smtp_port", "465"))
            smtp_sender = st.text_input("SMTP Sender", config.get("smtp_sender", ""))
            submit_admin = st.form_submit_button("Save admin settings")
        if submit_admin:
            set_config_entry(db, "ai_provider", ai_provider)
            set_config_entry(db, "ai_model", ai_model)
            set_config_entry(db, "smtp_server", smtp_server)
            set_config_entry(db, "smtp_port", smtp_port)
            set_config_entry(db, "smtp_sender", smtp_sender)
            st.success("Admin settings updated.")

        st.markdown("---")
        st.subheader("Google OAuth Configuration")
        st.write("Use your Google client credentials to authorize Gmail send and Calendar access.")
        st.write("Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your environment, then authorize below.")
        if st.button("Authorize with Google"):
            authorize_google()


def main():
    init_app()
    with SessionLocal() as db:
        if "action" not in state:
            state.action = "login"
        if state.action == "login":
            login_user(db)
            if st.button("Switch to register"):
                state.action = "register"
        elif state.action == "register":
            register_user(db)
            if st.button("Switch to sign in"):
                state.action = "login"

        user = get_current_user()
        if user:
            st.sidebar.success(f"Signed in as {user.email}")
            main_app(db, user)
        else:
            st.warning("Please sign in to continue.")


if __name__ == "__main__":
    main()
