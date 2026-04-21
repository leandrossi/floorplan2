from __future__ import annotations

from typing import Any

import streamlit as st

from review_bundle_io import STRUCT_ENCODING
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import (
    build_review_image,
    patch_list_to_map,
    patch_map_to_list,
    render_interactive_review,
)
from ui_components import STRUCT_RGB, WIZARD_VALIDATION_LEGEND_ROWS, wizard_legend_swatch_row_html


def _apply_review_event(
    *,
    event: dict[str, Any] | None,
    mode: str,
    paint_value: int | None,
    patch_map: dict[tuple[int, int], int],
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    effective_struct,
) -> tuple[dict[tuple[int, int], int], list[int] | None, list[int] | None, str | None, bool]:
    if not event:
        return patch_map, main_entry, electric_board, None, False

    updated_patch_map = dict(patch_map)
    updated_main = main_entry
    updated_board = electric_board
    flash = None
    changed = False

    if event.get("kind") == "stroke" and mode == "paint" and paint_value is not None:
        raw_cells = event.get("cells") or []
        dedupe_key = (event.get("stroke_id"), tuple(tuple(cell) for cell in raw_cells))
        if dedupe_key == st.session_state.get("review_last_paint_dedupe"):
            return patch_map, main_entry, electric_board, None, False
        st.session_state["review_last_paint_dedupe"] = dedupe_key
        for pair in raw_cells:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            cx, cy = int(pair[0]), int(pair[1])
            if 0 <= cy < effective_struct.shape[0] and 0 <= cx < effective_struct.shape[1]:
                updated_patch_map[(cy, cx)] = int(paint_value)
                changed = True

    if event.get("kind") == "pick" and mode in {"main_entry", "electric_board"}:
        cx = int(event["cx"])
        cy = int(event["cy"])
        dedupe_key = ("pick", mode, event.get("pick_id"), cx, cy)
        if dedupe_key == st.session_state.get("review_last_grid_pick_dedupe"):
            return patch_map, main_entry, electric_board, None, False
        st.session_state["review_last_grid_pick_dedupe"] = dedupe_key
        picked_value = int(effective_struct[cy, cx])
        if mode == "main_entry":
            if picked_value != 3:
                flash = "La entrada principal tiene que marcarse sobre una puerta."
            else:
                updated_main = [cy, cx]
                changed = True
        elif mode == "electric_board":
            if picked_value != 4:
                flash = "El cuadro eléctrico tiene que marcarse sobre una celda interior."
            else:
                updated_board = [cy, cx]
                changed = True

    return updated_patch_map, updated_main, updated_board, flash, changed


def render(controller) -> None:
    state = controller.state()
    validation = controller.get_review_validation()
    bundle = validation["bundle"]
    effective_struct = validation["effective_struct"]

    patch_map = patch_list_to_map(state.struct_patch)
    main_entry = state.main_entry
    electric_board = state.electric_board

    canvas_col, side_col = st.columns([3.2, 1.3], gap="large")

    with side_col:
        st.markdown('<div class="wizard-card">', unsafe_allow_html=True)
        st.subheader("Revisá la interpretación")
        st.caption("Corregí solo lo necesario y marcá la entrada principal y el cuadro eléctrico.")
        mode = st.radio(
            "Herramienta",
            options=["view", "main_entry", "electric_board", "paint"],
            format_func=lambda value: {
                "view": "Ver",
                "main_entry": "Entrada principal",
                "electric_board": "Cuadro eléctrico",
                "paint": "Corregir plano",
            }[value],
        )
        paint_value = None
        if mode == "paint":
            paint_value = st.selectbox(
                "Tipo de celda",
                options=[1, 2, 3, 4, 0],
                format_func=lambda value: STRUCT_ENCODING.get(value, str(value)),
            )
            st.caption("Usá este modo solo para corregir celdas puntuales.")
        st.divider()
        st.markdown("**Checklist**")
        for item in validation["checklist"]:
            icon = "OK" if item.ok else "Falta"
            text = item.detail if (not item.ok and item.detail) else item.label
            st.write(f"- {icon}: {text}")
        st.divider()
        st.markdown("**Estado actual**")
        st.write(
            "Entrada principal:",
            f"fila {main_entry[0]}, col {main_entry[1]}" if main_entry else "Sin marcar",
        )
        st.write(
            "Cuadro eléctrico:",
            f"fila {electric_board[0]}, col {electric_board[1]}" if electric_board else "Sin marcar",
        )
        st.write("Correcciones:", len(patch_map))
        if st.button("Limpiar marcadores", width="stretch"):
            controller.update_review_draft(
                struct_patch=state.struct_patch,
                main_entry=None,
                electric_board=None,
            )
            st.rerun()
        if st.button("Limpiar correcciones", width="stretch"):
            controller.update_review_draft(
                struct_patch=[],
                main_entry=main_entry,
                electric_board=electric_board,
            )
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Confirmá que entendimos bien tu plano</p>
              <p class="wizard-subtitle">
                Esta revisión no es un editor técnico: es solo para ajustar la interpretación automática.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if flash := st.session_state.pop("review_flash", None):
            st.warning(flash)

        img_width = st.slider(
            "Tamaño del plano",
            min_value=500,
            max_value=2200,
            value=min(1400, max(700, bundle.grid_shape[1] * 6)),
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
            paint_enabled=mode == "paint",
            key="wizard_review_canvas",
        )
        updated_patch_map, updated_main, updated_board, flash, changed = _apply_review_event(
            event=event,
            mode=mode,
            paint_value=paint_value,
            patch_map=patch_map,
            main_entry=main_entry,
            electric_board=electric_board,
            effective_struct=effective_struct,
        )
        if flash:
            st.session_state["review_flash"] = flash
            st.rerun()
        if changed:
            controller.update_review_draft(
                struct_patch=patch_map_to_list(updated_patch_map),
                main_entry=updated_main,
                electric_board=updated_board,
            )
            st.rerun()

        with st.expander("Leyenda"):
            cols = st.columns(5)
            for idx, (code, name) in enumerate(STRUCT_ENCODING.items()):
                rgb = STRUCT_RGB[code]
                cols[idx].markdown(
                    wizard_legend_swatch_row_html(rgb, f"{code} = {name}"),
                    unsafe_allow_html=True,
                )
            st.markdown(
                wizard_legend_swatch_row_html((255, 0, 0), "Marcador · entrada principal")
                + wizard_legend_swatch_row_html((0, 0, 255), "Marcador · cuadro eléctrico"),
                unsafe_allow_html=True,
            )
            for rgb, label in WIZARD_VALIDATION_LEGEND_ROWS:
                st.markdown(wizard_legend_swatch_row_html(rgb, label), unsafe_allow_html=True)

        back_clicked, next_clicked = render_action_footer(
            back_label="Volver",
            next_label="Confirmar plano",
            next_disabled=bool(validation["blocking_errors"]),
        )
        if back_clicked:
            controller.back()
            st.rerun()
        if next_clicked:
            result = controller.approve_review()
            if result.approved:
                st.rerun()
            for error in result.blocking_errors:
                st.error(error)
