"""Presentación de Muro. Los estilos se cargan localmente, sin recursos externos."""

from html import escape
from pathlib import Path

import streamlit as st

STYLES = Path(__file__).resolve().parents[2] / "assets" / "app.css"


def apply_design():
    st.markdown(f"<style>{STYLES.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def header(interview, stage):
    st.markdown(
        f'<div class="muro-topbar"><div class="muro-breadcrumb">'
        f"Muro &nbsp; / &nbsp; <strong>{stage}</strong></div>"
        '<span class="muro-badge">Tu espacio de práctica</span></div>',
        unsafe_allow_html=True,
    )
    if interview is None and stage == "Preparación":
        bars = "".join(
            f'<i style="height:{height}px"></i>'
            for height in (12, 24, 38, 25, 55, 72, 48, 32, 58, 43, 26, 15)
        )
        st.markdown(
            '<div class="muro-hero"><div><div class="muro-eyebrow">'
            "Un poco de práctica. Mucha más confianza.</div>"
            "<h1>Tu talento merece<br>una <em>buena entrevista.</em></h1>"
            "<p>Convierte una oferta laboral en tu próxima sesión de práctica. "
            "Responde con voz o texto y recibe una guía para seguir mejorando.</p></div>"
            '<div class="muro-hero-note" aria-hidden="true">'
            f'<div class="muro-signal">{bars}</div>'
            "<strong>Practica. Ajusta. Avanza.</strong>"
            "<span>Una pregunta a la vez.</span></div></div>",
            unsafe_allow_html=True,
        )
    else:
        complete = interview is not None and interview.report is not None
        titles = {
            "Preparación": (
                "Tu contexto, siempre a mano.",
                "El punto de partida",
                "Revisa la oferta y continúa tu sesión cuando estés listo.",
            ),
            "Práctica": (
                "Cada respuesta es un paso." if complete else "Una pregunta a la vez.",
                "Práctica completada" if complete else "Este es tu momento de practicar",
                "Tómate tu tiempo. Explica tus ideas y apóyate en tu experiencia.",
            ),
            "Historial": (
                "Tu recorrido, en tus palabras.",
                "La conversación completa",
                "Revisa tus respuestas, retoma la práctica o descarga tu entrevista.",
            ),
            "Evaluación": (
                "Una mirada para seguir creciendo.",
                "Tus próximos pasos",
                "Reconoce tus fortalezas y elige qué practicar después.",
            ),
        }
        title, eyebrow, subtitle = titles[stage]
        st.markdown(
            '<div class="muro-hero compact"><div><div class="muro-eyebrow">'
            f"{eyebrow}"
            f"</div><h1>{title}</h1><p>{subtitle}</p></div></div>",
            unsafe_allow_html=True,
        )


def sidebar_brand():
    st.markdown(
        '<div class="muro-brand"><div class="muro-monogram">m</div>'
        '<div><div class="muro-wordmark">Muro</div><small>ENTREVISTA CON CONFIANZA</small></div></div>'
        '<div class="muro-sidebar-label">Tu recorrido</div>',
        unsafe_allow_html=True,
    )


def sidebar_note():
    st.markdown(
        '<div class="muro-sidebar-note"><strong>La confianza se practica.</strong>'
        "<p>No necesitas una respuesta perfecta. Este es el lugar para encontrarla.</p></div>",
        unsafe_allow_html=True,
    )


def step(number, label):
    st.markdown(
        f'<div class="muro-step"><b>{escape(number)}</b><span>{escape(label)}</span></div>',
        unsafe_allow_html=True,
    )


def tip(title, content):
    st.markdown(
        f'<div class="muro-tip"><strong>{escape(title)}</strong><p>{escape(content)}</p></div>',
        unsafe_allow_html=True,
    )


def empty_evaluation():
    st.markdown(
        '<div class="muro-empty"><span class="empty-symbol" aria-hidden="true">✧</span>'
        "<h3>Tu progreso merece una mirada.</h3>"
        "<p>Al terminar la entrevista encontrarás aquí tus fortalezas, "
        "ejemplos para mejorar tus respuestas y tus próximos pasos de práctica.</p></div>",
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(
        '<div class="muro-footer"><span>Muro · Un espacio para crecer profesionalmente.</span>'
        "<span>Práctica personal con IA</span></div>",
        unsafe_allow_html=True,
    )
