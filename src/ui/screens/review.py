from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from domain.enums import WizardScreen
from review_bundle_io import STRUCT_ENCODING
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import (
    build_review_image,
    patch_list_to_map,
    patch_map_to_list,
    render_interactive_review,
)
from ui_components import STRUCT_RGB, WIZARD_VALIDATION_LEGEND_ROWS, wizard_legend_swatch_row_html


def _plain_validation_text(item) -> str:
    if item.ok:
        ok_messages = {
            "marker_main": "Front door marker is placed.",
            "marker_board": "Electrical board marker is placed.",
            "struct_patches": "Your matrix edits are valid.",
            "main_door_cell": "Front door is on a door cell.",
            "board_interior": "Electrical board is inside the home.",
            "main_entry_exterior": "Front door has an outdoor cell directly next to it.",
            "no_interior": "The plan includes indoor space.",
            "int_ext_adj": "Indoor areas are separated from outdoor areas.",
            "exterior_island": "Outdoor areas look connected correctly.",
            "opening_adjacent_free": "Doors and windows touch indoor or outdoor space.",
            "opening_geometry": "Door and window shapes look reasonable.",
        }
        return ok_messages.get(item.id, str(item.label))

    fail_messages = {
        "marker_main": "Place the front door marker on the main entrance door.",
        "marker_board": "Place the electrical board marker inside the home.",
        "struct_patches": "One matrix edit is outside the plan or uses an invalid cell type.",
        "main_door_cell": "Move the front door marker to a cell marked as Door.",
        "board_interior": "Move the electrical board marker to an Interior cell.",
        "main_entry_exterior": "Move the front door to a Door cell that has an Outdoor cell directly next to it.",
        "no_interior": "Mark at least one room or indoor area as Interior.",
        "int_ext_adj": "Some indoor cells touch outdoor cells directly. Add a wall, door, or window between them.",
        "exterior_island": "An outdoor area appears trapped inside the home. Check if a patio or empty area was marked incorrectly.",
        "opening_adjacent_free": "A door or window is isolated. It must touch an indoor or outdoor cell.",
        "opening_geometry": "Check the highlighted doors or windows. The surrounding wall shape may need correction.",
    }
    return fail_messages.get(item.id, "Check the highlighted cells and correct this part of the matrix.")


def _coords_preview(cells: set[tuple[int, int]], limit: int = 8) -> str:
    if not cells:
        return "None"
    ordered = sorted(cells)[:limit]
    rendered = ", ".join(f"({r},{c})" for r, c in ordered)
    extra = max(0, len(cells) - len(ordered))
    return f"{rendered}{f' (+{extra} more)' if extra else ''}"


def _apply_review_event(
    *,
    event: dict[str, Any] | None,
    mode: str,
    paint_value: int | None,
    patch_map: dict[tuple[int, int], int],
    effective_struct,
) -> tuple[dict[tuple[int, int], int], str | None, bool]:
    if not event:
        return patch_map, None, False

    updated_patch_map = dict(patch_map)
    flash = None
    changed = False

    if event.get("kind") == "stroke" and mode == "paint" and paint_value is not None:
        raw_cells = event.get("cells") or []
        dedupe_key = (event.get("stroke_id"), tuple(tuple(cell) for cell in raw_cells))
        if dedupe_key == st.session_state.get("review_last_paint_dedupe"):
            return patch_map, None, False
        st.session_state["review_last_paint_dedupe"] = dedupe_key
        for pair in raw_cells:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            cx, cy = int(pair[0]), int(pair[1])
            if 0 <= cy < effective_struct.shape[0] and 0 <= cx < effective_struct.shape[1]:
                updated_patch_map[(cy, cx)] = int(paint_value)
                changed = True

    return updated_patch_map, flash, changed


