from django.urls import path

from entrevistador.views import actions, media, pages

urlpatterns = [
    path("", pages.page, {"section": "preparacion"}, name="preparacion"),
    path("practica/", pages.page, {"section": "practica"}, name="practica"),
    path("historial/", pages.page, {"section": "historial"}, name="historial"),
    path("evaluacion/", pages.page, {"section": "evaluacion"}, name="evaluacion"),
    path("accion/", actions.action, name="accion"),
    path("borrador/", actions.draft, name="borrador"),
    path("audio/<str:kind>/", media.audio, name="audio"),
    path("descargar/<str:kind>/", media.download, name="descargar"),
    path("health/", pages.health, name="health"),
]
