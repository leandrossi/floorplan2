#!/usr/bin/env python3
"""
Final Step 05 — Run deterministic alarm planner on the step04 grid.

Reads:
  output/final/step04/final_structure_matrix.npy  (0=ext, 1=wall, 2=window, 3=door, 4=int)
  output/final/step04/final_rooms_matrix.npy
  output/final/step04/final_rooms_inferred_mask.npy
  output/final/step04/floor_like_tokens.npy  (optional, for merged human CSV)
  config/pipeline_config.json  (matrix.cell_size_cm → cell_size_m)

Writes:
  output/final/step05/installation_proposal.json   (alarm device plan)
  output/final/step05/alarm_plan_report.json
  output/final/step05/final_floorplan_grid.json     (full struct+rooms after review; same role as review_bundle + patches applied)
  output/final/step05/final_structure_effective.npy (patched structure matrix only)
  output/final/step05/devices_layer.csv
  output/final/step05/floor_like_with_devices.csv

Reads review_approved.json from step04 if present (--review overrides).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, save_json
from review_bundle_io import apply_struct_patches, build_final_floorplan_grid_dict, load_approved

STEP04_DIR = PROJECT_ROOT / "output" / "final" / "step04"
OUT_DIR = PROJECT_ROOT / "output" / "final" / "step05"

# final_structure_matrix encoding (see final_step04)
_STRUCT_EXTERIOR = 0
_STRUCT_WALL = 1
_STRUCT_WINDOW = 2
_STRUCT_DOOR = 3
_STRUCT_INTERIOR = 4

# acala_engine.model.CellType: OUTDOOR=-1, INDOOR=0, WALL=1, DOOR=2, WINDOW=3, PROHIBITED=4
_STRUCT_TO_ACALA = {
    _STRUCT_EXTERIOR: -1,
    _STRUCT_WALL: 1,
    _STRUCT_WINDOW: 3,
    _STRUCT_DOOR: 2,
    _STRUCT_INTERIOR: 0,
}

_DEVICE_CODES: dict[str, str] = {
    "panel": "A",
    "keyboard": "k",
    "pir": "p",
    "pircam": "P",
    "magnetic": "m",
    "siren_indoor": "si",
    "siren_outdoor": "so",
}


def _struct_to_acala_cells(struct_m: np.ndarray) -> list[list[int]]:
    return [
        [_STRUCT_TO_ACALA[int(v)] for v in row]
        for row in struct_m.astype(int).tolist()
    ]


def _largest_cc_rep(mask: np.ndarray) -> tuple[int, int] | None:
    """Return top-left-most cell in the largest 4-connected True region."""
    if not np.any(mask):
        return None
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
    best_len = 0

    for r in range(h):
        for c in range(w):
            if not mask[r, c] or visited[r, c]:
                continue
            stack = [(r, c)]
            comp: list[tuple[int, int]] = []
            visited[r, c] = True
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            if len(comp) > best_len:
                best_len = len(comp)
                best = comp
    if not best:
        return None
    return min(best, key=lambda rc: (rc[0], rc[1]))


def _infer_exterior_door_cells(struct_m: np.ndarray) -> list[tuple[int, int]]:
    h, w = struct_m.shape
    out: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if int(struct_m[r, c]) != _STRUCT_DOOR:
                continue
            ok = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and int(struct_m[nr, nc]) == _STRUCT_EXTERIOR:
                    ok = True
                    break
            if ok:
                out.append((r, c))
    return out


def _infer_main_entry(struct_m: np.ndarray) -> tuple[int, int] | None:
    """Pick a door cell on the largest exterior-adjacent door component."""
    doors = _infer_exterior_door_cells(struct_m)
    if not doors:
        return None
    mask = np.zeros_like(struct_m, dtype=bool)
    for r, c in doors:
        mask[r, c] = True
    return _largest_cc_rep(mask)


def _infer_electric_board(struct_m: np.ndarray) -> tuple[int, int] | None:
    """Indoor cell nearest to the centroid of all interior cells (struct 4)."""
    ys, xs = np.where(struct_m == _STRUCT_INTERIOR)
    if ys.size == 0:
        return None
    cy = float(ys.mean())
    cx = float(xs.mean())
    indoor = np.stack([ys, xs], axis=1)
    d = (indoor[:, 0].astype(float) - cy) ** 2 + (indoor[:, 1].astype(float) - cx) ** 2
    idx = int(np.argmin(d))
    return int(indoor[idx, 0]), int(indoor[idx, 1])


def _collect_rooms(
    struct_m: np.ndarray,
    room_m: np.ndarray,
    inferred_m: np.ndarray,
) -> list[Any]:
    from acala_engine import make_room

    rooms: list[Any] = []
    for rid in sorted({int(x) for x in np.unique(room_m) if int(x) > 0}):
        sel = (room_m == rid) & (struct_m == _STRUCT_INTERIOR)
        ys, xs = np.where(sel)
        cells = list(zip(ys.tolist(), xs.tolist()))
        if not cells:
            sel2 = (room_m == rid) & (struct_m != _STRUCT_EXTERIOR) & (struct_m != _STRUCT_WALL)
            ys, xs = np.where(sel2)
            cells = list(zip(ys.tolist(), xs.tolist()))
        if cells:
            rooms.append(make_room(id=f"room_{rid}", cells=cells))

    for nid in sorted({int(x) for x in np.unique(inferred_m) if int(x) < 0}):
        sel = inferred_m == nid
        ys, xs = np.where(sel)
        cells = list(zip(ys.tolist(), xs.tolist()))
        if cells:
            rooms.append(make_room(id=f"room_inferred_{abs(nid)}", cells=cells))

    return rooms


def _elements_from_heuristics(
    struct_m: np.ndarray,
    *,
    main: tuple[int, int] | None,
    board: tuple[int, int] | None,
) -> list[Any]:
    from acala_engine import make_element

    elements: list[Any] = []
    if main is not None:
        elements.append(
            make_element(id="inferred_main_entry", element_type="main_entry", position=main)
        )
    if board is not None:
        elements.append(
            make_element(
                id="inferred_electric_board",
                element_type="electric_board",
                position=board,
            )
        )
    return elements


def _diagnose_red_zone_seeding(grid: Any) -> list[str]:
    """
    acala_engine red zones start BFS only from INDOOR 4-neighbours of an exterior
    opening. If the discretized plan has a door/window flush to outdoor with no
    adjacent indoor cell (e.g. door row only touches outdoor + wall/other doors),
    that opening produces no red zone and typically no PIRs.
    """
    from acala_engine.grid_utils import is_interior_opening_to_outdoor, iter_neighbors_4
    from acala_engine.model import CellType

    bad_cells: list[tuple[int, int]] = []
    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if not is_interior_opening_to_outdoor(grid, coord):
                continue
            has_indoor_nb = any(
                CellType(grid.cells[n[0]][n[1]]) is CellType.INDOOR
                for n in iter_neighbors_4(grid, coord)
            )
            if not has_indoor_nb:
                bad_cells.append(coord)

    if not bad_cells:
        return []

    # One warning per 4-connected cluster of problematic opening cells
    h, w = grid.height, grid.width
    in_bad = np.zeros((h, w), dtype=bool)
    for r, c in bad_cells:
        in_bad[r, c] = True
    visited = np.zeros_like(in_bad, dtype=bool)
    warnings: list[str] = []
    for r, c in bad_cells:
        if visited[r, c]:
            continue
        stack = [(r, c)]
        visited[r, c] = True
        rep = (r, c)
        while stack:
            y, x = stack.pop()
            rep = min(rep, (y, x))
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and in_bad[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((ny, nx))
        ry, rcx = rep
        warnings.append(
            f"Exterior opening cluster (repr row={ry},col={rcx}) has no INDOOR 4-neighbour "
            "(acala red-zone BFS never seeds → usually no PIRs for that perimeter). "
            "Try a 1-cell indoor band inside the façade or adjust downsampling."
        )
    return warnings


def _device_layer(devices: list[Any], h: int, w: int) -> list[list[str]]:
    layer: list[list[str]] = [["" for _ in range(w)] for _ in range(h)]
    for d in devices:
        code = _DEVICE_CODES.get(d.device_type.value, d.device_type.value[:2])
        r, c = d.cell
        if not (0 <= r < h and 0 <= c < w):
            continue
        if layer[r][c]:
            layer[r][c] = f"{layer[r][c]}+{code}"
        else:
            layer[r][c] = code
    return layer


def _write_semicolon_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter=";", lineterminator="\n")
        for row in rows:
            wr.writerow(row)


def run(
    step04_dir: Path,
    config_path: Path,
    out_dir: Path,
    *,
    security_level: str = "optimal",
    review_path: Path | None = None,
) -> None:
    from acala_engine import build_scenario, plan_installation
    from acala_engine.io_json import installation_to_dict

    cfg = load_config(config_path)
    mx = cfg.get("matrix") or {}
    cell_cm = float(mx.get("cell_size_cm", 5))
    cell_size_m = cell_cm / 100.0

    struct_path = step04_dir / "final_structure_matrix.npy"
    room_path = step04_dir / "final_rooms_matrix.npy"
    inferred_path = step04_dir / "final_rooms_inferred_mask.npy"
    tokens_path = step04_dir / "floor_like_tokens.npy"

    report: dict[str, Any] = {
        "ok": False,
        "security_level": security_level,
        "cell_size_m": cell_size_m,
        "warnings": [],
        "inferred_elements": {},
        "errors": [],
    }

    if not struct_path.is_file():
        report["errors"].append(f"Missing {struct_path}")
        out_dir.mkdir(parents=True, exist_ok=True)
        save_json(out_dir / "alarm_plan_report.json", report)
        print(f"FinalStep05 FAILED: {report['errors']}", flush=True)
        return

    struct_m = np.load(struct_path).astype(np.uint8)
    room_m = np.load(room_path).astype(np.int32) if room_path.is_file() else np.zeros_like(struct_m, dtype=np.int32)
    inferred_m = (
        np.load(inferred_path).astype(np.int32)
        if inferred_path.is_file()
        else np.zeros_like(struct_m, dtype=np.int32)
    )

    if tokens_path.is_file():
        tokens = np.load(tokens_path, allow_pickle=True)
    else:
        tokens = None

    approved_path = review_path if review_path is not None else (step04_dir / "review_approved.json")
    approved = load_approved(approved_path) if approved_path.is_file() else None
    element_source = "heuristic"

    if approved:
        element_source = "user"
        patches = approved.get("struct_patch") or []
        if patches:
            struct_m = apply_struct_patches(struct_m, patches)
        me_raw = approved.get("main_entry")
        eb_raw = approved.get("electric_board")
        main_cell: tuple[int, int] | None = (
            (int(me_raw[0]), int(me_raw[1])) if isinstance(me_raw, (list, tuple)) and len(me_raw) == 2 else None
        )
        board_cell: tuple[int, int] | None = (
            (int(eb_raw[0]), int(eb_raw[1])) if isinstance(eb_raw, (list, tuple)) and len(eb_raw) == 2 else None
        )
        if main_cell is None:
            main_cell = _infer_main_entry(struct_m)
            element_source = "user+heuristic_main"
        if board_cell is None:
            board_cell = _infer_electric_board(struct_m)
            if element_source == "user":
                element_source = "user+heuristic_board"
            elif element_source == "user+heuristic_main":
                element_source = "user+heuristic_both"
    else:
        main_cell = _infer_main_entry(struct_m)
        board_cell = _infer_electric_board(struct_m)
        if main_cell is None:
            report["warnings"].append(
                "No exterior-adjacent door found; main_entry not set — MIN profile magnetics and keyboard may be skipped."
            )
        if board_cell is None:
            report["warnings"].append("No interior cells; electric_board not set.")

    report["inferred_elements"] = {
        "main_entry": list(main_cell) if main_cell else None,
        "electric_board": list(board_cell) if board_cell else None,
        "source": element_source,
        "review_file": str(approved_path) if approved else None,
    }

    acala_cells = _struct_to_acala_cells(struct_m)
    rooms = _collect_rooms(struct_m, room_m, inferred_m)
    elements = _elements_from_heuristics(struct_m, main=main_cell, board=board_cell)

    try:
        scenario = build_scenario(
            cells=acala_cells,
            cell_size_m=cell_size_m,
            security_level=security_level,
            rooms=rooms,
            elements=elements,
            fixture_name="final_pipeline_step04",
            notes=f"Elements source: {element_source}.",
        )
        report["warnings"].extend(_diagnose_red_zone_seeding(scenario.grid_map))
        proposal = plan_installation(scenario)
    except Exception as e:  # noqa: BLE001
        report["errors"].append(f"plan_installation failed: {e!r}")
        out_dir.mkdir(parents=True, exist_ok=True)
        save_json(out_dir / "alarm_plan_report.json", report)
        print(f"FinalStep05 FAILED: {e}", flush=True)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    prop_dict = installation_to_dict(proposal)
    save_json(out_dir / "installation_proposal.json", prop_dict)

    h, w = struct_m.shape
    dev_layer = _device_layer(proposal.devices, h, w)
    _write_semicolon_csv(out_dir / "devices_layer.csv", dev_layer)

    if tokens is not None and tokens.shape == struct_m.shape:
        merged: list[list[str]] = []
        for r in range(h):
            row: list[str] = []
            for c in range(w):
                tok = str(tokens[r, c])
                dcode = dev_layer[r][c]
                row.append(f"{tok}:{dcode}" if dcode else tok)
            merged.append(row)
        _write_semicolon_csv(out_dir / "floor_like_with_devices.csv", merged)
    else:
        report["warnings"].append(
            "floor_like_tokens.npy missing or shape mismatch; skipped floor_like_with_devices.csv"
        )

    report["ok"] = True
    report["device_counts"] = {}
    for d in proposal.devices:
        k = d.device_type.value
        report["device_counts"][k] = report["device_counts"].get(k, 0) + 1

    zc: dict[str, int] = {}
    total_zone_cells = 0
    for z in proposal.zones:
        key = z.zone_type.value
        zc[key] = zc.get(key, 0) + 1
        total_zone_cells += len(z.cells)
    report["zone_summaries"] = {
        "zones_by_type": zc,
        "total_zone_cells": total_zone_cells,
    }
    report["notes"] = (
        "PIR/PIRCAM appear only when RED zones exist after magnetic suppression. "
        "Empty red zones usually mean exterior openings have no INDOOR neighbour in the grid."
    )

    save_json(out_dir / "alarm_plan_report.json", report)

    grid_json = build_final_floorplan_grid_dict(
        struct_m=struct_m,
        room_m=room_m,
        inferred_m=inferred_m,
        cell_size_m=cell_size_m,
        approved=approved if isinstance(approved, dict) else None,
        approved_path=approved_path if approved_path.is_file() else None,
        security_level=security_level,
    )
    save_json(out_dir / "final_floorplan_grid.json", grid_json)
    np.save(out_dir / "final_structure_effective.npy", struct_m.astype(np.uint8))
    print(f"FinalStep05 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Plan alarm installation from step04 matrices.")
    ap.add_argument("--step04", type=Path, default=STEP04_DIR)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument(
        "--review",
        type=Path,
        default=None,
        help="Path to review_approved.json (default: STEP04/review_approved.json if present)",
    )
    ap.add_argument(
        "--security-level",
        choices=("min", "optimal", "max"),
        default="optimal",
    )
    args = ap.parse_args()
    run(
        args.step04,
        args.config,
        args.out,
        security_level=args.security_level,
        review_path=args.review,
    )


if __name__ == "__main__":
    main()
