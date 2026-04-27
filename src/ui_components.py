"""
Shared UI helpers for floorplan visualization.

Used by wizard_app.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

STRUCT_RGB: dict[int, tuple[int, int, int]] = {
    0: (217, 214, 243),  # exterior (lavender / cool gray)
    1: (63, 70, 82),     # wall
    2: (143, 211, 255),  # window
    3: (185, 137, 90),   # door
    4: (243, 245, 247),  # interior
}

DEVICE_STYLE: dict[str, dict[str, object]] = {
    "panel":         {"code": 10, "rgb": (68, 114, 196),  "label": "PB",  "name": "Panel"},
    "keyboard":      {"code": 11, "rgb": (112, 173, 71),  "label": "KB",  "name": "Teclado"},
    "magnetic":      {"code": 12, "rgb": (255, 192, 0),   "label": "MG",  "name": "Magnetico"},
    "pir":           {"code": 13, "rgb": (255, 87, 34),   "label": "PIR", "name": "PIR"},
    "siren_indoor":  {"code": 14, "rgb": (156, 39, 176),  "label": "SI",  "name": "Sirena Int."},
    "siren_outdoor": {"code": 15, "rgb": (33, 150, 243),  "label": "SO",  "name": "Sirena Ext."},
}

ICON_ROOT = Path(__file__).resolve().parents[1] / "assets" / "icons"
MARKER_ICON_PATHS: dict[str, Path] = {
    "main_entry": ICON_ROOT / "main-entry-door.png",
    "electric_board": ICON_ROOT / "electric-panel.png",
}
DEVICE_ICON_PATHS: dict[str, Path] = {
    "panel": ICON_ROOT / "panel.png",
    "keyboard": ICON_ROOT / "keyboard.png",
    "magnetic": ICON_ROOT / "magnetic.png",
    "pir": ICON_ROOT / "pir.png",
    "siren_indoor": ICON_ROOT / "siren-indoor.png",
    "siren_outdoor": ICON_ROOT / "siren-outdoor.png",
}

# Cell radius for proposal device squares (radius 2 → 5×5 cells), aligned with
# ``overlay_markers(..., marker_radius=2)`` for front door / electrical board.
DEVICE_DRAW_RADIUS: int = 2

# Wizard: validation highlight on struct preview (row, col cells).
VALIDATION_ERROR_OVERLAY_RGB: tuple[int, int, int] = (255, 0, 180)
VALIDATION_WARNING_SHORT_FREE_RGB: tuple[int, int, int] = (255, 165, 0)
# Long-side wall warning: the cell is usually struct=1 (dark gray), so use a distinct color.
VALIDATION_WARNING_LONG_WALL_RGB: tuple[int, int, int] = (0, 255, 220)

WIZARD_VALIDATION_LEGEND_ROWS: tuple[tuple[tuple[int, int, int], str], ...] = (
    (VALIDATION_WARNING_SHORT_FREE_RGB, "Check opening edge"),
    (VALIDATION_WARNING_LONG_WALL_RGB, "Check nearby wall"),
    (VALIDATION_ERROR_OVERLAY_RGB, "Must fix before continuing"),
)


def wizard_legend_swatch_row_html(rgb: tuple[int, int, int], label: str) -> str:
    """One row: colored square + label (same layout as struct legend in wizard)."""
    r, g, b = rgb
    return (
        f'<div style="display:flex;align-items:center;gap:6px;margin:0.35em 0">'
        f'<div style="min-width:18px;width:18px;height:18px;flex-shrink:0;'
        f'background:rgb({r},{g},{b});border:1px solid #999;border-radius:3px"></div>'
        f'<span style="font-size:13px;line-height:1.35">{label}</span></div>'
    )


def rgb_from_struct(z: np.ndarray) -> np.ndarray:
    """H x W x 3 RGB image, one pixel per cell."""
    h, w = z.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in STRUCT_RGB.items():
        rgb[z == k] = col
    return rgb


def overlay_validation_highlights(
    rgb: np.ndarray,
    *,
    error_cells: set[tuple[int, int]] | None = None,
    warning_short_free_cells: set[tuple[int, int]] | None = None,
    warning_long_wall_cells: set[tuple[int, int]] | None = None,
    error_alpha: float = 0.52,
    warning_alpha: float = 0.42,
    long_wall_alpha: float = 0.55,
) -> np.ndarray:
    """Tint grid cells that appear in topology / placement validation (row, col)."""
    out = rgb.copy()
    h, w = rgb.shape[:2]
    if warning_long_wall_cells:
        lm = np.zeros((h, w), dtype=bool)
        for r, c in warning_long_wall_cells:
            if 0 <= r < h and 0 <= c < w:
                lm[r, c] = True
        if lm.any():
            out = alpha_blend(out, lm, VALIDATION_WARNING_LONG_WALL_RGB, alpha=long_wall_alpha)
    if warning_short_free_cells:
        wm = np.zeros((h, w), dtype=bool)
        for r, c in warning_short_free_cells:
            if 0 <= r < h and 0 <= c < w:
                wm[r, c] = True
        if wm.any():
            out = alpha_blend(out, wm, VALIDATION_WARNING_SHORT_FREE_RGB, alpha=warning_alpha)
    if error_cells:
        em = np.zeros((h, w), dtype=bool)
        for r, c in error_cells:
            if 0 <= r < h and 0 <= c < w:
                em[r, c] = True
        if em.any():
            out = alpha_blend(out, em, VALIDATION_ERROR_OVERLAY_RGB, alpha=error_alpha)
    return out


def overlay_markers(
    rgb: np.ndarray,
    *,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    marker_radius: int = DEVICE_DRAW_RADIUS,
) -> np.ndarray:
    out = rgb.copy()
    if main_entry is not None and len(main_entry) == 2:
        draw_square(out, int(main_entry[0]), int(main_entry[1]), (255, 0, 0), radius=marker_radius)
    if electric_board is not None and len(electric_board) == 2:
        draw_square(out, int(electric_board[0]), int(electric_board[1]), (0, 0, 255), radius=marker_radius)
    return out


def alpha_blend(
    base: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float,
) -> np.ndarray:
    out = base.copy().astype(np.float32)
    c = np.array(color, dtype=np.float32).reshape(3)
    out[mask] = out[mask] * (1.0 - alpha) + c * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def draw_square(
    img: np.ndarray, r: int, c: int, color: tuple[int, int, int], radius: int = 1,
) -> None:
    h, w, _ = img.shape
    r0, r1 = max(0, r - radius), min(h - 1, r + radius)
    c0, c1 = max(0, c - radius), min(w - 1, c + radius)
    img[r0 : r1 + 1, c0 : c1 + 1] = np.array(color, dtype=np.uint8)


def _load_icon_rgba(path: Path, size: int) -> np.ndarray | None:
    if not path.is_file():
        return None
    try:
        with Image.open(path) as icon_image:
            rgba = icon_image.convert("RGBA")
            alpha = rgba.split()[3]
            bbox = alpha.getbbox()
            if bbox is not None:
                rgba = rgba.crop(bbox)
            resized = rgba.resize((size, size), Image.LANCZOS)
            return np.asarray(resized)
    except Exception:
        return None


def apply_highlight_ring_to_rgb(
    rgb: np.ndarray,
    *,
    grid_h: int,
    grid_w: int,
    row: int | None = None,
    col: int | None = None,
    pixel_center: tuple[int, int] | None = None,
    color: tuple[int, int, int] = (220, 38, 38),
    ring_fraction: float = 0.4,
) -> np.ndarray:
    """Draw a circular highlight ring around a cell center or explicit pixel center."""
    if grid_h <= 0 or grid_w <= 0:
        return rgb
    h_px, w_px = rgb.shape[0], rgb.shape[1]
    scale_x = w_px / float(grid_w)
    scale_y = h_px / float(grid_h)
    radius = max(14, int(min(scale_x, scale_y) * ring_fraction))

    if pixel_center is not None:
        cx, cy = int(pixel_center[0]), int(pixel_center[1])
    elif row is not None and col is not None:
        if not (0 <= row < grid_h and 0 <= col < grid_w):
            return rgb
        cx = int(round((col + 0.5) * scale_x))
        cy = int(round((row + 0.5) * scale_y))
    else:
        return rgb

    base = Image.fromarray(rgb.astype(np.uint8), mode="RGB").convert("RGBA")
    ring_layer = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring_layer)
    bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(bbox, outline=(*color, 255), width=5)
    inner = max(8, radius - 10)
    bbox2 = (cx - inner, cy - inner, cx + inner, cy + inner)
    draw.ellipse(bbox2, outline=(*color, 140), width=3)
    combined = Image.alpha_composite(base, ring_layer)
    return np.asarray(combined.convert("RGB"))


def _paste_icon_at_cell(
    canvas: Image.Image,
    icon_rgba: np.ndarray,
    *,
    row: int,
    col: int,
    grid_h: int,
    grid_w: int,
    offset_px: tuple[int, int] = (0, 0),
    draw_halo: bool = False,
) -> None:
    if not (0 <= row < grid_h and 0 <= col < grid_w):
        return
    scale_x = canvas.width / float(grid_w)
    scale_y = canvas.height / float(grid_h)
    center_x = int(round((col + 0.5) * scale_x)) + int(offset_px[0])
    center_y = int(round((row + 0.5) * scale_y)) + int(offset_px[1])
    icon = Image.fromarray(icon_rgba, mode="RGBA")
    left = center_x - icon.width // 2
    top = center_y - icon.height // 2
    # Keep icon fully visible even when collision-offset pushes it to borders.
    left = max(0, min(left, canvas.width - icon.width))
    top = max(0, min(top, canvas.height - icon.height))
    if draw_halo:
        draw = ImageDraw.Draw(canvas, mode="RGBA")
        halo_radius = max(icon.width, icon.height) // 2 + 3
        draw.ellipse(
            (
                center_x - halo_radius,
                center_y - halo_radius,
                center_x + halo_radius,
                center_y + halo_radius,
            ),
            fill=(255, 255, 255, 148),
        )
    canvas.alpha_composite(icon, (left, top))


def overlay_marker_icons(
    rgb: np.ndarray,
    *,
    grid_h: int,
    grid_w: int,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    icon_size_px: int = 20,
) -> np.ndarray:
    out = Image.fromarray(rgb.astype(np.uint8), mode="RGB").convert("RGBA")
    if main_entry is not None and len(main_entry) == 2:
        icon = _load_icon_rgba(MARKER_ICON_PATHS["main_entry"], icon_size_px)
        if icon is not None:
            _paste_icon_at_cell(
                out,
                icon,
                row=int(main_entry[0]),
                col=int(main_entry[1]),
                grid_h=grid_h,
                grid_w=grid_w,
            )
    if electric_board is not None and len(electric_board) == 2:
        icon = _load_icon_rgba(MARKER_ICON_PATHS["electric_board"], icon_size_px)
        if icon is not None:
            _paste_icon_at_cell(
                out,
                icon,
                row=int(electric_board[0]),
                col=int(electric_board[1]),
                grid_h=grid_h,
                grid_w=grid_w,
            )
    return np.asarray(out.convert("RGB"))


def overlay_device_icons(
    rgb: np.ndarray,
    *,
    grid_h: int,
    grid_w: int,
    devices: list[dict[str, Any]],
    icon_size_px: int = 20,
    reserved_cells: set[tuple[int, int]] | None = None,
) -> tuple[np.ndarray, dict[str, int]]:
    out = Image.fromarray(rgb.astype(np.uint8), mode="RGB").convert("RGBA")
    counts: dict[str, int] = {}
    used_per_cell: dict[tuple[int, int], int] = {}
    for reserved in reserved_cells or set():
        used_per_cell[reserved] = max(used_per_cell.get(reserved, 0), 1)

    spread = max(6, int(icon_size_px * 0.8))
    offset_slots = [
        (0, 0),
        (spread, 0),
        (-spread, 0),
        (0, spread),
        (0, -spread),
        (spread, spread),
        (-spread, spread),
        (spread, -spread),
        (-spread, -spread),
    ]

    for device in devices:
        device_type = str(device.get("device_type") or "").lower()
        cell = device.get("cell") or []
        if device_type not in DEVICE_ICON_PATHS or not isinstance(cell, (list, tuple)) or len(cell) != 2:
            continue
        row, col = int(cell[0]), int(cell[1])
        icon = _load_icon_rgba(DEVICE_ICON_PATHS[device_type], icon_size_px)
        if icon is None:
            continue
        cell_key = (row, col)
        slot_idx = used_per_cell.get(cell_key, 0)
        used_per_cell[cell_key] = slot_idx + 1
        offset = offset_slots[slot_idx % len(offset_slots)]
        _paste_icon_at_cell(
            out,
            icon,
            row=row,
            col=col,
            grid_h=grid_h,
            grid_w=grid_w,
            offset_px=offset,
            draw_halo=True,
        )
        counts[device_type] = counts.get(device_type, 0) + 1
    return np.asarray(out.convert("RGB")), counts


def proposal_device_icon_pixel_center(
    devices: list[dict[str, Any]],
    device_index: int,
    *,
    grid_h: int,
    grid_w: int,
    image_h: int,
    image_w: int,
    reserved_cells: set[tuple[int, int]] | None = None,
    icon_size_px: int = 24,
) -> tuple[int, int] | None:
    """Pixel center of the device icon as drawn by overlay_device_icons (offsets + collisions)."""
    if device_index < 0 or device_index >= len(devices):
        return None

    used_per_cell: dict[tuple[int, int], int] = {}
    for reserved in reserved_cells or set():
        used_per_cell[reserved] = max(used_per_cell.get(reserved, 0), 1)

    spread = max(6, int(icon_size_px * 0.8))
    offset_slots = [
        (0, 0),
        (spread, 0),
        (-spread, 0),
        (0, spread),
        (0, -spread),
        (spread, spread),
        (-spread, spread),
        (spread, -spread),
        (-spread, -spread),
    ]

    def _cell_center_pixels(r: int, c: int) -> tuple[int, int]:
        sx = image_w / float(grid_w)
        sy = image_h / float(grid_h)
        return (int(round((c + 0.5) * sx)), int(round((r + 0.5) * sy)))

    for idx, device in enumerate(devices):
        device_type = str(device.get("device_type") or "").lower()
        cell = device.get("cell") or []
        if device_type not in DEVICE_ICON_PATHS or not isinstance(cell, (list, tuple)) or len(cell) != 2:
            if idx == device_index:
                raw = devices[device_index].get("cell")
                if isinstance(raw, (list, tuple)) and len(raw) == 2:
                    return _cell_center_pixels(int(raw[0]), int(raw[1]))
                return None
            continue
        row, col = int(cell[0]), int(cell[1])
        icon = _load_icon_rgba(DEVICE_ICON_PATHS[device_type], icon_size_px)
        if icon is None:
            if idx == device_index:
                return _cell_center_pixels(row, col)
            continue
        cell_key = (row, col)
        slot_idx = used_per_cell.get(cell_key, 0)
        used_per_cell[cell_key] = slot_idx + 1
        offset = offset_slots[slot_idx % len(offset_slots)]

        if idx == device_index:
            sx = image_w / float(grid_w)
            sy = image_h / float(grid_h)
            cx = int(round((col + 0.5) * sx)) + int(offset[0])
            cy = int(round((row + 0.5) * sy)) + int(offset[1])
            return (cx, cy)

    raw_cell = devices[device_index].get("cell")
    if isinstance(raw_cell, (list, tuple)) and len(raw_cell) == 2:
        return _cell_center_pixels(int(raw_cell[0]), int(raw_cell[1]))
    return None


def get_device_icon_image(device_type: str, *, size: int = 20) -> np.ndarray | None:
    return _load_icon_rgba(DEVICE_ICON_PATHS.get(str(device_type).lower(), Path()), size)


def upscale_rgb(rgb: np.ndarray, target_w: int) -> np.ndarray:
    """Nearest-neighbour upscale to *target_w* keeping aspect ratio.

    Returns an array whose naturalWidth matches the display width so the
    ``streamlit_image_coordinates`` component reports pixel-perfect coordinates
    with no CSS scaling ambiguity.
    """
    from PIL import Image

    h, w = rgb.shape[:2]
    if w <= 0 or h <= 0 or target_w <= w:
        return rgb
    target_h = max(1, round(h * target_w / w))
    pil = Image.fromarray(rgb).resize((target_w, target_h), Image.NEAREST)
    return np.asarray(pil)


def grid_cell_from_display_click(
    coord: dict,
    *,
    native_img_w: int,
    native_img_h: int,
    grid_w: int,
    grid_h: int,
) -> tuple[int, int] | None:
    """Map streamlit_image_coordinates click to grid (col, row).

    When the image was pre-upscaled with :func:`upscale_rgb`,
    ``native_img_w == display_width`` and the mapping is a direct
    division by scale factor.
    """
    if not coord or "x" not in coord or "y" not in coord:
        return None
    disp_w = coord.get("width")
    disp_h = coord.get("height")
    if not disp_w or not disp_h:
        return None
    disp_w = float(disp_w)
    disp_h = float(disp_h)
    if disp_w <= 0 or disp_h <= 0:
        return None
    cx = int(float(coord["x"]) * grid_w / disp_w)
    cy = int(float(coord["y"]) * grid_h / disp_h)
    cx = max(0, min(grid_w - 1, cx))
    cy = max(0, min(grid_h - 1, cy))
    return cx, cy


def effective_struct(base_np: np.ndarray, patch_map: dict[tuple[int, int], int]) -> np.ndarray:
    out = base_np.copy()
    h, w = out.shape
    for (r, c), v in patch_map.items():
        if 0 <= r < h and 0 <= c < w:
            out[r, c] = v
    return out


def load_step05_outputs(step05_dir: Path) -> tuple[dict | None, dict | None]:
    proposal_p = step05_dir / "installation_proposal.json"
    report_p = step05_dir / "alarm_plan_report.json"
    proposal = report = None
    if proposal_p.is_file():
        try:
            proposal = json.loads(proposal_p.read_text(encoding="utf-8"))
        except Exception:
            pass
    if report_p.is_file():
        try:
            report = json.loads(report_p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return proposal, report


def render_proposal_views(
    eff: np.ndarray,
    *,
    proposal: dict | None,
    show_red_zones: bool,
    show_devices: bool,
    replace_base_with_devices: bool,
    main_entry: list[int] | None = None,
    electric_board: list[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, int], int]:
    red_img = rgb_from_struct(eff)
    dev_img = rgb_from_struct(eff)
    device_counts: dict[str, int] = {}
    red_cells_count = 0
    if not proposal:
        return red_img, dev_img, device_counts, red_cells_count

    zones = proposal.get("zones") or []
    devices = proposal.get("devices") or []
    h, w = eff.shape

    if show_red_zones:
        red_mask = np.zeros((h, w), dtype=bool)
        for z in zones:
            zt = str(z.get("zone_type") or "").lower()
            if zt != "red":
                continue
            for rc in z.get("cells") or []:
                if not isinstance(rc, (list, tuple)) or len(rc) != 2:
                    continue
                r, c = int(rc[0]), int(rc[1])
                if 0 <= r < h and 0 <= c < w:
                    red_mask[r, c] = True
        red_cells_count = int(red_mask.sum())
        if red_cells_count > 0:
            red_img = alpha_blend(red_img, red_mask, (220, 20, 60), alpha=0.42)

    if show_devices:
        dev_img, device_counts = overlay_device_icons(
            dev_img,
            grid_h=h,
            grid_w=w,
            devices=[d for d in devices if isinstance(d, dict)],
            icon_size_px=20,
        )

    if main_entry is not None or electric_board is not None:
        dev_img = overlay_marker_icons(
            dev_img,
            grid_h=h,
            grid_w=w,
            main_entry=main_entry,
            electric_board=electric_board,
            icon_size_px=20,
        )

    return red_img, dev_img, device_counts, red_cells_count


def compute_pre_suppression_red_mask(
    eff: np.ndarray,
    *,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    cell_size_m: float,
    security_level: str = "optimal",
) -> np.ndarray | None:
    """Build RED zones from exterior openings (before magnetic/PIR suppression)."""
    try:
        from acala_engine import build_scenario, make_element
        from acala_engine.zones import build_red_zones_for_exterior_openings
    except Exception:
        return None

    struct_to_acala = {0: -1, 1: 1, 2: 3, 3: 2, 4: 0}
    cells = [[struct_to_acala[int(v)] for v in row] for row in eff]
    elements: list[Any] = []
    if main_entry is not None and len(main_entry) == 2:
        elements.append(
            make_element(id="e_me", element_type="main_entry", position=(int(main_entry[0]), int(main_entry[1])))
        )
    if electric_board is not None and len(electric_board) == 2:
        elements.append(
            make_element(id="e_eb", element_type="electric_board", position=(int(electric_board[0]), int(electric_board[1])))
        )
    scenario = build_scenario(
        cells=cells, cell_size_m=float(cell_size_m), security_level=str(security_level),
        fixture_name="preview", rooms=[], elements=elements,
    )
    zones = build_red_zones_for_exterior_openings(scenario)
    h, w = eff.shape
    mask = np.zeros((h, w), dtype=bool)
    for z in zones:
        for rc in z.cells:
            r, c = int(rc[0]), int(rc[1])
            if 0 <= r < h and 0 <= c < w:
                mask[r, c] = True
    return mask


def render_stepper(current: int, labels: tuple[str, ...] = ("Upload plan", "Configure", "Result")) -> None:
    """Render a 3-step wizard stepper bar via HTML/CSS."""
    css = """
    <style>
    .wiz-stepper{display:flex;align-items:center;justify-content:center;gap:0;margin:0.6rem 0 1.4rem 0}
    .wiz-step{display:flex;align-items:center;gap:0}
    .wiz-circle{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;
      font-weight:700;font-size:15px;border:2px solid #d0d0d0;color:#999;background:#fafafa;flex-shrink:0}
    .wiz-circle.active{border-color:#1976d2;color:#fff;background:#1976d2}
    .wiz-circle.done{border-color:#43a047;color:#fff;background:#43a047}
    .wiz-label{margin-left:8px;font-size:14px;color:#888;white-space:nowrap}
    .wiz-label.active{color:#1976d2;font-weight:600}
    .wiz-label.done{color:#43a047;font-weight:500}
    .wiz-line{width:60px;height:2px;background:#d0d0d0;margin:0 12px;flex-shrink:0}
    .wiz-line.done{background:#43a047}
    </style>
    """
    parts = [css, '<div class="wiz-stepper">']
    for i, label in enumerate(labels):
        step_num = i + 1
        if step_num < current:
            cls_c, cls_l, txt = "done", "done", "&#10003;"
        elif step_num == current:
            cls_c, cls_l, txt = "active", "active", str(step_num)
        else:
            cls_c, cls_l, txt = "", "", str(step_num)
        parts.append(f'<div class="wiz-step"><div class="wiz-circle {cls_c}">{txt}</div>')
        parts.append(f'<span class="wiz-label {cls_l}">{label}</span></div>')
        if i < len(labels) - 1:
            line_cls = "done" if step_num < current else ""
            parts.append(f'<div class="wiz-line {line_cls}"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def inject_wizard_css() -> None:
    """Global CSS tweaks for modern/minimal wizard look."""
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden}
    footer {visibility: hidden}
    .block-container {padding-top: 1.5rem}
    div[data-testid="stMetric"] {
        background: #f8f9fa; border-radius: 8px; padding: 12px 16px;
        border: 1px solid #e9ecef; text-align: center;
    }
    div[data-testid="stMetric"] label {font-size: 13px !important; color: #666 !important}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 28px !important; font-weight: 700 !important}
    </style>
    """, unsafe_allow_html=True)
