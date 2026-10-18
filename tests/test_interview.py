import wave
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, AuthenticationError, RateLimitError

from entrevistador.interview import AIProvider, Interview, InterviewError, Settings

OFFER = "Ingeniero mecánico con experiencia en termodinámica y diseño de equipos industriales."


@pytest.fixture
def provider():
    return MagicMock(spec=AIProvider)


def test_questions_keep_context_history_and_finish_at_limit(provider):
    provider.generate.side_effect = ["Pregunta uno", "Repregunta dos", "Informe final"]
    interview = Interview(OFFER, question_limit=2)
    interview.start(provider)
    interview.answer(provider, "  Mi primera respuesta  ")
    second_request = provider.generate.call_args.args
    assert "termodin" in second_request[1][0]["content"]
    assert second_request[1][1:4] == [
        {"role": "assistant", "content": "Pregunta uno"},
        {"role": "user", "content": "Mi primera respuesta"},
    ] + [second_request[1][-1]]
    assert "pregunta 2 de 2" in second_request[1][-1]["content"]
    interview.answer(provider, "Mi segunda respuesta")
    assert interview.answered == 2
    assert interview.report == "Informe final"
    assert len(interview.messages) == 4
    with pytest.raises(InterviewError):
        interview.answer(provider, "Respuesta duplicada")
    interview.finish(provider)
    assert provider.generate.call_count == 3


def test_failed_question_keeps_state_and_retry_does_not_duplicate(provider):
    provider.generate.side_effect = ["Pregunta", InterviewError("Sin conexión"), "Siguiente"]
    interview = Interview(OFFER)
    interview.start(provider)
    before = interview.messages.copy()
    with pytest.raises(InterviewError):
        interview.answer(provider, "Mi respuesta")
    assert interview.messages == before
    assert interview.answered == 0
    interview.answer(provider, "Mi respuesta")
    assert interview.answered == 1


def test_failed_report_can_be_retried(provider):
    provider.generate.side_effect = ["Pregunta", InterviewError("Error"), "Informe"]
    interview = Interview(OFFER, question_limit=1)
    interview.start(provider)
    with pytest.raises(InterviewError):
        interview.answer(provider, "Respuesta")
    assert interview.report is None
    assert interview.answered == 0
    interview.answer(provider, "Respuesta")
    assert interview.report == "Informe"
    assert interview.answered == 1


def test_early_report_excludes_unanswered_question(provider):
    provider.generate.side_effect = ["Pregunta", "Pregunta sin responder", "Informe"]
    interview = Interview(OFFER)
    interview.start(provider)
    with pytest.raises(InterviewError):
        interview.finish(provider)
    interview.answer(provider, "Respuesta")
    interview.finish(provider)
    assert "Pregunta sin responder" not in str(provider.generate.call_args.args[1])
    exported = interview.export_markdown()
    assert OFFER in exported
    assert "Respuesta" in exported
    assert "Informe" in exported
    assert interview.report == "Informe"


@pytest.mark.parametrize("text", ["", "   ", "a" * 12_001])
def test_invalid_answer_does_not_call_api(provider, text):
    provider.generate.return_value = "Pregunta"
    interview = Interview(OFFER)
    interview.start(provider)
    provider.reset_mock()
    with pytest.raises(InterviewError):
        interview.answer(provider, text)
    provider.generate.assert_not_called()


def test_start_error_does_not_leave_partial_interview(provider):
    provider.generate.side_effect = InterviewError("Error")
    interview = Interview(OFFER)
    with pytest.raises(InterviewError):
        interview.start(provider)
    assert interview.messages == []


@pytest.mark.parametrize(
    "kwargs", [{"question_limit": 0}, {"question_limit": 16}, {"language": "xx"}, {"level": "x"}]
)
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        Interview(OFFER, **kwargs)


def test_provider_uses_responses_without_server_storage():
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(
        status="completed", output_text=" Pregunta "
    )
    provider = AIProvider(client, Settings(chat_model="configured-model"))
    messages = [{"role": "user", "content": "Oferta"}]
    assert provider.generate("Instrucciones", messages) == "Pregunta"
    request = client.responses.create.call_args.kwargs
    assert request["store"] is False
    assert request["input"] == messages
    assert request["model"] == "configured-model"


@pytest.mark.parametrize(("status", "text"), [("incomplete", "Parcial"), ("completed", " ")])
def test_provider_rejects_incomplete_output(status, text):
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(status=status, output_text=text)
    with pytest.raises(InterviewError, match="completa"):
        AIProvider(client, Settings()).generate("Instructions", [])


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")), "conectar"),
        (
            AuthenticationError(
                "secret",
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://api.openai.com")
                ),
                body=None,
            ),
            "clave",
        ),
        (
            RateLimitError(
                "secret",
                response=httpx.Response(
                    429, request=httpx.Request("POST", "https://api.openai.com")
                ),
                body=None,
            ),
            "límite",
        ),
    ],
)
def test_api_errors_are_actionable_without_exposing_raw_details(error, message):
    client = MagicMock()
    client.responses.create.side_effect = error
    with pytest.raises(InterviewError, match=message) as caught:
        AIProvider(client, Settings()).generate("Instructions", [])
    assert "secret" not in str(caught.value)


def wav_bytes(frames=8000):
    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * frames)
    return output.getvalue()


def test_transcription_sends_wav_and_language():
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text=" Mi respuesta ")
    provider = AIProvider(client, Settings())
    data = wav_bytes()
    assert provider.transcribe(data, "es") == "Mi respuesta"
    request = client.audio.transcriptions.create.call_args.kwargs
    assert request["file"] == ("respuesta.wav", data, "audio/wav")
    assert request["language"] == "es"


@pytest.mark.parametrize(
    "data", [b"", b"not wav", wav_bytes(frames=2), b"x" * (24 * 1024 * 1024 + 1)]
)
def test_invalid_recordings_never_call_api(data):
    client = MagicMock()
    with pytest.raises(InterviewError):
        AIProvider(client, Settings()).transcribe(data, "es")
    client.audio.transcriptions.create.assert_not_called()


def test_empty_transcription_and_connection_error():
    client = MagicMock()
    provider = AIProvider(client, Settings())
    client.audio.transcriptions.create.return_value = SimpleNamespace(text=" ")
    with pytest.raises(InterviewError, match="voz"):
        provider.transcribe(wav_bytes(), "es")
    client.audio.transcriptions.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "https://api.openai.com"),
    )
    with pytest.raises(InterviewError, match="conectar"):
        provider.transcribe(wav_bytes(), "en")


def test_speech_returns_audio_in_memory():
    client = MagicMock()
    stream = client.audio.speech.with_streaming_response.create.return_value
    stream.__enter__.return_value.read.return_value = b"mp3"
    assert AIProvider(client, Settings()).speak("Pregunta") == b"mp3"
    assert (
        client.audio.speech.with_streaming_response.create.call_args.kwargs["input"] == "Pregunta"
    )