def render(controller) -> None:
    state = controller.state()
    validation = controller.get_review_validation(require_markers=False)
    bundle = validation["bundle"]
    effective_struct = validation["effective_struct"]

    patch_map = patch_list_to_map(state.struct_patch)

    st.markdown(
        """
        <style>
        .review-card {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            box-shadow: 0 6px 16px rgba(16, 24, 40, 0.04);
            margin-bottom: 0.8rem;
        }
        .review-card h4 {
            margin: 0 0 0.55rem 0;
            font-size: 0.98rem;
            color: #111827;
        }
        .review-status-row {
            display: flex;
            align-items: center;
            gap: 0.62rem;
            margin: 0.55rem 0;
        }
        .review-status-light {
            width: 16px;
            height: 16px;
            border-radius: 999px;
            box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.04);
            flex-shrink: 0;
        }
        .review-status-red {
            background: #e45b5b;
            box-shadow: 0 0 10px rgba(228, 91, 91, 0.34);
        }
        .review-status-green {
            background: #2ca86f;
            box-shadow: 0 0 10px rgba(44, 168, 111, 0.35);
        }
        .review-status-text {
            color: #1f2937;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 3A · Correct floorplan</p>
          <h1 class="wizard-page-title">Validation floor plan.</h1>
          <p class="wizard-page-subtitle">
            Compare the detected matrix with your uploaded plan. Fix walls, doors, windows, or interior areas before continuing.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    has_blocking_errors = bool(validation["blocking_errors"])
    ready_to_continue = not has_blocking_errors
    st.session_state["review_mode"] = st.session_state.get("review_mode", "view")
    st.session_state["corrections"] = len(patch_map)
    st.session_state["validations"] = {
        "ready_to_continue": ready_to_continue,
        "blocking_errors": list(validation["blocking_errors"]),
    }

    canvas_col, compare_col = st.columns([2, 1.35], gap="large")

    with compare_col:
        st.markdown('<div class="review-card"><h4>Original uploaded floorplan</h4>', unsafe_allow_html=True)
        upload_path = Path(state.upload_path) if state.upload_path else None
        if upload_path and upload_path.is_file():
            if upload_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                st.image(str(upload_path), width="stretch")
            else:
                st.info(f"Current file: {upload_path.name}")
                st.caption("PDF preview is not shown here. The matrix on the left is your editable view.")
        else:
            st.warning("No uploaded floorplan found in this session.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="review-card"><h4>What needs to be valid</h4>', unsafe_allow_html=True)
        def _render_status(label: str, ok: bool) -> None:
            css_class = "review-status-green" if ok else "review-status-red"
            st.markdown(
                f"""
                <div class="review-status-row">
                  <span class="review-status-light {css_class}"></span>
                  <span class="review-status-text">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        _render_status("Corrected matrix has no blocking errors", ready_to_continue)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="review-card"><h4>Editing mode</h4>', unsafe_allow_html=True)
        mode = st.radio(
            "Review mode",
            options=["view", "paint"],
            format_func=lambda value: {
                "view": "View matrix",
                "paint": "Correct matrix",
            }[value],
            key="review_mode",
            horizontal=True,
            label_visibility="collapsed",
        )
        paint_value = None
        paint_tool = "cell"
        if mode == "paint":
            paint_tool = st.radio(
                "Correction tool",
                options=["cell", "line", "area"],
                format_func=lambda value: {
                    "cell": "◻️ Cell by cell",
                    "line": "📏 Line",
                    "area": "▭ Area",
                }[value],
                horizontal=True,
                key="review_paint_tool",
            )
            paint_value = st.selectbox(
                "Cell type",
                options=[1, 2, 3, 4, 0],
                format_func=lambda value: STRUCT_ENCODING.get(value, str(value)),
            )
            st.caption(
                "Cell: one by one · Line: continuous stroke · Area: rectangle. "
                "Line and area show live preview while drawing."
            )
        st.markdown("</div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### Current status")
            st.write("Corrections applied:", len(patch_map))

        with st.container(border=True):
            st.markdown("#### Secondary actions")
            if st.button("Clear corrections", width="stretch"):
                controller.update_review_draft(
                    struct_patch=[],
                    main_entry=state.main_entry,
                    electric_board=state.electric_board,
                )
                st.rerun()

        show_technical_validation = st.toggle(
            "Show floorplan checks",
            key="review_show_technical_validation",
        )
        if show_technical_validation:
            with st.expander("Floorplan checks", expanded=True):
                for item in validation["checklist"]:
                    dot = "🟢" if item.ok else "🔴"
                    text = _plain_validation_text(item)
                    st.write(f"{dot} {text}")
                st.markdown("**Cells to review**")
                st.markdown(f"- Must fix: `{_coords_preview(validation['error_cells'])}`")
                st.markdown(f"- Check these openings: `{_coords_preview(validation['warning_short_cells'])}`")
                st.markdown(f"- Check nearby walls: `{_coords_preview(validation['warning_long_cells'])}`")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Detected matrix editor</p>
              <p class="wizard-subtitle">
                Use this matrix to apply corrections before placing references in the next step.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if flash := st.session_state.pop("review_flash", None):
            st.warning(flash)

        img_width = st.slider(
            "Matrix size",
            min_value=500,
            max_value=2200,
            value=min(1400, max(700, bundle.grid_shape[1] * 6)),
        )
        review_image = build_review_image(
            effective_struct,
            main_entry=state.main_entry,
            electric_board=state.electric_board,
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
            paint_enabled=mode == "paint",
            paint_mode=paint_tool,
            key="wizard_review_canvas",
        )
        updated_patch_map, flash, changed = _apply_review_event(
            event=event,
            mode=mode,
            paint_value=paint_value,
            patch_map=patch_map,
            effective_struct=effective_struct,
        )
        if flash:
            st.session_state["review_flash"] = flash
            st.rerun()
        if changed:
            controller.update_review_draft(
                struct_patch=patch_map_to_list(updated_patch_map),
                main_entry=state.main_entry,
                electric_board=state.electric_board,
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

            for rgb, label in WIZARD_VALIDATION_LEGEND_ROWS:
                st.markdown(wizard_legend_swatch_row_html(rgb, label), unsafe_allow_html=True)

        if has_blocking_errors:
            st.error("There is still a blocking validation issue in the corrected matrix.")
            if not (validation["error_cells"] or validation["warning_short_cells"] or validation["warning_long_cells"]):
                st.markdown("**Validation details:**")
                for item in validation["blocking_errors"]:
                    st.markdown(f"- {item}")
        else:
            st.success("Matrix is valid. Continue to place references.")

        back_clicked, next_clicked = render_action_footer(
            back_label="Back to upload",
            next_label="Continue to references",
            next_disabled=not ready_to_continue,
        )
        if back_clicked:
            controller.go_to(WizardScreen.UPLOAD)
            st.rerun()
        if next_clicked:
            if has_blocking_errors:
                st.error("There is still a blocking validation issue in the corrected matrix.")
                return
            controller.go_to(WizardScreen.REVIEW_MARKERS)
            st.rerun()
    st.markdown("</main>", unsafe_allow_html=True)
