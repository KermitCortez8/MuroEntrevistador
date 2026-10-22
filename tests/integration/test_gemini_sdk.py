"""Ejercita el SDK real sobre un transporte HTTP local, sin acceder a la red."""

import base64
import json

import httpx
from google import genai
from google.genai import types

from entrevistador.domain.ai import Settings
from entrevistador.integrations.gemini import AIProvider
from tests.factories import wav_bytes


def test_gemini_text_transcription_and_speech_with_real_sdk():
    requests = []
    data = wav_bytes()

    def handler(request):
        requests.append(request)
        body = json.loads(request.content)
        assert request.headers["x-goog-api-key"] == "test-key-not-real"
        if "tts-model" in request.url.path:
            parts = [
                {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(data).decode()}}
            ]
        elif "inlineData" in body["contents"][0]["parts"][0]:
            parts = [{"text": "Respuesta oral"}]
        else:
            parts = [{"text": "Pregunta"}]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}
                ],
            },
        )

    with genai.Client(
        api_key="test-key-not-real",
        vertexai=False,
        http_options=types.HttpOptions(
            httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    ) as client:
        provider = AIProvider(client, Settings(tts_model="tts-model"))
        assert (
            provider.generate(
                "Entrevista",
                [
                    {"role": "user", "content": "Oferta"},
                    {"role": "assistant", "content": "Pregunta anterior"},
                    {"role": "user", "content": "Respuesta anterior"},
                    {"role": "system", "content": "Continúa"},
                ],
            )
            == "Pregunta"
        )
        assert provider.transcribe(data, "es") == "Respuesta oral"
        assert provider.speak("Pregunta") == data

    assert all(request.url.path.endswith(":generateContent") for request in requests)
    question = json.loads(requests[0].content)
    assert question["systemInstruction"]["parts"][0]["text"] == "Entrevista\n\nContinúa"
    assert [content["role"] for content in question["contents"]] == ["user", "model", "user"]
    blob = json.loads(requests[1].content)["contents"][0]["parts"][0]["inlineData"]
    assert blob["mime_type"] == "audio/wav"
    encoded_audio = blob["data"]
    assert base64.urlsafe_b64decode(encoded_audio + "=" * (-len(encoded_audio) % 4)) == data
    speech = json.loads(requests[2].content)["generationConfig"]
    assert speech["responseModalities"] == ["AUDIO"]
    assert speech["speechConfig"]["voice_config"]["voice"] == "Kore"
