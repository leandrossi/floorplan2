#!/usr/bin/env python3
"""Step 04: repaired walls + openings with wall-support validation."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT, load_config, save_matrix_png


def filter_opening_components(
    opening_binary: np.ndarray,
    wall_support: np.ndarray,
    label: str,
) -> tuple[np.ndarray, list[str]]:
    ob = (opening_binary > 0).astype(np.uint8)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(ob, connectivity=8)
    accepted = np.zeros_like(ob, dtype=np.uint8)
    bad: list[str] = []
    sup = wall_support > 0
    for i in range(1, num):
        comp = labels == i
        if (comp & sup).any():
            accepted[comp] = 1
        else:
            a = int(stats[i, cv2.CC_STAT_AREA])
            x, y = int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP])
            bad.append(f"{label} cc={i} area={a} bbox_origin=({x},{y}) no_wall_support")
    return accepted, bad


def run(raw_npy: Path, repaired_npy: Path, config_path: Path, out_dir: Path) -> None:
    cfg = load_config(config_path)
    dil = int(cfg.get("openings", {}).get("wall_support_dilate_px", 2))
    kr = max(3, 2 * dil + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kr, kr))

    raw = np.load(raw_npy)
    repaired = np.load(repaired_npy)
    if repaired.ndim > 2:
        repaired = repaired.squeeze()
    repaired_bin = (repaired > 0).astype(np.uint8)
    wall_support = cv2.dilate(repaired_bin, kernel, iterations=1)

    door_src = (raw == 3).astype(np.uint8)
    win_src = (raw == 2).astype(np.uint8)

    door_acc, bad_d = filter_opening_components(door_src, wall_support, "door")
    win_acc, bad_w = filter_opening_components(win_src, wall_support, "window")

    final = np.zeros_like(raw, dtype=np.uint8)
    final[repaired_bin > 0] = 1
    final[win_acc > 0] = 2
    final[door_acc > 0] = 3

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "structural_mask.npy", final)

    colors = {
        0: (255, 255, 255),
        1: (40, 40, 40),
        2: (0, 180, 255),
        3: (0, 100, 0),
    }
    save_matrix_png(final, out_dir / "structural_mask.png", colors)

    floor = PROJECT_ROOT / "Floorplan2.png"
    if floor.is_file():
        base = cv2.imread(str(floor), cv2.IMREAD_COLOR)
        h, w = final.shape[:2]
        if base.shape[0] == h and base.shape[1] == w:
            cm = np.zeros_like(base)
            cm[final == 1] = (40, 40, 40)
            cm[final == 2] = (255, 180, 0)
            cm[final == 3] = (0, 100, 0)
            over = cv2.addWeighted(base, 0.65, cm, 0.35, 0)
            cv2.imwrite(str(out_dir / "structural_overlay.png"), over)
        else:
            import shutil

            shutil.copy(out_dir / "structural_mask.png", out_dir / "structural_overlay.png")
    else:
        import shutil

        shutil.copy(out_dir / "structural_mask.png", out_dir / "structural_overlay.png")

    lines = [
        f"wall_support_dilate_px={dil} kernel={kr}",
        "",
        "rejected_openings:",
        *[f"  {x}" for x in bad_w],
        *[f"  {x}" for x in bad_d],
    ]
    (out_dir / "structural_conflicts_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Step04 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=PROJECT_ROOT / "output" / "step02" / "raw_structure_mask.npy")
    ap.add_argument(
        "--repaired",
        type=Path,
        default=PROJECT_ROOT / "output" / "step03" / "repaired_wall_mask.npy",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step04")
    args = ap.parse_args()
    run(args.raw, args.repaired, args.config, args.out)


if __name__ == "__main__":
    main()
