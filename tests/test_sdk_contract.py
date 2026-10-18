"""Ejercita el SDK real sobre un transporte HTTP local, sin acceder a la red."""

import json

import httpx
from openai import OpenAI

from entrevistador.interview import AIProvider, Settings
from tests.test_interview import wav_bytes


def test_responses_transcription_and_speech_with_real_sdk():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/v1/responses":
            return httpx.Response(
                200,
                json={
                    "id": "resp_test",
                    "object": "response",
                    "created_at": 1,
                    "status": "completed",
                    "model": "gpt-4.1-mini",
                    "output": [
                        {
                            "id": "msg_test",
                            "type": "message",
                            "status": "completed",
                            "role": "assistant",
                            "content": [
                                {"type": "output_text", "text": "Pregunta", "annotations": []}
                            ],
                        }
                    ],
                },
            )
        if request.url.path == "/v1/audio/transcriptions":
            return httpx.Response(200, json={"text": "Respuesta oral"})
        if request.url.path == "/v1/audio/speech":
            return httpx.Response(200, content=b"mp3", headers={"Content-Type": "audio/mpeg"})
        raise AssertionError(f"Unexpected request: {request.url}")

    with OpenAI(
        api_key="test-key-not-real",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        provider = AIProvider(client, Settings())
        assert (
            provider.generate("Entrevista", [{"role": "user", "content": "Oferta"}]) == "Pregunta"
        )
        assert provider.transcribe(wav_bytes(), "es") == "Respuesta oral"
        assert provider.speak("Pregunta") == b"mp3"

    assert json.loads(requests[0].content)["store"] is False
    assert "multipart/form-data" in requests[1].headers["content-type"]
    assert b"respuesta.wav" in requests[1].content
    assert json.loads(requests[2].content)["response_format"] == "mp3"
