import os
from typing import Optional

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None


def load_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if not api_key:
        return None
    if openai:
        openai.api_key = api_key
    return api_key


def generate_ai_response(prompt: str, provider: str, model_name: str, system_prompt: str = "") -> str:
    provider = provider.lower()
    if provider == "openai" and openai:
        api_key = load_openai_api_key()
        if not api_key:
            return "OpenAI API key is not configured. Set OPENAI_API_KEY in your environment."

        if model_name.startswith("gpt"):
            try:
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful email and calendar assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                return f"OpenAI request failed: {exc}"
        try:
            response = openai.Completion.create(model=model_name, prompt=prompt, max_tokens=450)
            return response.choices[0].text.strip()
        except Exception as exc:
            return f"OpenAI request failed: {exc}"

    if provider == "local":
        return f"[Local model placeholder] Received prompt: {prompt[:240]}"

    if provider == "skilit":
        return f"[Skilit model placeholder] Received prompt: {prompt[:240]}"

    if provider == "groq":
        return f"[Groq model placeholder] Received prompt: {prompt[:240]}"

    return "No valid AI provider selected. Please configure the assistant provider in Admin."


def draft_email(subject: str, context: str, tone: str, provider: str, model_name: str) -> str:
    prompt = (
        f"You are an email assistant. Draft a professional email with the subject '{subject}' using the following context: {context}. "
        f"Use a {tone} tone."
    )
    return generate_ai_response(prompt=prompt, provider=provider, model_name=model_name)


def summarize_calendar(items: list[dict], date_range: str, provider: str, model_name: str) -> str:
    context = "\n".join([f"- {item.get('title')} at {item.get('when')}" for item in items])
    prompt = f"Summarize the following calendar plan for {date_range}:\n{context}"
    return generate_ai_response(prompt=prompt, provider=provider, model_name=model_name)
