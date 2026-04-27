from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from domain.enums import WizardScreen

VIDEO_PATH = Path(__file__).resolve().parents[3] / "assets" / "icons" / "Video" / "VideoMaxV2.mp4"
HOUSE_PATH = Path(__file__).resolve().parents[3] / "assets" / "icons" / "house.png"
WATCH_TRIGGER_KEY = "intro_watch_trigger"
WATCHED_KEY = "introVideoWatched"
SKIPPED_KEY = "introSkipped"
WATCHED_QUERY_KEY = "intro_video_watched"


def render(controller) -> None:
    if WATCH_TRIGGER_KEY not in st.session_state:
        st.session_state[WATCH_TRIGGER_KEY] = 0
    if WATCHED_KEY not in st.session_state:
        st.session_state[WATCHED_KEY] = False
    if SKIPPED_KEY not in st.session_state:
        st.session_state[SKIPPED_KEY] = False

    watched_via_query = str(st.query_params.get(WATCHED_QUERY_KEY, "")).lower() in {"1", "true", "yes"}
    if watched_via_query:
        st.session_state[WATCHED_KEY] = True
        st.query_params.clear()
        st.rerun()
        return

    start_requested = str(st.query_params.get("start_guided_setup", "")).lower() in {"1", "true", "yes"}
    if start_requested:
        st.session_state[SKIPPED_KEY] = True
        st.query_params.clear()
        controller.go_to(WizardScreen.UPLOAD)
        st.rerun()
        return

    house_background_rule = ""
    if HOUSE_PATH.exists():
        encoded_house = base64.b64encode(HOUSE_PATH.read_bytes()).decode("ascii")
        house_background_rule = f'background-image: url("data:image/png;base64,{encoded_house}");'

    st.markdown(
        """
        <style>
        .welcome-shell {
            max-width: 1280px;
            margin: 0 auto;
            padding: 28px 0 calc(120px + env(safe-area-inset-bottom)) 0;
            animation: welcomeFadeIn 240ms ease-out both;
        }
        .welcome-shell .welcome-page-eyebrow {
            margin: 0 0 18px 2px !important;
            color: #0A84FF !important;
            font-size: 30px !important;
            line-height: 1 !important;
            font-weight: 800 !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
        }
        .welcome-hero {
            background: #050505;
            background-image:
              radial-gradient(circle at 86% 14%, rgba(10, 132, 255, 0.2), transparent 36%),
              radial-gradient(circle at 82% 92%, rgba(10, 132, 255, 0.14), transparent 34%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 48px 44px 36px 44px;
            min-height: 650px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.16);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }
        .welcome-hero-content {
            position: relative;
            z-index: 2;
        }
        .welcome-hero-visual {
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 58%;
            background-repeat: no-repeat;
            background-position: center bottom;
            background-size: 112% auto;
            opacity: 0.94;
            pointer-events: none;
            z-index: 1;
            __HOUSE_BACKGROUND_RULE__
        }
        .welcome-hero-visual::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, rgba(5, 5, 5, 0) 0%, rgba(5, 5, 5, 0.14) 44%, rgba(5, 5, 5, 0.24) 100%);
        }
        .welcome-eyebrow {
            margin: 0;
            color: #0A84FF;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .welcome-hero .welcome-title {
            margin: 0 !important;
            color: #FAFAFC !important;
            -webkit-text-fill-color: #FAFAFC !important;
            font-size: clamp(44px, 4vw, 58px) !important;
            line-height: 1.08 !important;
            letter-spacing: -0.02em !important;
            font-weight: 760 !important;
            max-width: none !important;
            text-shadow: 0 2px 22px rgba(255, 255, 255, 0.08), 0 8px 28px rgba(0, 0, 0, 0.72) !important;
        }
        .welcome-subtitle {
            margin: 16px 0 0 0;
            color: rgba(255, 255, 255, 0.72);
            font-size: 17px;
            line-height: 1.47;
            max-width: 38ch;
        }
        .welcome-badges {
            margin-top: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            position: relative;
            z-index: 2;
        }
        .welcome-badge {
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.08);
            color: rgba(255, 255, 255, 0.82);
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 500;
            line-height: 1.2;
            white-space: nowrap;
        }
        #intro-video-card-marker {
            display: none;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(#intro-video-card-marker) {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 24px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
            padding: 30px 30px 22px 30px;
            min-height: 650px;
        }
        .welcome-video-title {
            margin: 0;
            color: #111827;
            font-size: 40px;
            line-height: 1.2;
            letter-spacing: -0.01em;
            font-weight: 600;
        }
        .welcome-video-helper {
            margin: 10px 0 0 0;
            color: #6B7280;
            font-size: 16px;
            line-height: 1.45;
            max-width: 68ch;
        }
        .welcome-video-status {
            margin-top: 10px;
            color: #6B7280;
            font-size: 14px;
            line-height: 1.35;
        }
        .welcome-video-status[data-ready="true"] {
            color: #4B5563;
        }
        .welcome-video-status[data-error="true"] {
            color: #9A3412;
        }
        .welcome-video-status:empty {
            display: none;
        }
        .welcome-video-shell {
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid #E5E7EB;
            background: #000000;
            margin-top: 16px;
        }
        .welcome-video-error {
            margin: 0;
            color: #6B7280;
            font-size: 15px;
            line-height: 1.45;
            text-align: center;
            padding: 32px 16px;
        }
        .welcome-actions-shell {
            margin-top: 18px;
            padding-top: 0;
            animation: welcomeFadeIn 280ms ease-out both;
        }
        .welcome-actions-shell div[data-testid="stButton"] button {
            min-height: 50px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.29;
        }
        .welcome-actions-shell div[data-testid="stButton"] button[kind="secondary"] {
            background: #FFFFFF;
            color: #111827;
            border: 1px solid #D1D5DB;
        }
        .welcome-actions-shell div[data-testid="stButton"] button[kind="secondary"]:hover {
            background: #F9FAFB;
            border-color: #D1D5DB;
            transform: translateY(-1px);
        }
        .welcome-actions-shell div[data-testid="stButton"] button[kind="primary"] {
            background: #0A84FF;
            border-color: #0A84FF;
            color: #FFFFFF;
        }
        .welcome-actions-shell div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #007AFF;
            border-color: #007AFF;
        }
        .welcome-actions-shell div[data-testid="stButton"] button:active {
            transform: scale(0.98);
        }
        .welcome-trust-strip {
            margin-top: 20px;
            border-radius: 16px;
            border: 1px solid #E5E7EB;
            background: #FFFFFF;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .welcome-trust-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #F3F4F6;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #6B7280;
            font-size: 16px;
            flex-shrink: 0;
        }
        .welcome-trust-title {
            margin: 0;
            color: #111827;
            font-size: 20px;
            font-weight: 600;
            line-height: 1.2;
        }
        .welcome-trust-subtitle {
            margin: 4px 0 0 0;
            color: #6B7280;
            font-size: 14px;
            line-height: 1.35;
        }
        @keyframes welcomeFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @media (prefers-reduced-motion: reduce) {
            .welcome-shell,
            .welcome-actions-shell {
                animation: none;
            }
            .welcome-actions-shell div[data-testid="stButton"] button {
                transition: none;
                transform: none;
            }
        }
        @media (max-width: 1240px) {
            .welcome-shell {
                max-width: 1120px;
            }
            .welcome-title {
                font-size: 50px !important;
            }
            .welcome-video-title {
                font-size: 34px;
            }
        }
        @media (max-width: 1024px) {
            .welcome-hero {
                padding: 44px 40px 38px 40px;
                min-height: 0;
            }
            .welcome-title {
                font-size: 48px !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#intro-video-card-marker) {
                min-height: 0;
                padding: 24px 24px 18px 24px;
            }
            .welcome-video-title {
                font-size: 30px;
            }
            .welcome-actions-shell {
                margin-top: 14px;
                padding-top: 0;
            }
        }
        @media (max-width: 639px) {
            .welcome-shell {
                padding: 10px 0 calc(170px + env(safe-area-inset-bottom)) 0;
            }
            .welcome-hero {
                padding: 30px 28px 28px 28px;
                border-radius: 28px;
                min-height: 0;
            }
            .welcome-title {
                font-size: clamp(32px, 8.8vw, 38px) !important;
                max-width: none !important;
            }
            .welcome-subtitle {
                font-size: 15px;
                line-height: 1.42;
            }
            .welcome-hero-visual {
                height: 45%;
                background-size: 118% auto;
                opacity: 0.88;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(#intro-video-card-marker) {
                border-radius: 20px;
                padding: 20px 16px 16px 16px;
            }
            .welcome-video-title {
                font-size: 24px;
            }
            .welcome-video-helper {
                font-size: 15px;
            }
            .welcome-actions-shell {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 110;
                padding: 12px 16px calc(12px + env(safe-area-inset-bottom)) 16px;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                background: rgba(255, 255, 255, 0.92);
                border-top: 1px solid #E5E7EB;
            }
            .welcome-actions-shell [data-testid="stHorizontalBlock"] {
                flex-direction: column;
                gap: 10px;
            }
            .welcome-actions-shell [data-testid="stColumn"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            .welcome-trust-strip {
                margin-top: 14px;
                padding: 14px 14px;
            }
            .welcome-trust-title {
                font-size: 16px;
            }
            .welcome-trust-subtitle {
                font-size: 13px;
            }
        }
        </style>
        """.replace("__HOUSE_BACKGROUND_RULE__", house_background_rule),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="welcome-shell">', unsafe_allow_html=True)
    st.markdown(
        '<p class="welcome-page-eyebrow" style="font-size:30px;color:#0A84FF;font-weight:800;line-height:1;">WELCOME</p>',
        unsafe_allow_html=True,
    )
    left_col, right_col = st.columns([46, 54], gap="large")

    with left_col:
        st.markdown(
            """
            <section class="welcome-hero">
              <div class="welcome-hero-content">
                <h1 class="welcome-title" style="color:#FAFAFC;-webkit-text-fill-color:#FAFAFC;">Design the right protection for your home.</h1>
                <p class="welcome-subtitle">
                  Watch a short introduction or start directly. The wizard will guide you step by step to create a personalized protection plan.
                </p>
              </div>
              <div class="welcome-badges">
                <span class="welcome-badge">Guided process</span>
                <span class="welcome-badge">No technical knowledge required</span>
                <span class="welcome-badge">5–7 min</span>
              </div>
              <div class="welcome-hero-visual" aria-hidden="true"></div>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with right_col:
        with st.container(border=True):
            st.markdown('<div id="intro-video-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<h2 class="welcome-video-title">Quick introduction</h2>', unsafe_allow_html=True)
            st.markdown(
                '<p class="welcome-video-helper">See how wizard works</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="welcome-video-status" id="intro-video-status" aria-live="polite">Loading video preview…</p>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="welcome-video-shell" id="intro-video-anchor">', unsafe_allow_html=True)

            video_available = VIDEO_PATH.exists()
            play_on_render = st.session_state[WATCH_TRIGGER_KEY] > 0
            if video_available:
                st.video(
                    str(VIDEO_PATH),
                    autoplay=play_on_render,
                    width="stretch",
                )
                if play_on_render:
                    st.session_state[WATCHED_KEY] = True
            else:
                st.markdown(
                    '<p class="welcome-video-error">The introduction video couldn’t be loaded. You can continue with the guided setup.</p>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="welcome-actions-shell">', unsafe_allow_html=True)
            action_left, action_right = st.columns(2)
            with action_left:
                watch_clicked = st.button(
                    "Watch introduction",
                    use_container_width=True,
                    key="intro_watch_video",
                    help="Play the introduction video",
                    type="secondary",
                )
            with action_right:
                primary_label = "Continue to guided setup" if st.session_state[WATCHED_KEY] else "Start guided setup"
                go_wizard = st.button(
                    primary_label,
                    type="primary",
                    use_container_width=True,
                    key="intro_start_setup",
                    help="Start the guided wizard setup",
                )
            st.markdown("</div>", unsafe_allow_html=True)
    if watch_clicked:
        st.session_state[WATCH_TRIGGER_KEY] += 1
        components.html(
            """
            <script>
              const doc = window.parent.document;
              const anchor = doc.querySelector('#intro-video-anchor');
              const vid = doc.querySelector('video');
              if (anchor) {
                anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }
              if (vid) {
                const attempt = vid.play();
                if (attempt && typeof attempt.then === 'function') {
                  attempt.catch(() => {});
                }
                vid.focus({ preventScroll: true });
              }
            </script>
            """,
            height=0,
        )
        st.rerun()

    if go_wizard:
        st.session_state[SKIPPED_KEY] = True
        controller.go_to(WizardScreen.UPLOAD)
        st.rerun()

    components.html(
        f"""
        <script>
          localStorage.setItem('introSkipped', {str(st.session_state[SKIPPED_KEY]).lower()});
          localStorage.setItem('introVideoWatched', {str(st.session_state[WATCHED_KEY]).lower()});

          const doc = window.parent.document;
          const status = doc.querySelector('#intro-video-status');
          const video = doc.querySelector('video');
          if (video) {{
            video.setAttribute('aria-label', 'Introduction video for guided home protection setup');
            video.setAttribute('preload', 'metadata');
            video.addEventListener('loadeddata', () => {{
              if (!status) return;
              status.setAttribute('data-ready', 'true');
              status.textContent = '';
            }}, {{ once: true }});
            video.addEventListener('error', () => {{
              if (!status) return;
              status.setAttribute('data-error', 'true');
              status.textContent = "The introduction video couldn’t be loaded. You can continue with the guided setup.";
            }}, {{ once: true }});
            video.addEventListener('ended', () => {{
              localStorage.setItem('introVideoWatched', 'true');
              const url = new URL(window.parent.location.href);
              if (!url.searchParams.get('{WATCHED_QUERY_KEY}')) {{
                url.searchParams.set('{WATCHED_QUERY_KEY}', '1');
                window.parent.location.assign(url.toString());
              }}
            }}, {{ once: true }});
          }}
        </script>
        """,
        height=0,
    )
    st.markdown(
        """
        <section class="welcome-trust-strip">
          <span class="welcome-trust-icon" aria-hidden="true">🔒</span>
          <div>
            <p class="welcome-trust-title">Your information is safe and private.</p>
            <p class="welcome-trust-subtitle">We use industry-standard encryption to protect your data at every step.</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
