#!/usr/bin/env python3
"""
Varias fusiones estructura (space_classified) + habitaciones (room_id_matrix) para comparar.

Salida típica: output/step08/v01_*.jpg … + fusion_variants.json con descripción.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, save_json

# BGR (OpenCV)
STRUCT_BGR = {
    0: (220, 220, 255),
    1: (40, 40, 40),
    2: (0, 180, 255),
    3: (0, 100, 0),
    4: (200, 220, 255),
}


def structure_layer_bgr(space: np.ndarray) -> np.ndarray:
    h, w = space.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for k, col in STRUCT_BGR.items():
        out[space == k] = col
    return out


def room_colors_bgr(room: np.ndarray, *, seed: int = 42) -> np.ndarray:
    h, w = room.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    rng = np.random.default_rng(seed)
    mx = int(room.max())
    for rid in range(1, mx + 1):
        bgr = tuple(int(x) for x in rng.integers(50, 230, size=3))
        out[room == rid] = bgr
    return out


def v01_barriers_on_top(space: np.ndarray, room: np.ndarray) -> np.ndarray:
    """Habitaciones a color; muro/ventana/puerta pintados encima."""
    rgb_rooms = room_colors_bgr(room)
    out = rgb_rooms.copy()
    for lab, col in [(1, STRUCT_BGR[1]), (2, STRUCT_BGR[2]), (3, STRUCT_BGR[3])]:
        out[space == lab] = col
    return out


def v02_classified_then_rooms(space: np.ndarray, room: np.ndarray) -> np.ndarray:
    """Base = clasificación espacio completa; donde room>0, sustituye por color habitación."""
    out = structure_layer_bgr(space)
    rc = room_colors_bgr(room)
    m = room > 0
    out[m] = rc[m]
    return out


def v03_rooms_only_where_interior(space: np.ndarray, room: np.ndarray) -> np.ndarray:
    """Solo muestra id de habitación donde el modelo estructural dice interior (4)."""
    out = structure_layer_bgr(space)
    rc = room_colors_bgr(room)
    m = (space == 4) & (room > 0)
    out[m] = rc[m]
    return out


def v04_soft_blend_floorplan(
    floor_bgr: np.ndarray,
    space: np.ndarray,
    room: np.ndarray,
    alpha_room: float,
    alpha_struct: float,
) -> np.ndarray:
    """Plano base + transparencias habitación y capa estructura (barras)."""
    base = floor_bgr.astype(np.float32) / 255.0
    h, w = space.shape
    lay = np.zeros_like(base)
    # habitaciones
    rc = room_colors_bgr(room).astype(np.float32) / 255.0
    rm = (room > 0)[..., np.newaxis]
    lay = np.where(rm, rc, lay)
    x = base * (1 - alpha_room * rm) + lay * (alpha_room * rm)
    # barreras encima
    barrier = np.isin(space, [1, 2, 3])
    sb = structure_layer_bgr(space).astype(np.float32) / 255.0
    b = barrier[..., np.newaxis]
    x = np.where(b, x * (1 - alpha_struct) + sb * alpha_struct, x)
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def v05_room_with_wall_outline(space: np.ndarray, room: np.ndarray, thickness: int) -> np.ndarray:
    """Habitaciones rellenas; contorno de muros (1) dilatado dibujado en oscuro."""
    out = room_colors_bgr(room)
    wall = (space == 1).astype(np.uint8) * 255
    if thickness > 1:
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (thickness, thickness))
        wall = cv2.dilate(wall, k)
    edge = cv2.Canny(wall, 50, 150)
    out[edge > 0] = (0, 0, 0)
    for lab, col in [(2, STRUCT_BGR[2]), (3, STRUCT_BGR[3])]:
        out[space == lab] = col
    return out


def v06_montage(space: np.ndarray, room: np.ndarray, floor_bgr: np.ndarray | None) -> np.ndarray:
    """Tira horizontal: estructura | habitaciones | v01."""
    a = structure_layer_bgr(space)
    b = room_colors_bgr(room)
    c = v01_barriers_on_top(space, room)
    if floor_bgr is not None and floor_bgr.shape[:2] == space.shape:
        row = [
            a,
            b,
            c,
            cv2.addWeighted(floor_bgr, 0.55, v02_classified_then_rooms(space, room), 0.45, 0),
        ]
    else:
        row = [a, b, c]
    return cv2.hconcat(row)


def run(
    space_npy: Path,
    room_npy: Path,
    out_dir: Path,
    floor_png: Path | None,
) -> None:
    space = np.load(space_npy).astype(np.uint8)
    room = np.load(room_npy).astype(np.int32)
    if space.shape != room.shape:
        raise ValueError(f"shape mismatch {space.shape} vs {room.shape}")

    floor = None
    if floor_png and floor_png.is_file():
        floor = cv2.imread(str(floor_png), cv2.IMREAD_COLOR)
        if floor.shape[:2] != space.shape:
            floor = None

    out_dir.mkdir(parents=True, exist_ok=True)
    jpeg = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    variants: list[tuple[str, str, np.ndarray]] = [
        (
            "v01_barriers_on_top",
            "Rooms rellenas; pared/ventana/puerta pisan el color habitación.",
            v01_barriers_on_top(space, room),
        ),
        (
            "v02_replace_by_room_id",
            "Toda la clasificación espacial; cualquier píxel con room>0 pasa a color de habitación.",
            v02_classified_then_rooms(space, room),
        ),
        (
            "v03_rooms_on_interior4_only",
            "Color habitación solo donde space==4 (interior estructural); resto clasificado.",
            v03_rooms_only_where_interior(space, room),
        ),
    ]

    if floor is not None:
        variants.append(
            (
                "v04_soft_blend_floorplan",
                "Plano + alpha habitación 0.45 + alpha barrera 0.5 sobre barreras.",
                v04_soft_blend_floorplan(floor, space, room, 0.45, 0.5),
            )
        )

    variants.append(
        (
            "v05_rooms_wall_outline",
            "Rooms + bordes dilatados de muro + ventana/puerta sólidas.",
            v05_room_with_wall_outline(space, room, thickness=3),
        )
    )

    mont = v06_montage(space, room, floor)
    cv2.imwrite(str(out_dir / "v06_montage.jpg"), mont, jpeg)

    meta = {
        "inputs": {"space_classified": str(space_npy), "room_id_matrix": str(room_npy)},
        "variants": [],
    }
    for vid, desc, img in variants:
        path = out_dir / f"{vid}.jpg"
        cv2.imwrite(str(path), img, jpeg)
        meta["variants"].append({"file": path.name, "id": vid, "description": desc})

    meta["variants"].append(
        {
            "file": "v06_montage.jpg",
            "id": "v06_montage",
            "description": "Concat horizontal: estructura | rooms | v01 | (floor+clasificación si hay plano).",
        }
    )

    save_json(out_dir / "fusion_variants.json", meta)
    print(f"Step08 OK -> {out_dir} ({len(meta['variants'])} artefactos)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", type=Path, default=PROJECT_ROOT / "output" / "step05" / "space_classified.npy")
    ap.add_argument("--rooms", type=Path, default=PROJECT_ROOT / "output" / "step06" / "room_id_matrix.npy")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step08")
    ap.add_argument(
        "--floor",
        type=Path,
        default=PROJECT_ROOT / "Floorplan2.png",
        help="Opcional; si coincide tamaño habilita v04 y 4ª columna en v06",
    )
    args = ap.parse_args()
    run(args.space, args.rooms, args.out, args.floor)


if __name__ == "__main__":
    main()
