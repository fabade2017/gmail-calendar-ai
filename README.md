# gmail-calendar-ai

Gmail-Calendar Assistant built with Streamlit, MySQL, JWT auth, and AI integration.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in a `.env` file or your shell:
   ```bash
   DB_USER=root
   DB_PASSWORD=yourpassword
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=gmail_calendar_ai
   JWT_SECRET=supersecret
   OPENAI_API_KEY=your_openai_api_key
   SMTP_USER=your_smtp_user
   SMTP_PASSWORD=your_smtp_password
   SMTP_SENDER=you@example.com
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Features

- JWT authentication with registration and login
- Email drafting and sending
- AI provider selection (OpenAI, Local, Skilit, Groq)
- Admin panel for app settings
- Calendar summary assistant
- Voice interaction placeholder support
