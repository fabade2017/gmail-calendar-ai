# gmail-calendar-ai

Gmail-Calendar Assistant built with Streamlit, MySQL, JWT auth, and AI integration.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in a `.env` file or your shell. If you want to use SQLite by default, no database connection variables are required.
   ```bash
   JWT_SECRET=supersecret
   OPENAI_API_KEY=your_openai_api_key
   SMTP_USER=your_smtp_user
   SMTP_PASSWORD=your_smtp_password
   SMTP_SENDER=you@example.com
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8501/
   ```

   Optional MySQL settings (only if you want MySQL instead of SQLite):
   ```bash
   DATABASE_URL=mysql+pymysql://root:yourpassword@127.0.0.1:3306/gmail_calendar_ai
   ```


3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Features

- JWT authentication with registration and login
- SQLite by default, with automatic database creation if needed
- Optional MySQL support via `DATABASE_URL`
- Google OAuth support for Gmail send and Calendar access
- Email drafting and sending
- AI provider selection (OpenAI, Local, Skilit, Groq)
- Admin panel for app settings
- Calendar summary assistant
- Browser voice recording and speech-to-speech response support
