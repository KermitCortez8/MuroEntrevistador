"""Vista de preparación; las acciones de negocio pertenecen al controlador."""

import streamlit as st

from entrevistador.interview import InterviewError
from entrevistador.views import components as ui
from entrevistador.views import navigation as nav
from entrevistador.views.forms import save_field, seed


def render(controller):
    if controller.interview is not None:
        st.subheader("Tu entrevista está preparada")
        st.caption("Puedes revisar el contexto o continuar desde donde lo dejaste.")
        with st.expander("Oferta o plantilla de esta sesión", expanded=True):
            st.text(controller.interview.context)
        nav.session_progress(controller.interview)
        target = nav.EVALUATION if controller.interview.report is not None else nav.PRACTICE
        st.page_link(
            target, label="Ver evaluación" if target == nav.EVALUATION else "Continuar práctica"
        )
        return

    session = controller.session
    draft = session.preparation
    prefix = f"setup_{session.session_id}"
    offer_column, options_column = st.columns([1.45, 1], gap="large")
    with offer_column, st.container(border=True, key="offer_card"):
        ui.step("01", "El punto de partida")
        st.subheader("¿Para qué puesto te preparas?")
        st.caption(
            "Comparte la oferta o una plantilla. Las preguntas se adaptarán a sus requisitos."
        )
        source_key = seed(f"{prefix}_source", draft.source)
        source = st.radio(
            "¿Cómo agregarás la oferta?",
            ["Pegar texto", "Cargar archivo"],
            horizontal=True,
            key=source_key,
            on_change=save_field,
            args=(draft, "source", source_key),
        )
        context = draft.context if source == "Pegar texto" else draft.document_context
        if source == "Pegar texto":
            context_key = seed(f"{prefix}_context", draft.context)
            context = st.text_area(
                "Oferta laboral o plantilla de entrevista",
                height=275,
                max_chars=20_000,
                placeholder="Pega la oferta aquí…\n\nIncluye el puesto, las responsabilidades, las herramientas y la experiencia que buscan.",
                key=context_key,
                on_change=save_field,
                args=(draft, "context", context_key),
            )
        else:
            uploaded = st.file_uploader(
                "Oferta o plantilla · máximo 5 MB",
                type=["txt", "md", "pdf", "docx"],
                key=f"{prefix}_document",
            )
            if uploaded is not None:
                try:
                    context = controller.load_document(uploaded.name, uploaded.getvalue())
                except ValueError as exc:
                    context = ""
                    st.error(str(exc))
            if context:
                st.caption(f"Documento: {draft.document_name}")
                with st.expander("Texto extraído", expanded=True):
                    st.text(context)
        ui.tip(
            "Un buen contexto hace la diferencia",
            "Incluye los requisitos técnicos y las responsabilidades para practicar con preguntas más relevantes.",
        )

    with options_column, st.container(border=True, key="options_card"):
        ui.step("02", "A tu medida")
        st.subheader("Diseña tu práctica")
        st.caption("Elige el ritmo y la forma en que te sientas más cómodo.")
        left, right = st.columns(2)
        level_key = seed(f"{prefix}_level", draft.level)
        level = left.selectbox(
            "Nivel",
            ["Inicial", "Intermedio", "Avanzado"],
            key=level_key,
            on_change=save_field,
            args=(draft, "level", level_key),
        )
        language_key = seed(f"{prefix}_language", draft.language)
        language = right.selectbox(
            "Idioma de la entrevista",
            ["Español", "English"],
            key=language_key,
            on_change=save_field,
            args=(draft, "language", language_key),
        )
        limit_key = seed(f"{prefix}_limit", draft.question_limit)
        limit = st.slider(
            "Número de preguntas (incluye repreguntas)",
            1,
            15,
            key=limit_key,
            on_change=save_field,
            args=(draft, "question_limit", limit_key),
        )
        mode_key = seed(f"{prefix}_mode", session.response_mode)
        st.radio(
            "¿Cómo prefieres responder?",
            ["Audio", "Texto"],
            horizontal=True,
            key=mode_key,
            on_change=save_field,
            args=(session, "response_mode", mode_key),
            help="Puedes cambiar de modalidad en cualquier pregunta. Las preguntas siempre se pueden leer o escuchar.",
        )
        st.caption("Puedes cambiar entre voz y texto durante la entrevista.")
        st.divider()
        if not controller.available:
            st.info("Configura tu clave de Gemini en la barra lateral o en .env para comenzar.")
        if st.button(
            "Comenzar entrevista",
            type="primary",
            disabled=not controller.available,
            use_container_width=True,
        ):
            try:
                with st.spinner("Preparando tu primera pregunta…"):
                    controller.start(context, level, "es" if language == "Español" else "en", limit)
                st.switch_page(nav.PRACTICE)
            except (ValueError, InterviewError) as exc:
                st.error(str(exc))
        st.caption("Una pregunta por turno. Una evaluación al finalizar.")
    st.markdown(
        '<div class="muro-benefits"><span>Preguntas según tu oferta</span>'
        "<span>Voz o texto, tú eliges</span><span>Recomendaciones para mejorar</span></div>",
        unsafe_allow_html=True,
    )
