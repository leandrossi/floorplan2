from __future__ import annotations

import streamlit as st

from domain.enums import WizardScreen
from ui.components.action_footer import render_action_footer
from ui.components.kit_cards import render_kit_cards
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    kit_view = controller.get_kit_view()
    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")

    with canvas_col:
        st.markdown(
            f"""
            <div class="wizard-card">
              <p class="wizard-title">Kit recomendado{f" · {kit_view.level_label}" if kit_view.level_label else ""}</p>
              <p class="wizard-subtitle">{kit_view.hero_summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_kit_cards(kit_view.items)

    with side_col:
        render_side_panel(
            title="Cómo leer este kit",
            description="Traducimos la propuesta técnica a una lista simple de componentes.",
            checklist=[f"{item['name']} · {item['quantity']}" for item in kit_view.items],
        )
        back_clicked, next_clicked = render_action_footer(
            back_label="Volver a la solución",
            next_label="Empezar otro plano",
        )
        if back_clicked:
            controller.go_to(WizardScreen.PROPOSAL)
            st.rerun()
        if next_clicked:
            controller.reset_all()
            st.rerun()
