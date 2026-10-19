"""Pregunta actual y respuesta por audio o texto."""

import streamlit as st

from entrevistador.interview import InterviewError
from entrevistador.views import components as ui
from entrevistador.views import navigation as nav
from entrevistador.views.forms import save_field, save_recording, seed


def render(controller):
    if not nav.require_interview(controller):
        return
    interview = controller.interview
    nav.session_progress(interview)
    if interview.report is not None:
        st.success("Práctica completada. Tu evaluación ya está disponible.")
        st.page_link(nav.EVALUATION, label="Ver mi evaluación", icon="✨")
        return
    if not controller.available:
        st.info("Agrega tu clave de Gemini para continuar esta entrevista.")
    question_column, answer_column = st.columns([1, 1.15], gap="large")
    with question_column, st.container(border=True, key="question_card"):
        ui.step("01", "Escucha o lee")
        st.caption(f"PREGUNTA {interview.answered + 1} DE {interview.question_limit}")
        st.markdown(interview.messages[-1]["content"])
        if st.button("🔊 Escuchar pregunta", disabled=not controller.available):
            try:
                with st.spinner("Generando voz…"):
                    controller.speak()
            except InterviewError as exc:
                st.error(str(exc))
        if controller.session.draft.voice is not None:
            st.audio(controller.session.draft.voice, format="audio/wav")
        st.caption("La voz del entrevistador es generada por IA.")
        ui.tip(
            "Haz visible tu razonamiento",
            "Describe la situación, explica tu decisión y cuenta qué resultado esperabas o conseguiste.",
        )

    with answer_column, st.container(border=True, key="answer_card"):
        render_answer(controller)
    st.divider()
    if st.button(
        "Terminar y evaluar lo respondido",
        disabled=not interview.answered or not controller.available,
        help="La respuesta pendiente de envío no se incluirá en la evaluación.",
    ):
        try:
            with st.spinner("Preparando tu evaluación…"):
                controller.finish()
            st.switch_page(nav.EVALUATION)
        except InterviewError as exc:
            st.error(str(exc))


def render_answer(controller):
    session = controller.session
    draft = session.draft
    ui.step("02", "Dale forma a tu respuesta")
    st.subheader("Tu respuesta")
    mode_key = seed(f"mode_{session.turn}", session.response_mode)
    mode = st.radio(
        "¿Cómo prefieres responder?",
        ["Audio", "Texto"],
        horizontal=True,
        key=mode_key,
        on_change=save_field,
        args=(session, "response_mode", mode_key),
        help="Puedes cambiar de modalidad en cualquier pregunta. Las preguntas siempre se pueden leer o escuchar.",
    )
    if mode == "Audio":
        st.caption(
            "Graba hasta 14 MB, detén la grabación y pulsa Transcribir. Puedes corregir el texto antes de enviarlo."
        )
        audio_key = f"audio_{session.turn}"
        audio = st.audio_input(
            "Graba tu respuesta",
            key=audio_key,
            sample_rate=16000,
            on_change=save_recording,
            args=(draft, audio_key),
        )
        if audio is not None:
            draft.recording = audio.getvalue()
        elif draft.recording is not None:
            st.caption("Tu grabación anterior sigue disponible para transcribir.")
            st.audio(draft.recording, format="audio/wav")
        if st.button(
            "Transcribir respuesta", disabled=draft.recording is None or not controller.available
        ):
            try:
                with st.spinner("Transcribiendo tu respuesta…"):
                    controller.transcribe()
                # Una nueva transcripción reemplaza el texto editable de esta modalidad.
                st.session_state[f"transcript_{session.turn}"] = draft.transcript
            except InterviewError as exc:
                st.error(str(exc))
    else:
        st.caption("Escribe tu respuesta y envíala cuando estés listo. No necesitas grabar audio.")

    if mode == "Texto" or draft.transcript is not None:
        field = "written" if mode == "Texto" else "transcript"
        draft_key = seed(f"{field}_{session.turn}", getattr(draft, field) or "")
        answer = st.text_area(
            "Escribe tu respuesta" if mode == "Texto" else "Revisa tu transcripción",
            key=draft_key,
            max_chars=12_000,
            height=200,
            placeholder="Explica tu razonamiento y acompáñalo con un ejemplo…",
            on_change=save_field,
            args=(draft, field, draft_key),
        )
        if st.button(
            "Enviar respuesta",
            type="primary",
            disabled=not controller.available,
            use_container_width=True,
        ):
            try:
                with st.spinner("Evaluando tu respuesta…"):
                    controller.answer(answer)
                if controller.interview.report is not None:
                    st.switch_page(nav.EVALUATION)
                st.rerun()
            except InterviewError as exc:
                st.error(str(exc))
