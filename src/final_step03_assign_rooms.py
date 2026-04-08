#!/usr/bin/env python3
"""
Final Step 03 — Assign room IDs to interior pixels.

Uses room polygons rasterized in step01 (claim by confidence, already done).
Keeps only detected rooms; remaining interior pixels stay 0 and will be
handled later as low-confidence inferred rooms in step04.

Outputs:
  room_id_matrix.npy   — 0=no room, 1..K=room_id  (pixel-level)
  room_id_preview.png  — color preview
  rooms_report.txt
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, save_json

STEP01_DIR = PROJECT_ROOT / "output" / "final" / "step01"
STEP02_DIR = PROJECT_ROOT / "output" / "final" / "step02"
OUT_DIR = PROJECT_ROOT / "output" / "final" / "step03"


def run(space_npy: Path, room_npy: Path, out_dir: Path) -> None:
    space = np.load(space_npy).astype(np.uint8)
    room = np.load(room_npy).astype(np.int32)
    H, W = space.shape

    n_rooms = int(room.max())
    interior = space == 4
    result = room.copy()
    # Keep only detected room polygons on interior; do not force-fill holes.
    result[~interior] = 0

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "room_id_matrix.npy", result)

    rng = np.random.default_rng(42)
    prev = np.full((H, W, 3), 240, dtype=np.uint8)
    for rid in range(1, n_rooms + 1):
        col = tuple(int(v) for v in rng.integers(60, 230, size=3))
        prev[result == rid] = col
    cv2.imwrite(str(out_dir / "room_id_preview.png"), prev)

    assigned_from_polygon = int((result > 0).sum())
    interior_undetected = int((interior & (result == 0)).sum())
    report = [
        f"n_rooms: {n_rooms}",
        f"interior_pixels: {int(interior.sum())}",
        f"assigned_from_polygon: {assigned_from_polygon}",
        f"interior_pixels_without_detected_room: {interior_undetected}",
    ]
    for rid in range(1, n_rooms + 1):
        report.append(f"  room_{rid}: {int((result == rid).sum())} px")
    (out_dir / "rooms_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"FinalStep03 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", type=Path, default=STEP02_DIR / "space_classified.npy")
    ap.add_argument("--rooms", type=Path, default=STEP01_DIR / "room_polygons.npy")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    run(args.space, args.rooms, args.out)


if __name__ == "__main__":
    main()
