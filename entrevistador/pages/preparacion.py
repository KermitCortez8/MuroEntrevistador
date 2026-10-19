"""Página de preparación de la entrevista."""

from entrevistador.runtime import controller_scope
from entrevistador.views.preparation import render

with controller_scope() as controller:
    render(controller)
