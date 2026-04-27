from __future__ import annotations

import streamlit as st

from application.navigation import SCREEN_ORDER
from domain.enums import WizardScreen
from ui.theme import tokens

STEPPER_ORDER = tuple(screen for screen in SCREEN_ORDER if screen is not WizardScreen.INTRO)


def render_stepper(current_screen: WizardScreen) -> None:
    css = f"""
    <style>
    .wizard-stepper{{display:flex;align-items:center;justify-content:center;gap:0;margin:0.15rem auto 1.35rem auto;
      padding:0.65rem 0.85rem;background:#fff;border:1px solid {tokens.SOFT_BORDER};border-radius:999px;
      box-shadow:0 6px 18px rgba(15,23,42,0.06);max-width:max-content}}
    .wizard-step{{display:flex;align-items:center;gap:0}}
    .wizard-circle{{width:30px;height:30px;border-radius:999px;display:flex;align-items:center;justify-content:center;
      font-weight:{tokens.FONT_WEIGHT_BOLD};font-size:13px;border:1px solid #d1d5db;color:#9ca3af;background:#fff;flex-shrink:0}}
    .wizard-circle.active{{border-color:{tokens.PRIMARY};color:#fff;background:{tokens.PRIMARY}}}
    .wizard-circle.done{{border-color:{tokens.SUCCESS};color:#fff;background:{tokens.SUCCESS}}}
    .wizard-label{{margin-left:8px;font-size:{tokens.FONT_SIZE_LABEL};color:{tokens.MUTED};white-space:nowrap}}
    .wizard-label.active{{color:{tokens.PRIMARY};font-weight:{tokens.FONT_WEIGHT_SEMIBOLD}}}
    .wizard-label.done{{color:{tokens.SUCCESS};font-weight:{tokens.FONT_WEIGHT_SEMIBOLD}}}
    .wizard-line{{width:28px;height:1px;background:#e5e7eb;margin:0 10px;flex-shrink:0}}
    .wizard-line.done{{background:{tokens.SUCCESS}}}
    @media (max-width: 980px){{.wizard-label{{display:none}}.wizard-line{{width:18px;margin:0 6px}}.wizard-stepper{{max-width:100%;overflow-x:auto;justify-content:flex-start}}}}
    </style>
    """
    parts = [css, '<div class="wizard-stepper">']
    current_index = STEPPER_ORDER.index(current_screen)
    for idx, screen in enumerate(STEPPER_ORDER):
        if idx < current_index:
            circle_cls = "done"
            label_cls = "done"
            circle_content = "&#10003;"
        elif idx == current_index:
            circle_cls = "active"
            label_cls = "active"
            circle_content = str(idx + 1)
        else:
            circle_cls = ""
            label_cls = ""
            circle_content = str(idx + 1)
        parts.append(f'<div class="wizard-step"><div class="wizard-circle {circle_cls}">{circle_content}</div>')
        parts.append(f'<span class="wizard-label {label_cls}">{screen.label}</span></div>')
        if idx < len(STEPPER_ORDER) - 1:
            parts.append(f'<div class="wizard-line {"done" if idx < current_index else ""}"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
