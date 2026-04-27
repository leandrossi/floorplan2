from __future__ import annotations

import streamlit as st

from domain.enums import SecurityLevel


def render_security_level_selector(current: SecurityLevel) -> SecurityLevel:
    options = [SecurityLevel.BASIC, SecurityLevel.RECOMMENDED, SecurityLevel.MAXIMUM]
    selected = st.radio(
        "Protection level",
        options=options,
        index=options.index(current),
        horizontal=True,
        format_func=lambda level: level.label,
    )
    hints = {
        SecurityLevel.BASIC: "Essential coverage for the main access points.",
        SecurityLevel.RECOMMENDED: "The balanced option recommended for most homes.",
        SecurityLevel.MAXIMUM: "More complete coverage for access points and movement areas.",
    }
    st.caption(hints[selected])
    return selected
