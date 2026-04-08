"""
Shared helpers for floorplan matrix pipeline.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "pipeline_config.json"
DEFAULT_STRUCTURE_JSON = PROJECT_ROOT / "output" / "result.json"
DEFAULT_ROOMS_JSON = PROJECT_ROOT / "output" / "result_workflow2.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_CONFIG
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def alias_class_name(raw_name: str) -> str:
    """Case-insensitive, trimmed; returns normalized class key."""
    s = raw_name.strip().lower()
    s = re.sub(r"\s+", "-", s)
    aliases = {
        "wall": "wall",
        "diagonal": "wall",
        "window": "window",
        "door": "door",
        "sliding-door": "door",
        "garage-door": "door",
        "sliding_door": "door",
        "garage_door": "door",
        "room": "room",
    }
    return aliases.get(s, "unknown")


def threshold_for_class(class_norm: str, cfg: dict[str, Any]) -> float | None:
    th = cfg.get("confidence_thresholds") or {}
    if class_norm == "unknown":
        return float(th.get("unknown", 1.0))
    return float(th[class_norm]) if class_norm in th else None


def bbox_from_prediction(p: dict[str, Any]) -> dict[str, float] | None:
    needed = ("x", "y", "width", "height")
    if not all(k in p for k in needed):
        return None
    return {
        "x": float(p["x"]),
        "y": float(p["y"]),
        "width": float(p["width"]),
        "height": float(p["height"]),
    }


def points_from_prediction(p: dict[str, Any]) -> list[list[float]] | None:
    pts = p.get("points")
    if not isinstance(pts, list) or len(pts) == 0:
        return None
    out: list[list[float]] = []
    for q in pts:
        if isinstance(q, dict) and "x" in q and "y" in q:
            out.append([float(q["x"]), float(q["y"])])
        elif isinstance(q, (list, tuple)) and len(q) >= 2:
            out.append([float(q[0]), float(q[1])])
    return out if len(out) >= 3 else (out if len(out) >= 1 else None)


def polygon_from_prediction(p: dict[str, Any]) -> tuple[list[list[float]], str]:
    pts = points_from_prediction(p)
    if pts and len(pts) >= 3:
        return pts, "points"
    bb = bbox_from_prediction(p)
    if bb:
        x, y, w, h = bb["x"], bb["y"], bb["width"], bb["height"]
        hw, hh = w / 2.0, h / 2.0
        poly = [
            [x - hw, y - hh],
            [x + hw, y - hh],
            [x + hw, y + hh],
            [x - hw, y + hh],
        ]
        return poly, "bbox_fallback"
    return [], "invalid"


def iter_schema_a(data: dict[str, Any]) -> Iterator[tuple[int | None, int | None, dict[str, Any]]]:
    """Workflow style: runs[].workflow_output[].predictions."""
    runs = data.get("runs")
    if not isinstance(runs, list):
        return
    for run in runs:
        wo = run.get("workflow_output") or []
        if not isinstance(wo, list):
            continue
        for block in wo:
            if not isinstance(block, dict):
                continue
            preds = block.get("predictions")
            if not isinstance(preds, dict):
                continue
            img = preds.get("image") or {}
            w = int(img["width"]) if img.get("width") is not None else None
            h = int(img["height"]) if img.get("height") is not None else None
            for pr in preds.get("predictions") or []:
                if isinstance(pr, dict):
                    yield w, h, pr


def iter_schema_b(data: dict[str, Any]) -> Iterator[tuple[int | None, int | None, dict[str, Any]]]:
    """Flat: root.predictions[]. Optional root image size."""
    w0 = h0 = None
    img = data.get("image")
    if isinstance(img, dict):
        if img.get("width") is not None:
            w0 = int(img["width"])
        if img.get("height") is not None:
            h0 = int(img["height"])
    preds = data.get("predictions")
    if not isinstance(preds, list):
        return
    for pr in preds:
        if isinstance(pr, dict):
            yield w0, h0, pr


def detect_schema(data: dict[str, Any]) -> str:
    if isinstance(data.get("runs"), list) and len(data["runs"]) > 0:
        return "A"
    if isinstance(data.get("predictions"), list):
        return "B"
    raise ValueError("JSON no coincide con schema A (runs) ni B (predictions[]).")


def collect_image_size_from_structure(data: dict[str, Any], schema: str) -> tuple[int, int]:
    wn = hn = None
    if schema == "A":
        gen = iter_schema_a(data)
    else:
        gen = iter_schema_b(data)
    for w, h, _ in gen:
        if w is not None:
            wn = w
        if h is not None:
            hn = h
        if wn and hn:
            return wn, hn
    raise ValueError("No se pudo resolver image width/height desde JSON de estructura.")


def normalize_detection(
    p: dict[str, Any],
    *,
    source_type: str,
    image_w: int,
    image_h: int,
    cfg: dict[str, Any],
) -> dict[str, Any] | None:
    c_raw = str(p.get("class", ""))
    class_norm = alias_class_name(c_raw)
    conf = float(p.get("confidence", 0.0))
    det_id = p.get("detection_id")
    poly, geom_src = polygon_from_prediction(p)
    th = threshold_for_class(class_norm, cfg)
    passes = th is not None and conf >= th

    bb = bbox_from_prediction(p)
    if geom_src == "invalid":
        return {
            "source_type": source_type,
            "image_width": image_w,
            "image_height": image_h,
            "class_raw": c_raw,
            "class_norm": class_norm,
            "confidence": conf,
            "points": [],
            "bbox": bb,
            "geometry_source": "invalid",
            "detection_id": det_id,
            "threshold_used": th,
            "passes_threshold": False,
            "exclude_reason": "missing_geometry",
        }

    return {
        "source_type": source_type,
        "image_width": image_w,
        "image_height": image_h,
        "class_raw": c_raw,
        "class_norm": class_norm,
        "confidence": conf,
        "points": [[int(round(x)), int(round(y))] for x, y in poly],
        "bbox": bb,
        "geometry_source": geom_src,
        "detection_id": det_id,
        "threshold_used": th,
        "passes_threshold": passes,
    }


def rasterize_polygons(
    height: int,
    width: int,
    items: list[tuple[list[list[int]], int]],
) -> np.ndarray:
    """items: list of (points int xy, class value 1..3). Later items paint over earlier."""
    import cv2

    mask = np.zeros((height, width), dtype=np.uint8)
    for pts, val in items:
        if len(pts) < 3:
            continue
        arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [arr], int(val))
    return mask


def save_matrix_png(mask: np.ndarray, path: Path, color_map: dict[int, tuple[int, int, int]]) -> None:
    import cv2

    h, w = mask.shape[:2]
    bgr = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in color_map.items():
        bgr[mask == k] = col[::-1]  # RGB to BGR for cv2
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), bgr)
