from __future__ import annotations

import streamlit as st

from ui_components import get_device_icon_image


def render_kit_cards(items: list[dict]) -> None:
    if not items:
        st.info("No kit has been generated yet.")
        return
    st.markdown(
        """
        <style>
        .kit-card-title {
            margin: 0;
            color: #111827;
            font-size: 1.08rem;
            font-weight: 650;
            line-height: 1.25;
        }
        .kit-card-purpose {
            margin: 0.45rem 0 0 0;
            color: #6B7280;
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .kit-card-qty {
            margin: 0.35rem 0 0 0;
            color: #0071E3;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.15;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for idx, item in enumerate(items):
        with cols[idx % 2]:
            with st.container(border=True):
                thumb_col, text_col = st.columns([1, 2], gap="medium")
                device_type = str(item.get("device_type") or "")
                icon = get_device_icon_image(device_type, size=96)
                with thumb_col:
                    if icon is not None:
                        st.image(icon, use_container_width=True)
                    else:
                        st.caption("—")
                with text_col:
                    st.markdown(f'<p class="kit-card-title">{item["name"]}</p>', unsafe_allow_html=True)
                    st.markdown(
                        f'<p class="kit-card-qty">{int(item["quantity"])} units</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f'<p class="kit-card-purpose">{item["purpose"]}</p>', unsafe_allow_html=True)
