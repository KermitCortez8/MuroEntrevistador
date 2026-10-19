"""Coordina los casos de uso sin importar Streamlit ni dibujar la interfaz."""

from uuid import uuid4

from entrevistador.documents import extract_document
from entrevistador.interview import AIProvider, Interview, InterviewError, Settings
from entrevistador.session import AnswerDraft, InterviewSession, PreparationDraft


class InterviewController:
    def __init__(
        self,
        session: InterviewSession,
        provider: AIProvider | None = None,
        settings: Settings | None = None,
    ):
        self.session = session
        self.provider = provider
        self.settings = settings or session.settings or Settings()

    @property
    def available(self) -> bool:
        return self.provider is not None

    @property
    def interview(self) -> Interview | None:
        return self.session.interview

    def _provider(self) -> AIProvider:
        if self.provider is None:
            raise InterviewError("Agrega tu clave de Gemini para continuar esta entrevista.")
        return self.provider

    def _interview(self) -> Interview:
        if self.interview is None:
            raise InterviewError("Primero prepara e inicia una entrevista.")
        return self.interview

    def start(self, context: str, level: str, language: str, question_limit: int) -> None:
        if self.interview is not None:
            raise InterviewError(
                "Ya tienes una entrevista. Usa Nueva entrevista para comenzar otra."
            )
        candidate = Interview(
            context, level=level, language=language, question_limit=question_limit
        )
        candidate.start(self._provider())
        self.session.interview = candidate
        self.session.settings = self.settings
        self.session.session_id = uuid4().hex
        self.session.draft = AnswerDraft()

    def load_document(self, name: str, data: bytes) -> str:
        context = extract_document(name, data)
        self.session.preparation.document_name = name
        self.session.preparation.document_context = context
        return context

    def transcribe(self, data: bytes | None = None) -> str:
        interview = self._interview()
        if data is not None:
            self.session.draft.recording = data
        transcript = self._provider().transcribe(
            self.session.draft.recording or b"",
            interview.language,
        )
        self.session.draft.transcript = transcript
        return transcript

    def speak(self) -> bytes:
        interview = self._interview()
        if interview.report is not None:
            raise InterviewError("La entrevista ya terminó.")
        if self.session.draft.voice is None:
            self.session.draft.voice = self._provider().speak(interview.messages[-1]["content"])
        return self.session.draft.voice

    def answer(self, text: str) -> None:
        # Conserva el borrador y el turno si falla la solicitud al proveedor.
        self._interview().answer(self._provider(), text)
        self.session.draft = AnswerDraft()

    def finish(self) -> None:
        self._interview().finish(self._provider())
        self.session.draft = AnswerDraft()

    def reset(self) -> None:
        self.session.interview = None
        self.session.settings = None
        self.session.session_id = uuid4().hex
        self.session.draft = AnswerDraft()
        self.session.preparation = PreparationDraft()
        self.session.working_models.clear()
