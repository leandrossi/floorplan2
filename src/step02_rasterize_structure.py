#!/usr/bin/env python3
"""Step 02: rasterize structural detections (passing threshold only)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import (
    DEFAULT_CONFIG,
    PROJECT_ROOT,
    load_config,
    load_json,
    rasterize_polygons,
    save_matrix_png,
)


def run(
    in_json: Path,
    config_path: Path,
    out_dir: Path,
    *,
    ignore_threshold: bool = False,
) -> None:
    cfg = load_config(config_path)
    doc = load_json(in_json)
    meta = doc["meta"]
    h, w = int(meta["image_height"]), int(meta["image_width"])
    dets = doc["detections"]

    items: list[tuple[list[list[int]], int]] = []
    order = [("wall", 1), ("window", 2), ("door", 3)]
    skipped_threshold = 0
    skipped_short_poly = 0
    for class_norm, val in order:
        for d in dets:
            if d.get("exclude_reason"):
                continue
            if not ignore_threshold and not d.get("passes_threshold"):
                if d["class_norm"] == class_norm:
                    skipped_threshold += 1
                continue
            if ignore_threshold and not d.get("passes_threshold"):
                if d.get("class_norm") not in ("wall", "window", "door"):
                    continue
            if d["class_norm"] != class_norm:
                continue
            pts = d.get("points") or []
            if len(pts) < 3:
                skipped_short_poly += 1
                continue
            pi = [[int(p[0]), int(p[1])] for p in pts]
            items.append((pi, val))

    print(
        f"step02: polígonos rasterizados={len(items)} "
        f"(omitidos por umbral confidence={skipped_threshold}, por <3 puntos={skipped_short_poly}"
        f"{'; UMBRAL IGNORADO' if ignore_threshold else ''})",
        file=sys.stderr,
    )

    mask = rasterize_polygons(h, w, items)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "raw_structure_mask.npy", mask)

    colors = {
        0: (255, 255, 255),
        1: (40, 40, 40),
        2: (0, 180, 255),
        3: (0, 100, 0),
    }
    save_matrix_png(mask, out_dir / "raw_structure_mask.png", colors)

    floor = PROJECT_ROOT / "Floorplan2.png"
    if floor.is_file():
        base = cv2.imread(str(floor), cv2.IMREAD_COLOR)
        if base.shape[0] == h and base.shape[1] == w:
            over = base.copy()
            cm = np.zeros_like(base)
            cm[mask == 1] = (40, 40, 40)
            cm[mask == 2] = (255, 180, 0)
            cm[mask == 3] = (0, 100, 0)
            over = cv2.addWeighted(over, 0.65, cm, 0.35, 0)
            cv2.imwrite(str(out_dir / "raw_structure_overlay.png"), over)
        else:
            cv2.imwrite(str(out_dir / "raw_structure_overlay.png"), cv2.imread(str(out_dir / "raw_structure_mask.png")))
    else:
        import shutil

        shutil.copy(out_dir / "raw_structure_mask.png", out_dir / "raw_structure_overlay.png")

    print(f"Step02 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in-json",
        type=Path,
        default=PROJECT_ROOT / "output" / "step01" / "normalized_structure.json",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step02")
    ap.add_argument(
        "--ignore-threshold",
        action="store_true",
        help="Rasteriza wall/window/door aunque no cumplan passes_threshold",
    )
    ap.add_argument(
        "--debug-include-rejected",
        action="store_true",
        help="(alias) igual que --ignore-threshold",
    )
    args = ap.parse_args()
    run(
        args.in_json,
        args.config,
        args.out,
        ignore_threshold=bool(args.ignore_threshold or args.debug_include_rejected),
    )


if __name__ == "__main__":
    main()
