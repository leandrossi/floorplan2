from __future__ import annotations

import streamlit as st

from domain.enums import WizardScreen
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import show_image_path
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    try:
        risk_view = controller.ensure_risk_view()
    except Exception as exc:  # noqa: BLE001
        st.error(f"No pudimos construir el diagnóstico visual: {exc}")
        if st.button("Volver a la revisión", width="stretch"):
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        return
    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Estas son las áreas que necesitan protección</p>
              <p class="wizard-subtitle">
                Este diagnóstico base queda fijo. Después vas a comparar distintas soluciones para cubrirlo.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        show_image_path(risk_view.risk_overlay_path, caption="Diagnóstico base del plano")

    with side_col:
        render_side_panel(
            title="Diagnóstico",
            description=risk_view.summary_text,
            checklist=[detail for detail in risk_view.details],
            callout="El selector de nivel viene después y no modifica este mapa rojo.",
        )
        back_clicked, next_clicked = render_action_footer(back_label="Volver", next_label="Ver solución")
        if back_clicked:
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        if next_clicked:
            controller.go_to(WizardScreen.PROPOSAL)
            st.rerun()
