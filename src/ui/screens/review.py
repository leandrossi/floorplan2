from __future__ import annotations

from typing import Any

import streamlit as st

from review_bundle_io import STRUCT_ENCODING
from ui.components.action_footer import render_action_footer
from ui.components.plan_canvas import (
    build_review_image,
    marker_legend_icon_row_html,
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
                flash = "El tablero eléctrico tiene que marcarse sobre una celda interior."
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

    st.markdown(
        """
        <style>
        .review-step-meta {
            color: #667085;
            font-size: 0.92rem;
            margin: 0.1rem 0 0.2rem 0;
            font-weight: 600;
        }
        .review-title {
            font-size: 1.72rem;
            font-weight: 700;
            color: #111827;
            margin: 0 0 0.3rem 0;
            line-height: 1.22;
        }
        .review-subtitle {
            color: #667085;
            font-size: 0.98rem;
            margin: 0 0 1rem 0;
        }
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
    st.markdown('<p class="review-step-meta">Paso 2 de 8 · Revisar y confirmar plano</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="review-title">Revisá el plano y completá dos referencias importantes</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="review-subtitle">Marcá la entrada principal y el tablero eléctrico. Si algo no coincide, podés corregirlo antes de continuar.</p>',
        unsafe_allow_html=True,
    )

    has_main_entry = bool(main_entry and len(main_entry) == 2)
    has_electric_board = bool(electric_board and len(electric_board) == 2)
    has_blocking_errors = bool(validation["blocking_errors"])
    ready_to_continue = has_main_entry and has_electric_board and (not has_blocking_errors)
    st.session_state["review_mode"] = st.session_state.get("review_mode", "view")
    st.session_state["main_entry"] = main_entry
    st.session_state["electric_board"] = electric_board
    st.session_state["corrections"] = len(patch_map)
    st.session_state["validations"] = {
        "entry_marked": has_main_entry,
        "electric_board_marked": has_electric_board,
        "ready_to_continue": ready_to_continue,
        "blocking_errors": list(validation["blocking_errors"]),
    }

    canvas_col, side_col = st.columns([2.2, 1], gap="large")

    with side_col:
        st.markdown('<div class="review-card"><h4>Qué falta para continuar</h4>', unsafe_allow_html=True)

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

        _render_status("Entrada principal marcada", has_main_entry)
        _render_status("Tablero eléctrico marcado", has_electric_board)
        _render_status("Plano listo para continuar", ready_to_continue)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="review-card"><h4>Qué querés hacer ahora</h4>', unsafe_allow_html=True)
        mode = st.radio(
            "Modo de revisión",
            options=["view", "main_entry", "electric_board", "paint"],
            format_func=lambda value: {
                "view": "Ver plano",
                "main_entry": "Marcar entrada principal",
                "electric_board": "Marcar tablero eléctrico",
                "paint": "Corregir plano",
            }[value],
            key="review_mode",
            horizontal=True,
            label_visibility="collapsed",
        )
        paint_value = None
        if mode == "paint":
            paint_value = st.selectbox(
                "Tipo de celda",
                options=[1, 2, 3, 4, 0],
                format_func=lambda value: STRUCT_ENCODING.get(value, str(value)),
            )
            st.caption("Usá este modo solo para corregir celdas puntuales.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="review-card"><h4>Estado actual</h4>', unsafe_allow_html=True)
        st.write(
            "Entrada principal:",
            f"Marcada (fila {main_entry[0]}, col {main_entry[1]})" if main_entry else "Pendiente",
        )
        st.write(
            "Tablero eléctrico:",
            f"Marcado (fila {electric_board[0]}, col {electric_board[1]})" if electric_board else "Pendiente",
        )
        st.write("Correcciones aplicadas:", len(patch_map))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="review-card"><h4>Acciones secundarias</h4>', unsafe_allow_html=True)
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

        show_technical_validation = st.toggle(
            "Mostrar validación técnica",
            key="review_show_technical_validation",
        )
        if show_technical_validation:
            with st.expander("Validación técnica del plano", expanded=True):
                for item in validation["checklist"]:
                    dot = "🟢" if item.ok else "🔴"
                    text = item.detail if (not item.ok and item.detail) else item.label
                    st.write(f"{dot} {text}")

    with canvas_col:
        st.markdown(
            """
            <div class="wizard-card">
              <p class="wizard-title">Plano interpretado</p>
              <p class="wizard-subtitle">
                Revisá el plano y completá los dos puntos clave para continuar.
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

        with st.expander("Leyenda del plano", expanded=False):
            legend_rows = [
                (0, "Exterior"),
                (4, "Interior"),
                (1, "Pared"),
                (2, "Ventana"),
                (3, "Puerta"),
            ]
            for code, label in legend_rows:
                st.markdown(wizard_legend_swatch_row_html(STRUCT_RGB[code], label), unsafe_allow_html=True)

            st.markdown(
                marker_legend_icon_row_html("main_entry", "Entrada principal"),
                unsafe_allow_html=True,
            )
            st.markdown(
                marker_legend_icon_row_html("electric_board", "Tablero eléctrico"),
                unsafe_allow_html=True,
            )

            for rgb, label in WIZARD_VALIDATION_LEGEND_ROWS:
                st.markdown(wizard_legend_swatch_row_html(rgb, label), unsafe_allow_html=True)

        if not has_main_entry:
            st.error("Te falta marcar la entrada principal para continuar.")
        elif not has_electric_board:
            st.error("Te falta marcar el tablero eléctrico para continuar.")
        elif has_blocking_errors:
            st.error("Todavía hay una validación pendiente en el plano.")
        else:
            st.success("Plano listo. Ya podés continuar.")

        back_clicked, next_clicked = render_action_footer(
            back_label="Volver",
            next_label="Confirmar plano",
            next_disabled=False,
        )
        if back_clicked:
            controller.back()
            st.rerun()
        if next_clicked:
            if not has_main_entry:
                st.error("Te falta marcar la entrada principal para continuar.")
                return
            if not has_electric_board:
                st.error("Te falta marcar el tablero eléctrico para continuar.")
                return
            if has_blocking_errors:
                st.error("Todavía hay una validación pendiente en el plano.")
                return
            result = controller.approve_review()
            if result.approved:
                st.rerun()
            for error in result.blocking_errors:
                st.error(error)
