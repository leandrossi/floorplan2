from __future__ import annotations

import streamlit as st

from domain.enums import WizardScreen
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import marker_legend_icon
from ui.components.plan_canvas import show_image_path


def render(controller) -> None:
    try:
        risk_view = controller.ensure_risk_view()
    except Exception as exc:  # noqa: BLE001
        st.error(f"We couldn't build the visual diagnosis: {exc}")
        if st.button("Back to review", width="stretch"):
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        return

    st.markdown(
        """
        <style>
        .risk-map-card {
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
            border: 1px solid #E8EDF3;
            border-radius: 20px;
            padding: 16px;
            box-shadow: 0 10px 28px rgba(16, 24, 40, 0.05);
        }
        .risk-card {
            background:#fff;border:1px solid #E8EDF3;border-radius:16px;
            padding:14px;box-shadow:0 6px 16px rgba(16,24,40,0.04);margin-bottom:0.75rem;
        }
        .risk-card h4 {margin:0 0 0.55rem 0;color:#101828;font-size:1rem;}
        .risk-body {color:#475467;font-size:0.95rem;line-height:1.52;}
        .risk-callout {
            background:#EEF4FF;border:1px solid #D9E6FF;color:#1849A9;border-radius:14px;
            padding:12px;font-size:0.92rem;margin-top:0.2rem;
        }
        .risk-legend-wrap {display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
        .risk-chip {
            display:inline-flex;align-items:center;gap:8px;border:1px solid #E6EAF0;background:#F9FAFB;
            border-radius:999px;padding:7px 10px;font-size:0.84rem;color:#344054;
        }
        .risk-swatch {width:12px;height:12px;border-radius:999px;display:inline-block;}
        .risk-caption {text-align:center;color:#667085;font-size:0.88rem;margin-top:8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 4 · Risk diagnosis</p>
          <h1 class="wizard-page-title">These areas need the most attention.</h1>
          <p class="wizard-page-subtitle">
            We highlight the most exposed zones so you can understand where protection matters before choosing a solution.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    canvas_col, side_col = st.columns([2.2, 1], gap="large")

    with canvas_col:
        st.markdown('<div class="risk-map-card">', unsafe_allow_html=True)
        show_image_path(risk_view.risk_overlay_path, caption="Baseline risk overlay on your floorplan")
        st.markdown(
            '<p class="risk-caption">Baseline risk overlay on your floorplan</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="risk-legend-wrap">
                <div class="risk-chip"><span class="risk-swatch" style="background:#E85D75;"></span>Highest exposure</div>
                <div class="risk-chip"><span class="risk-swatch" style="background:#F7B3C2;"></span>Medium exposure</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        icon_col_1, text_col_1, icon_col_2, text_col_2 = st.columns([0.08, 0.42, 0.08, 0.42], gap="small")
        with icon_col_1:
            st.image(marker_legend_icon("main_entry"), width=18)
        with text_col_1:
            st.caption("Main entrance")
        with icon_col_2:
            st.image(marker_legend_icon("electric_board"), width=18)
        with text_col_2:
            st.caption("Electrical board")
        st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown('<div class="risk-card"><h4>Diagnosis</h4>', unsafe_allow_html=True)
        st.markdown(f'<p class="risk-body">{risk_view.summary_text}</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="risk-card"><h4>Key findings</h4>', unsafe_allow_html=True)
        st.markdown(
            "<ul>"
            + "".join(f"<li>{detail}</li>" for detail in risk_view.details[:3])
            + "</ul>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="risk-callout">
            This diagnosis stays fixed. Next, you’ll compare protection options for these areas.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "You don’t need to interpret every detail. The next step translates this into a recommended solution."
        )
        back_clicked, next_clicked = render_action_footer(back_label="Back to review", next_label="View solution")
        if back_clicked:
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        if next_clicked:
            controller.go_to(WizardScreen.PROPOSAL)
            st.rerun()
    st.markdown("</main>", unsafe_allow_html=True)
