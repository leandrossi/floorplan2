from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

from ui_components import (
    overlay_markers,
    overlay_validation_highlights,
    rgb_from_struct,
    upscale_rgb,
)

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
except ImportError:  # pragma: no cover - optional dependency
    streamlit_image_coordinates = None  # type: ignore[misc,assignment]

try:
    from streamlit_grid_paint import grid_paint_image
except ImportError:  # pragma: no cover - optional dependency
    grid_paint_image = None  # type: ignore[misc,assignment]


def patch_list_to_map(patches: list[dict[str, int]]) -> dict[tuple[int, int], int]:
    out: dict[tuple[int, int], int] = {}
    for patch in patches:
        out[(int(patch["r"]), int(patch["c"]))] = int(patch["v"])
    return out


def patch_map_to_list(patch_map: dict[tuple[int, int], int]) -> list[dict[str, int]]:
    return [{"r": r, "c": c, "v": int(v)} for (r, c), v in sorted(patch_map.items())]


def build_review_image(
    struct: np.ndarray,
    *,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    error_cells: set[tuple[int, int]] | None = None,
    warning_short_cells: set[tuple[int, int]] | None = None,
    warning_long_cells: set[tuple[int, int]] | None = None,
    img_width: int = 1200,
) -> np.ndarray:
    rgb = rgb_from_struct(struct)
    if error_cells or warning_short_cells or warning_long_cells:
        rgb = overlay_validation_highlights(
            rgb,
            error_cells=error_cells,
            warning_short_free_cells=warning_short_cells,
            warning_long_wall_cells=warning_long_cells,
        )
    rgb = overlay_markers(
        rgb,
        main_entry=main_entry,
        electric_board=electric_board,
        marker_radius=2,
    )
    return upscale_rgb(rgb, int(img_width))


def render_interactive_review(
    image: np.ndarray,
    *,
    grid_w: int,
    grid_h: int,
    mode: str,
    paint_enabled: bool,
    key: str,
) -> dict[str, Any] | None:
    if grid_paint_image is not None:
        result = grid_paint_image(
            image,
            grid_w=grid_w,
            grid_h=grid_h,
            width=image.shape[1],
            height=image.shape[0],
            key=key,
            cursor="crosshair",
            enable_paint=paint_enabled,
            pick_on_click=mode in ("main_entry", "electric_board"),
        )
        return result if isinstance(result, dict) else None

    if streamlit_image_coordinates is not None and mode in ("main_entry", "electric_board"):
        coord = streamlit_image_coordinates(image, key=f"{key}_coords")
        if coord is None:
            return None
        disp_w = float(coord.get("width") or 0)
        disp_h = float(coord.get("height") or 0)
        if disp_w <= 0 or disp_h <= 0:
            return None
        cx = int(float(coord["x"]) * grid_w / disp_w)
        cy = int(float(coord["y"]) * grid_h / disp_h)
        cx = max(0, min(grid_w - 1, cx))
        cy = max(0, min(grid_h - 1, cy))
        return {"kind": "pick", "cx": cx, "cy": cy, "pick_id": f"{cx}:{cy}"}

    st.image(image, width="content")
    return None


def show_image_path(path: str | Path | None, *, caption: str | None = None) -> None:
    if path:
        st.image(str(path), caption=caption, width="stretch")
