from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from domain.enums import SecurityLevel, WizardScreen
from infrastructure.artifact_store import ArtifactStore
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import show_image_path
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    state = controller.state()
    level = SecurityLevel(state.proposal_level)
    proposal = controller.ensure_proposal_view()
    kit = controller.get_kit_view()
    risk_view = controller.ensure_risk_view()
    artifact_store = ArtifactStore()

    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")
    with canvas_col:
        st.markdown(
            f"""
            <div class="wizard-card">
              <p class="wizard-title">Resumen final</p>
              <p class="wizard-subtitle">
                Tu plano quedó validado y ya tenés una propuesta {level.label.lower()} con su kit asociado.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        show_image_path(proposal.overlay_path or risk_view.risk_overlay_path, caption="Vista final del plano")
        metrics = st.columns(3)
        metrics[0].metric("Nivel elegido", level.label)
        metrics[1].metric("Componentes", sum(proposal.counts_by_type.values()))
        metrics[2].metric("Items del kit", len(kit.items))

        if proposal.proposal_path and Path(proposal.proposal_path).is_file():
            st.download_button(
                "Descargar propuesta",
                data=Path(proposal.proposal_path).read_text(encoding="utf-8"),
                file_name="installation_proposal.json",
                mime="application/json",
                width="stretch",
            )
        if proposal.report_path and Path(proposal.report_path).is_file():
            report = artifact_store.read_json(Path(proposal.report_path))
            st.download_button(
                "Descargar resumen técnico",
                data=json.dumps(report, indent=2, ensure_ascii=False),
                file_name="alarm_plan_report.json",
                mime="application/json",
                width="stretch",
            )

    with side_col:
        render_side_panel(
            title="Qué lograste",
            description="Completaste el flujo sin entrar en detalles internos del pipeline ni del planner.",
            checklist=[
                "Plano interpretado y corregido",
                "Diagnóstico base confirmado",
                f"Propuesta {level.label.lower()} generada",
                "Kit listo para avanzar",
            ],
            callout="Siguiente paso natural: pedir este kit o compartir el resumen con un asesor.",
        )
        back_clicked, next_clicked = render_action_footer(
            back_label="Volver al kit",
            next_label="Empezar otro plano",
        )
        if back_clicked:
            controller.go_to(WizardScreen.KIT)
            st.rerun()
        if next_clicked:
            controller.reset_all()
            st.rerun()
