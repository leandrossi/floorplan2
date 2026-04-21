from __future__ import annotations

import streamlit as st

from application.wizard_controller import WizardController
from domain.enums import WizardScreen
from ui.components.stepper import render_stepper
from ui.screens import intro, kit, processing, proposal, review, risk, summary, upload
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
    current_screen = WizardScreen(state.current_screen)

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
        WizardScreen.SUMMARY: summary.render,
    }
    dispatch[current_screen](controller)


if __name__ == "__main__":
    main()
