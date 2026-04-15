"""Streamlit component: paint many grid cells in one mouse drag (mouseup sends batch)."""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import streamlit.components.v1 as components
from PIL import Image

_frontend = Path(__file__).resolve().parent / "frontend"
_grid_paint = components.declare_component("grid_paint", path=str(_frontend))


def grid_paint_image(
    source: str | Path | np.ndarray | object,
    *,
    grid_w: int,
    grid_h: int,
    width: int | None = None,
    height: int | None = None,
    key: str | None = None,
    cursor: str = "crosshair",
    enable_paint: bool = True,
    pick_on_click: bool = False,
    image_format: str = "PNG",
    png_compression_level: int = 3,
) -> dict | None:
    """
    Returns ``None`` until the user finishes a drag (or click) on the image.
    Then ``{"kind": "stroke", "stroke_id": int, "cells": [[cx, cy], ...], "width": int, "height": int}``.
    """
    if isinstance(source, (Path, str)) and not str(source).startswith("http"):
        content = Path(source).read_bytes()
        src = "data:image/png;base64," + base64.b64encode(content).decode("utf-8")
    elif isinstance(source, str):
        src = source
    elif hasattr(source, "save"):
        buffered = BytesIO()
        source.save(buffered, format="PNG", compress_level=png_compression_level)  # type: ignore[union-attr]
        src = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")
    elif isinstance(source, np.ndarray):
        image = Image.fromarray(source)
        buffered = BytesIO()
        image.save(buffered, format="PNG", compress_level=png_compression_level)
        src = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")
    else:
        raise ValueError("source must be path, url str, ndarray, or PIL Image")

    return _grid_paint(
        src=src,
        grid_w=int(grid_w),
        grid_h=int(grid_h),
        width=width,
        height=height,
        key=key,
        cursor=cursor,
        enable_paint=bool(enable_paint),
        pick_on_click=bool(pick_on_click),
    )
