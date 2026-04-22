from __future__ import annotations

import streamlit as st

from ui_components import get_device_icon_image


def render_kit_cards(items: list[dict]) -> None:
    if not items:
        st.info("Todavía no hay un kit generado.")
        return
    cols = st.columns(2)
    for idx, item in enumerate(items):
        with cols[idx % 2]:
            device_type = str(item.get("device_type") or "")
            icon = get_device_icon_image(device_type, size=30)
            if icon is not None:
                icon_col, title_col = st.columns([0.12, 0.88], gap="small")
                with icon_col:
                    st.image(icon, width=28)
                with title_col:
                    st.markdown(f"### {item['name']}")
            else:
                st.markdown(f"### {item['name']}")
            st.metric("Cantidad", int(item["quantity"]))
            st.caption(str(item["purpose"]))
