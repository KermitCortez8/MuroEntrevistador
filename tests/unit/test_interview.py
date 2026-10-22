"""Reglas de preguntas, respuestas y evaluación, sin llamadas a Gemini."""

from unittest.mock import MagicMock

import pytest

from entrevistador.domain.ai import InterviewError, InterviewProvider
from entrevistador.domain.interview import Interview

OFFER = "Ingeniero mecánico con experiencia en termodinámica y diseño de equipos industriales."


@pytest.fixture
def provider():
    return MagicMock(spec=InterviewProvider)


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
