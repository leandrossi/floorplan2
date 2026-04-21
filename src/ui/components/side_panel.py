from __future__ import annotations

import streamlit as st


def render_side_panel(
    *,
    title: str,
    description: str,
    checklist: list[str] | None = None,
    callout: str | None = None,
) -> None:
    st.subheader(title)
    st.caption(description)
    if callout:
        st.info(callout)
    if checklist:
        for item in checklist:
            st.markdown(f"- {item}")
