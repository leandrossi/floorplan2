from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

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


ICON_PATHS = {
    "main_entry": Path(__file__).resolve().parents[3] / "assets" / "icons" / "main-entry-door.png",
    "electric_board": Path(__file__).resolve().parents[3] / "assets" / "icons" / "electric-panel.png",
}


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
    upscaled = upscale_rgb(rgb, int(img_width))
    return overlay_marker_icons(
        upscaled,
        grid_h=struct.shape[0],
        grid_w=struct.shape[1],
        main_entry=main_entry,
        electric_board=electric_board,
    )


def _build_marker_icon(kind: str, size: int) -> np.ndarray:
    icon_path = ICON_PATHS.get(kind)
    if icon_path and icon_path.is_file():
        try:
            with Image.open(icon_path) as icon_image:
                rgba = icon_image.convert("RGBA")
                alpha = rgba.split()[3]
                bbox = alpha.getbbox()
                if bbox is not None:
                    rgba = rgba.crop(bbox)
                resized = rgba.resize((size, size), Image.LANCZOS)
                return np.asarray(resized)
        except Exception:
            # Fallback to generated icon when external asset cannot be loaded.
            pass

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    if kind == "main_entry":
        # Door-like icon on transparent canvas.
        fill = (192, 64, 64, 232)
        outline = (146, 38, 38, 255)
        draw.rounded_rectangle(
            [size * 0.24, size * 0.12, size * 0.76, size * 0.88],
            radius=max(2, int(size * 0.09)),
            fill=fill,
            outline=outline,
            width=max(1, int(size * 0.06)),
        )
        draw.ellipse(
            [size * 0.63, size * 0.47, size * 0.71, size * 0.55],
            fill=(255, 241, 177, 255),
        )
    else:
        # Electrical panel icon on transparent canvas.
        fill = (59, 114, 205, 235)
        outline = (35, 81, 157, 255)
        draw.rounded_rectangle(
            [size * 0.14, size * 0.18, size * 0.86, size * 0.86],
            radius=max(2, int(size * 0.1)),
            fill=fill,
            outline=outline,
            width=max(1, int(size * 0.06)),
        )
        bolt = [
            (size * 0.56, size * 0.24),
            (size * 0.42, size * 0.50),
            (size * 0.56, size * 0.50),
            (size * 0.45, size * 0.78),
            (size * 0.64, size * 0.46),
            (size * 0.50, size * 0.46),
        ]
        draw.polygon(bolt, fill=(255, 232, 115, 255))

    return np.asarray(base)


def overlay_marker_icons(
    image_rgb: np.ndarray,
    *,
    grid_h: int,
    grid_w: int,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    icon_size_px: int | None = None,
) -> np.ndarray:
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3 or grid_h <= 0 or grid_w <= 0:
        return image_rgb

    base = Image.fromarray(image_rgb, mode="RGB").convert("RGBA")
    scale_x = base.width / float(grid_w)
    scale_y = base.height / float(grid_h)
    auto_size = max(14, min(46, int(min(scale_x, scale_y) * 1.2)))
    icon_size = int(icon_size_px) if icon_size_px is not None else auto_size

    def paste_icon(kind: str, marker: list[int] | None) -> None:
        if marker is None or len(marker) != 2:
            return
        row = int(marker[0])
        col = int(marker[1])
        if not (0 <= row < grid_h and 0 <= col < grid_w):
            return
        icon = Image.fromarray(_build_marker_icon(kind, icon_size), mode="RGBA")
        center_x = int(round((col + 0.5) * scale_x))
        center_y = int(round((row + 0.5) * scale_y))
        left = center_x - icon.width // 2
        top = center_y - icon.height // 2
        base.alpha_composite(icon, (left, top))

    paste_icon("main_entry", main_entry)
    paste_icon("electric_board", electric_board)
    return np.asarray(base.convert("RGB"))


def marker_legend_icon(kind: str, *, size: int = 22) -> np.ndarray:
    return _build_marker_icon(kind, size)


def marker_legend_icon_row_html(kind: str, label: str, *, size: int = 18) -> str:
    icon_rgba = _build_marker_icon(kind, size)
    icon = Image.fromarray(icon_rgba, mode="RGBA")
    buffer = io.BytesIO()
    icon.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        '<div style="display:flex;align-items:center;gap:6px;margin:0.35em 0">'
        f'<img src="data:image/png;base64,{encoded}" '
        'style="min-width:18px;width:18px;height:18px;flex-shrink:0;'
        'border:1px solid #999;border-radius:3px;background:#fff;object-fit:contain"/>'
        f'<span style="font-size:13px;line-height:1.35">{label}</span></div>'
    )


def render_interactive_review(
    image: np.ndarray,
    *,
    grid_w: int,
    grid_h: int,
    mode: str,
    paint_enabled: bool,
    paint_mode: str,
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
            paint_mode=paint_mode,
            max_height=760,
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
