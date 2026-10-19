"""Página de historial. No necesita conexión con Gemini."""

from entrevistador.controllers.interview import InterviewController
from entrevistador.runtime import get_session
from entrevistador.views.history import render

render(InterviewController(get_session()))
