"""Página de evaluación. No necesita conexión con Gemini."""

from entrevistador.controllers.interview import InterviewController
from entrevistador.runtime import get_session
from entrevistador.views.evaluation import render

render(InterviewController(get_session()))
