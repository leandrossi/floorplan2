"""
Shared helpers for the final floorplan pipeline (final_step* + wizard).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "pipeline_config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_CONFIG
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def save_matrix_png(mask: np.ndarray, path: Path, color_map: dict[int, tuple[int, int, int]]) -> None:
    import cv2

    h, w = mask.shape[:2]
    bgr = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in color_map.items():
        bgr[mask == k] = col[::-1]  # RGB to BGR for cv2
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), bgr)
