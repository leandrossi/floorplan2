from __future__ import annotations

from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
FEEDBACK_KEY = "step1_upload_feedback"

def _validate_uploaded_plan(uploaded_file) -> tuple[bool, str | None, bytes | None, bool]:
    if uploaded_file is None:
        return False, "Subí un archivo para continuar.", None, False

    filename = (uploaded_file.name or "").strip()
    extension = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return False, "Este formato no es compatible. Usá PDF, JPG o PNG.", None, False

    raw_bytes = uploaded_file.getvalue()
    if not raw_bytes:
        return False, "No pudimos leer bien este archivo. Probá con una versión más clara del plano.", None, False

    is_image = extension in {"png", "jpg", "jpeg"}
    if is_image:
        try:
            with Image.open(BytesIO(raw_bytes)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            return False, "No pudimos leer bien este archivo. Probá con una versión más clara del plano.", None, False

    return True, None, raw_bytes, is_image


def render(controller) -> None:
    st.markdown(
        """
        <style>
        .wizard-step-context {
            margin: 0.1rem 0 0.95rem 0;
            color: #64748B;
            font-size: 0.9rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .wizard-main-shell {
            max-width: 860px;
            margin: 0 auto;
        }
        .wizard-pill-row {
            display: flex;
            gap: 0.45rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 0.9rem;
        }
        .wizard-pill {
            background: #EEF3FF;
            border: 1px solid #D9E2F1;
            color: #1E3A8A;
            border-radius: 999px;
            padding: 0.28rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .wizard-trust-note {
            margin-top: 1rem;
            text-align: center;
            color: #64748B;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<p class="wizard-step-context">Paso 1 de 8 · Cargar plano</p>', unsafe_allow_html=True)

    feedback = st.session_state.pop(FEEDBACK_KEY, None)
    if feedback == "success":
        st.success("Plano cargado correctamente. Ya podés continuar.")

    st.markdown('<div class="wizard-main-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="wizard-card">
          <p class="wizard-title">Subí el plano de tu casa</p>
          <p class="wizard-subtitle">
            Con ese archivo vamos a analizar los accesos y prepararte una propuesta clara de protección, paso a paso.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("wizard_step1_upload_form", clear_on_submit=False):
        uploaded_file = st.file_uploader(
            "Cargar plano",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        st.caption(
            "Aceptamos archivos PDF, JPG y PNG. Idealmente, que el plano se vea completo y con buena claridad."
        )

        is_valid, validation_message, raw_bytes, is_image = _validate_uploaded_plan(uploaded_file)

        if uploaded_file is not None:
            if is_valid:
                st.success("Plano cargado correctamente. Ya podés continuar.")
            elif validation_message:
                st.error(validation_message)

        if uploaded_file is not None and is_valid and raw_bytes is not None:
            if is_image:
                st.image(raw_bytes, caption=uploaded_file.name, width="stretch")
            else:
                st.info(f"Archivo PDF cargado: {uploaded_file.name}")

        submitted = st.form_submit_button("Continuar", type="primary", use_container_width=True)
        if submitted:
            if not is_valid or uploaded_file is None or raw_bytes is None:
                st.error(validation_message or "Subí un archivo para continuar.")
            else:
                st.session_state["uploaded_plan"] = {
                    "name": uploaded_file.name,
                    "bytes": raw_bytes,
                    "mime": uploaded_file.type,
                }
                st.session_state["current_step"] = 1
                st.session_state[FEEDBACK_KEY] = "success"
                controller.save_upload(uploaded_file.name, raw_bytes)
                st.rerun()

    st.markdown(
        """
        <div class="wizard-pill-row">
          <span class="wizard-pill">Simple de usar</span>
          <span class="wizard-pill">Análisis guiado</span>
          <span class="wizard-pill">Resultado claro</span>
        </div>
        <p class="wizard-trust-note">
          No necesitás conocimientos técnicos. Nosotros interpretamos el plano y te guiamos en cada paso.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
