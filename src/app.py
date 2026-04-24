from __future__ import annotations

import streamlit as st

from application.navigation import SCREEN_ORDER
from application.wizard_controller import WizardController
from domain.enums import WizardScreen
from ui.components.stepper import render_stepper
from ui.screens import intro, kit, processing, proposal, review, risk, upload
from ui.theme.styles import inject_app_styles


def main() -> None:
    st.set_page_config(
        page_title="Wizard de Alarmas",
        page_icon="🏠",
        layout="wide",
    )
    inject_app_styles()

    controller = WizardController()
    state = controller.state()
    try:
        current_screen = WizardScreen(state.current_screen)
    except ValueError:
        controller.go_to(WizardScreen.KIT)
        st.rerun()
        return
    if current_screen not in SCREEN_ORDER:
        controller.go_to(WizardScreen.KIT)
        st.rerun()
        return

    if current_screen is not WizardScreen.INTRO:
        st.caption("Asesor visual para protección domiciliaria")
        render_stepper(current_screen)

    dispatch = {
        WizardScreen.INTRO: intro.render,
        WizardScreen.UPLOAD: upload.render,
        WizardScreen.PROCESSING: processing.render,
        WizardScreen.REVIEW: review.render,
        WizardScreen.RISK: risk.render,
        WizardScreen.PROPOSAL: proposal.render,
        WizardScreen.KIT: kit.render,
    }
    dispatch[current_screen](controller)


if __name__ == "__main__":
    main()
