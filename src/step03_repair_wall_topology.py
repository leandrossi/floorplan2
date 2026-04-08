#!/usr/bin/env python3
"""Step 03: repair wall layer continuity (morph close + small component removal)."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, save_matrix_png


def run(raw_npy: Path, config_path: Path, out_dir: Path) -> None:
    cfg = load_config(config_path)
    wr = cfg.get("wall_repair") or {}
    gap = int(wr.get("close_gap_px", 6))
    min_px = int(wr.get("remove_small_components_px", 20))

    raw = np.load(raw_npy)
    wall = (raw == 1).astype(np.uint8) * 255

    k = max(3, gap | 1)  # odd kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    closed = cv2.morphologyEx(wall, cv2.MORPH_CLOSE, kernel, iterations=1)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    kept = np.zeros_like(closed)
    removed = 0
    for i in range(1, num):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_px:
            removed += 1
            continue
        kept[labels == i] = 255

    repaired_bin = (kept > 0).astype(np.uint8)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "repaired_wall_mask.npy", repaired_bin)

    colors = {0: (255, 255, 255), 1: (40, 40, 40)}
    save_matrix_png(repaired_bin, out_dir / "repaired_wall_mask.png", colors)

    w0 = (wall > 0).astype(np.uint8)
    w1 = repaired_bin
    diff = np.zeros((*w0.shape, 3), dtype=np.uint8)
    diff[(w1 == 1) & (w0 == 0)] = (0, 255, 0)  # added
    diff[(w0 == 1) & (w1 == 0)] = (0, 0, 255)  # removed
    cv2.imwrite(str(out_dir / "wall_diff.png"), diff)

    report = [
        f"close_gap_px kernel: {k}x{k}",
        f"remove_small_components_px: {min_px}",
        f"components_removed_small: {removed}",
        f"wall_pixels_before: {int(w0.sum())}",
        f"wall_pixels_after: {int(w1.sum())}",
    ]
    (out_dir / "wall_repair_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Step03 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--raw",
        type=Path,
        default=PROJECT_ROOT / "output" / "step02" / "raw_structure_mask.npy",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step03")
    args = ap.parse_args()
    run(args.raw, args.config, args.out)


if __name__ == "__main__":
    main()
