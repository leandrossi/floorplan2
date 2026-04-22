from __future__ import annotations

import streamlit as st
from domain.enums import WizardScreen


def render(controller) -> None:
    controller.go_to(WizardScreen.INTRO)
    st.rerun()
