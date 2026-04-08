#!/usr/bin/env python3
"""
Step 05: exterior (borde) vs interior; más dos capas paralelas:

- space_classified.npy — igual que antes (0 ext, 1–3 barrera, 4 interior).
- space_interior_topology.npy — componentes conexas del interior (4-conexo); ids 1..M.
- space_interior_room_proposal.npy — K regiones (K = detecciones room): dominio = unión de todos
  los polígonos room (no solo píxeles clase 4), para alinear con el vis del modelo aunque parte
  caiga en exterior/puerta en la capa estructural.
"""
from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, load_json, rasterize_polygons, save_matrix_png


def flood_exterior(free: np.ndarray) -> np.ndarray:
    h, w = free.shape
    vis = np.zeros_like(free, dtype=bool)
    q: deque[tuple[int, int]] = deque()

    def push(y: int, x: int) -> None:
        if 0 <= y < h and 0 <= x < w and free[y, x] and not vis[y, x]:
            vis[y, x] = True
            q.append((y, x))

    for x in range(w):
        push(0, x)
        push(h - 1, x)
    for y in range(h):
        push(y, 0)
        push(y, w - 1)

    while q:
        y, x = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            push(y + dy, x + dx)
    return vis


def room_detections_list(doc: dict, *, ignore_threshold: bool) -> list[dict]:
    out: list[dict] = []
    for d in doc.get("detections", []):
        if d.get("exclude_reason"):
            continue
        if not ignore_threshold and not d.get("passes_threshold"):
            continue
        if d.get("class_norm") != "room":
            continue
        pts = d.get("points") or []
        if len(pts) < 3:
            continue
        out.append(d)
    return out


def raster_room_mask(h: int, w: int, det: dict) -> np.ndarray:
    pts = [[int(p[0]), int(p[1])] for p in det["points"]]
    m = rasterize_polygons(h, w, [(pts, 1)])
    return m > 0


def room_centroids(room_dets: list[dict]) -> np.ndarray:
    c: list[tuple[float, float]] = []
    for d in room_dets:
        pts = np.array([[float(p[0]), float(p[1])] for p in d["points"]], dtype=np.float64)
        c.append((float(pts[:, 0].mean()), float(pts[:, 1].mean())))
    return np.array(c, dtype=np.float64)


def proposal_layer(domain: np.ndarray, room_dets: list[dict], h: int, w: int) -> np.ndarray:
    """
    Partición 1..K sobre `domain` (típicamente ∪ polígonos room):

    1) Orden (-confidence, índice): cada detección reclama polígono ∩ domain aún libre.
    2) Huecos en domain: Voronoi euclídeo al centroide más cercano.

    Usar solo interior estructural (4) deja habitaciones en 0 píxeles cuando el modelo dibuja
    room sobre exterior/puertas respecto al flood fill.
    """
    if not room_dets:
        return np.zeros((h, w), dtype=np.int32)

    order = sorted(
        range(len(room_dets)),
        key=lambda i: (-float(room_dets[i].get("confidence", 0.0)), i),
    )
    out = np.zeros((h, w), dtype=np.int32)
    for i in order:
        rid = i + 1
        m = raster_room_mask(h, w, room_dets[i]) & domain & (out == 0)
        out[m] = rid

    hole = domain & (out == 0)
    ys, xs = np.where(hole)
    if ys.size == 0:
        return out

    cmat = room_centroids(room_dets)
    grid = np.column_stack([xs.astype(np.float64), ys.astype(np.float64)])
    d2 = np.sum((grid[:, None, :] - cmat[None, :, :]) ** 2, axis=2)
    out[ys, xs] = np.argmin(d2, axis=1).astype(np.int32) + 1
    return out


def label_preview(labels: np.ndarray, *, skip_zero: bool = True) -> np.ndarray:
    """RGB preview; 0 negro o gris si skip_zero."""
    h, w = labels.shape[:2]
    prev = np.full((h, w, 3), 240, dtype=np.uint8)
    u = [int(x) for x in np.unique(labels) if x != 0 or not skip_zero]
    if not skip_zero and 0 in np.unique(labels):
        u = [int(x) for x in np.unique(labels)]
    rng = np.random.default_rng(123)
    cols = {0: (240, 240, 240)} if not skip_zero else {}
    for lab in u:
        if lab == 0:
            continue
        cols[lab] = tuple(int(x) for x in rng.integers(60, 230, size=3))
    for lab, rgb in cols.items():
        prev[labels == lab] = rgb
    return prev


def run(
    struct_npy: Path,
    rooms_json: Path,
    out_dir: Path,
    *,
    ignore_threshold: bool = False,
) -> None:
    sm = np.load(struct_npy)
    barrier = (sm == 1) | (sm == 2) | (sm == 3)
    free = (sm == 0) & (~barrier)
    ext = flood_exterior(free)

    space = np.zeros_like(sm, dtype=np.uint8)
    space[sm == 1] = 1
    space[sm == 2] = 2
    space[sm == 3] = 3
    space[free & ext] = 0
    space[free & (~ext)] = 4

    h, w = space.shape[:2]
    interior = space == 4

    out_dir.mkdir(parents=True, exist_ok=True)
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

    # --- Capa A: topología pura (CC del interior, 4-conexo) ---
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

    # --- Capa B: propuestas room (ids del JSON, partición por confianza) ---
    rooms_doc = load_json(rooms_json)
    room_dets = room_detections_list(rooms_doc, ignore_threshold=ignore_threshold)
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
    topo_ids = int(n_cc - 1)
    prop_ids = len(room_dets)
    prop_labeled = int(np.sum(proposal > 0))

    counts_prop: list[str] = []
    for rid in range(1, prop_ids + 1):
        a = int(np.sum(proposal == rid))
        ov = int(np.sum((proposal == rid) & interior))
        counts_prop.append(f"  room_proposal_id={rid} pixels={a} overlap_struct_interior={ov}")

    report = [
        f"interior_pixels: {n_int}",
        f"exterior_pixels: {n_ext}",
        f"barrier_wall: {int((space==1).sum())}",
        f"barrier_window: {int((space==2).sum())}",
        f"barrier_door: {int((space==3).sum())}",
        "",
        f"topology_interior_components: {topo_ids}",
        f"room_detections_used: {prop_ids}",
        f"interior_pixels_assigned_a_room_proposal: {prop_labeled}",
        "",
        "room_proposal_pixel_counts:",
        *counts_prop,
        "",
        "notes:",
        "- space_interior_topology: componentes del interior solo por geometría estructural (pocas regiones grandes).",
        "- space_interior_room_proposal: dominio = unión polígonos room; claim por conf + Voronoi en huecos.",
    ]
    if n_int == 0:
        report.append("WARNING: no interior pixels — check structural closure.")
    if n_ext == 0:
        report.append("WARNING: no exterior pixels — unusual for border flood.")

    (out_dir / "regions_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Step05 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in",
        dest="inp",
        type=Path,
        default=PROJECT_ROOT / "output" / "step04b" / "structural_mask_sealed.npy",
    )
    ap.add_argument(
        "--rooms-json",
        type=Path,
        default=PROJECT_ROOT / "output" / "step01" / "normalized_rooms.json",
    )
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step05")
    ap.add_argument(
        "--ignore-threshold",
        action="store_true",
        help="Incluye detecciones room aunque no cumplan passes_threshold",
    )
    args = ap.parse_args()
    run(
        args.inp,
        args.rooms_json,
        args.out,
        ignore_threshold=bool(args.ignore_threshold),
    )


if __name__ == "__main__":
    main()
