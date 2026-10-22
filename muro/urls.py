"""Punto de entrada de las rutas del proyecto."""

from django.urls import include, path

urlpatterns = [path("", include("entrevistador.urls"))]
