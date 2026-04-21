from __future__ import annotations

import streamlit as st

from domain.enums import SecurityLevel


def render_security_level_selector(current: SecurityLevel) -> SecurityLevel:
    options = [SecurityLevel.BASIC, SecurityLevel.RECOMMENDED, SecurityLevel.MAXIMUM]
    selected = st.radio(
        "Nivel de protección",
        options=options,
        index=options.index(current),
        horizontal=True,
        format_func=lambda level: level.label,
    )
    hints = {
        SecurityLevel.BASIC: "Lo esencial para cubrir los accesos principales.",
        SecurityLevel.RECOMMENDED: "El balance recomendado para la mayoría de las viviendas.",
        SecurityLevel.MAXIMUM: "Cobertura más completa sobre accesos y circulación.",
    }
    st.caption(hints[selected])
    return selected
