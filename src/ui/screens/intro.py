from __future__ import annotations

from pathlib import Path

import streamlit as st
from domain.enums import WizardScreen

VIDEO_PATH = Path(__file__).resolve().parents[3] / "assets" / "icons" / "Video" / "VideoMaxV2.mp4"


def render(controller) -> None:
    st.markdown(
        """
        <style>
        .welcome-shell {
            max-width: 1220px;
            margin: 0 auto;
            padding: 0.8rem 0 1.2rem 0;
        }
        .welcome-hero {
            background: linear-gradient(180deg, #000000 0%, #1d1d1f 52%, #000000 100%);
            border: 1px solid #2a2a2c;
            border-radius: 32px;
            padding: 2.1rem 2.1rem 1.9rem 2.1rem;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
        }
        .welcome-eyebrow {
            margin: 0;
            color: #2997ff;
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }
        .welcome-title {
            margin: 0.6rem 0 0 0;
            color: #f5f5f7;
            font-size: clamp(2rem, 4.8vw, 3.6rem);
            line-height: 1.05;
            letter-spacing: -0.02em;
            font-weight: 600;
            max-width: 18ch;
        }
        .welcome-subtitle {
            margin: 0.8rem 0 0 0;
            color: #d2d2d7;
            font-size: 1.08rem;
            line-height: 1.45;
            max-width: 62ch;
        }
        .welcome-chip-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 1.1rem;
        }
        .welcome-chip {
            border-radius: 999px;
            border: 1px solid #424245;
            color: #f5f5f7;
            background: rgba(255, 255, 255, 0.05);
            padding: 0.3rem 0.85rem;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .welcome-video-shell {
            border-radius: 28px;
            overflow: hidden;
            border: 1px solid #2a2a2c;
            background: #000000;
            margin-top: 1.25rem;
        }
        .welcome-footer {
            margin-top: 1.05rem;
            color: #86868b;
            font-size: 0.9rem;
            text-align: center;
        }
        .welcome-missing-video {
            margin-top: 1.05rem;
            border-radius: 16px;
            padding: 0.95rem 1rem;
            border: 1px solid #424245;
            background: rgba(255, 255, 255, 0.03);
            color: #f5f5f7;
            text-align: center;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="welcome-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <section class="welcome-hero">
          <p class="welcome-eyebrow">Bienvenido</p>
          <h1 class="welcome-title">Diseñá la protección ideal para tu hogar</h1>
          <p class="welcome-subtitle">
            Mirá esta presentación rápida para entender cómo funciona el asistente visual.
            Cuando quieras, podés saltar el video y empezar directamente con el wizard.
          </p>
          <div class="welcome-chip-row">
            <span class="welcome-chip">Recorrido guiado</span>
            <span class="welcome-chip">Análisis inteligente</span>
            <span class="welcome-chip">Propuesta clara</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    side_left, center_col, side_right = st.columns([1, 6, 1])
    with center_col:
        st.markdown('<div class="welcome-video-shell">', unsafe_allow_html=True)
        if VIDEO_PATH.exists():
            st.video(str(VIDEO_PATH))
        else:
            st.markdown(
                '<div class="welcome-missing-video">No encontramos el video de presentación.</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        go_wizard = st.button(
            "Jump video go to wizard",
            type="primary",
            use_container_width=True,
            key="intro_skip_video",
        )
        if go_wizard:
            controller.go_to(WizardScreen.UPLOAD)
            st.rerun()

    st.markdown(
        '<p class="welcome-footer">Hacé click en Play para iniciar el video, o usá el botón para continuar al wizard.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
