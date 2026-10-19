"""Página de práctica con respuestas por audio o texto."""

from entrevistador.runtime import controller_scope
from entrevistador.views.practice import render

with controller_scope() as controller:
    render(controller)
