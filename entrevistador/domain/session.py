"""Estado de una sesión, independiente de la interfaz web."""

from dataclasses import dataclass, field
from uuid import uuid4

from entrevistador.domain.ai import Settings
from entrevistador.domain.interview import Interview


@dataclass
class AnswerDraft:
    written: str = ""
    transcript: str | None = None
    recording: bytes | None = None
    voice: bytes | None = None


@dataclass
class PreparationDraft:
    context: str = ""
    level: str = "Intermedio"
    language: str = "Español"
    question_limit: int = 5
    document_name: str = ""
    document_context: str = ""


@dataclass
class InterviewSession:
    interview: Interview | None = None
    settings: Settings | None = None
    session_id: str = field(default_factory=lambda: uuid4().hex)
    response_mode: str = "Texto"
    draft: AnswerDraft = field(default_factory=AnswerDraft)
    preparation: PreparationDraft = field(default_factory=PreparationDraft)
    working_models: dict[str, str] = field(default_factory=dict)

    @property
    def turn(self) -> str:
        answered = self.interview.answered if self.interview else 0
        return f"{self.session_id}_{answered}"
