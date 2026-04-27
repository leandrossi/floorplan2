from __future__ import annotations

import streamlit as st

from domain.enums import ProcessingStatus
from ui.components.side_panel import render_side_panel


def render(controller) -> None:
    state = controller.state()
    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 2 · Floorplan analysis</p>
          <h1 class="wizard-page-title">We’re reading your home layout.</h1>
          <p class="wizard-page-subtitle">
            This usually takes a moment. We’re preparing a clean visual review so you can confirm the important points without technical work.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )
    canvas_col, side_col = st.columns([3, 1.25], gap="large")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Analyzing the floorplan</p>
              <p class="wizard-subtitle">
                We detect walls, openings, and interior areas so the next step is simple to review.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        progress = st.progress(0, text="Preparing analysis...")
        phases = st.empty()

        def _progress(ratio: float, message: str) -> None:
            progress.progress(max(0.0, min(1.0, ratio)), text=message)
            phases.markdown(
                "\n".join(
                    [
                        f"- {message}",
                        "- Detecting walls and openings",
                        "- Organizing the interior layout",
                        "- Preparing the visual review",
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
            progress.progress(0.0, text="We couldn’t finish the analysis.")
            st.error(state.last_error or "Something went wrong while analyzing the floorplan.")
            if st.button("Upload another floorplan", width="stretch"):
                controller.start_flow()
                st.rerun()

    with side_col:
        render_side_panel(
            title="What’s happening",
            description="We’re turning your file into a reviewable plan. You’ll confirm the key references before any recommendation is created.",
            checklist=[
                "Automatic floorplan interpretation",
                "Clean review grid generation",
                "Visual review preparation",
            ],
        )
    st.markdown("</main>", unsafe_allow_html=True)
