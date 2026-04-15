#!/usr/bin/env python3
"""
Final Step 04 — Downsample to cell grid + export CSV.

Reads pixel-level space_classified + room_id_matrix, downsamples to
cell_size_px blocks, exports:
  final_structure_matrix.npy/.csv
  final_rooms_matrix.npy/.csv
  floor_like.csv            — combined tokens (#, W, D, i, -N, N, 0)
  floor_like_preview.png
  final_metadata.json
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from opening_adjacency import enforce_opening_adjacency
from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, save_json, save_matrix_png
from review_bundle_io import write_review_bundle
from struct_border_exterior_pad import pad_struct_grids_in_place

STEP02_DIR = PROJECT_ROOT / "output" / "final" / "step02"
STEP03_DIR = PROJECT_ROOT / "output" / "final" / "step03"
OUT_DIR = PROJECT_ROOT / "output" / "final" / "step04"


def _struct_cell(block: np.ndarray, wall_fill_ratio: float) -> int:
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
    return 4 if n_int > n_ext else 0


def _room_vote(block: np.ndarray) -> int:
    pos = block[block > 0]
    if pos.size == 0:
        return 0
    return int(np.argmax(np.bincount(pos.astype(int))))


def _free_cell_vote(block: np.ndarray) -> int:
    n0 = int(np.sum(block == 0))
    n4 = int(np.sum(block == 4))
    return 4 if n4 >= n0 else 0


def _seal_exterior_interior_boundary(
    struct_out: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    """
    Convert exterior cells (0) directly 4-adjacent to interior cells (4) into
    wall (1).  Returns (boolean mask of converted cells, log lines).

    These are boundary holes where the model failed to detect a wall segment
    between the building interior and the outside.
    """
    h, w = struct_out.shape
    is_interior = struct_out == 4
    is_exterior = struct_out == 0

    adj_interior = np.zeros((h, w), dtype=bool)
    adj_interior[1:, :] |= is_interior[:-1, :]
    adj_interior[:-1, :] |= is_interior[1:, :]
    adj_interior[:, 1:] |= is_interior[:, :-1]
    adj_interior[:, :-1] |= is_interior[:, 1:]

    sealed = is_exterior & adj_interior
    struct_out[sealed] = 1

    logs: list[str] = []
    if int(sealed.sum()) > 0:
        ys, xs = np.where(sealed)
        logs.append(f"sealed {int(sealed.sum())} exterior→wall cells at interior boundary")
        for y, x in zip(ys.tolist(), xs.tolist()):
            logs.append(f"  ({y},{x})")
    return sealed, logs


def _label_inferred_interior_components(
    struct_out: np.ndarray, room_out: np.ndarray
) -> tuple[np.ndarray, list[str]]:
    """
    Keep detected rooms untouched.
    For interior cells with no detected room, assign connected-component
    negative ids: -1, -2, ...
    """
    unknown = (struct_out == 4) & (room_out == 0)
    ncc, labels = cv2.connectedComponents(unknown.astype(np.uint8), connectivity=4)
    inferred_neg = np.zeros_like(room_out, dtype=np.int32)
    report: list[str] = []
    next_id = 1
    for cc in range(1, ncc):
        comp = labels == cc
        area = int(comp.sum())
        if area == 0:
            continue
        neg_id = -next_id
        next_id += 1
        inferred_neg[comp] = neg_id
        report.append(f"cc={cc} area={area} -> inferred_room={neg_id}")
    return inferred_neg, report


def _combine_tokens(
    struct_m: np.ndarray, rooms_m: np.ndarray, inferred_m: np.ndarray | None,
) -> np.ndarray:
    h, w = struct_m.shape
    out = np.full((h, w), "0", dtype=object)
    out[rooms_m > 0] = rooms_m[rooms_m > 0].astype(str)

    if inferred_m is not None:
        inf = inferred_m < 0
        out[inf] = inferred_m[inf].astype(str)

    rr = rooms_m
    non_struct = (struct_m != 1) & (struct_m != 2) & (struct_m != 3)
    inferred_wall = np.zeros((h, w), dtype=bool)
    diff_h = (rr[:, 1:] > 0) & (rr[:, :-1] > 0) & (rr[:, 1:] != rr[:, :-1])
    inferred_wall[:, 1:] |= diff_h
    inferred_wall[:, :-1] |= diff_h
    diff_v = (rr[1:, :] > 0) & (rr[:-1, :] > 0) & (rr[1:, :] != rr[:-1, :])
    inferred_wall[1:, :] |= diff_v
    inferred_wall[:-1, :] |= diff_v
    inferred_wall &= non_struct
    out[inferred_wall] = "i"

    # Around openings, prefer contextual free-space token (room/exterior) over inferred wall.
    opening = (struct_m == 2) | (struct_m == 3)
    if np.any(opening):
        near_open = np.zeros((h, w), dtype=bool)
        near_open[1:, :] |= opening[:-1, :]
        near_open[:-1, :] |= opening[1:, :]
        near_open[:, 1:] |= opening[:, :-1]
        near_open[:, :-1] |= opening[:, 1:]
        cand = (out == "i") & near_open
        ys, xs = np.where(cand)
        for y, x in zip(ys.tolist(), xs.tolist()):
            neigh_room: list[int] = []
            has_exterior = False
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    rv = int(rooms_m[ny, nx])
                    sv = int(struct_m[ny, nx])
                    if rv > 0 and sv not in (1, 2, 3):
                        neigh_room.append(rv)
                    if sv == 0:
                        has_exterior = True
            if neigh_room:
                out[y, x] = str(int(np.argmax(np.bincount(np.array(neigh_room, dtype=np.int32)))))
            elif has_exterior:
                out[y, x] = "0"

    out[struct_m == 3] = "D"
    out[struct_m == 2] = "W"
    out[struct_m == 1] = "#"
    return out


def _token_preview(tokens: np.ndarray) -> np.ndarray:
    h, w = tokens.shape
    img = np.full((h, w, 3), (240, 240, 240), dtype=np.uint8)
    img[tokens == "#"] = (40, 40, 40)
    img[tokens == "W"] = (0, 180, 255)
    img[tokens == "D"] = (0, 100, 0)
    img[tokens == "i"] = (120, 120, 120)
    img[tokens == "0"] = (220, 220, 255)
    ids = sorted({int(x) for x in np.unique(tokens) if str(x).isdigit() and int(x) > 0})
    neg_ids = sorted({int(x) for x in np.unique(tokens) if str(x).startswith("-") and str(x)[1:].isdigit()})
    rng = np.random.default_rng(101)
    for rid in ids:
        col = tuple(int(v) for v in rng.integers(60, 235, size=3))
        img[tokens == str(rid)] = col
    for nid in neg_ids:
        # inferred room ids use darker magenta palette
        base = tuple(int(v) for v in rng.integers(120, 220, size=3))
        img[tokens == str(nid)] = (max(0, base[0] - 40), 40, max(0, base[2] - 20))
    return img


def run(space_npy: Path, room_npy: Path, config_path: Path, out_dir: Path) -> None:
    cfg = load_config(config_path)
    mx = cfg.get("matrix") or {}
    cell_px = max(1, int(mx.get("cell_size_px", 5)))
    wall_fill = float(mx.get("wall_fill_ratio", 0.2))

    space = np.load(space_npy).astype(np.uint8)
    room = np.load(room_npy).astype(np.int32)
    h, w = space.shape

    Hc = (h + cell_px - 1) // cell_px
    Wc = (w + cell_px - 1) // cell_px
    struct_out = np.zeros((Hc, Wc), dtype=np.uint8)
    room_out = np.zeros((Hc, Wc), dtype=np.int32)
    free_pref = np.zeros((Hc, Wc), dtype=np.uint8)

    for gi in range(Hc):
        for gj in range(Wc):
            ys, ye = gi * cell_px, min((gi + 1) * cell_px, h)
            xs, xe = gj * cell_px, min((gj + 1) * cell_px, w)
            sb = space[ys:ye, xs:xe]
            struct_out[gi, gj] = _struct_cell(sb, wall_fill)
            room_out[gi, gj] = _room_vote(room[ys:ye, xs:xe])
            free_pref[gi, gj] = _free_cell_vote(sb)

    pad_report: list[str] = []
    if bool(mx.get("pad_exterior_border", True)):
        struct_out, room_out, free_pref, _cum_pad, pad_report = pad_struct_grids_in_place(
            struct_out, room_out, free_pref, max_passes=4
        )

    opening_fix_report = enforce_opening_adjacency(struct_out, free_pref)
    sealed_mask, seal_report = _seal_exterior_interior_boundary(struct_out)

    inferred_mask, infer_report = _label_inferred_interior_components(struct_out, room_out)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "final_structure_matrix.npy", struct_out)
    np.save(out_dir / "final_rooms_matrix.npy", room_out)
    np.save(out_dir / "final_rooms_inferred_mask.npy", inferred_mask)
    np.savetxt(out_dir / "final_structure_matrix.csv", struct_out, fmt="%d", delimiter=",")
    np.savetxt(out_dir / "final_rooms_matrix.csv", room_out, fmt="%d", delimiter=",")

    s_colors = {0: (200, 200, 255), 1: (40, 40, 40), 2: (0, 180, 255), 3: (0, 100, 0), 4: (255, 220, 180)}
    save_matrix_png(struct_out, out_dir / "final_structure_preview.png", s_colors)

    tokens = _combine_tokens(struct_out, room_out, inferred_mask)
    tokens[sealed_mask] = "i"
    csv_path = out_dir / "floor_like.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter=";", lineterminator="\n")
        for row in tokens.tolist():
            wr.writerow(row)
    np.save(out_dir / "floor_like_tokens.npy", tokens)
    cv2.imwrite(str(out_dir / "floor_like_preview.png"), _token_preview(tokens))

    meta = {
        "cell_size_px": cell_px,
        "grid_shape": [int(struct_out.shape[0]), int(struct_out.shape[1])],
        "source_shape": [h, w],
        "downsample_grid_shape": [int(Hc), int(Wc)],
        "wall_fill_ratio": wall_fill,
        "pad_exterior_border_applied": bool(mx.get("pad_exterior_border", True)),
        "exterior_border_pad_log": pad_report,
        "unique_tokens": sorted({str(x) for x in np.unique(tokens)}),
        "token_meaning": {
            "#": "wall", "W": "window", "D": "door",
            "i": "inferred_wall", "0": "exterior",
            "1..N": "room_id", "-1..-N": "inferred_room_id",
        },
    }
    save_json(out_dir / "final_metadata.json", meta)
    (out_dir / "infer_report.txt").write_text(
        "\n".join(infer_report) + ("\n" if infer_report else ""), encoding="utf-8",
    )
    (out_dir / "opening_adjacency_report.txt").write_text(
        "\n".join(opening_fix_report) + ("\n" if opening_fix_report else ""), encoding="utf-8",
    )
    (out_dir / "exterior_border_pad_report.txt").write_text(
        "\n".join(pad_report) + ("\n" if pad_report else ""), encoding="utf-8",
    )
    (out_dir / "seal_boundary_report.txt").write_text(
        "\n".join(seal_report) + ("\n" if seal_report else ""), encoding="utf-8",
    )
    try:
        write_review_bundle(out_dir, config_path, security_level="optimal")
    except Exception as e:  # noqa: BLE001
        print(f"FinalStep04 warning: review_bundle skipped: {e}", flush=True)
    print(f"FinalStep04 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", type=Path, default=STEP02_DIR / "space_classified.npy")
    ap.add_argument("--rooms", type=Path, default=STEP03_DIR / "room_id_matrix.npy")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    run(args.space, args.rooms, args.config, args.out)


if __name__ == "__main__":
    main()
