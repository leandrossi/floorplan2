#!/usr/bin/env python3
"""Step 07: downsample to cell matrices + final metadata."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import (
    DEFAULT_CONFIG,
    PROJECT_ROOT,
    load_config,
    save_json,
    save_matrix_png,
)


def struct_cell_from_block(block: np.ndarray, wall_fill_ratio: float) -> int:
    flat = block.ravel()
    n = flat.size
    if n == 0:
        return 0
    if np.any(flat == 3):
        return 3
    if np.any(flat == 2):
        return 2
    n_wall = int(np.sum(flat == 1))
    if n_wall / n >= wall_fill_ratio:
        return 1
    n_int = int(np.sum(flat == 4))
    n_ext = int(np.sum(flat == 0))
    if n_int > n_ext:
        return 4
    return 0


def room_vote(rm_b: np.ndarray) -> int:
    v = rm_b
    if v.size == 0:
        return 0
    pos = v[v > 0]
    if pos.size == 0:
        return 0
    bc = np.bincount(pos.astype(int))
    return int(np.argmax(bc))


def fill_unknown_interior_rooms(
    struct_out: np.ndarray,
    room_out: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Rellena celdas interiores (struct==4) con room==0 usando vecindad de room ids.
    Devuelve (room_filled, inferred_mask_id, report_lines).
    """
    import cv2

    room_filled = room_out.copy()
    unknown = (struct_out == 4) & (room_filled == 0)
    unknown_u8 = unknown.astype(np.uint8)
    ncc, labels = cv2.connectedComponents(unknown_u8, connectivity=4)
    inferred_mask = np.zeros_like(room_filled, dtype=np.int32)
    report: list[str] = []

    for cc in range(1, ncc):
        comp = labels == cc
        if not np.any(comp):
            continue

        # Vecinos 4-conexos alrededor del componente
        neigh_ids: list[int] = []
        ys, xs = np.where(comp)
        for y, x in zip(ys.tolist(), xs.tolist()):
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < room_filled.shape[0] and 0 <= nx < room_filled.shape[1]:
                    rid = int(room_filled[ny, nx])
                    if rid > 0:
                        neigh_ids.append(rid)

        if not neigh_ids:
            report.append(f"cc={cc} area={int(comp.sum())} -> sin vecinos room, queda 0")
            continue

        bc = np.bincount(np.array(neigh_ids, dtype=np.int32))
        chosen = int(np.argmax(bc))
        room_filled[comp] = chosen
        inferred_mask[comp] = chosen
        report.append(
            f"cc={cc} area={int(comp.sum())} -> inferred_room={chosen} neighbor_votes={int(bc[chosen])}"
        )

    return room_filled, inferred_mask, report


def run(
    space_npy: Path,
    room_npy: Path,
    config_path: Path,
    out_dir: Path,
) -> None:
    cfg = load_config(config_path)
    mx = cfg.get("matrix") or {}
    mode = str(mx.get("mode", "relative_scale"))
    cell_cm_req = float(mx.get("cell_size_cm", 5))
    ppm = mx.get("pixels_per_meter")
    wall_fill_ratio = float(mx.get("wall_fill_ratio", 0.2))

    space = np.load(space_npy).astype(np.uint8)
    room = np.load(room_npy).astype(np.int32)
    h, w = space.shape[:2]

    if mode == "real_scale" and ppm is not None:
        cell_size_px = max(1, int(round(float(ppm) * 0.05)))
        scale_mode = "real_scale"
        cell_cm_real = cell_cm_req
        note = "Metric scale from pixels_per_meter; cell ~5cm."
    else:
        cell_size_px = max(1, int(mx.get("cell_size_px", 5)))
        scale_mode = "relative_scale"
        cell_cm_real = None
        note = "No real-world metric scale available; matrix built using relative pixel blocks."

    Hc = (h + cell_size_px - 1) // cell_size_px
    Wc = (w + cell_size_px - 1) // cell_size_px
    struct_out = np.zeros((Hc, Wc), dtype=np.uint8)
    room_out = np.zeros((Hc, Wc), dtype=np.int32)

    for gi in range(Hc):
        for gj in range(Wc):
            ys, ye = gi * cell_size_px, min((gi + 1) * cell_size_px, h)
            xs, xe = gj * cell_size_px, min((gj + 1) * cell_size_px, w)
            sb = space[ys:ye, xs:xe]
            rb = room[ys:ye, xs:xe]
            sc = struct_cell_from_block(sb, wall_fill_ratio)
            struct_out[gi, gj] = sc
            # Nueva regla: room ids no dependen de que la celda sea interior(4).
            # Esto preserva la particion de 10 habitaciones definida en step06.
            room_out[gi, gj] = room_vote(rb)

    # Inferencia de 0 interiores restantes en malla final
    room_out_filled, inferred_mask, infer_report = fill_unknown_interior_rooms(struct_out, room_out)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "final_structure_matrix.npy", struct_out)
    np.save(out_dir / "final_rooms_matrix.npy", room_out_filled)
    np.save(out_dir / "final_rooms_inferred_mask.npy", inferred_mask)
    np.savetxt(out_dir / "final_structure_matrix.csv", struct_out, fmt="%d", delimiter=",")
    np.savetxt(out_dir / "final_rooms_matrix.csv", room_out_filled, fmt="%d", delimiter=",")

    colors_s = {
        0: (200, 200, 255),
        1: (40, 40, 40),
        2: (0, 180, 255),
        3: (0, 100, 0),
        4: (255, 220, 180),
    }
    save_matrix_png(struct_out, out_dir / "final_structure_preview.png", colors_s)

    rng = np.random.default_rng(99)
    prev = np.zeros((*room_out.shape, 3), dtype=np.uint8)
    rid_max = int(room_out_filled.max())
    for i in range(1, rid_max + 1):
        prev[room_out_filled == i] = tuple(int(x) for x in rng.integers(60, 255, size=3))
    # Borde negro para celdas inferidas
    infer_edge = (inferred_mask > 0).astype(np.uint8) * 255
    infer_edge = cv2.Canny(infer_edge, 50, 150)
    prev[infer_edge > 0] = (0, 0, 0)
    cv2.imwrite(str(out_dir / "final_rooms_preview.png"), prev)

    meta = {
        "scale_mode": scale_mode,
        "cell_size_px": cell_size_px,
        "cell_size_cm_requested": cell_cm_req,
        "cell_size_cm_real": cell_cm_real,
        "pixels_per_meter": ppm,
        "grid_shape": [int(Hc), int(Wc)],
        "source_image_shape": [int(h), int(w)],
        "wall_fill_ratio": wall_fill_ratio,
        "structural_encoding": {"0": "exterior", "1": "wall", "2": "window", "3": "door", "4": "interior"},
        "room_encoding": {"0": "no_room_or_structure", "1..N": "room_id"},
        "inferred_room_encoding": {"0": "not_inferred", "1..N": "inferred_room_id"},
        "note": note,
    }
    save_json(out_dir / "final_metadata.json", meta)
    (out_dir / "final_rooms_inference_report.txt").write_text(
        "\n".join(infer_report) + ("\n" if infer_report else ""),
        encoding="utf-8",
    )
    print(f"Step07 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", type=Path, default=PROJECT_ROOT / "output" / "step05" / "space_classified.npy")
    ap.add_argument("--rooms", type=Path, default=PROJECT_ROOT / "output" / "step06" / "room_id_matrix.npy")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step07")
    args = ap.parse_args()
    run(args.space, args.rooms, args.config, args.out)


if __name__ == "__main__":
    main()
