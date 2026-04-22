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
        st.error(f"No pudimos construir el diagnóstico visual: {exc}")
        if st.button("Volver a la revisión", width="stretch"):
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        return

    st.markdown(
        """
        <style>
        .risk-step-meta {color:#667085;font-size:0.92rem;margin:0.1rem 0 0.2rem 0;font-weight:600;}
        .risk-title {font-size:1.72rem;font-weight:700;color:#111827;margin:0 0 0.28rem 0;line-height:1.2;}
        .risk-subtitle {color:#667085;font-size:0.98rem;margin:0 0 1rem 0;max-width:920px;}
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
    st.markdown('<p class="risk-step-meta">Paso 5 de 8 · Diagnóstico</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="risk-title">Estas son las áreas que hoy requieren mayor protección</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="risk-subtitle">Marcamos las zonas más expuestas de tu vivienda para que entiendas dónde conviene concentrar la cobertura.</p>',
        unsafe_allow_html=True,
    )

    canvas_col, side_col = st.columns([2.2, 1], gap="large")

    with canvas_col:
        st.markdown('<div class="risk-map-card">', unsafe_allow_html=True)
        show_image_path(risk_view.risk_overlay_path, caption="Diagnóstico base del plano")
        st.markdown('<p class="risk-caption">Diagnóstico base del plano</p>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="risk-legend-wrap">
                <div class="risk-chip"><span class="risk-swatch" style="background:#E85D75;"></span>Mayor exposición</div>
                <div class="risk-chip"><span class="risk-swatch" style="background:#F7B3C2;"></span>Exposición media</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        icon_col_1, text_col_1, icon_col_2, text_col_2 = st.columns([0.08, 0.42, 0.08, 0.42], gap="small")
        with icon_col_1:
            st.image(marker_legend_icon("main_entry"), width=18)
        with text_col_1:
            st.caption("Entrada principal")
        with icon_col_2:
            st.image(marker_legend_icon("electric_board"), width=18)
        with text_col_2:
            st.caption("Tablero eléctrico")
        st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown('<div class="risk-card"><h4>Diagnóstico</h4>', unsafe_allow_html=True)
        st.markdown(f'<p class="risk-body">{risk_view.summary_text}</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="risk-card"><h4>Hallazgos principales</h4>', unsafe_allow_html=True)
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
            Este diagnóstico base queda fijo. En el siguiente paso vas a comparar distintas soluciones para proteger estas áreas.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "No necesitás interpretar cada detalle del mapa: en el siguiente paso te mostramos cómo cubrir estas zonas."
        )
        back_clicked, next_clicked = render_action_footer(back_label="Volver", next_label="Ver solución")
        if back_clicked:
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        if next_clicked:
            controller.go_to(WizardScreen.PROPOSAL)
            st.rerun()
