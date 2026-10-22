"""Contrato de IA y configuración compartida de una entrevista."""

from dataclasses import dataclass
from typing import Protocol


class InterviewError(Exception):
    """Error recuperable que puede mostrarse al usuario."""


@dataclass(frozen=True)
class Settings:
    chat_model: str = "gemini-3.8-flash"
    transcription_model: str = "gemini-3.8-flash"
    tts_model: str = "gemini-3.8-flash-tts"
    chat_fallback_models: tuple[str, ...] = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite")
    transcription_fallback_models: tuple[str, ...] = (
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    )
    tts_fallback_models: tuple[str, ...] = ("gemini-3.8-flash-lite-tts",)


class InterviewProvider(Protocol):
    """Operaciones que necesita la entrevista, independientemente del proveedor."""

    def generate(self, instructions: str, messages: list[dict[str, str]]) -> str: ...
    def transcribe(self, data: bytes, language: str) -> str: ...
    def speak(self, text: str) -> bytes: ...
