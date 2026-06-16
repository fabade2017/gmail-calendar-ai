import base64
import io
import os

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

try:
    from gtts import gTTS
except ImportError:  # pragma: no cover
    gTTS = None


def load_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if not api_key:
        return None
    if openai:
        openai.api_key = api_key
    return api_key


def audio_bytes_from_base64(content: str) -> bytes:
    return base64.b64decode(content)


def transcribe_audio(audio_bytes: bytes, provider: str, model_name: str = "whisper-1") -> str:
    provider = provider.lower()
    if provider == "openai" and openai:
        api_key = load_openai_api_key()
        if not api_key:
            return "OpenAI API key is not configured. Set OPENAI_API_KEY in your environment."
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice.wav"
            if hasattr(openai.Audio, "transcribe"):
                transcript = openai.Audio.transcribe(model=model_name, file=audio_file)
            elif hasattr(openai.Audio, "transcriptions"):
                transcript = openai.Audio.transcriptions.create(file=audio_file, model=model_name)
            else:
                return "OpenAI transcribe API is not available in this library version."
            return getattr(transcript, "text", transcript.get("text", ""))
        except Exception as exc:
            return f"Speech transcription failed: {exc}"

    return "Speech transcription is not implemented for this provider."


def synthesize_speech(text: str, provider: str, model_name: str = "gpt-4o-mini") -> tuple[bytes, str]:
    provider = provider.lower()
    if provider == "openai" and openai:
        api_key = load_openai_api_key()
        if api_key:
            try:
                audio_resp = None
                if hasattr(openai.audio, "speech") and hasattr(openai.audio.speech, "create"):
                    audio_resp = openai.audio.speech.create(model=model_name, voice="alloy", input=text)
                elif hasattr(openai, "Audio") and hasattr(openai.Audio, "speech"):
                    audio_resp = openai.Audio.speech.create(model=model_name, voice="alloy", input=text)

                if isinstance(audio_resp, bytes):
                    return audio_resp, "audio/mp3"
                if hasattr(audio_resp, "content"):
                    return audio_resp.content, "audio/mp3"
                if isinstance(audio_resp, dict) and audio_resp.get("audio"):
                    return audio_resp["audio"], "audio/mp3"
            except Exception:
                pass

    if gTTS:
        try:
            output = io.BytesIO()
            gTTS(text=text, lang="en").write_to_fp(output)
            output.seek(0)
            return output.read(), "audio/mp3"
        except Exception as exc:
            return b"", f"TTS generation failed: {exc}"

    return b"", "Text-to-speech provider unavailable. Install gTTS for local TTS."