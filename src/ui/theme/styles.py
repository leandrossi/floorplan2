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
            font-family: "SF Pro Text", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }}
        .block-container {{
            padding-top: {tokens.SPACE_LG};
            padding-bottom: 2.5rem;
            max-width: 1380px;
        }}
        .wizard-card {{
            background: {tokens.SURFACE};
            border: 1px solid {tokens.BORDER};
            border-radius: {tokens.RADIUS};
            padding: {tokens.SPACE_LG} 1.35rem;
            box-shadow: {tokens.SHADOW_CARD};
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        .wizard-card:hover {{
            box-shadow: {tokens.SHADOW_CARD_HOVER};
            border-color: #C6D4EB;
        }}
        .wizard-card--subtle {{
            background: {tokens.SURFACE_ALT};
            border-radius: {tokens.RADIUS_MD};
        }}
        .wizard-muted {{
            color: {tokens.MUTED};
            font-size: {tokens.FONT_SIZE_BODY};
        }}
        .wizard-title {{
            font-family: "SF Pro Display", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: {tokens.FONT_SIZE_TITLE};
            line-height: 1.15;
            margin: 0 0 {tokens.SPACE_SM} 0;
            letter-spacing: -0.01em;
        }}
        .wizard-subtitle {{
            color: {tokens.MUTED};
            font-size: {tokens.FONT_SIZE_SUBTITLE};
            margin-bottom: 0;
        }}
        .wizard-section-title {{
            margin: 0 0 {tokens.SPACE_XS} 0;
            font-size: 1.25rem;
            font-weight: {tokens.FONT_WEIGHT_SEMIBOLD};
            color: {tokens.TEXT};
        }}
        .wizard-section-subtitle {{
            margin: 0 0 {tokens.SPACE_MD} 0;
            color: {tokens.MUTED};
            font-size: {tokens.FONT_SIZE_BODY};
        }}
        .wizard-bullet-list {{
            margin: 0;
            padding-left: 1.1rem;
            color: {tokens.TEXT};
        }}
        .wizard-bullet-list li {{
            margin: {tokens.SPACE_XS} 0;
        }}
        .wizard-kpi {{
            background: {tokens.SURFACE_ALT};
            border: 1px solid {tokens.BORDER};
            border-radius: {tokens.RADIUS_MD};
            padding: {tokens.SPACE_SM} {tokens.SPACE_MD};
            margin-top: {tokens.SPACE_XS};
        }}
        .wizard-kpi-label {{
            font-size: {tokens.FONT_SIZE_LABEL};
            color: {tokens.MUTED};
            margin: 0 0 0.1rem 0;
        }}
        .wizard-kpi-value {{
            font-size: 1.05rem;
            font-weight: {tokens.FONT_WEIGHT_SEMIBOLD};
            margin: 0;
        }}

        div[data-testid="stButton"] button {{
            border-radius: {tokens.RADIUS_MD};
            border: 1px solid {tokens.BORDER};
            font-weight: {tokens.FONT_WEIGHT_SEMIBOLD};
            transition: transform 0.08s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }}
        div[data-testid="stButton"] button:hover {{
            border-color: #B8CAE6;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
            transform: translateY(-1px);
        }}
        div[data-testid="stButton"] button:focus {{
            box-shadow: {tokens.FOCUS_RING};
            outline: none;
        }}
        div[data-testid="stButton"] button:disabled {{
            background: {tokens.DISABLED_BG};
            color: {tokens.DISABLED_TEXT};
            border-color: #D6DEE9;
            box-shadow: none;
            transform: none;
            cursor: not-allowed;
        }}
        div[data-testid="stButton"] button[kind="primary"] {{
            background: {tokens.PRIMARY};
            border-color: {tokens.PRIMARY};
            color: #FFFFFF;
        }}
        div[data-testid="stButton"] button[kind="primary"]:hover {{
            background: {tokens.PRIMARY_HOVER};
            border-color: {tokens.PRIMARY_HOVER};
        }}
        div[data-testid="stButton"] button[kind="primary"]:focus {{
            box-shadow: {tokens.FOCUS_RING};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
