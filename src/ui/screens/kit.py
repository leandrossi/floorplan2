from __future__ import annotations

import streamlit as st

from domain.enums import WizardScreen
from ui.components.action_footer import render_action_footer
from ui.components.kit_cards import render_kit_cards
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    kit_view = controller.get_kit_view()
    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 7 · Final kit</p>
          <h1 class="wizard-page-title">Your protection kit is ready.</h1>
          <p class="wizard-page-subtitle">
            We translated the plan into a simple component list you can review before taking the next step.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )
    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")

    with canvas_col:
        st.markdown(
            f"""
            <div class="wizard-card">
              <p class="wizard-title">Recommended kit{f" · {kit_view.level_label}" if kit_view.level_label else ""}</p>
              <p class="wizard-subtitle">{kit_view.hero_summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_kit_cards(kit_view.items)

    with side_col:
        render_side_panel(
            title="How to read this kit",
            description="We translated the technical recommendation into a simple component list.",
            checklist=[f"{item['name']} · {item['quantity']}" for item in kit_view.items],
        )
        back_clicked, next_clicked = render_action_footer(
            back_label="Back to solution",
            next_label="Start another floorplan",
        )
        if back_clicked:
            controller.go_to(WizardScreen.PROPOSAL)
            st.rerun()
        if next_clicked:
            controller.reset_all()
            st.rerun()
    st.markdown("</main>", unsafe_allow_html=True)
