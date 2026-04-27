from __future__ import annotations

import streamlit as st


def render_action_footer(
    *,
    back_label: str | None = None,
    next_label: str | None = None,
    next_disabled: bool = False,
    back_disabled: bool = False,
) -> tuple[bool, bool]:
    st.markdown('<div class="wizard-action-footer">', unsafe_allow_html=True)
    cols = st.columns([1, 1], gap="small")
    back_clicked = False
    next_clicked = False
    with cols[0]:
        if back_label:
            back_clicked = st.button(back_label, width="stretch", disabled=back_disabled)
    with cols[1]:
        if next_label:
            next_clicked = st.button(
                next_label,
                type="primary",
                width="stretch",
                disabled=next_disabled,
            )
    st.markdown("</div>", unsafe_allow_html=True)
    return back_clicked, next_clicked
