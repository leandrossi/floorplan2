from __future__ import annotations

import streamlit as st

from ui.theme import tokens


def inject_app_styles() -> None:
    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stApp {{
            background: {tokens.BACKGROUND};
            color: {tokens.TEXT};
        }}
        .block-container {{
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            max-width: 1380px;
        }}
        .wizard-card {{
            background: {tokens.SURFACE};
            border: 1px solid {tokens.BORDER};
            border-radius: {tokens.RADIUS};
            padding: 1.25rem 1.35rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }}
        .wizard-muted {{
            color: {tokens.MUTED};
            font-size: 0.95rem;
        }}
        .wizard-title {{
            font-size: 2rem;
            line-height: 1.1;
            margin: 0 0 0.5rem 0;
        }}
        .wizard-subtitle {{
            color: {tokens.MUTED};
            font-size: 1rem;
            margin-bottom: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
