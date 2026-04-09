"""
Shared UI helpers for floorplan visualization.

Used by both matrix_review_app.py (advanced tool) and wizard_app.py (user wizard).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

STRUCT_RGB: dict[int, tuple[int, int, int]] = {
    0: (200, 200, 255),  # exterior
    1: (40, 40, 40),     # wall
    2: (0, 180, 255),    # window
    3: (0, 100, 0),      # door
    4: (255, 220, 180),  # interior
}

DEVICE_STYLE: dict[str, dict[str, object]] = {
    "panel":         {"code": 10, "rgb": (68, 114, 196),  "label": "PB",  "name": "Panel"},
    "keyboard":      {"code": 11, "rgb": (112, 173, 71),  "label": "KB",  "name": "Teclado"},
    "magnetic":      {"code": 12, "rgb": (255, 192, 0),   "label": "MG",  "name": "Magnetico"},
    "pir":           {"code": 13, "rgb": (255, 87, 34),   "label": "PIR", "name": "PIR"},
    "siren_indoor":  {"code": 14, "rgb": (156, 39, 176),  "label": "SI",  "name": "Sirena Int."},
    "siren_outdoor": {"code": 15, "rgb": (33, 150, 243),  "label": "SO",  "name": "Sirena Ext."},
}

# Cell radius for proposal device squares (radius 2 → 5×5 cells), aligned with
# ``overlay_markers(..., marker_radius=2)`` for puerta principal / tablero.
DEVICE_DRAW_RADIUS: int = 2


def rgb_from_struct(z: np.ndarray) -> np.ndarray:
    """H x W x 3 RGB image, one pixel per cell."""
    h, w = z.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in STRUCT_RGB.items():
        rgb[z == k] = col
    return rgb


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
    for (r, c), v in patch_map.items():
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
        if replace_base_with_devices:
            repl = eff.copy()
            for d in devices:
                dt = str(d.get("device_type") or "").lower()
                style = DEVICE_STYLE.get(dt)
                cell = d.get("cell") or []
                if style is None or not isinstance(cell, (list, tuple)) or len(cell) != 2:
                    continue
                r, c = int(cell[0]), int(cell[1])
                if 0 <= r < h and 0 <= c < w:
                    repl[r, c] = int(style["code"])  # type: ignore[index]
                    device_counts[dt] = device_counts.get(dt, 0) + 1
            dev_img = rgb_from_struct(repl)
            for dt, style in DEVICE_STYLE.items():
                code = int(style["code"])  # type: ignore[index]
                rgb_val = style["rgb"]
                dev_img[repl == code] = np.array(rgb_val, dtype=np.uint8)
            for d in devices:
                dt = str(d.get("device_type") or "").lower()
                style = DEVICE_STYLE.get(dt)
                cell = d.get("cell") or []
                if style is None or not isinstance(cell, (list, tuple)) or len(cell) != 2:
                    continue
                r, c = int(cell[0]), int(cell[1])
                if 0 <= r < h and 0 <= c < w:
                    draw_square(
                        dev_img, r, c, style["rgb"], radius=DEVICE_DRAW_RADIUS  # type: ignore[index]
                    )
        else:
            for d in devices:
                dt = str(d.get("device_type") or "").lower()
                style = DEVICE_STYLE.get(dt)
                cell = d.get("cell") or []
                if style is None or not isinstance(cell, (list, tuple)) or len(cell) != 2:
                    continue
                r, c = int(cell[0]), int(cell[1])
                if 0 <= r < h and 0 <= c < w:
                    draw_square(
                        dev_img, r, c, style["rgb"], radius=DEVICE_DRAW_RADIUS  # type: ignore[index]
                    )
                    device_counts[dt] = device_counts.get(dt, 0) + 1

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


def render_stepper(current: int, labels: tuple[str, ...] = ("Cargar plano", "Configurar", "Resultado")) -> None:
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
