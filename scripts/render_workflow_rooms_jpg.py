#!/usr/bin/env python3
"""Dibuja predicciones room del workflow 2 sobre fondo blanco → JPG (sin plano base)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def iter_room_predictions(doc: dict):
    for run in doc.get("runs") or []:
        if not isinstance(run, dict):
            continue
        for block in run.get("workflow_output") or []:
            if not isinstance(block, dict):
                continue
            preds = block.get("predictions")
            if not isinstance(preds, dict):
                continue
            img = preds.get("image") or {}
            w, h = int(img["width"]), int(img["height"])
            for p in preds.get("predictions") or []:
                if not isinstance(p, dict):
                    continue
                yield w, h, p


def points_to_int_array(p: dict) -> np.ndarray | None:
    pts = p.get("points")
    if not isinstance(pts, list) or len(pts) < 3:
        return None
    arr = []
    for q in pts:
        if isinstance(q, dict) and "x" in q and "y" in q:
            arr.append([float(q["x"]), float(q["y"])])
        elif isinstance(q, (list, tuple)) and len(q) >= 2:
            arr.append([float(q[0]), float(q[1])])
    if len(arr) < 3:
        return None
    return np.array(arr, dtype=np.int32).reshape((-1, 1, 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent.parent
    ap.add_argument(
        "--in",
        dest="inp",
        type=Path,
        default=root / "output" / "result_workflow2.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=root / "output" / "visualizations" / "Floorplan2_workflow2_rooms_only.jpg",
    )
    args = ap.parse_args()

    doc = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    canvas = None
    w0 = h0 = None
    rng = np.random.default_rng(42)
    colors = rng.integers(40, 220, size=(128, 3), dtype=np.uint8)

    for i, (w, h, p) in enumerate(iter_room_predictions(doc)):
        if canvas is None:
            w0, h0 = w, h
            canvas = np.full((h0, w0, 3), 255, dtype=np.uint8)
        if (w, h) != (w0, h0):
            raise ValueError(f"Tamaños inconsistentes {(w,h)} vs {(w0,h0)}")

        arr = points_to_int_array(p)
        if arr is None:
            continue
        col = tuple(int(x) for x in colors[i % len(colors)])
        cv2.fillPoly(canvas, [arr], col)
        cv2.polylines(canvas, [arr], isClosed=True, color=(20, 20, 20), thickness=2)

    if canvas is None:
        raise ValueError("No hay predicciones para dibujar.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out), canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"Escrito: {args.out}", flush=True)


if __name__ == "__main__":
    main()
