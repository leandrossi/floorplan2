#!/usr/bin/env python3
"""
Step 04b: cerrar micro-gaps en la envolvente estructural (muro+ventana+puerta)
antes del flood fill del paso 5.

Uniendo 1|2|3, morphological close; píxeles nuevos se etiquetan como muro (1).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, save_matrix_png


def run(struct_npy: Path, config_path: Path, out_dir: Path) -> None:
    cfg = load_config(config_path)
    seal = cfg.get("barrier_seal") or {}
    gap = int(seal.get("close_gap_px", 5))
    iters = int(seal.get("close_iterations", 1))

    sm = np.load(struct_npy).astype(np.uint8)
    barrier = ((sm >= 1) & (sm <= 3)).astype(np.uint8)

    if gap <= 0:
        sealed = sm.copy()
        seal_mask = np.zeros_like(sm, dtype=np.uint8)
    else:
        k = max(3, gap | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        bar_closed = barrier.copy()
        for _ in range(max(1, iters)):
            bar_closed = cv2.morphologyEx(bar_closed, cv2.MORPH_CLOSE, kernel)
        new_barrier = (bar_closed > 0) & (barrier == 0)
        sealed = sm.copy()
        sealed[new_barrier] = 1
        seal_mask = new_barrier.astype(np.uint8)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "structural_mask_sealed.npy", sealed)

    colors = {
        0: (255, 255, 255),
        1: (40, 40, 40),
        2: (0, 180, 255),
        3: (0, 100, 0),
    }
    save_matrix_png(sealed, out_dir / "structural_mask_sealed.png", colors)

    diff_rgb = np.full((*sm.shape, 3), 255, dtype=np.uint8)
    diff_rgb[seal_mask > 0] = (0, 0, 255)
    cv2.imwrite(str(out_dir / "barrier_seal_diff.png"), diff_rgb)

    floor = PROJECT_ROOT / "Floorplan2.png"
    if floor.is_file():
        base = cv2.imread(str(floor), cv2.IMREAD_COLOR)
        if base.shape[:2] == sealed.shape:
            cm = np.zeros_like(base)
            cm[sealed == 1] = (40, 40, 40)
            cm[sealed == 2] = (255, 180, 0)
            cm[sealed == 3] = (0, 100, 0)
            cm[seal_mask > 0] = (0, 0, 255)
            over = cv2.addWeighted(base, 0.62, cm, 0.38, 0)
            cv2.imwrite(str(out_dir / "structural_overlay_sealed.png"), over)
        else:
            import shutil

            shutil.copy(out_dir / "structural_mask_sealed.png", out_dir / "structural_overlay_sealed.png")
    else:
        import shutil

        shutil.copy(out_dir / "structural_mask_sealed.png", out_dir / "structural_overlay_sealed.png")

    added = int(seal_mask.sum())
    report = [
        f"input: {struct_npy}",
        f"close_gap_px: {gap} (kernel ~{max(3, gap | 1)})",
        f"close_iterations: {iters}",
        f"barrier_pixels_before: {int(barrier.sum())}",
        f"barrier_pixels_after: {int(((sealed >= 1) & (sealed <= 3)).sum())}",
        f"seal_pixels_added_as_wall: {added}",
    ]
    (out_dir / "barrier_seal_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Step04b OK -> {out_dir} (+{added} px sellados)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in",
        dest="inp",
        type=Path,
        default=PROJECT_ROOT / "output" / "step04" / "structural_mask.npy",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step04b")
    args = ap.parse_args()
    run(args.inp, args.config, args.out)


if __name__ == "__main__":
    main()
