"""Configuración desde el entorno y cierre garantizado del cliente de Gemini."""

import os
from contextlib import contextmanager

from google import genai
from google.genai import types

from entrevistador import interview as domain


def settings_from_env() -> domain.Settings:
    return domain.Settings(
        chat_model=os.getenv("GEMINI_CHAT_MODEL") or domain.Settings.chat_model,
        transcription_model=os.getenv("GEMINI_TRANSCRIPTION_MODEL")
        or domain.Settings.transcription_model,
        tts_model=os.getenv("GEMINI_TTS_MODEL") or domain.Settings.tts_model,
    )


def resolve_api_key(override: str = "") -> str:
    return override or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")


@contextmanager
def provider_scope(api_key: str, settings: domain.Settings, working_models: dict[str, str]):
    if not api_key:
        yield None
        return
    client = genai.Client(
        api_key=api_key,
        vertexai=False,
        http_options=types.HttpOptions(
            timeout=20_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    try:
        yield domain.AIProvider(client, settings, working_models)
    finally:
        client.close()
