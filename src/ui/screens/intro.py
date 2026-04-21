from __future__ import annotations

import streamlit as st


def render(controller) -> None:
    st.markdown(
        """
        <div class="wizard-card">
          <p class="wizard-title">Protegé tu casa en pocos pasos</p>
          <p class="wizard-subtitle">
            Subí tu plano, revisá lo que interpretamos y te mostramos una solución clara para proteger los accesos.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    benefits = st.columns(3)
    benefit_copy = [
        ("No necesitás conocimientos técnicos", "El wizard te guía de punta a punta."),
        ("Tu plano es el protagonista", "Vas viendo la interpretación y la solución sobre la vivienda."),
        ("Recibís un kit claro", "Terminás con una propuesta entendible y lista para avanzar."),
    ]
    for col, (title, body) in zip(benefits, benefit_copy, strict=False):
        with col:
            st.markdown('<div class="wizard-card">', unsafe_allow_html=True)
            st.markdown(f"### {title}")
            st.caption(body)
            st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("Comenzar", type="primary", width="stretch"):
        controller.start_flow()
        st.rerun()
