#!/usr/bin/env python3
"""
Final Step 02 — Classify exterior / interior.

Strategy: flood fill from image border marks exterior; pixels inside ∪room
polygons that the flood mistakenly reached are forced back to interior.

Outputs:
  space_classified.npy  — 0=ext, 1=wall, 2=window, 3=door, 4=interior
  space_classified.png  — color preview
  space_overlay.png     — over floorplan image
  classify_report.txt
"""
from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, save_matrix_png

IN_DIR = PROJECT_ROOT / "output" / "final" / "step01"
OUT_DIR = PROJECT_ROOT / "output" / "final" / "step02"


def _flood_exterior(free: np.ndarray) -> np.ndarray:
    h, w = free.shape
    vis = np.zeros_like(free, dtype=bool)
    q: deque[tuple[int, int]] = deque()

    def push(y: int, x: int) -> None:
        if 0 <= y < h and 0 <= x < w and free[y, x] and not vis[y, x]:
            vis[y, x] = True
            q.append((y, x))

    for x in range(w):
        push(0, x); push(h - 1, x)
    for y in range(h):
        push(y, 0); push(y, w - 1)
    while q:
        y, x = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            push(y + dy, x + dx)
    return vis


def run(struct_npy: Path, room_npy: Path, out_dir: Path) -> None:
    sm = np.load(struct_npy).astype(np.uint8)
    room = np.load(room_npy).astype(np.int32)
    H, W = sm.shape

    barrier = (sm >= 1) & (sm <= 3)
    free = ~barrier
    ext_flood = _flood_exterior(free)

    room_union = room > 0

    space = np.zeros((H, W), dtype=np.uint8)
    space[sm == 1] = 1
    space[sm == 2] = 2
    space[sm == 3] = 3

    exterior = ext_flood & free & (~room_union)
    interior = free & (~exterior)

    space[exterior] = 0
    space[interior] = 4

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "space_classified.npy", space)

    colors = {0: (200, 200, 255), 1: (40, 40, 40), 2: (0, 180, 255), 3: (0, 100, 0), 4: (255, 220, 180)}
    save_matrix_png(space, out_dir / "space_classified.png", colors)

    floor = PROJECT_ROOT / "Floorplan2.png"
    if floor.is_file():
        base = cv2.imread(str(floor), cv2.IMREAD_COLOR)
        if base.shape[:2] == (H, W):
            cm = np.zeros_like(base)
            for k, rgb in colors.items():
                cm[space == k] = rgb
            over = cv2.addWeighted(base, 0.6, cm, 0.4, 0)
            cv2.imwrite(str(out_dir / "space_overlay.png"), over)

    n_ext = int((space == 0).sum())
    n_int = int((space == 4).sum())
    n_forced = int((ext_flood & free & room_union).sum())
    report = [
        f"exterior_pixels: {n_ext}",
        f"interior_pixels: {n_int}",
        f"barrier_pixels: {int(barrier.sum())}",
        f"room_union_pixels: {int(room_union.sum())}",
        f"forced_interior_from_room_union: {n_forced}",
    ]
    (out_dir / "classify_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"FinalStep02 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--struct", type=Path, default=IN_DIR / "structural_mask.npy")
    ap.add_argument("--rooms", type=Path, default=IN_DIR / "room_polygons.npy")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    run(args.struct, args.rooms, args.out)


if __name__ == "__main__":
    main()
