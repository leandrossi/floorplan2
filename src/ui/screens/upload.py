from __future__ import annotations

from io import BytesIO

import streamlit as st
from PIL import Image, UnidentifiedImageError

from ui.components.action_footer import render_action_footer
from ui.components.side_panel import render_side_panel

MAX_UPLOAD_MB = 15
MAX_IMAGE_WIDTH = 6000
MAX_IMAGE_HEIGHT = 6000


def render(controller) -> None:
    state = controller.state()
    canvas_col, side_col = st.columns([3, 1.25], gap="large")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Subí el plano de tu vivienda</p>
              <p class="wizard-subtitle">
                Usá una imagen clara del plano. Si algo no se interpreta bien, después lo vas a poder corregir.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Plano",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        if state.last_error:
            st.error(state.last_error)

        if uploaded is not None:
            raw = uploaded.getvalue()
            size_mb = len(raw) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_MB:
                st.error(f"El archivo pesa {size_mb:.1f} MB y supera el máximo de {MAX_UPLOAD_MB} MB.")
                return
            try:
                with Image.open(BytesIO(raw)) as image:
                    width, height = image.size
                    preview = image.copy()
            except UnidentifiedImageError:
                st.error("No pudimos leer esa imagen. Probá con PNG, JPG o WebP.")
                return

            if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                st.error(
                    f"La imagen es demasiado grande ({width}x{height}). "
                    f"Máximo permitido: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}."
                )
                return

            st.image(preview, caption=f"{uploaded.name} · {width}x{height}px", width="stretch")
            _, next_clicked = render_action_footer(next_label="Analizar plano")
            if next_clicked:
                controller.save_upload(uploaded.name, raw)
                st.rerun()
        else:
            st.info("Arrastrá o seleccioná una imagen para empezar.")

    with side_col:
        render_side_panel(
            title="Qué necesitás",
            description="Buscamos que subir el plano sea lo más simple posible.",
            checklist=[
                "Plano completo y legible",
                "Imagen sin recortes fuertes",
                "Después vas a poder corregir muros, puertas y ventanas",
            ],
            callout="Todavía no tomes decisiones técnicas. Primero te mostramos cómo interpretamos la vivienda.",
        )
