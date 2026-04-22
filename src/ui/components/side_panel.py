from __future__ import annotations

import streamlit as st


def render_side_panel(
    *,
    title: str,
    description: str,
    checklist: list[str] | None = None,
    callout: str | None = None,
) -> None:
    st.markdown('<aside class="wizard-card wizard-card--subtle">', unsafe_allow_html=True)
    st.markdown(f'<p class="wizard-section-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="wizard-section-subtitle">{description}</p>', unsafe_allow_html=True)
    if callout:
        st.info(callout)
    if checklist:
        items = "".join(f"<li>{item}</li>" for item in checklist)
        st.markdown(f'<ul class="wizard-bullet-list">{items}</ul>', unsafe_allow_html=True)
    st.markdown("</aside>", unsafe_allow_html=True)
