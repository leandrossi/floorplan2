#!/usr/bin/env python3
"""
Ejecuta en paralelo (4 workers) cuatro alternativas al sellado morfológico global (step04b):

Alt1 — Tras flood fill, fuerza interior (4) en píxeles libres cubiertos por ∪ polígonos room.
Alt2 — Puentes entre extremos de segmentos wall (JSON) casi colineales y cercanos.
Alt3 — Extensión de cada arista wall unos píxeles en su dirección hasta chocar barrera/borde.
Alt4 — Itera: leak = exterior_flood ∧ ∪room ∧ libre; BFS camino libre leak→borde; pinta muro (1) en el camino.

Salida: output/step05_variants/<alt_* >/ (mismos artefactos que step05) + manifest.json.

Por defecto usa structural_mask.npy de step04 (sin 4b); --struct permite otro .npy.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, load_json, rasterize_polygons, save_matrix_png
from step05_classify_exterior_interior import (
    flood_exterior,
    label_preview,
    proposal_layer,
    room_centroids,
    room_detections_list,
    raster_room_mask,
)


def _wall_detections(doc: dict, *, ignore_threshold: bool) -> list[dict]:
    out: list[dict] = []
    for d in doc.get("detections", []):
        if d.get("exclude_reason"):
            continue
        if not ignore_threshold and not d.get("passes_threshold"):
            continue
        if d.get("class_norm") != "wall":
            continue
        pts = d.get("points") or []
        if len(pts) < 2:
            continue
        out.append(d)
    return out


def _polygon_edges(pts: list[list[float]]) -> list[tuple[np.ndarray, np.ndarray]]:
    """Aristas como pares de puntos float (x,y). Polígono cerrado si len>=3."""
    n = len(pts)
    if n < 2:
        return []
    p = np.array(pts, dtype=np.float64)
    edges: list[tuple[np.ndarray, np.ndarray]] = []
    if n >= 3 and np.allclose(p[0], p[-1]):
        q = p[:-1]
        m = len(q)
        for i in range(m):
            edges.append((q[i], q[(i + 1) % m]))
    else:
        for i in range(n - 1):
            edges.append((p[i], p[i + 1]))
    return edges


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.hypot(v[0], v[1]))
    if n < 1e-6:
        return np.array([0.0, 0.0], dtype=np.float64)
    return v / n


def _build_union_room(h: int, w: int, room_dets: list[dict]) -> np.ndarray:
    u = np.zeros((h, w), dtype=bool)
    for d in room_dets:
        u |= raster_room_mask(h, w, d)
    return u


def _space_from_struct(
    sm: np.ndarray,
    *,
    room_force_mask: np.ndarray | None = None,
) -> np.ndarray:
    barrier = (sm == 1) | (sm == 2) | (sm == 3)
    free = (sm == 0) & (~barrier)
    ext = flood_exterior(free)
    space = np.zeros_like(sm, dtype=np.uint8)
    space[sm == 1] = 1
    space[sm == 2] = 2
    space[sm == 3] = 3
    space[free & ext] = 0
    space[free & (~ext)] = 4
    if room_force_mask is not None:
        q = room_force_mask & free & (space == 0)
        if np.any(q):
            space[q] = 4
    return space


def _write_step05_like(
    sm: np.ndarray,
    space: np.ndarray,
    *,
    room_dets: list[dict],
    out_dir: Path,
    tag: str,
    struct_src: str,
) -> dict[str, Any]:
    h, w = space.shape[:2]
    interior = space == 4
    out_dir.mkdir(parents=True, exist_ok=True)

    np.save(out_dir / "structural_mask_used.npy", sm)
    np.save(out_dir / "space_classified.npy", space)
    colors = {
        0: (200, 200, 255),
        1: (40, 40, 40),
        2: (0, 180, 255),
        3: (0, 100, 0),
        4: (255, 220, 180),
    }
    save_matrix_png(space, out_dir / "space_classified.png", colors)

    floor = PROJECT_ROOT / "Floorplan2.png"
    if floor.is_file():
        base = cv2.imread(str(floor), cv2.IMREAD_COLOR)
        if base.shape[:2] == space.shape:
            cm = np.zeros_like(base)
            for k, rgb in colors.items():
                cm[space == k] = rgb
            over = cv2.addWeighted(base, 0.6, cm, 0.4, 0)
            cv2.imwrite(str(out_dir / "space_overlay.png"), over)
        else:
            import shutil

            shutil.copy(out_dir / "space_classified.png", out_dir / "space_overlay.png")
    else:
        import shutil

        shutil.copy(out_dir / "space_classified.png", out_dir / "space_overlay.png")

    interior_u8 = interior.astype(np.uint8)
    n_cc, cc_labels = cv2.connectedComponents(interior_u8, connectivity=4)
    topology = np.zeros((h, w), dtype=np.int32)
    for lab in range(1, n_cc):
        topology[cc_labels == lab] = lab
    np.save(out_dir / "space_interior_topology.npy", topology)
    cv2.imwrite(
        str(out_dir / "space_interior_topology_preview.png"),
        label_preview(topology, skip_zero=True),
    )

    if not room_dets:
        proposal = np.zeros((h, w), dtype=np.int32)
    else:
        union_room = np.zeros((h, w), dtype=bool)
        for d in room_dets:
            union_room |= raster_room_mask(h, w, d)
        proposal = proposal_layer(union_room, room_dets, h, w)
    np.save(out_dir / "space_interior_room_proposal.npy", proposal)
    prop_prev = label_preview(proposal, skip_zero=True)
    cv2.imwrite(str(out_dir / "space_interior_room_proposal_preview.png"), prop_prev)
    cv2.imwrite(
        str(out_dir / "space_interior_room_proposal_preview.jpg"),
        prop_prev,
        [int(cv2.IMWRITE_JPEG_QUALITY), 92],
    )

    n_int = int(interior.sum())
    n_ext = int((space == 0).sum())
    report_lines = [
        f"variant: {tag}",
        f"structural_npy_source: {struct_src}",
        f"interior_pixels: {n_int}",
        f"exterior_pixels: {n_ext}",
        f"topology_interior_components: {int(n_cc - 1)}",
        f"room_detections: {len(room_dets)}",
    ]
    (out_dir / "regions_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "tag": tag,
        "out_dir": str(out_dir),
        "interior_pixels": n_int,
        "exterior_pixels": n_ext,
        "topology_components": int(n_cc - 1),
    }


def _struct_alt2_endpoint_bridge(
    sm: np.ndarray,
    wall_dets: list[dict],
    *,
    max_endpoint_dist_px: float,
    min_abs_dot: float,
    line_thickness: int,
) -> np.ndarray:
    out = sm.copy()
    h, w = out.shape[:2]
    edges: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for d in wall_dets:
        for a, b in _polygon_edges(d["points"]):
            dseg = _unit(b - a)
            if float(np.hypot(dseg[0], dseg[1])) < 0.5:
                continue
            edges.append((a, b, dseg))
    # (punto extremo, dirección del segmento hacia el interior de la arista, índice arista, 0=inicio 1=fin)
    caps: list[tuple[np.ndarray, np.ndarray, int, int]] = []
    for ei, (a, b, dseg) in enumerate(edges):
        caps.append((a.copy(), dseg, ei, 0))
        caps.append((b.copy(), dseg, ei, 1))
    for i in range(len(caps)):
        p_i, di, ei, _ = caps[i]
        for j in range(i + 1, len(caps)):
            p_j, dj, ej, _ = caps[j]
            if ei == ej:
                continue
            v = p_j - p_i
            dist = float(np.hypot(v[0], v[1]))
            if dist < 1.0 or dist > max_endpoint_dist_px:
                continue
            uv = _unit(v)
            if abs(float(np.dot(di, uv))) < min_abs_dot:
                continue
            if abs(float(np.dot(dj, uv))) < min_abs_dot:
                continue
            p0 = (int(round(p_i[0])), int(round(p_i[1])))
            p1 = (int(round(p_j[0])), int(round(p_j[1])))
            cv2.line(out, p0, p1, 1, thickness=max(1, int(line_thickness)))
    return out


def _struct_alt3_extend_segments(
    sm: np.ndarray,
    wall_dets: list[dict],
    *,
    max_extend_px: int,
    line_thickness: int,
) -> np.ndarray:
    out = sm.copy()
    h, w = out.shape[:2]
    th = max(1, int(line_thickness))

    def barrier_at(yi: int, xi: int) -> bool:
        if xi < 0 or yi < 0 or xi >= w or yi >= h:
            return True
        v = int(out[yi, xi])
        return 1 <= v <= 3

    for d in wall_dets:
        for a, b in _polygon_edges(d["points"]):
            dseg = b - a
            du = _unit(dseg)
            if float(np.hypot(du[0], du[1])) < 0.5:
                continue
            x0, y0 = float(a[0]), float(a[1])

            def ray_from(x: float, y: float, dir_vec: np.ndarray, steps: int) -> None:
                for _k in range(steps):
                    x += float(dir_vec[0])
                    y += float(dir_vec[1])
                    xi, yi = int(round(x)), int(round(y))
                    if barrier_at(yi, xi):
                        return
                    cv2.line(out, (xi, yi), (xi, yi), 1, thickness=th)

            ray_from(x0, y0, -du, max_extend_px)
            x1, y1 = float(b[0]), float(b[1])
            ray_from(x1, y1, du, max_extend_px)
    return out


def _bfs_path_leak_to_border(leak: np.ndarray, free: np.ndarray) -> list[tuple[int, int]] | None:
    h, w = free.shape
    from collections import deque

    q: deque[tuple[int, int]] = deque()
    parent = np.full((h, w, 2), -1, dtype=np.int32)
    vis = np.zeros((h, w), dtype=bool)
    ys, xs = np.where(leak & free)
    for y, x in zip(ys.tolist(), xs.tolist()):
        vis[y, x] = True
        parent[y, x] = [-2, -2]
        q.append((y, x))
    goal: tuple[int, int] | None = None
    while q:
        y, x = q.popleft()
        if y == 0 or y == h - 1 or x == 0 or x == w - 1:
            goal = (y, x)
            break
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if ny < 0 or nx < 0 or ny >= h or nx >= w:
                continue
            if not free[ny, nx] or vis[ny, nx]:
                continue
            vis[ny, nx] = True
            parent[ny, nx] = [y, x]
            q.append((ny, nx))
    if goal is None:
        return None
    path: list[tuple[int, int]] = []
    y, x = goal
    while True:
        path.append((y, x))
        py, px = int(parent[y, x, 0]), int(parent[y, x, 1])
        if py == -2 and px == -2:
            break
        if py < 0:
            break
        y, x = py, px
    path.reverse()
    return path


def _struct_alt4_leak_path(sm: np.ndarray, union_room: np.ndarray, *, max_iterations: int, max_path_len: int) -> np.ndarray:
    out = sm.copy()
    for _it in range(max(1, max_iterations)):
        barrier = (out >= 1) & (out <= 3)
        free = (out == 0) & (~barrier)
        ext = flood_exterior(free)
        leak = ext & union_room & free
        if not np.any(leak):
            break
        path = _bfs_path_leak_to_border(leak, free)
        if not path:
            break
        if len(path) > max_path_len:
            path = path[:max_path_len]
        for y, x in path:
            if 0 <= y < out.shape[0] and 0 <= x < out.shape[1]:
                if out[y, x] == 0:
                    out[y, x] = 1
    return out


def _run_alt1(payload: dict[str, Any]) -> dict[str, Any]:
    struct_npy = Path(payload["struct_npy"])
    rooms_json = Path(payload["rooms_json"])
    out_dir = Path(payload["out_dir"])
    ignore_thr = bool(payload["ignore_threshold"])
    struct_src = str(struct_npy)
    sm = np.load(struct_npy).astype(np.uint8, copy=False)
    h, w = sm.shape[:2]
    rooms_doc = load_json(rooms_json)
    room_dets = room_detections_list(rooms_doc, ignore_threshold=ignore_thr)
    union_room = _build_union_room(h, w, room_dets)
    space = _space_from_struct(sm, room_force_mask=union_room)
    meta = _write_step05_like(
        sm,
        space,
        room_dets=room_dets,
        out_dir=out_dir,
        tag="alt1_rooms_force_interior",
        struct_src=struct_src,
    )
    return meta


def _run_alt2(payload: dict[str, Any]) -> dict[str, Any]:
    struct_npy = Path(payload["struct_npy"])
    structure_json = Path(payload["structure_json"])
    rooms_json = Path(payload["rooms_json"])
    out_dir = Path(payload["out_dir"])
    cfg = payload["cfg_alt2"]
    ignore_thr = bool(payload["ignore_threshold"])
    sm0 = np.load(struct_npy).astype(np.uint8, copy=False)
    sdoc = load_json(structure_json)
    wall_dets = _wall_detections(sdoc, ignore_threshold=ignore_thr)
    sm = _struct_alt2_endpoint_bridge(
        sm0,
        wall_dets,
        max_endpoint_dist_px=float(cfg.get("max_endpoint_dist_px", 28)),
        min_abs_dot=float(cfg.get("min_abs_dot", 0.88)),
        line_thickness=int(cfg.get("line_thickness", 2)),
    )
    rooms_doc = load_json(rooms_json)
    room_dets = room_detections_list(rooms_doc, ignore_threshold=ignore_thr)
    space = _space_from_struct(sm, room_force_mask=None)
    meta = _write_step05_like(
        sm,
        space,
        room_dets=room_dets,
        out_dir=out_dir,
        tag="alt2_endpoint_bridge",
        struct_src=str(struct_npy),
    )
    meta["wall_detections_used"] = len(wall_dets)
    return meta


def _run_alt3(payload: dict[str, Any]) -> dict[str, Any]:
    struct_npy = Path(payload["struct_npy"])
    structure_json = Path(payload["structure_json"])
    rooms_json = Path(payload["rooms_json"])
    out_dir = Path(payload["out_dir"])
    cfg = payload["cfg_alt3"]
    ignore_thr = bool(payload["ignore_threshold"])
    sm0 = np.load(struct_npy).astype(np.uint8, copy=False)
    sdoc = load_json(structure_json)
    wall_dets = _wall_detections(sdoc, ignore_threshold=ignore_thr)
    sm = _struct_alt3_extend_segments(
        sm0,
        wall_dets,
        max_extend_px=int(cfg.get("max_extend_px", 40)),
        line_thickness=int(cfg.get("line_thickness", 2)),
    )
    rooms_doc = load_json(rooms_json)
    room_dets = room_detections_list(rooms_doc, ignore_threshold=ignore_thr)
    space = _space_from_struct(sm, room_force_mask=None)
    meta = _write_step05_like(
        sm,
        space,
        room_dets=room_dets,
        out_dir=out_dir,
        tag="alt3_extend_wall_segments",
        struct_src=str(struct_npy),
    )
    meta["wall_detections_used"] = len(wall_dets)
    return meta


def _run_alt4(payload: dict[str, Any]) -> dict[str, Any]:
    struct_npy = Path(payload["struct_npy"])
    rooms_json = Path(payload["rooms_json"])
    out_dir = Path(payload["out_dir"])
    cfg = payload["cfg_alt4"]
    ignore_thr = bool(payload["ignore_threshold"])
    sm0 = np.load(struct_npy).astype(np.uint8, copy=False)
    rooms_doc = load_json(rooms_json)
    room_dets = room_detections_list(rooms_doc, ignore_threshold=ignore_thr)
    h, w = sm0.shape[:2]
    union_room = _build_union_room(h, w, room_dets)
    sm = _struct_alt4_leak_path(
        sm0,
        union_room,
        max_iterations=int(cfg.get("max_iterations", 80)),
        max_path_len=int(cfg.get("max_path_length", 8000)),
    )
    space = _space_from_struct(sm, room_force_mask=None)
    meta = _write_step05_like(
        sm,
        space,
        room_dets=room_dets,
        out_dir=out_dir,
        tag="alt4_leak_path_wall",
        struct_src=str(struct_npy),
    )
    return meta


def run_all(
    *,
    struct_npy: Path,
    structure_json: Path,
    rooms_json: Path,
    out_root: Path,
    config_path: Path,
    ignore_threshold: bool,
    jobs: int | None = None,
) -> None:
    cfg = load_config(config_path)
    vcfg = cfg.get("exterior_interior_variants") or {}
    out_root.mkdir(parents=True, exist_ok=True)

    alt_dirs = {
        "alt1_rooms_force_interior": out_root / "alt1_rooms_force_interior",
        "alt2_endpoint_bridge": out_root / "alt2_endpoint_bridge",
        "alt3_extend_wall_segments": out_root / "alt3_extend_wall_segments",
        "alt4_leak_path_wall": out_root / "alt4_leak_path_wall",
    }

    payloads = [
        {
            "struct_npy": str(struct_npy),
            "rooms_json": str(rooms_json),
            "out_dir": str(alt_dirs["alt1_rooms_force_interior"]),
            "ignore_threshold": ignore_threshold,
        },
        {
            "struct_npy": str(struct_npy),
            "structure_json": str(structure_json),
            "rooms_json": str(rooms_json),
            "out_dir": str(alt_dirs["alt2_endpoint_bridge"]),
            "ignore_threshold": ignore_threshold,
            "cfg_alt2": vcfg.get("alt2_endpoint_bridge") or {},
        },
        {
            "struct_npy": str(struct_npy),
            "structure_json": str(structure_json),
            "rooms_json": str(rooms_json),
            "out_dir": str(alt_dirs["alt3_extend_wall_segments"]),
            "ignore_threshold": ignore_threshold,
            "cfg_alt3": vcfg.get("alt3_extend_segments") or {},
        },
        {
            "struct_npy": str(struct_npy),
            "rooms_json": str(rooms_json),
            "out_dir": str(alt_dirs["alt4_leak_path_wall"]),
            "ignore_threshold": ignore_threshold,
            "cfg_alt4": vcfg.get("alt4_leak_path") or {},
        },
    ]

    workers = jobs if jobs and jobs > 0 else 4
    futs: dict[Any, str] = {}
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=min(workers, 4)) as ex:
        futs[ex.submit(_run_alt1, payloads[0])] = "alt1"
        futs[ex.submit(_run_alt2, payloads[1])] = "alt2"
        futs[ex.submit(_run_alt3, payloads[2])] = "alt3"
        futs[ex.submit(_run_alt4, payloads[3])] = "alt4"
        for fu in as_completed(futs):
            tag = futs[fu]
            results.append({"worker": tag, "result": fu.result()})

    manifest = {
        "structural_input": str(struct_npy),
        "structure_json": str(structure_json),
        "rooms_json": str(rooms_json),
        "ignore_threshold": ignore_threshold,
        "variants_config": vcfg,
        "results": sorted(results, key=lambda r: r["worker"]),
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Step05 variants OK -> {out_root} (4 paralelas)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--struct",
        dest="struct_npy",
        type=Path,
        default=PROJECT_ROOT / "output" / "step04" / "structural_mask.npy",
        help="Máscara estructural base (default: step04, sin 4b)",
    )
    ap.add_argument(
        "--structure-json",
        type=Path,
        default=PROJECT_ROOT / "output" / "step01" / "normalized_structure.json",
    )
    ap.add_argument(
        "--rooms-json",
        type=Path,
        default=PROJECT_ROOT / "output" / "step01" / "normalized_rooms.json",
    )
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step05_variants")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--ignore-threshold", action="store_true")
    ap.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Workers ProcessPool (1–4)",
    )
    args = ap.parse_args()
    run_all(
        struct_npy=args.struct_npy,
        structure_json=args.structure_json,
        rooms_json=args.rooms_json,
        out_root=args.out,
        config_path=args.config,
        ignore_threshold=bool(args.ignore_threshold),
        jobs=int(args.jobs),
    )


if __name__ == "__main__":
    main()
