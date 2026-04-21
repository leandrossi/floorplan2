from __future__ import annotations

import streamlit as st


def render_kit_cards(items: list[dict]) -> None:
    if not items:
        st.info("Todavía no hay un kit generado.")
        return
    cols = st.columns(2)
    for idx, item in enumerate(items):
        with cols[idx % 2]:
            st.markdown(f"### {item['name']}")
            st.metric("Cantidad", int(item["quantity"]))
            st.caption(str(item["purpose"]))
