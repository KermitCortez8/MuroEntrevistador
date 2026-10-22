"""Respuestas del SDK y audios de ejemplo compartidos por las pruebas."""

import wave
from io import BytesIO

from google.genai import types


def text_response(text="Respuesta", finish="STOP"):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=finish,
                content=types.Content(role="model", parts=[types.Part.from_text(text=text)]),
            )
        ]
    )


def wav_bytes(frames=8000):
    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * frames)
    return output.getvalue()


def audio_response(data, mime):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason="STOP",
                content=types.Content(
                    role="model", parts=[types.Part.from_bytes(data=data, mime_type=mime)]
                ),
            )
        ]
    )
