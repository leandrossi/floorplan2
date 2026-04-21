from __future__ import annotations

from pathlib import Path

import streamlit as st

from domain.enums import SecurityLevel, WizardScreen
from infrastructure.artifact_store import ArtifactStore
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import show_image_path
from ui.components.security_level_selector import render_security_level_selector
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    state = controller.state()
    current_level = SecurityLevel(state.proposal_level)
    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")
    artifact_store = ArtifactStore()

    with side_col:
        st.markdown('<div class="wizard-card">', unsafe_allow_html=True)
        st.subheader("Elegí el nivel")
        selected_level = render_security_level_selector(current_level)
        st.markdown("</div>", unsafe_allow_html=True)
        if selected_level is not current_level:
            controller.set_proposal_level(selected_level)
            st.rerun()

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Esta es la solución sobre tu plano</p>
              <p class="wizard-subtitle">
                Cambiá el nivel para comparar cantidades y cobertura, sin alterar el diagnóstico base.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        progress = st.progress(0, text="Preparando la propuesta...")

        def _progress(ratio: float, message: str) -> None:
            progress.progress(ratio, text=message)

        try:
            proposal_view = controller.ensure_proposal_view(progress_cb=_progress)
        except Exception as exc:  # noqa: BLE001
            progress.empty()
            st.error(
                "No pudimos generar la propuesta con el nivel elegido. "
                f"Probá revisar el plano o volver a intentarlo. Detalle: {exc}"
            )
            if st.button("Volver al diagnóstico", width="stretch"):
                controller.go_to(WizardScreen.RISK)
                st.rerun()
            return
        progress.empty()
        show_image_path(proposal_view.overlay_path, caption=f"Propuesta {selected_level.label}")

        stats = st.columns(max(1, len(proposal_view.counts_by_type)))
        for idx, (device_type, count) in enumerate(sorted(proposal_view.counts_by_type.items())):
            with stats[idx % len(stats)]:
                st.metric(device_type.replace("_", " ").title(), int(count))

        st.caption(proposal_view.proposal_summary)

        report_path = proposal_view.report_path
        if report_path and Path(report_path).is_file():
            report = artifact_store.read_json(Path(report_path))
            warnings = list(report.get("warnings") or [])
            errors = list(report.get("errors") or [])
            if warnings or errors:
                with st.expander(f"Detalle técnico controlado ({len(warnings)} advertencias, {len(errors)} errores)"):
                    for warning in warnings:
                        st.warning(warning)
                    for error in errors:
                        st.error(error)

    with side_col:
        render_side_panel(
            title="Qué cambia",
            description="El nivel solo ajusta la propuesta de dispositivos y el kit resultante.",
            checklist=[
                "Básico: cobertura esencial",
                "Recomendado: balance general",
                "Máximo: cobertura más completa",
            ],
        )
        back_clicked, next_clicked = render_action_footer(
            back_label="Volver al diagnóstico",
            next_label="Ver kit",
        )
        if back_clicked:
            controller.go_to(WizardScreen.RISK)
            st.rerun()
        if next_clicked:
            controller.go_to(WizardScreen.KIT)
            st.rerun()
