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
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }}
        .wizard-page-shell {{
            max-width: 1240px;
            margin: 0 auto;
        }}
        .wizard-page-header {{
            margin: 0 0 1.25rem 0;
        }}
        .wizard-step-context {{
            margin: 0 0 0.45rem 0;
            color: {tokens.PRIMARY};
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }}
        .wizard-page-title {{
            margin: 0;
            color: {tokens.TEXT};
            font-family: "SF Pro Display", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: clamp(2rem, 3vw, 3rem);
            font-weight: 650;
            line-height: 1.08;
            letter-spacing: -0.035em;
        }}
        .wizard-page-subtitle {{
            margin: 0.65rem 0 0 0;
            color: {tokens.MUTED};
            font-size: 1.05rem;
            line-height: 1.52;
            max-width: 760px;
        }}
        .wizard-card {{
            background: {tokens.SURFACE};
            border: 1px solid {tokens.SOFT_BORDER};
            border-radius: {tokens.RADIUS};
            padding: 1.5rem;
            box-shadow: {tokens.SHADOW_CARD};
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        .wizard-card:hover {{
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.1);
            border-color: #DADDE3;
        }}
        .wizard-card--subtle {{
            background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFC 100%);
            border-radius: {tokens.RADIUS_MD};
        }}
        .wizard-card--dark {{
            background: #050505;
            color: #FFFFFF;
            border-color: rgba(255,255,255,0.1);
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
            letter-spacing: -0.025em;
            font-weight: {tokens.FONT_WEIGHT_SEMIBOLD};
        }}
        .wizard-subtitle {{
            color: {tokens.MUTED};
            font-size: {tokens.FONT_SIZE_SUBTITLE};
            line-height: 1.5;
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
            line-height: 1.45;
        }}
        .wizard-trust-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        .wizard-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: {tokens.PRIMARY_SOFT};
            border: 1px solid #D6E9FF;
            color: {tokens.PRIMARY_HOVER};
            border-radius: {tokens.RADIUS_PILL};
            padding: 0.45rem 0.75rem;
            font-size: 0.84rem;
            font-weight: 650;
            line-height: 1;
        }}
        .wizard-layout {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
            gap: 1.25rem;
            align-items: start;
        }}
        .wizard-upload-box {{
            border: 1px dashed #BCC7D8;
            border-radius: 22px;
            background: linear-gradient(180deg, #FFFFFF 0%, #FAFBFC 100%);
            padding: 1.25rem;
        }}
        .wizard-inline-note {{
            border-radius: 16px;
            border: 1px solid {tokens.SOFT_BORDER};
            background: #F9FAFB;
            padding: 0.85rem 1rem;
            color: {tokens.MUTED};
            font-size: 0.92rem;
            line-height: 1.45;
        }}
        .wizard-status-list {{
            display: grid;
            gap: 0.55rem;
            margin-top: 0.8rem;
        }}
        .wizard-status-item {{
            display: flex;
            align-items: flex-start;
            gap: 0.65rem;
            color: {tokens.TEXT};
            font-size: 0.94rem;
            line-height: 1.4;
        }}
        .wizard-status-dot {{
            width: 9px;
            height: 9px;
            margin-top: 0.38rem;
            border-radius: 999px;
            background: {tokens.PRIMARY};
            flex: 0 0 auto;
        }}
        .wizard-action-footer {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid {tokens.SOFT_BORDER};
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
            border-radius: {tokens.RADIUS_PILL};
            border: 1px solid {tokens.BORDER};
            font-weight: {tokens.FONT_WEIGHT_SEMIBOLD};
            font-size: 14px;
            min-height: 44px;
            transition: transform 0.08s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }}
        div[data-testid="stButton"] button:hover {{
            border-color: {tokens.BORDER};
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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
        div[data-testid="stFileUploader"] section {{
            border-radius: 18px;
            border-color: #CBD5E1;
            background: #FFFFFF;
        }}
        div[data-testid="stAlert"] {{
            border-radius: 16px;
        }}
        @media (max-width: 900px) {{
            .wizard-layout {{
                grid-template-columns: 1fr;
            }}
            .wizard-page-title {{
                font-size: 2rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
