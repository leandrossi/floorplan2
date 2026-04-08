#!/usr/bin/env python3
"""
Step 09: export único CSV tipo floor.csv.

Precedencia de token por celda:
1) wall   -> '#'
2) window -> 'W'
3) door   -> 'D'
4) room_id>0 -> '<id>'
5) otro -> '0'
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, save_json


def combine_tokens(
    struct_m: np.ndarray,
    rooms_m: np.ndarray,
    inferred_rooms_m: np.ndarray | None = None,
) -> np.ndarray:
    if struct_m.shape != rooms_m.shape:
        raise ValueError(f"shape mismatch struct={struct_m.shape} rooms={rooms_m.shape}")

    h, w = struct_m.shape
    out = np.full((h, w), "0", dtype=object)

    # Rooms first.
    room_mask = rooms_m > 0
    out[room_mask] = rooms_m[room_mask].astype(str)

    # Inferred rooms: token "-<id>" (e.g. -1, -2).
    if inferred_rooms_m is not None:
        if inferred_rooms_m.shape != rooms_m.shape:
            raise ValueError(
                f"shape mismatch inferred_rooms={inferred_rooms_m.shape} rooms={rooms_m.shape}"
            )
        inf = inferred_rooms_m > 0
        out[inf] = np.char.add("-", inferred_rooms_m[inf].astype(str))

    # Inferred low-confidence wall between different room ids when no structure.
    # Symbol: 'i' (inferred wall, lower certainty than '#').
    inferred = np.zeros((h, w), dtype=bool)
    non_struct = (struct_m != 1) & (struct_m != 2) & (struct_m != 3)
    rr = rooms_m

    # Horizontal room boundaries
    diff_h = (rr[:, 1:] > 0) & (rr[:, :-1] > 0) & (rr[:, 1:] != rr[:, :-1])
    inferred[:, 1:] |= diff_h
    inferred[:, :-1] |= diff_h

    # Vertical room boundaries
    diff_v = (rr[1:, :] > 0) & (rr[:-1, :] > 0) & (rr[1:, :] != rr[:-1, :])
    inferred[1:, :] |= diff_v
    inferred[:-1, :] |= diff_v

    inferred &= non_struct
    out[inferred] = "i"

    # Finally, structure overwrites everything.
    out[struct_m == 3] = "D"
    out[struct_m == 2] = "W"
    out[struct_m == 1] = "#"
    return out


def preview_from_tokens(tokens: np.ndarray) -> np.ndarray:
    h, w = tokens.shape
    out = np.full((h, w, 3), (240, 240, 240), dtype=np.uint8)
    out[tokens == "#"] = (40, 40, 40)
    out[tokens == "W"] = (0, 180, 255)
    out[tokens == "D"] = (0, 100, 0)
    out[tokens == "i"] = (120, 120, 120)
    out[tokens == "0"] = (220, 220, 255)

    # Room ids palette
    ids = sorted({int(x) for x in np.unique(tokens) if str(x).isdigit() and int(x) > 0})
    rng = np.random.default_rng(101)
    for rid in ids:
        col = tuple(int(v) for v in rng.integers(60, 235, size=3))
        out[tokens == str(rid)] = col
    return out


def write_csv_semicolon(path: Path, tokens: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter=";", lineterminator="\n")
        for row in tokens.tolist():
            wr.writerow(row)


def run(
    struct_npy: Path,
    rooms_npy: Path,
    inferred_rooms_npy: Path | None,
    out_dir: Path,
) -> None:
    struct_m = np.load(struct_npy).astype(np.uint8)
    rooms_m = np.load(rooms_npy).astype(np.int32)
    inferred_rooms_m = None
    if inferred_rooms_npy is not None and inferred_rooms_npy.is_file():
        inferred_rooms_m = np.load(inferred_rooms_npy).astype(np.int32)
    tokens = combine_tokens(struct_m, rooms_m, inferred_rooms_m)

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "floor_like.csv"
    npy_path = out_dir / "floor_like_tokens.npy"
    png_path = out_dir / "floor_like_preview.png"

    write_csv_semicolon(csv_path, tokens)
    np.save(npy_path, tokens)
    cv2.imwrite(str(png_path), preview_from_tokens(tokens))

    unique_tokens = sorted({str(x) for x in np.unique(tokens)})
    meta = {
        "inputs": {
            "structure_matrix_npy": str(struct_npy),
            "rooms_matrix_npy": str(rooms_npy),
            "inferred_rooms_npy": str(inferred_rooms_npy) if inferred_rooms_npy else None,
        },
        "shape": [int(tokens.shape[0]), int(tokens.shape[1])],
        "csv_delimiter": ";",
        "token_precedence": ["#", "W", "D", "i", "-<room_id>", "<room_id>", "0"],
        "token_meaning": {
            "#": "wall",
            "W": "window",
            "D": "door",
            "i": "inferred_wall_low_confidence",
            "-1..-N": "inferred_room_id_low_confidence",
            "0": "exterior_or_empty",
            "1..N": "room_id",
        },
        "unique_tokens": unique_tokens,
    }
    save_json(out_dir / "floor_like_metadata.json", meta)
    print(f"Step09 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--structure",
        type=Path,
        default=PROJECT_ROOT / "output" / "step07" / "final_structure_matrix.npy",
    )
    ap.add_argument(
        "--rooms",
        type=Path,
        default=PROJECT_ROOT / "output" / "step07" / "final_rooms_matrix.npy",
    )
    ap.add_argument(
        "--rooms-inferred",
        type=Path,
        default=PROJECT_ROOT / "output" / "step07" / "final_rooms_inferred_mask.npy",
    )
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step09")
    args = ap.parse_args()
    run(args.structure, args.rooms, args.rooms_inferred, args.out)


if __name__ == "__main__":
    main()
