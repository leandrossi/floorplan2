"""
Matrix review UI (MVP): validate step04 grid, place main_entry + electric_board, optional struct paint.

Workflow: run final step04 → review_bundle.json is written →
  streamlit run src/matrix_review_app.py
Then save review_approved.json and run:
  python src/final_step05_plan_alarm.py

Run from project root: PYTHONPATH=src streamlit run src/matrix_review_app.py

Large matrices: use the sidebar "Preview display width" for the floor PNG tab.
Use **Full struct** for labeled row/col, pan/zoom (View mode), and click-to-place (placement tools).
Full struct placement uses raster clicks (display→cell mapping); Plotly is for labeled navigation / zoom.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import streamlit as st

# Project root = parent of src/
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from review_bundle_io import (  # noqa: E402
    STRUCT_ENCODING,
    load_approved,
    validate_approved,
)

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
except ImportError:
    streamlit_image_coordinates = None  # type: ignore[misc, assignment]

try:
    import plotly.graph_objects as go
except ImportError:
    go = None  # type: ignore[assignment]

DEFAULT_BUNDLE = _PROJECT_ROOT / "output" / "final" / "step04" / "review_bundle.json"
DEFAULT_STEP05_DIR = _PROJECT_ROOT / "output" / "final" / "step05"

# Match final_step04 struct preview colors (BGR-ish order for OpenCV; here RGB for plotly/UI)
_STRUCT_RGB: dict[int, tuple[int, int, int]] = {
    0: (200, 200, 255),  # exterior
    1: (40, 40, 40),  # wall
    2: (0, 180, 255),  # window
    3: (0, 100, 0),  # door
    4: (255, 220, 180),  # interior
}

_DEVICE_STYLE: dict[str, dict[str, object]] = {
    "panel": {"code": 10, "rgb": (68, 114, 196), "label": "PB"},
    "keyboard": {"code": 11, "rgb": (112, 173, 71), "label": "KB"},
    "magnetic": {"code": 12, "rgb": (255, 192, 0), "label": "MG"},
    "pir": {"code": 13, "rgb": (255, 87, 34), "label": "PIR"},
    "siren_indoor": {"code": 14, "rgb": (156, 39, 176), "label": "SI"},
    "siren_outdoor": {"code": 15, "rgb": (33, 150, 243), "label": "SO"},
}


def _effective_struct(base_np: np.ndarray, patch_map: dict[tuple[int, int], int]) -> np.ndarray:
    out = base_np.copy()
    for (r, c), v in patch_map.items():
        out[r, c] = v
    return out


def _patch_map_to_list(pm: dict[tuple[int, int], int]) -> list[dict[str, int]]:
    return [{"r": r, "c": c, "v": int(v)} for (r, c), v in sorted(pm.items())]


def _rgb_from_struct(z: np.ndarray) -> np.ndarray:
    """H×W×3 RGB image, one pixel per cell (same geometry as floor_like_preview)."""
    h, w = z.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in _STRUCT_RGB.items():
        rgb[z == k] = col
    return rgb


def _grid_cell_from_display_click(
    coord: dict,
    *,
    native_img_w: int,
    native_img_h: int,
    grid_w: int,
    grid_h: int,
) -> tuple[int, int] | None:
    """
    streamlit_image_coordinates returns x,y in the **rendered** image (width/height pixels).
    Map through native bitmap size to grid column/row (0-based).
    """
    if not coord or "x" not in coord or "y" not in coord:
        return None
    if native_img_w <= 0 or native_img_h <= 0:
        return None
    disp_w = max(1, int(coord.get("width") or 1))
    disp_h = max(1, int(coord.get("height") or 1))
    x_nat = float(coord["x"]) * native_img_w / disp_w
    y_nat = float(coord["y"]) * native_img_h / disp_h
    cx = int(x_nat * grid_w / native_img_w)
    cy = int(y_nat * grid_h / native_img_h)
    cx = max(0, min(grid_w - 1, cx))
    cy = max(0, min(grid_h - 1, cy))
    return cx, cy


def _native_png_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(path) as im:
            w_px, h_px = im.size
            return int(w_px), int(h_px)
    except Exception:
        return None


def _overlay_markers(
    rgb: np.ndarray,
    *,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
) -> np.ndarray:
    out = rgb.copy()
    if main_entry is not None and len(main_entry) == 2:
        r, c = int(main_entry[0]), int(main_entry[1])
        if 0 <= r < out.shape[0] and 0 <= c < out.shape[1]:
            out[r, c] = (255, 0, 0)
    if electric_board is not None and len(electric_board) == 2:
        r, c = int(electric_board[0]), int(electric_board[1])
        if 0 <= r < out.shape[0] and 0 <= c < out.shape[1]:
            out[r, c] = (0, 0, 255)
    return out


def _alpha_blend(base: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    out = base.copy().astype(np.float32)
    c = np.array(color, dtype=np.float32).reshape(1, 1, 3)
    out[mask] = out[mask] * (1.0 - alpha) + c.reshape(3) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def _draw_square(img: np.ndarray, r: int, c: int, color: tuple[int, int, int], radius: int = 1) -> None:
    h, w, _ = img.shape
    r0, r1 = max(0, r - radius), min(h - 1, r + radius)
    c0, c1 = max(0, c - radius), min(w - 1, c + radius)
    img[r0 : r1 + 1, c0 : c1 + 1] = np.array(color, dtype=np.uint8)


def _load_step05_outputs(step05_dir: Path) -> tuple[dict | None, dict | None]:
    proposal_p = step05_dir / "installation_proposal.json"
    report_p = step05_dir / "alarm_plan_report.json"
    proposal = None
    report = None
    if proposal_p.is_file():
        try:
            proposal = json.loads(proposal_p.read_text(encoding="utf-8"))
        except Exception:
            proposal = None
    if report_p.is_file():
        try:
            report = json.loads(report_p.read_text(encoding="utf-8"))
        except Exception:
            report = None
    return proposal, report


def _render_proposal_views(
    eff: np.ndarray,
    *,
    proposal: dict | None,
    show_red_zones: bool,
    show_devices: bool,
    replace_base_with_devices: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, int], int]:
    red_img = _rgb_from_struct(eff)
    dev_img = _rgb_from_struct(eff)
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
            red_img = _alpha_blend(red_img, red_mask, (220, 20, 60), alpha=0.42)

    if show_devices:
        if replace_base_with_devices:
            repl = eff.copy()
            for d in devices:
                dt = str(d.get("device_type") or "").lower()
                style = _DEVICE_STYLE.get(dt)
                cell = d.get("cell") or []
                if style is None or not isinstance(cell, (list, tuple)) or len(cell) != 2:
                    continue
                r, c = int(cell[0]), int(cell[1])
                if 0 <= r < h and 0 <= c < w:
                    repl[r, c] = int(style["code"])  # type: ignore[index]
                    device_counts[dt] = device_counts.get(dt, 0) + 1
            dev_img = _rgb_from_struct(repl)
            for dt, style in _DEVICE_STYLE.items():
                code = int(style["code"])  # type: ignore[index]
                rgb = style["rgb"]  # type: ignore[assignment]
                dev_img[repl == code] = np.array(rgb, dtype=np.uint8)
        else:
            for d in devices:
                dt = str(d.get("device_type") or "").lower()
                style = _DEVICE_STYLE.get(dt)
                cell = d.get("cell") or []
                if style is None or not isinstance(cell, (list, tuple)) or len(cell) != 2:
                    continue
                r, c = int(cell[0]), int(cell[1])
                if 0 <= r < h and 0 <= c < w:
                    _draw_square(dev_img, r, c, style["rgb"])  # type: ignore[index]
                    device_counts[dt] = device_counts.get(dt, 0) + 1

    return red_img, dev_img, device_counts, red_cells_count


def _compute_pre_suppression_red_mask(
    eff: np.ndarray,
    *,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
    cell_size_m: float,
    security_level: str = "optimal",
) -> np.ndarray | None:
    """
    Build RED zones directly from exterior openings (before magnetic/PIR suppression),
    using current effective struct + markers.
    """
    try:
        from acala_engine import build_scenario, make_element
        from acala_engine.zones import build_red_zones_for_exterior_openings
    except Exception:
        return None

    struct_to_acala = {0: -1, 1: 1, 2: 3, 3: 2, 4: 0}
    cells = [[struct_to_acala[int(v)] for v in row] for row in eff]
    elements: list = []
    if main_entry is not None and len(main_entry) == 2:
        elements.append(
            make_element(
                id="elem_main_entry",
                element_type="main_entry",
                position=(int(main_entry[0]), int(main_entry[1])),
            )
        )
    if electric_board is not None and len(electric_board) == 2:
        elements.append(
            make_element(
                id="elem_electric_board",
                element_type="electric_board",
                position=(int(electric_board[0]), int(electric_board[1])),
            )
        )
    scenario = build_scenario(
        cells=cells,
        cell_size_m=float(cell_size_m),
        security_level=str(security_level),
        fixture_name="proposal_preview",
        rooms=[],
        elements=elements,
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


def _discrete_struct_colorscale() -> list[list]:
    """Piecewise [0,1] colorscale: (z - zmin) / (zmax - zmin) with zmin=-0.5, zmax=4.5 → bands for 0..4."""
    stops: list[list] = []
    for v in range(5):
        r, g, b = _STRUCT_RGB[v]
        col = f"rgb({r},{g},{b})"
        t0 = v / 5.0
        t1 = (v + 1) / 5.0
        stops.append([t0, col])
        stops.append([t1, col])
    return stops


def _plotly_struct_figure(
    eff: np.ndarray,
    *,
    title: str,
    main_entry: list[int] | None,
    electric_board: list[int] | None,
):
    """Heatmap for labeled navigation; row 0 at top (same as matrix / PNG). Placement uses raster clicks."""
    assert go is not None
    h_cells, w_cells = eff.shape
    z = eff.astype(float)
    xs = list(range(w_cells))
    ys = list(range(h_cells))
    hm = go.Heatmap(
        z=z,
        x=xs,
        y=ys,
        zmin=-0.5,
        zmax=4.5,
        colorscale=_discrete_struct_colorscale(),
        showscale=False,
        hovertemplate="row=%{y}<br>col=%{x}<br>struct=%{z}<extra></extra>",
        xgap=0,
        ygap=0,
    )
    fig = go.Figure(data=[hm])
    if main_entry is not None and len(main_entry) == 2:
        mr, mc = int(main_entry[0]), int(main_entry[1])
        if 0 <= mr < h_cells and 0 <= mc < w_cells:
            fig.add_trace(
                go.Scatter(
                    x=[mc],
                    y=[mr],
                    mode="markers",
                    name="main entry",
                    marker=dict(size=12, color="red", symbol="circle", line=dict(width=2, color="white")),
                    hovertemplate="main entry<br>row=%{y}<br>col=%{x}<extra></extra>",
                )
            )
    if electric_board is not None and len(electric_board) == 2:
        br, bc = int(electric_board[0]), int(electric_board[1])
        if 0 <= br < h_cells and 0 <= bc < w_cells:
            fig.add_trace(
                go.Scatter(
                    x=[bc],
                    y=[br],
                    mode="markers",
                    name="electric board",
                    marker=dict(size=12, color="blue", symbol="square", line=dict(width=2, color="white")),
                    hovertemplate="electric board<br>row=%{y}<br>col=%{x}<extra></extra>",
                )
            )
    # Tighter margins + taller figure so cells are larger and wide layouts use space better.
    row_px = max(10, min(22, int(3200 / max(h_cells, 1))))
    fig_h = min(2800, max(480, h_cells * row_px))
    fig.update_layout(
        title=title,
        margin=dict(l=52, r=16, t=48, b=36),
        height=int(fig_h),
        autosize=True,
        dragmode="pan",
        xaxis=dict(side="top", constrain="domain", title="Column", dtick=1),
        yaxis=dict(
            title="Row",
            autorange="reversed",
            scaleanchor="x",
            scaleratio=1,
            constrain="domain",
            dtick=1,
        ),
    )
    return fig


def _init_session(bundle: dict, bundle_path: Path) -> None:
    struct = np.array(bundle["struct"], dtype=np.uint8)
    st.session_state.struct_base = struct
    st.session_state.bundle_path = str(bundle_path)
    st.session_state.step04_dir = bundle.get("step04_dir") or str(bundle_path.parent)
    st.session_state.patch_map = {}
    st.session_state._img_click_sig = None
    approved_path = Path(st.session_state.step04_dir) / "review_approved.json"
    existing = load_approved(approved_path)
    if existing:
        st.session_state.main_entry = existing.get("main_entry")
        st.session_state.electric_board = existing.get("electric_board")
        for p in existing.get("struct_patch") or []:
            st.session_state.patch_map[(int(p["r"]), int(p["c"]))] = int(p["v"])
    else:
        st.session_state.main_entry = None
        st.session_state.electric_board = None


def _apply_click(
    cx: int,
    cy: int,
    mode: str,
    paint_val: int | None,
    w: int,
    h: int,
    eff: np.ndarray,
) -> None:
    if not (0 <= cx < w and 0 <= cy < h):
        return
    pv = int(paint_val) if mode == "Paint cell" and paint_val is not None else -1
    cur_sig = (cx, cy, mode, pv)
    if cur_sig == st.session_state.get("_img_click_sig"):
        return

    if mode == "Place main entry":
        if int(eff[cy, cx]) != 3:
            st.session_state._review_flash = (
                "Main entry must be a **door** cell (struct=3). In **Full struct** that’s the **green** cell; "
                "on floor_like it’s usually `D` on the façade."
            )
            st.rerun()
            return
    elif mode == "Place electric board":
        if int(eff[cy, cx]) != 4:
            st.session_state._review_flash = (
                "Electric board must be an **interior** cell (struct=4): inside a room — "
                "the beige/tan area in **Full struct**, **not** on wall, door, window, or outside. "
                "Use **Paint cell** with brush 4 first if the grid mislabels that spot."
            )
            st.rerun()
            return

    st.session_state._img_click_sig = cur_sig
    if mode == "Place main entry":
        st.session_state.main_entry = [cy, cx]
    elif mode == "Place electric board":
        st.session_state.electric_board = [cy, cx]
    elif mode == "Paint cell" and paint_val is not None:
        st.session_state.patch_map[(cy, cx)] = int(paint_val)
    st.rerun()


def main() -> None:
    st.set_page_config(page_title="Matrix review", layout="wide")
    st.title("Floorplan matrix review (MVP)")
    st.caption(
        "Pipeline: step04 → this UI → save `review_approved.json` → `python src/final_step05_plan_alarm.py`"
    )

    with st.sidebar:
        st.subheader("Load bundle")
        default_path = st.text_input("review_bundle.json path", value=str(DEFAULT_BUNDLE))
        load_btn = st.button("Load / reload bundle")
        st.subheader("Proposal preview")
        step05_dir_input = st.text_input("step05 dir", value=str(DEFAULT_STEP05_DIR))

    bundle_path = Path(default_path).expanduser()
    if load_btn or "struct_base" not in st.session_state:
        if not bundle_path.is_file():
            st.error(f"File not found: {bundle_path}")
            st.stop()
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        _init_session(bundle, bundle_path)
        st.success(f"Loaded {bundle_path.name} ({bundle['grid_shape'][0]}×{bundle['grid_shape'][1]})")
    elif st.session_state.get("bundle_path") != str(bundle_path):
        if bundle_path.is_file():
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            _init_session(bundle, bundle_path)

    struct_base: np.ndarray = st.session_state.struct_base
    h, w = struct_base.shape
    eff = _effective_struct(struct_base, st.session_state.patch_map)
    native_w_px = w
    native_h_px = h

    if msg := st.session_state.pop("_review_flash", None):
        st.warning(msg)

    with st.sidebar:
        st.subheader("Display")
        preview_width = st.slider(
            "Preview display width (px)",
            min_value=200,
            max_value=2400,
            value=int(min(1400, max(400, min(native_w_px * 4, 1400)))),
            help="Smaller value shrinks the whole map so it fits on screen; coordinates stay correct.",
        )
        struct_map_width = st.slider(
            "Full struct map width (px)",
            min_value=400,
            max_value=3200,
            value=int(min(3000, max(720, min(native_w_px * 10, 2200)))),
            help="Raster struct map (placement tools): one cell per pixel scaled to this width; clicks use display→grid math.",
        )
        st.caption(f"Native grid: {native_w_px}×{native_h_px} cells (1 px/cell in PNG).")

        st.subheader("Mode")
        mode = st.radio(
            "Tool",
            ("View", "Place main entry", "Place electric board", "Paint cell"),
            horizontal=False,
        )
        paint_val = None
        if mode == "Paint cell":
            paint_val = st.selectbox(
                "Brush (struct)",
                options=list(range(5)),
                format_func=lambda v: f"{v} = {STRUCT_ENCODING.get(v, v)}",
            )
        st.subheader("Manual cell (fallback)")
        mr = st.number_input("Row", min_value=0, max_value=h - 1, value=0)
        mc = st.number_input("Col", min_value=0, max_value=w - 1, value=0)
        if st.button("Apply manual cell to current mode"):
            mr_i, mc_i = int(mr), int(mc)
            if mode == "Place main entry":
                if int(eff[mr_i, mc_i]) != 3:
                    st.session_state._review_flash = "Main entry must be struct=3 (door)."
                    st.rerun()
                else:
                    st.session_state.main_entry = [mr_i, mc_i]
            elif mode == "Place electric board":
                if int(eff[mr_i, mc_i]) != 4:
                    st.session_state._review_flash = "Electric board must be struct=4 (interior)."
                    st.rerun()
                else:
                    st.session_state.electric_board = [mr_i, mc_i]
            elif mode == "Paint cell" and paint_val is not None:
                st.session_state.patch_map[(mr_i, mc_i)] = int(paint_val)
            st.rerun()

    preview_path = Path(st.session_state.step04_dir) / "floor_like_preview.png"

    _mode_hints = {
        "View": "Browse only — **Full struct** uses pan (drag) + scroll zoom.",
        "Place main entry": (
            "**Full struct** tab → click the **struct raster** (green = door, struct=3). Adjust *Full struct map width* "
            "for size; Plotly below is zoom-only."
        ),
        "Place electric board": (
            "**Full struct** → raster click on **beige interior** (struct=4). Same scaling as above."
        ),
        "Paint cell": (
            "**Full struct** raster or **Floor preview** → click. Brush **4 = interior** for a valid board cell if needed."
        ),
    }
    st.info(_mode_hints.get(mode, ""))

    tab_click, tab_full, tab_proposal, tab_legend = st.tabs(
        ("Floor preview (click)", "Full struct (pan/zoom)", "Proposal preview", "Legend / status")
    )

    with tab_click:
        st.markdown(
            "**Tip:** Clicks register **only** on this tab’s image. "
            "If the map is too tall, reduce “Preview display width” (scales the whole image)."
        )
        # Always use a live RGB preview here so edits (markers/paint) are visible immediately.
        rgb = _overlay_markers(
            _rgb_from_struct(eff),
            main_entry=st.session_state.get("main_entry"),
            electric_board=st.session_state.get("electric_board"),
        )
        if streamlit_image_coordinates is not None:
            coord = streamlit_image_coordinates(
                rgb,
                key="preview_coords_live",
                width=int(preview_width),
            )
            if coord is not None and mode != "View":
                gh, gw = rgb.shape[0], rgb.shape[1]
                picked = _grid_cell_from_display_click(
                    coord,
                    native_img_w=gw,
                    native_img_h=gh,
                    grid_w=w,
                    grid_h=h,
                )
                if picked is not None:
                    cx, cy = picked
                    _apply_click(cx, cy, mode, paint_val, w, h, eff)
        else:
            st.image(rgb, width=int(preview_width))
            st.warning(
                "Install `streamlit-image-coordinates` for click-to-place: pip install streamlit-image-coordinates"
            )

        if preview_path.is_file():
            with st.expander("Original floor_like preview (reference)", expanded=False):
                st.image(str(preview_path), width=int(preview_width))

    with tab_full:
        st.markdown(
            "**View:** Plotly heatmap with row/column ticks (row **0** at **top**), pan + scroll zoom. "
            "**Place / paint:** use the **struct raster** below — one pixel per cell, scaled to sidebar *Full struct map width*; "
            "clicks map through display size so they track the right cell (Plotly cell-click selection is unreliable on large heatmaps)."
        )
        rgb_struct = _overlay_markers(
            _rgb_from_struct(eff),
            main_entry=st.session_state.get("main_entry"),
            electric_board=st.session_state.get("electric_board"),
        )
        # Placement / paint: raster pick (always reliable vs Plotly selectedData on big grids).
        if mode != "View":
            if streamlit_image_coordinates is None:
                st.warning(
                    "Install `streamlit-image-coordinates` to place markers on Full struct: "
                    "pip install streamlit-image-coordinates"
                )
            else:
                gh, gw = rgb_struct.shape[0], rgb_struct.shape[1]
                coord_fs = streamlit_image_coordinates(
                    rgb_struct,
                    key="full_struct_raster",
                    width=int(struct_map_width),
                    cursor="crosshair",
                )
                if coord_fs is not None:
                    picked_fs = _grid_cell_from_display_click(
                        coord_fs,
                        native_img_w=gw,
                        native_img_h=gh,
                        grid_w=w,
                        grid_h=h,
                    )
                    if picked_fs is not None:
                        cx_fs, cy_fs = picked_fs
                        _apply_click(cx_fs, cy_fs, mode, paint_val, w, h, eff)
        if go is None:
            if mode == "View":
                st.warning("Install plotly for the zoomable chart: pip install plotly")
                st.image(
                    rgb_struct,
                    width=int(struct_map_width),
                    caption="Struct raster fallback (no axis ticks until plotly is installed).",
                )
        else:
            fig = _plotly_struct_figure(
                eff,
                title=f"Full matrix {h}×{w} (● red = main entry, ■ blue = electric board)",
                main_entry=st.session_state.get("main_entry"),
                electric_board=st.session_state.get("electric_board"),
            )
            if mode == "View":
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="struct_plotly_view",
                    on_select="ignore",
                    config={
                        "scrollZoom": True,
                        "displayModeBar": True,
                        "modeBarButtonsToAdd": ["resetViews"],
                    },
                )
            else:
                with st.expander("Zoomable Plotly (same grid — pan/zoom only; place cells on the raster above)", expanded=False):
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        key="struct_plotly_ref",
                        on_select="ignore",
                        config={
                            "scrollZoom": True,
                            "displayModeBar": True,
                            "modeBarButtonsToAdd": ["resetViews"],
                        },
                    )

        st.caption(
            "Markers: main entry • red pixel; electric board • blue pixel. "
            "Widen/tall layout: sidebar *Full struct map width* + Plotly figure height scales with row count."
        )

    with tab_proposal:
        st.markdown("### Step05 proposal preview")
        step05_dir = Path(step05_dir_input).expanduser()
        proposal, report = _load_step05_outputs(step05_dir)
        copt1, copt2, copt3 = st.columns(3)
        with copt1:
            show_red_zones = st.checkbox("Show red zones", value=True)
        with copt2:
            show_devices = st.checkbox("Show devices", value=True)
        with copt3:
            replace_base_with_devices = st.checkbox("Replace base cell with device", value=True)

        if proposal is None:
            st.warning(
                f"Could not load `installation_proposal.json` from `{step05_dir}`. "
                "Run step05 first, then reload this tab."
            )
        red_img, dev_img, device_counts, red_cells_count = _render_proposal_views(
            eff,
            proposal=proposal,
            show_red_zones=show_red_zones,
            show_devices=show_devices,
            replace_base_with_devices=replace_base_with_devices,
        )
        if show_red_zones:
            cell_size_from_report = 0.05
            sec_level_from_report = "optimal"
            if report is not None:
                try:
                    cell_size_from_report = float(report.get("cell_size_m") or cell_size_from_report)
                except Exception:
                    pass
                sec_level_from_report = str(report.get("security_level") or sec_level_from_report)
            pre_mask = _compute_pre_suppression_red_mask(
                eff,
                main_entry=st.session_state.get("main_entry"),
                electric_board=st.session_state.get("electric_board"),
                cell_size_m=cell_size_from_report,
                security_level=sec_level_from_report,
            )
            if pre_mask is not None:
                pre_cnt = int(pre_mask.sum())
                if pre_cnt > 0:
                    red_img = _alpha_blend(_rgb_from_struct(eff), pre_mask, (220, 20, 60), alpha=0.42)
                    red_cells_count = pre_cnt
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("**Floorplan + red zones (before suppression by devices)**")
            st.image(red_img, width=int(preview_width))
            if show_red_zones and red_cells_count == 0:
                st.info("No pre-suppression red zones detected.")
        with v2:
            st.markdown("**Floorplan + devices**")
            st.image(dev_img, width=int(preview_width))

        if show_devices and not device_counts:
            st.warning(
                "Device list is empty. We can still proceed manually, but usually this means "
                "planning constraints removed all placements or proposal data is missing."
            )
            if report:
                st.caption(
                    f"Report hints — warnings: {len(report.get('warnings') or [])}, "
                    f"errors: {len(report.get('errors') or [])}, "
                    f"security_level: {report.get('security_level')}"
                )

        st.markdown("**Device legend / counts**")
        if device_counts:
            st.json(device_counts)
        else:
            st.caption("No devices rendered.")

        if report:
            with st.expander("Step05 report summary"):
                st.json(
                    {
                        "ok": report.get("ok"),
                        "warnings": report.get("warnings"),
                        "errors": report.get("errors"),
                        "device_counts": report.get("device_counts"),
                        "zone_summaries": report.get("zone_summaries"),
                    }
                )

    with tab_legend:
        st.subheader("Legend / struct")
        st.code("\n".join(f"{k}: {v}" for k, v in sorted(STRUCT_ENCODING.items())))
        st.write("**main_entry**", st.session_state.get("main_entry"))
        st.write("**electric_board**", st.session_state.get("electric_board"))
        st.write("**local patches**", len(st.session_state.patch_map))

    approved = {
        "version": 1,
        "main_entry": st.session_state.get("main_entry"),
        "electric_board": st.session_state.get("electric_board"),
        "struct_patch": _patch_map_to_list(st.session_state.patch_map),
        "source_bundle": st.session_state.get("bundle_path"),
    }
    err, warn = validate_approved(approved, eff, require_markers=True)
    st.subheader("Validation")
    if err:
        st.error("Blocking issues:\n- " + "\n- ".join(err))
    else:
        st.success("Ready to save (no blocking errors)")
    for wmsg in warn:
        st.warning(wmsg)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Clear markers"):
            st.session_state.main_entry = None
            st.session_state.electric_board = None
            st.rerun()
    with c2:
        if st.button("Clear paint patches"):
            st.session_state.patch_map = {}
            st.rerun()
    with c3:
        notes = st.text_input("Notes (optional)", value="")

    if st.button("Save review_approved.json", type="primary", disabled=bool(err)):
        approved["notes"] = notes
        approved["approved_at"] = datetime.now(timezone.utc).isoformat()
        out_p = Path(st.session_state.step04_dir) / "review_approved.json"
        out_p.write_text(json.dumps(approved, indent=2), encoding="utf-8")
        st.success(f"Wrote {out_p}")

    with st.expander("Effective struct (corner sample)"):
        st.dataframe(eff[: min(24, h), : min(40, w)], use_container_width=True)


if __name__ == "__main__":
    main()
