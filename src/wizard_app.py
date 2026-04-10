"""
Floorplan Security Wizard — MVP

3-step flow:
  1. Upload floorplan image → Roboflow API → pipeline steps 01-04
  2. Review matrix, place main entry + electric board, select security level
  3. Run step05 → show proposal (red zones + devices), download results

Run: PYTHONPATH=src streamlit run src/wizard_app.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent

if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from pipeline_common import PROJECT_ROOT, load_config, save_json
from review_bundle_io import (
    STRUCT_ENCODING,
    apply_struct_patches,
    load_approved,
    validate_approved,
    write_review_bundle,
)
from ui_components import (
    DEVICE_STYLE,
    STRUCT_RGB,
    alpha_blend,
    compute_pre_suppression_red_mask,
    draw_square,
    effective_struct,
    grid_cell_from_display_click,
    inject_wizard_css,
    load_step05_outputs,
    overlay_markers,
    render_proposal_views,
    render_stepper,
    rgb_from_struct,
    upscale_rgb,
)

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
except ImportError:
    streamlit_image_coordinates = None  # type: ignore[misc,assignment]

DEFAULT_CONFIG = _PROJECT_ROOT / "config" / "pipeline_config.json"
OUTPUT_DIR = _PROJECT_ROOT / "output"

SECURITY_LEVELS = {
    "Minimo": "min",
    "Optimo": "optimal",
    "Maximo": "max",
}

# Upload / processing guards for heterogeneous plans.
MAX_UPLOAD_MB = 15
MAX_IMAGE_WIDTH = 6000
MAX_IMAGE_HEIGHT = 6000
MAX_GRID_CELLS = 250_000


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _ss() -> Any:
    return st.session_state


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "wiz_step": 1,
        "uploaded_path": None,
        "roboflow_json": None,
        "step04_dir": None,
        "struct_base": None,
        "patch_map": {},
        "main_entry": None,
        "electric_board": None,
        "security_label": "Optimo",
        "cell_size_m": 0.05,
        "_img_click_sig": None,
        "_flash": None,
        "step05_dir": None,
        "proposal": None,
        "report": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_plan_state_for_new_upload() -> None:
    """Clear plan-specific state before loading a new floorplan."""
    st.session_state.patch_map = {}
    st.session_state.main_entry = None
    st.session_state.electric_board = None
    st.session_state._img_click_sig = None
    st.session_state.step05_dir = None
    st.session_state.proposal = None
    st.session_state.report = None


# ---------------------------------------------------------------------------
# Step 1: Upload + Roboflow + pipeline
# ---------------------------------------------------------------------------

def _run_roboflow(image_path: Path) -> Path:
    """
    Call Roboflow API via existing CLI script and return result_workflow_final.json.

    Using a subprocess gives us robust timeout/error handling so Streamlit does not
    appear frozen indefinitely.
    """
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    cmd = [
        sys.executable,
        str(_PROJECT_ROOT / "run_workflow_final.py"),
        str(image_path),
        "--output-dir",
        str(OUTPUT_DIR),
    ]
    env = dict(os.environ)
    # In this environment, local proxy variables are present and can return
    # "Tunnel connection failed: 403 Forbidden" for Roboflow.
    for key in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
        "SOCKS_PROXY", "SOCKS5_PROXY",
        "socks_proxy", "socks5_proxy",
        "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY",
    ):
        env.pop(key, None)
    env["NO_PROXY"] = ",".join(
        x for x in [env.get("NO_PROXY", ""), "serverless.roboflow.com", ".roboflow.com"] if x
    )
    env["no_proxy"] = env["NO_PROXY"]

    try:
        # Hard timeout avoids indefinite hangs when API/network gets stuck.
        proc = subprocess.run(
            cmd,
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Timeout llamando a Roboflow (180s). Revisá conexión/API key o probá de nuevo."
        ) from exc

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if not err:
            err = "Fallo desconocido en run_workflow_final.py"
        raise RuntimeError(err)

    json_path = OUTPUT_DIR / "result_workflow_final.json"
    if not json_path.is_file():
        raise RuntimeError(f"Roboflow terminó sin generar: {json_path}")
    return json_path


def _run_pipeline_steps(json_path: Path, progress_cb) -> Path:
    """Execute steps 01-04 in-process and return step04 output dir."""
    from final_step01_parse_and_rasterize import run as run_step01
    from final_step02_classify_space import run as run_step02
    from final_step03_assign_rooms import run as run_step03
    from final_step04_build_matrix_csv import run as run_step04

    step01_dir = OUTPUT_DIR / "final" / "step01"
    step02_dir = OUTPUT_DIR / "final" / "step02"
    step03_dir = OUTPUT_DIR / "final" / "step03"
    step04_dir = OUTPUT_DIR / "final" / "step04"

    progress_cb(0.10, "Step 01: parsing and rasterizing...")
    run_step01(json_path, step01_dir)

    progress_cb(0.30, "Step 02: classifying space (exterior/interior)...")
    run_step02(
        step01_dir / "structural_mask.npy",
        step01_dir / "room_polygons.npy",
        step02_dir,
    )

    progress_cb(0.55, "Step 03: assigning rooms...")
    run_step03(
        step02_dir / "space_classified.npy",
        step01_dir / "room_polygons.npy",
        step03_dir,
    )

    progress_cb(0.80, "Step 04: building matrix grid...")
    run_step04(
        step02_dir / "space_classified.npy",
        step03_dir / "room_id_matrix.npy",
        DEFAULT_CONFIG,
        step04_dir,
    )
    progress_cb(1.0, "Pipeline complete.")
    return step04_dir


def _load_bundle_into_session(step04_dir: Path) -> None:
    bundle_path = step04_dir / "review_bundle.json"
    if not bundle_path.is_file():
        write_review_bundle(step04_dir, DEFAULT_CONFIG)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    struct = np.array(bundle["struct"], dtype=np.uint8)
    h, w = struct.shape
    if h * w > MAX_GRID_CELLS:
        raise RuntimeError(
            f"Plano demasiado grande ({h}x{w} = {h*w} celdas). "
            f"Máximo permitido: {MAX_GRID_CELLS} celdas."
        )
    st.session_state.struct_base = struct
    st.session_state.step04_dir = str(step04_dir)
    st.session_state.cell_size_m = float(bundle.get("cell_size_m", 0.05))
    # New upload should start from clean user markers/patches.
    st.session_state.patch_map = {}
    st.session_state.main_entry = None
    st.session_state.electric_board = None
    st.session_state._img_click_sig = None


def render_step1() -> None:
    st.header("1. Cargar plano")
    st.markdown(
        "Subí la imagen del plano. Se enviará a Roboflow para detectar muros, "
        "puertas, ventanas y habitaciones, y luego se procesará automáticamente."
    )

    uploaded = st.file_uploader(
        "Imagen del plano",
        type=["png", "jpg", "jpeg", "webp"],
        key="fp_upload",
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        skip_roboflow = st.checkbox(
            "Usar JSON existente",
            help="Saltear la llamada a Roboflow si ya tenés result_workflow_final.json",
        )

    if skip_roboflow:
        json_path = OUTPUT_DIR / "result_workflow_final.json"
        if not json_path.is_file():
            st.warning(f"No se encontró `{json_path}`. Subí una imagen o generá el JSON primero.")
            return
        if st.button("Procesar con JSON existente", type="primary"):
            _reset_plan_state_for_new_upload()
            bar = st.progress(0, text="Iniciando pipeline...")
            def _progress(pct: float, text: str) -> None:
                bar.progress(pct, text=text)
            try:
                step04_dir = _run_pipeline_steps(json_path, _progress)
                _load_bundle_into_session(step04_dir)
                st.session_state.wiz_step = 2
                st.rerun()
            except Exception as e:
                st.error(f"Error en pipeline: {e}")
        return

    if uploaded is None:
        st.info("Arrastrá o seleccioná una imagen para comenzar.")
        return

    raw = uploaded.getvalue()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        st.error(
            f"Archivo demasiado grande ({size_mb:.1f} MB). "
            f"Máximo permitido: {MAX_UPLOAD_MB} MB."
        )
        return

    try:
        with Image.open(uploaded) as im:
            img_w, img_h = im.size
    except UnidentifiedImageError:
        st.error("No se pudo leer la imagen. Usá PNG/JPG/WebP válidos.")
        return
    except Exception as e:
        st.error(f"Error leyendo imagen: {e}")
        return

    if img_w > MAX_IMAGE_WIDTH or img_h > MAX_IMAGE_HEIGHT:
        st.error(
            f"Resolución demasiado grande ({img_w}x{img_h}). "
            f"Máximo permitido: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} px."
        )
        return

    st.image(uploaded, caption="Plano cargado", width=480)
    st.caption(f"Archivo: {size_mb:.2f} MB - Resolución: {img_w}x{img_h} px")

    if st.button("Procesar plano", type="primary"):
        _reset_plan_state_for_new_upload()
        tmp_dir = Path(tempfile.mkdtemp(prefix="fp_wiz_"))
        tmp_img = tmp_dir / uploaded.name
        tmp_img.write_bytes(raw)

        bar = st.progress(0, text="Conectando con Roboflow...")
        try:
            bar.progress(0.02, text="Enviando imagen a Roboflow API...")
            json_path = _run_roboflow(tmp_img)
            bar.progress(0.08, text="Roboflow completo. Iniciando pipeline...")
        except Exception as e:
            st.error(f"Error en Roboflow: {e}")
            return

        def _progress(pct: float, text: str) -> None:
            bar.progress(pct, text=text)

        try:
            step04_dir = _run_pipeline_steps(json_path, _progress)
            _load_bundle_into_session(step04_dir)
            st.session_state.wiz_step = 2
            st.rerun()
        except Exception as e:
            st.error(f"Error en pipeline: {e}")


# ---------------------------------------------------------------------------
# Step 2: Review matrix
# ---------------------------------------------------------------------------

def _patch_map_to_list(pm: dict[tuple[int, int], int]) -> list[dict[str, int]]:
    return [{"r": r, "c": c, "v": int(v)} for (r, c), v in sorted(pm.items())]


def _apply_click(
    cx: int, cy: int, mode: str, paint_val: int | None,
    w: int, h: int, eff: np.ndarray,
) -> None:
    if not (0 <= cx < w and 0 <= cy < h):
        return
    pv = int(paint_val) if mode == "Pintar celda" and paint_val is not None else -1
    cur_sig = (cx, cy, mode, pv)
    if cur_sig == st.session_state.get("_img_click_sig"):
        return

    if mode == "Puerta principal":
        if int(eff[cy, cx]) != 3:
            st.session_state._flash = "La puerta principal debe ser una celda **puerta** (struct=3, verde)."
            st.rerun()
            return
    elif mode == "Tablero eléctrico":
        if int(eff[cy, cx]) != 4:
            st.session_state._flash = "El tablero eléctrico debe ser una celda **interior** (struct=4, beige)."
            st.rerun()
            return

    st.session_state._img_click_sig = cur_sig
    if mode == "Puerta principal":
        st.session_state.main_entry = [cy, cx]
    elif mode == "Tablero eléctrico":
        st.session_state.electric_board = [cy, cx]
    elif mode == "Pintar celda" and paint_val is not None:
        st.session_state.patch_map[(cy, cx)] = int(paint_val)
    st.rerun()


def render_step2() -> None:
    struct_base: np.ndarray = st.session_state.struct_base
    h, w = struct_base.shape
    eff = effective_struct(struct_base, st.session_state.patch_map)

    st.header("2. Configurar")

    if msg := st.session_state.pop("_flash", None):
        st.warning(msg)

    toolbar, preview_area = st.columns([1, 3])

    with toolbar:
        st.subheader("Herramientas")
        mode = st.radio(
            "Acción",
            ("Ver", "Puerta principal", "Tablero eléctrico", "Pintar celda"),
        )
        paint_val = None
        if mode == "Pintar celda":
            paint_val = st.selectbox(
                "Pincel (struct)",
                options=list(range(5)),
                format_func=lambda v: f"{v} = {STRUCT_ENCODING.get(v, v)}",
            )

        st.divider()
        st.subheader("Nivel de seguridad")
        sec_label = st.radio(
            "Seleccioná el nivel",
            list(SECURITY_LEVELS.keys()),
            index=list(SECURITY_LEVELS.keys()).index(st.session_state.security_label),
            horizontal=True,
        )
        st.session_state.security_label = sec_label

        sec_hints = {
            "Minimo": "Solo puerta principal con magnético + PIR.",
            "Optimo": "Magnéticos en todas las puertas + PIRs en zonas rojas.",
            "Maximo": "Magnéticos en puertas y ventanas + PIRs completos.",
        }
        st.caption(sec_hints.get(sec_label, ""))

        st.divider()
        st.markdown("**Estado actual**")
        me = st.session_state.get("main_entry")
        eb = st.session_state.get("electric_board")
        st.write("Puerta principal:", f"fila {me[0]}, col {me[1]}" if me else "Sin definir")
        st.write("Tablero eléctrico:", f"fila {eb[0]}, col {eb[1]}" if eb else "Sin definir")
        st.write("Parches:", len(st.session_state.patch_map))

        img_width = st.slider("Ancho del mapa (px)", 400, 2400, min(1400, max(600, w * 6)))

        if st.button("Limpiar marcadores"):
            st.session_state.main_entry = None
            st.session_state.electric_board = None
            st.rerun()
        if st.button("Limpiar parches"):
            st.session_state.patch_map = {}
            st.rerun()

    with preview_area:
        mode_hints = {
            "Ver": "Modo visualización. Seleccioná una herramienta para editar.",
            "Puerta principal": "Hacé click en una celda **puerta** (verde, struct=3).",
            "Tablero eléctrico": "Hacé click en una celda **interior** (beige, struct=4).",
            "Pintar celda": "Hacé click para pintar con el pincel seleccionado.",
        }
        st.info(mode_hints.get(mode, ""))

        rgb = overlay_markers(
            rgb_from_struct(eff),
            main_entry=st.session_state.get("main_entry"),
            electric_board=st.session_state.get("electric_board"),
            marker_radius=2,
        )
        disp_w = int(img_width)
        rgb_up = upscale_rgb(rgb, disp_w)

        if streamlit_image_coordinates is not None and mode != "Ver":
            coord = streamlit_image_coordinates(
                rgb_up,
                key="wiz_struct_click",
            )
            if coord is not None:
                picked = grid_cell_from_display_click(
                    coord,
                    native_img_w=rgb_up.shape[1],
                    native_img_h=rgb_up.shape[0],
                    grid_w=w,
                    grid_h=h,
                )
                if picked is not None:
                    cx, cy = picked
                    cell_val = int(eff[cy, cx]) if 0 <= cy < h and 0 <= cx < w else -1
                    st.caption(
                        f"Click: px=({coord.get('x')}, {coord.get('y')}) "
                        f"disp=({coord.get('width')}x{coord.get('height')}) "
                        f"→ grid col={cx} row={cy} struct={cell_val}"
                    )
                    _apply_click(cx, cy, mode, paint_val, w, h, eff)
        else:
            st.image(rgb_up)
            if streamlit_image_coordinates is None and mode != "Ver":
                st.warning("Instalá `streamlit-image-coordinates` para hacer click: `pip install streamlit-image-coordinates`")

        with st.expander("Leyenda"):
            cols = st.columns(5)
            for i, (code, name) in enumerate(STRUCT_ENCODING.items()):
                r, g, b = STRUCT_RGB[code]
                cols[i].markdown(
                    f'<div style="display:flex;align-items:center;gap:6px">'
                    f'<div style="width:18px;height:18px;background:rgb({r},{g},{b});border:1px solid #999;border-radius:3px"></div>'
                    f'<span style="font-size:13px">{code} = {name}</span></div>',
                    unsafe_allow_html=True,
                )
            st.caption("Rojo = puerta principal · Azul = tablero eléctrico")

    err, warn = validate_approved(
        {
            "version": 1,
            "main_entry": st.session_state.get("main_entry"),
            "electric_board": st.session_state.get("electric_board"),
            "struct_patch": _patch_map_to_list(st.session_state.patch_map),
            "source_bundle": st.session_state.get("step04_dir"),
        },
        eff,
        require_markers=True,
    )

    st.divider()
    bcol1, bcol2, bcol3 = st.columns([2, 1, 1])
    with bcol1:
        if err:
            st.error("Antes de continuar: " + " · ".join(err))
        else:
            st.success("Listo para generar la propuesta.")
    with bcol2:
        if st.button("Volver", use_container_width=True):
            st.session_state.wiz_step = 1
            st.rerun()
    with bcol3:
        if st.button("Generar propuesta", type="primary", disabled=bool(err), use_container_width=True):
            _save_approved_and_advance(eff)


def _save_approved_and_advance(eff: np.ndarray) -> None:
    approved = {
        "version": 1,
        "main_entry": st.session_state.get("main_entry"),
        "electric_board": st.session_state.get("electric_board"),
        "struct_patch": _patch_map_to_list(st.session_state.patch_map),
        "source_bundle": st.session_state.get("step04_dir"),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    step04_dir = Path(st.session_state.step04_dir)
    out_p = step04_dir / "review_approved.json"
    out_p.write_text(json.dumps(approved, indent=2), encoding="utf-8")

    sec_code = SECURITY_LEVELS[st.session_state.security_label]
    bar = st.progress(0, text="Ejecutando plan de alarma (step 05)...")

    try:
        from final_step05_plan_alarm import run as run_step05
        step05_dir = OUTPUT_DIR / "final" / "step05"
        bar.progress(0.3, text="Planificando dispositivos...")
        run_step05(
            step04_dir,
            DEFAULT_CONFIG,
            step05_dir,
            security_level=sec_code,
            review_path=out_p,
        )
        bar.progress(1.0, text="Plan completo.")

        proposal, report = load_step05_outputs(step05_dir)
        st.session_state.step05_dir = str(step05_dir)
        st.session_state.proposal = proposal
        st.session_state.report = report
        st.session_state.wiz_step = 3
        st.rerun()
    except Exception as e:
        st.error(f"Error en step05: {e}")


# ---------------------------------------------------------------------------
# Step 3: Proposal
# ---------------------------------------------------------------------------

def render_step3() -> None:
    st.header("3. Resultado")

    struct_base: np.ndarray = st.session_state.struct_base
    eff = effective_struct(struct_base, st.session_state.patch_map)
    h, w = eff.shape
    proposal = st.session_state.proposal
    report = st.session_state.report

    sec_label = st.session_state.security_label
    sec_code = SECURITY_LEVELS[sec_label]

    # Metrics row
    device_counts: dict[str, int] = {}
    if report:
        device_counts = report.get("device_counts") or {}
    total_devices = sum(device_counts.values())
    n_warnings = len(report.get("warnings") or []) if report else 0
    plan_ok = report.get("ok", False) if report else False

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Nivel", sec_label)
    m2.metric("Dispositivos", total_devices)
    m3.metric("Advertencias", n_warnings)
    m4.metric("Estado", "OK" if plan_ok else "Error")

    st.divider()

    # Pre-suppression red zones
    pre_mask = compute_pre_suppression_red_mask(
        eff,
        main_entry=st.session_state.get("main_entry"),
        electric_board=st.session_state.get("electric_board"),
        cell_size_m=float(st.session_state.cell_size_m),
        security_level=sec_code,
    )

    red_img = rgb_from_struct(eff)
    red_count = 0
    if pre_mask is not None:
        red_count = int(pre_mask.sum())
        if red_count > 0:
            red_img = alpha_blend(red_img, pre_mask, (220, 20, 60), alpha=0.42)

    _, dev_img, device_counts_view, _ = render_proposal_views(
        eff,
        proposal=proposal,
        show_red_zones=False,
        show_devices=True,
        replace_base_with_devices=True,
    )

    img_width = st.slider("Ancho de imagen (px)", 400, 2400, min(1200, max(600, w * 5)), key="s3_width")
    disp_w = int(img_width)

    col_red, col_dev = st.columns(2)
    with col_red:
        st.markdown("**Zonas rojas (antes de cobertura)**")
        st.image(upscale_rgb(red_img, disp_w))
        st.caption(f"{red_count} celdas en zona roja")

    with col_dev:
        st.markdown("**Dispositivos colocados**")
        st.image(upscale_rgb(dev_img, disp_w))
        if not device_counts_view:
            st.warning("No se colocaron dispositivos. Verificá el plano y los marcadores.")

    # Device legend
    st.divider()
    st.subheader("Leyenda de dispositivos")
    legend_cols = st.columns(len(DEVICE_STYLE))
    for i, (dt_key, sty) in enumerate(DEVICE_STYLE.items()):
        r, g, b = sty["rgb"]  # type: ignore[misc]
        count = device_counts.get(dt_key, 0)
        legend_cols[i].markdown(
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<div style="width:22px;height:22px;background:rgb({r},{g},{b});border-radius:4px;border:1px solid #666"></div>'
            f'<div><strong>{sty["name"]}</strong> ({sty["label"]})<br/>'
            f'<span style="font-size:20px;font-weight:700">{count}</span></div></div>',
            unsafe_allow_html=True,
        )

    # Warnings / errors
    if report:
        warns = report.get("warnings") or []
        errs = report.get("errors") or []
        if warns or errs:
            with st.expander(f"Detalles del reporte ({len(warns)} advertencias, {len(errs)} errores)"):
                for w_msg in warns:
                    st.warning(w_msg)
                for e_msg in errs:
                    st.error(e_msg)

    # Downloads
    st.divider()
    st.subheader("Descargas")
    dl1, dl2, dl3 = st.columns(3)
    step05_dir = Path(st.session_state.step05_dir)

    proposal_path = step05_dir / "installation_proposal.json"
    report_path = step05_dir / "alarm_plan_report.json"

    with dl1:
        if proposal_path.is_file():
            st.download_button(
                "Propuesta (JSON)",
                data=proposal_path.read_text(encoding="utf-8"),
                file_name="installation_proposal.json",
                mime="application/json",
                use_container_width=True,
            )
    with dl2:
        if report_path.is_file():
            st.download_button(
                "Reporte (JSON)",
                data=report_path.read_text(encoding="utf-8"),
                file_name="alarm_plan_report.json",
                mime="application/json",
                use_container_width=True,
            )
    with dl3:
        devices_csv = step05_dir / "devices_layer.csv"
        if devices_csv.is_file():
            st.download_button(
                "Dispositivos (CSV)",
                data=devices_csv.read_text(encoding="utf-8"),
                file_name="devices_layer.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # Navigation
    st.divider()
    nav1, nav2 = st.columns([1, 1])
    with nav1:
        if st.button("Volver a configurar", use_container_width=True):
            st.session_state.wiz_step = 2
            st.rerun()
    with nav2:
        if st.button("Nuevo plano", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Floorplan Security Wizard",
        page_icon="🔒",
        layout="wide",
    )
    inject_wizard_css()
    _init_state()

    step = st.session_state.wiz_step
    render_stepper(step)

    if step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()


if __name__ == "__main__":
    main()
