from __future__ import annotations

import streamlit as st

from domain.enums import ProcessingStatus
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    state = controller.state()
    canvas_col, side_col = st.columns([3, 1.25], gap="large")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Estamos entendiendo tu casa</p>
              <p class="wizard-subtitle">
                Analizamos muros, aperturas y ambientes para prepararte una revisi?n visual simple.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        progress = st.progress(0, text="Preparando el an?lisis...")
        phases = st.empty()

        def _progress(ratio: float, message: str) -> None:
            progress.progress(max(0.0, min(1.0, ratio)), text=message)
            phases.markdown(
                "\n".join(
                    [
                        f"- {message}",
                        "- Detectando muros y aperturas",
                        "- Organizando la distribuci?n interior",
                        "- Preparando la revisi?n visual",
                    ]
                )
            )

        if state.processing_requested or state.processing_status in {
            ProcessingStatus.QUEUED.value,
            ProcessingStatus.RUNNING.value,
        }:
            controller.run_processing(progress_cb=_progress)
            st.rerun()

        if state.processing_status == ProcessingStatus.FAILED.value:
            progress.progress(0.0, text="No pudimos terminar el an?lisis.")
            st.error(state.last_error or "Ocurri? un problema durante el procesamiento.")
            if st.button("Volver a subir el plano", width="stretch"):
                controller.start_flow()
                st.rerun()

    with side_col:
        render_side_panel(
            title="Qu? est? pasando",
            description="Esta etapa corre sobre el pipeline actual del proyecto, pero la experiencia se mantiene guiada y simple.",
            checklist=[
                "Interpretaci?n autom?tica del plano",
                "Construcci?n de la grilla final",
                "Preparaci?n de la vista para correcci?n",
            ],
        )
