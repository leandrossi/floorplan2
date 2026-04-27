from __future__ import annotations

from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

from domain.enums import SecurityLevel, WizardScreen
from infrastructure.artifact_store import ArtifactStore
from services.proposal_service import PROPOSAL_MAP_ICON_SIZE_PX
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import show_image_path
from ui.components.security_level_selector import render_security_level_selector
from ui.components.side_panel import render_side_panel
from ui_components import (
    apply_highlight_ring_to_rgb,
    get_device_icon_image,
    proposal_device_icon_pixel_center,
)


def render(controller) -> None:
    state = controller.state()
    current_level = SecurityLevel(state.proposal_level)
    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 5 · Protection solution</p>
          <h1 class="wizard-page-title">Here’s the recommended coverage.</h1>
          <p class="wizard-page-subtitle">
            Compare protection levels and see how each option changes the recommended devices on your plan.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )
    canvas_col, side_col = st.columns([3.2, 1.2], gap="large")
    artifact_store = ArtifactStore()

    with side_col:
        st.markdown('<div class="wizard-card">', unsafe_allow_html=True)
        st.subheader("Choose protection level")
        selected_level = render_security_level_selector(current_level)
        st.markdown("</div>", unsafe_allow_html=True)
        if selected_level is not current_level:
            controller.set_proposal_level(selected_level)
            st.rerun()

    with canvas_col:
        st.markdown(
            """
            <style>
            .proposal-device-item {
                padding: 4px 2px 0 2px;
                text-align: center;
            }
            .proposal-device-label {
                margin: 0.32rem 0 0.18rem 0;
                color: #475467;
                font-size: 0.82rem;
                line-height: 1.2;
            }
            .proposal-device-value {
                margin: 0;
                color: #0F172A;
                font-size: 1.75rem;
                font-weight: 700;
                line-height: 1;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Recommended devices on your floorplan</p>
              <p class="wizard-subtitle">
                Change the level to compare coverage without changing the diagnosis you already approved.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        progress = st.progress(0, text="Preparing recommendation...")

        def _progress(ratio: float, message: str) -> None:
            progress.progress(ratio, text=message)

        try:
            proposal_view = controller.ensure_proposal_view(progress_cb=_progress)
        except Exception as exc:  # noqa: BLE001
            progress.empty()
            st.error(
                "We couldn’t generate the recommendation for this level. "
                f"Try reviewing the plan or running it again. Detail: {exc}"
            )
            if st.button("Back to diagnosis", width="stretch"):
                controller.go_to(WizardScreen.RISK)
                st.rerun()
            return
        progress.empty()

        hl_key = f"proposal_device_hl_{selected_level.value}"
        if hl_key not in st.session_state:
            st.session_state[hl_key] = None

        overlay_path = proposal_view.overlay_path
        display_rgb: np.ndarray | None = None
        if overlay_path and Path(overlay_path).is_file():
            with Image.open(overlay_path) as img_f:
                display_rgb = np.asarray(img_f.convert("RGB"))
            hl_idx = st.session_state.get(hl_key)
            if (
                display_rgb is not None
                and hl_idx is not None
                and isinstance(hl_idx, int)
                and proposal_view.grid_h > 0
                and proposal_view.grid_w > 0
                and 0 <= hl_idx < len(proposal_view.devices)
            ):
                reserved_cells: set[tuple[int, int]] = set()
                if state.main_entry and len(state.main_entry) == 2:
                    reserved_cells.add((int(state.main_entry[0]), int(state.main_entry[1])))
                if state.electric_board and len(state.electric_board) == 2:
                    reserved_cells.add((int(state.electric_board[0]), int(state.electric_board[1])))
                ih, iw = display_rgb.shape[0], display_rgb.shape[1]
                px_center = proposal_device_icon_pixel_center(
                    proposal_view.devices,
                    hl_idx,
                    grid_h=proposal_view.grid_h,
                    grid_w=proposal_view.grid_w,
                    image_h=ih,
                    image_w=iw,
                    reserved_cells=reserved_cells,
                    icon_size_px=PROPOSAL_MAP_ICON_SIZE_PX,
                )
                cell = proposal_view.devices[hl_idx].get("cell")
                if px_center is not None:
                    display_rgb = apply_highlight_ring_to_rgb(
                        display_rgb,
                        grid_h=proposal_view.grid_h,
                        grid_w=proposal_view.grid_w,
                        pixel_center=px_center,
                    )
                elif isinstance(cell, (list, tuple)) and len(cell) == 2:
                    display_rgb = apply_highlight_ring_to_rgb(
                        display_rgb,
                        grid_h=proposal_view.grid_h,
                        grid_w=proposal_view.grid_w,
                        row=int(cell[0]),
                        col=int(cell[1]),
                    )

        cap = f"{selected_level.label} · coverage map"
        if display_rgb is not None:
            st.image(display_rgb, caption=cap, width="stretch")
        else:
            show_image_path(overlay_path, caption=cap)

        placable = [
            (idx, d)
            for idx, d in enumerate(proposal_view.devices)
            if isinstance(d.get("cell"), (list, tuple)) and len(d["cell"]) == 2
        ]
        if placable and proposal_view.grid_h > 0:
            st.caption("Tap **Highlight on map** to show a ring on that device. Tap again on the same row to clear.")
            for idx, dev in placable:
                dtype = str(dev.get("device_type") or "device").replace("_", " ").title()
                cell = dev["cell"]
                r, c = int(cell[0]), int(cell[1])
                ic1, tx, btn = st.columns([0.09, 0.56, 0.35], gap="small")
                with ic1:
                    icon = get_device_icon_image(str(dev.get("device_type")), size=32)
                    if icon is not None:
                        st.image(icon, width=34)
                with tx:
                    st.markdown(f"**{dtype}** · ({r},{c})")
                with btn:
                    active = st.session_state.get(hl_key) == idx
                    if st.button(
                        "Hide highlight" if active else "Highlight on map",
                        key=f"proposal_hl_{selected_level.value}_{idx}",
                        width="stretch",
                    ):
                        st.session_state[hl_key] = None if active else idx
                        st.rerun()
            if st.session_state.get(hl_key) is not None:
                if st.button("Clear highlight", key=f"proposal_hl_clear_{selected_level.value}"):
                    st.session_state[hl_key] = None
                    st.rerun()

        stats = st.columns(max(1, len(proposal_view.counts_by_type)))
        for idx, (device_type, count) in enumerate(sorted(proposal_view.counts_by_type.items())):
            with stats[idx % len(stats)]:
                st.markdown('<div class="proposal-device-item">', unsafe_allow_html=True)
                icon = get_device_icon_image(device_type, size=44)
                if icon is not None:
                    st.image(icon, width=48)
                st.markdown(
                    f'<p class="proposal-device-label">{device_type.replace("_", " ").title()}</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<p class="proposal-device-value">{int(count)}</p>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.caption(proposal_view.proposal_summary)

        report_path = proposal_view.report_path
        if report_path and Path(report_path).is_file():
            report = artifact_store.read_json(Path(report_path))
            warnings = list(report.get("warnings") or [])
            errors = list(report.get("errors") or [])
            if warnings or errors:
                with st.expander(
                    f"Technical details ({len(warnings)} warnings, {len(errors)} errors)",
                ):
                    for warning in warnings:
                        st.warning(warning)
                    for error in errors:
                        st.error(error)

    with side_col:
        render_side_panel(
            title="What changes",
            description="The protection level only changes the recommended devices and resulting kit.",
            checklist=[
                "Basic: essential coverage",
                "Recommended: balanced protection",
                "Maximum: more complete coverage",
            ],
        )
        back_clicked, next_clicked = render_action_footer(
            back_label="Back to diagnosis",
            next_label="View kit",
        )
        if back_clicked:
            controller.go_to(WizardScreen.RISK)
            st.rerun()
        if next_clicked:
            controller.go_to(WizardScreen.KIT)
            st.rerun()
    st.markdown("</main>", unsafe_allow_html=True)
