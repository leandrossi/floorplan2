from __future__ import annotations

from typing import Any

import streamlit as st

from domain.enums import WizardScreen
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import (
    build_review_image,
    marker_legend_icon_row_html,
    patch_list_to_map,
    render_interactive_review,
)
from ui_components import STRUCT_RGB, WIZARD_VALIDATION_LEGEND_ROWS, wizard_legend_swatch_row_html


def _has_outdoor_neighbor(effective_struct, row: int, col: int) -> bool:
    h, w = effective_struct.shape
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < h and 0 <= nc < w and int(effective_struct[nr, nc]) == 0:
            return True
    return False


def _apply_marker_event(
    *,
    event: dict[str, Any] | None,
    mode: str,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    effective_struct,
) -> tuple[list[int] | None, list[int] | None, str | None, bool]:
    if not event or event.get("kind") != "pick" or mode not in {"main_entry", "electric_board"}:
        return main_entry, electric_board, None, False

    cx = int(event["cx"])
    cy = int(event["cy"])
    dedupe_key = ("pick", mode, event.get("pick_id"), cx, cy)
    if dedupe_key == st.session_state.get("review_last_grid_pick_dedupe"):
        return main_entry, electric_board, None, False
    st.session_state["review_last_grid_pick_dedupe"] = dedupe_key

    picked_value = int(effective_struct[cy, cx])
    updated_main = main_entry
    updated_board = electric_board
    if mode == "main_entry":
        if picked_value != 3:
            return main_entry, electric_board, "Front door must be placed on a Door cell.", False
        if not _has_outdoor_neighbor(effective_struct, cy, cx):
            return (
                main_entry,
                electric_board,
                "Front door must be on a Door cell with an Outdoor cell directly next to it.",
                False,
            )
        updated_main = [cy, cx]
    elif mode == "electric_board":
        if picked_value != 4:
            return main_entry, electric_board, "Electrical board must be placed on an interior cell.", False
        updated_board = [cy, cx]
    return updated_main, updated_board, None, True


def render(controller) -> None:
    state = controller.state()
    validation = controller.get_review_validation()
    effective_struct = validation["effective_struct"]
    bundle = validation["bundle"]
    patch_map = patch_list_to_map(state.struct_patch)
    main_entry = state.main_entry
    electric_board = state.electric_board

    has_main_entry = bool(main_entry and len(main_entry) == 2)
    has_electric_board = bool(electric_board and len(electric_board) == 2)
    ready_to_continue = has_main_entry and has_electric_board

    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 3B · Place references</p>
          <h1 class="wizard-page-title">Place two key references.</h1>
          <p class="wizard-page-subtitle">
            Click the matrix to mark the front door and the electrical board. The front door must be a Door cell with an Outdoor cell directly next to it.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    canvas_col, side_col = st.columns([2.2, 1], gap="large")

    with side_col:
        st.markdown('<div class="wizard-card wizard-card--subtle">', unsafe_allow_html=True)
        st.markdown('<p class="wizard-section-title">Placement status</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="wizard-status-list">'
            f'<div class="wizard-status-item"><span class="wizard-status-dot"></span><span>Front door: {"Marked" if has_main_entry else "Pending"}</span></div>'
            f'<div class="wizard-status-item"><span class="wizard-status-dot"></span><span>Electrical board: {"Marked" if has_electric_board else "Pending"}</span></div>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        mode = st.radio(
            "Placement mode",
            options=["view", "main_entry", "electric_board"],
            format_func=lambda value: {
                "view": "View matrix",
                "main_entry": "Place front door",
                "electric_board": "Place electrical board",
            }[value],
            key="review_marker_mode",
            horizontal=True,
        )
        st.caption("Select a mode and click on the matrix.")
        st.info(
            "Front door rule: choose a Door cell at the outside entrance. "
            "One of the cells directly above, below, left, or right must be Outdoor."
        )

        if st.button("Clear both markers", width="stretch"):
            controller.update_review_draft(
                struct_patch=state.struct_patch,
                main_entry=None,
                electric_board=None,
            )
            st.rerun()

    with canvas_col:
        if flash := st.session_state.pop("review_markers_flash", None):
            st.warning(flash)

        img_width = st.slider(
            "Matrix size",
            min_value=500,
            max_value=2200,
            value=min(1400, max(700, bundle.grid_shape[1] * 6)),
            key="review_markers_img_width",
        )
        review_image = build_review_image(
            effective_struct,
            main_entry=main_entry,
            electric_board=electric_board,
            error_cells=validation["error_cells"],
            warning_short_cells=validation["warning_short_cells"],
            warning_long_cells=validation["warning_long_cells"],
            img_width=img_width,
        )
        event = render_interactive_review(
            review_image,
            grid_w=bundle.grid_shape[1],
            grid_h=bundle.grid_shape[0],
            mode=mode,
            paint_enabled=False,
            paint_mode="cell",
            key="wizard_review_markers_canvas",
        )
        updated_main, updated_board, flash, changed = _apply_marker_event(
            event=event,
            mode=mode,
            main_entry=main_entry,
            electric_board=electric_board,
            effective_struct=effective_struct,
        )
        if flash:
            st.session_state["review_markers_flash"] = flash
            st.rerun()
        if changed:
            controller.update_review_draft(
                struct_patch=state.struct_patch,
                main_entry=updated_main,
                electric_board=updated_board,
            )
            st.rerun()

        with st.expander("Matrix legend", expanded=False):
            legend_rows = [
                (0, "Exterior"),
                (4, "Interior"),
                (1, "Wall"),
                (2, "Window"),
                (3, "Door"),
            ]
            for code, label in legend_rows:
                st.markdown(wizard_legend_swatch_row_html(STRUCT_RGB[code], label), unsafe_allow_html=True)
            st.markdown(marker_legend_icon_row_html("main_entry", "Front door"), unsafe_allow_html=True)
            st.markdown(marker_legend_icon_row_html("electric_board", "Electrical board"), unsafe_allow_html=True)
            for rgb, label in WIZARD_VALIDATION_LEGEND_ROWS:
                st.markdown(wizard_legend_swatch_row_html(rgb, label), unsafe_allow_html=True)

        if not has_main_entry:
            st.error("Mark the front door to continue.")
        elif not has_electric_board:
            st.error("Mark the electrical board to continue.")
        else:
            st.success("References complete. Continue to diagnosis.")

        back_clicked, next_clicked = render_action_footer(
            back_label="Back to corrections",
            next_label="Confirm references",
            next_disabled=not ready_to_continue,
        )
        if back_clicked:
            controller.go_to(WizardScreen.REVIEW)
            st.rerun()
        if next_clicked:
            result = controller.approve_review()
            if result.approved:
                st.rerun()
            for error in result.blocking_errors:
                st.error(error)
    st.markdown("</main>", unsafe_allow_html=True)

