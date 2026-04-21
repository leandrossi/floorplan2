from __future__ import annotations

import streamlit as st

from application.navigation import SCREEN_ORDER
from domain.enums import WizardScreen


def render_stepper(current_screen: WizardScreen) -> None:
    css = """
    <style>
    .wizard-stepper{display:flex;align-items:center;justify-content:center;gap:0;margin:0.2rem 0 1.2rem}
    .wizard-step{display:flex;align-items:center;gap:0}
    .wizard-circle{width:34px;height:34px;border-radius:999px;display:flex;align-items:center;justify-content:center;
      font-weight:700;font-size:14px;border:2px solid #cbd5e1;color:#94a3b8;background:#fff;flex-shrink:0}
    .wizard-circle.active{border-color:#1e3a8a;color:#fff;background:#1e3a8a}
    .wizard-circle.done{border-color:#2e7d32;color:#fff;background:#2e7d32}
    .wizard-label{margin-left:8px;font-size:13px;color:#64748b;white-space:nowrap}
    .wizard-label.active{color:#1e3a8a;font-weight:600}
    .wizard-label.done{color:#2e7d32;font-weight:600}
    .wizard-line{width:30px;height:2px;background:#dbe4f0;margin:0 10px;flex-shrink:0}
    .wizard-line.done{background:#2e7d32}
    </style>
    """
    parts = [css, '<div class="wizard-stepper">']
    current_index = SCREEN_ORDER.index(current_screen)
    for idx, screen in enumerate(SCREEN_ORDER):
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
        if idx < len(SCREEN_ORDER) - 1:
            parts.append(f'<div class="wizard-line {"done" if idx < current_index else ""}"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
