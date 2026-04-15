"""
review_bundle.json + review_approved.json I/O for matrix review MVP.

struct encoding (same as final_step04 final_structure_matrix):
  0 exterior, 1 wall, 2 window, 3 door, 4 interior
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from pipeline_common import PROJECT_ROOT, load_config, save_json

DEFAULT_STEP04 = PROJECT_ROOT / "output" / "final" / "step04"

STRUCT_ENCODING: dict[int, str] = {
    0: "exterior",
    1: "wall",
    2: "window",
    3: "door",
    4: "interior",
}


def build_review_bundle(
    out_dir: Path,
    cell_size_m: float,
    *,
    security_level: str = "optimal",
) -> dict[str, Any]:
    """Load npy from out_dir and return a JSON-serialisable bundle dict."""
    struct_path = out_dir / "final_structure_matrix.npy"
    if not struct_path.is_file():
        raise FileNotFoundError(f"Missing {struct_path}")

    struct = np.load(struct_path).astype(np.uint8)
    room_path = out_dir / "final_rooms_matrix.npy"
    inferred_path = out_dir / "final_rooms_inferred_mask.npy"
    room = (
        np.load(room_path).astype(np.int32)
        if room_path.is_file()
        else np.zeros_like(struct, dtype=np.int32)
    )
    inferred = (
        np.load(inferred_path).astype(np.int32)
        if inferred_path.is_file()
        else np.zeros_like(struct, dtype=np.int32)
    )

    preview = out_dir / "floor_like_preview.png"
    meta_path = out_dir / "final_metadata.json"
    meta: dict[str, Any] = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    bundle: dict[str, Any] = {
        "version": 1,
        "step04_dir": str(out_dir.resolve()),
        "grid_shape": [int(struct.shape[0]), int(struct.shape[1])],
        "cell_size_m": float(cell_size_m),
        "security_level": security_level,
        "struct_encoding": STRUCT_ENCODING,
        "struct": struct.astype(int).tolist(),
        "rooms": room.astype(int).tolist(),
        "rooms_inferred": inferred.astype(int).tolist(),
        "preview_image": str(preview.name if preview.is_file() else ""),
        "final_metadata": meta,
    }
    return bundle


def write_review_bundle(
    out_dir: Path,
    config_path: Path | None = None,
    *,
    security_level: str = "optimal",
) -> Path:
    """Write review_bundle.json next to step04 artifacts."""
    cfg = load_config(config_path)
    mx = cfg.get("matrix") or {}
    cell_cm = float(mx.get("cell_size_cm", 5))
    cell_size_m = cell_cm / 100.0

    bundle = build_review_bundle(out_dir, cell_size_m, security_level=security_level)
    path = out_dir / "review_bundle.json"
    save_json(path, bundle)
    return path


def apply_struct_patches(
    struct: np.ndarray, patches: list[dict[str, int]]
) -> np.ndarray:
    """Return a copy of struct with sparse patches applied. Each patch: r, c, v."""
    out = struct.copy()
    h, w = out.shape
    for p in patches:
        r, c, v = int(p["r"]), int(p["c"]), int(p["v"])
        if 0 <= r < h and 0 <= c < w and 0 <= v <= 4:
            out[r, c] = v
    return out


def validate_approved(
    approved: dict[str, Any],
    struct: np.ndarray,
    *,
    require_markers: bool = True,
) -> tuple[list[str], list[str]]:
    """
    Returns (errors, warnings). errors block save in UI; warnings are informational.
    """
    errors: list[str] = []
    warnings: list[str] = []
    h, w = struct.shape

    me = approved.get("main_entry")
    eb = approved.get("electric_board")
    if require_markers:
        if me is None:
            errors.append("main_entry is required (pick a door cell)")
        if eb is None:
            errors.append("electric_board is required (pick an interior cell)")
        if errors:
            return errors, warnings

    if me is not None:
        if not isinstance(me, (list, tuple)) or len(me) != 2:
            errors.append("main_entry must be [row, col] or null")
        else:
            r, c = int(me[0]), int(me[1])
            if not (0 <= r < h and 0 <= c < w):
                errors.append(f"main_entry ({r},{c}) out of bounds")
            elif int(struct[r, c]) != 3:
                errors.append(f"main_entry must be on a door cell (struct=3), got {int(struct[r, c])}")

    if eb is not None:
        if not isinstance(eb, (list, tuple)) or len(eb) != 2:
            errors.append("electric_board must be [row, col] or null")
        else:
            r, c = int(eb[0]), int(eb[1])
            if not (0 <= r < h and 0 <= c < w):
                errors.append(f"electric_board ({r},{c}) out of bounds")
            elif int(struct[r, c]) != 4:
                errors.append(
                    f"electric_board must be on interior (struct=4), got {int(struct[r, c])}"
                )

    for i, p in enumerate(approved.get("struct_patch") or []):
        if not all(k in p for k in ("r", "c", "v")):
            errors.append(f"struct_patch[{i}] needs r, c, v")
            continue
        r, c, v = int(p["r"]), int(p["c"]), int(p["v"])
        if not (0 <= r < h and 0 <= c < w):
            errors.append(f"struct_patch[{i}] out of bounds")
        elif v not in range(5):
            errors.append(f"struct_patch[{i}] v must be 0..4")

    return errors, warnings


def load_approved(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_final_floorplan_grid_dict(
    *,
    struct_m: np.ndarray,
    room_m: np.ndarray,
    inferred_m: np.ndarray,
    cell_size_m: float,
    approved: dict[str, Any] | None,
    approved_path: Path | None,
    security_level: str = "optimal",
) -> dict[str, Any]:
    """
    Single JSON snapshot of the reviewed grid (struct after patches, rooms, markers).
    Written by final_step05 after planning; same encoding as review_bundle struct.
    """
    return {
        "version": 1,
        "kind": "final_floorplan_grid",
        "cell_size_m": float(cell_size_m),
        "security_level": security_level,
        "grid_shape": [int(struct_m.shape[0]), int(struct_m.shape[1])],
        "struct_encoding": STRUCT_ENCODING,
        "struct": struct_m.astype(int).tolist(),
        "rooms": room_m.astype(int).tolist(),
        "rooms_inferred": inferred_m.astype(int).tolist(),
        "main_entry": approved.get("main_entry") if approved else None,
        "electric_board": approved.get("electric_board") if approved else None,
        "struct_patch": approved.get("struct_patch") if approved else [],
        "review_approved_path": str(approved_path.resolve()) if approved_path and approved_path.is_file() else None,
    }


def main_cli() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Write review_bundle.json from step04 npy outputs.")
    ap.add_argument("--step04", type=Path, default=DEFAULT_STEP04)
    ap.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "pipeline_config.json")
    ap.add_argument("--security-level", default="optimal")
    args = ap.parse_args()
    p = write_review_bundle(args.step04, args.config, security_level=args.security_level)
    print(f"Wrote {p}", flush=True)


if __name__ == "__main__":
    main_cli()
