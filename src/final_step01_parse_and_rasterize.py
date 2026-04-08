#!/usr/bin/env python3
"""
Final Step 01 — Parse unified JSON + rasterize.

Reads result_workflow_final.json (single workflow with structural_predictions
and room_predictions).

Outputs:
  structural_mask.npy   — 0=free, 1=wall, 2=window, 3=door  (bbox rects)
  room_polygons.npy     — 0=no room, 1..K=room_id             (filled polygons)
  structural_mask.png   — color preview
  room_polygons.png     — color preview
  parse_report.txt      — summary
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, load_json, save_json, save_matrix_png

DEFAULT_FINAL_JSON = PROJECT_ROOT / "output" / "result_workflow_final.json"
OUT_DIR = PROJECT_ROOT / "output" / "final" / "step01"

CLASS_VAL = {"wall": 1, "window": 2, "door": 3}


def _extract_block(doc: dict) -> dict:
    runs = doc.get("runs") or []
    if not runs:
        raise ValueError("JSON sin 'runs'")
    wo = runs[0].get("workflow_output") or []
    if not wo:
        raise ValueError("workflow_output vacío")
    return wo[0]


def _image_size(block: dict) -> tuple[int, int]:
    for key in ("structural_predictions", "room_predictions"):
        sub = block.get(key)
        if isinstance(sub, dict):
            img = sub.get("image") or {}
            w = img.get("width")
            h = img.get("height")
            if w and h:
                return int(h), int(w)
    raise ValueError("No image size found in JSON block")


def _rasterize_structural(preds: list[dict], H: int, W: int) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    # Walls first, then openings on top so windows/doors always win overlaps.
    for val_pass in (1, 2, 3):
        for p in preds:
            cls = str(p.get("class", "")).strip().lower()
            val = CLASS_VAL.get(cls, 0)
            if val != val_pass:
                continue
            x, y, w, h = float(p["x"]), float(p["y"]), float(p["width"]), float(p["height"])
            x0 = max(0, int(round(x - w / 2)))
            y0 = max(0, int(round(y - h / 2)))
            x1 = min(W, int(round(x + w / 2)))
            y1 = min(H, int(round(y + h / 2)))
            mask[y0:y1, x0:x1] = val
    return mask


def _rasterize_rooms(preds: list[dict], H: int, W: int) -> np.ndarray:
    order = sorted(
        range(len(preds)),
        key=lambda i: (-float(preds[i].get("confidence", 0)), i),
    )
    mask = np.zeros((H, W), dtype=np.int32)
    for idx in order:
        p = preds[idx]
        rid = idx + 1
        pts_raw = p.get("points") or []
        if len(pts_raw) < 3:
            continue
        poly = np.array(
            [[int(pt["x"]), int(pt["y"])] for pt in pts_raw],
            dtype=np.int32,
        )
        tmp = np.zeros((H, W), dtype=np.uint8)
        cv2.fillPoly(tmp, [poly], 1)
        mask[(tmp > 0) & (mask == 0)] = rid
    return mask


def run(json_path: Path, out_dir: Path) -> None:
    doc = load_json(json_path)
    block = _extract_block(doc)
    H, W = _image_size(block)

    sp = block.get("structural_predictions") or {}
    rp = block.get("room_predictions") or {}
    struct_preds = sp.get("predictions") or []
    room_preds = rp.get("predictions") or []

    struct_mask = _rasterize_structural(struct_preds, H, W)
    room_mask = _rasterize_rooms(room_preds, H, W)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "structural_mask.npy", struct_mask)
    np.save(out_dir / "room_polygons.npy", room_mask)

    struct_colors = {0: (255, 255, 255), 1: (40, 40, 40), 2: (0, 180, 255), 3: (0, 100, 0)}
    save_matrix_png(struct_mask, out_dir / "structural_mask.png", struct_colors)

    rng = np.random.default_rng(42)
    room_colors = {0: (240, 240, 240)}
    for rid in range(1, int(room_mask.max()) + 1):
        room_colors[rid] = tuple(int(v) for v in rng.integers(60, 230, size=3))
    save_matrix_png(room_mask.astype(np.uint8), out_dir / "room_polygons.png", room_colors)

    from collections import Counter
    cls_count = Counter(str(p.get("class", "")).lower() for p in struct_preds)
    report = [
        f"json: {json_path}",
        f"image: {W}x{H}",
        f"structural_predictions: {len(struct_preds)}",
        *(f"  {c}: {n}" for c, n in cls_count.most_common()),
        f"room_predictions: {len(room_preds)}",
        f"room_polygon_pixels: {int((room_mask > 0).sum())}",
        f"structural_barrier_pixels: {int((struct_mask > 0).sum())}",
    ]
    (out_dir / "parse_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    meta = {
        "image_width": W,
        "image_height": H,
        "structural_count": len(struct_preds),
        "room_count": len(room_preds),
        "room_ids": list(range(1, len(room_preds) + 1)),
        "room_confs": [round(float(p.get("confidence", 0)), 4) for p in room_preds],
    }
    save_json(out_dir / "parse_meta.json", meta)
    print(f"FinalStep01 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=DEFAULT_FINAL_JSON)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    run(args.json, args.out)


if __name__ == "__main__":
    main()
