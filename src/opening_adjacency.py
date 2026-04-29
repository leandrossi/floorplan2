"""
Shared opening (window/door) adjacency rules for bbox-oriented long/short sides.

Used by final_step04 (mutating fix) and grid_topology_validate (read-only check).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterator

import numpy as np


@dataclass(frozen=True)
class OpeningViolation:
    code: str
    message: str
    opening_label: str
    cc_id: int
    orient: str
    bbox: tuple[int, int, int, int]  # y0, y1, x0, x1
    # (row, col) to highlight — offending long/short-side cell
    cells: tuple[tuple[int, int], ...] = ()


def connected_components_4(mask: np.ndarray) -> tuple[int, np.ndarray]:
    """Return OpenCV-like 4-connected component labels without importing cv2 at app startup."""
    mask_bool = np.asarray(mask).astype(bool)
    h, w = mask_bool.shape
    labels = np.zeros((h, w), dtype=np.int32)
    current_label = 0

    for start_r, start_c in zip(*np.where(mask_bool & (labels == 0))):
        current_label += 1
        labels[start_r, start_c] = current_label
        q: deque[tuple[int, int]] = deque([(int(start_r), int(start_c))])

        while q:
            r, c = q.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w and mask_bool[nr, nc] and labels[nr, nc] == 0:
                    labels[nr, nc] = current_label
                    q.append((nr, nc))

    return current_label + 1, labels


def iter_opening_cc_boxes(struct_m: np.ndarray, opening_val: int) -> Iterator[tuple[int, int, int, int, int]]:
    """Yield (cc_id, y0, y1, x0, x1) per 4-connected component of opening_val."""
    ncc, labels = connected_components_4(struct_m == opening_val)
    for cc in range(1, ncc):
        ys, xs = np.where(labels == cc)
        if ys.size == 0:
            continue
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        yield cc, y0, y1, x0, x1


def scan_opening_adjacency_violations(struct_m: np.ndarray) -> list[OpeningViolation]:
    """
    Long sides of each opening bbox should face free space (not wall 1).
    Short sides should be wall-adjacent (not free 0/4).
    """
    out: list[OpeningViolation] = []
    h, w = struct_m.shape

    for opening_val, label in ((2, "window"), (3, "door")):
        for cc, y0, y1, x0, x1 in iter_opening_cc_boxes(struct_m, opening_val):
            bh = y1 - y0 + 1
            bw = x1 - x0 + 1
            orient = "H" if bw >= bh else "V"
            long_hit: tuple[int, int] | None = None
            short_hit: tuple[int, int] | None = None

            if orient == "H":
                for x in range(x0, x1 + 1):
                    for y in (y0 - 1, y1 + 1):
                        if 0 <= y < h and 0 <= x < w and int(struct_m[y, x]) == 1:
                            long_hit = (y, x)
                            break
                    if long_hit:
                        break
                if long_hit:
                    y, x = long_hit
                    out.append(
                        OpeningViolation(
                            code="OPENING_LONG_SIDE_WALL",
                            message=f"{label} opening at ({y0}:{y1},{x0}:{x1}): "
                            f"nearby wall at ({y},{x}) may need review",
                            opening_label=label,
                            cc_id=cc,
                            orient=orient,
                            bbox=(y0, y1, x0, x1),
                            cells=((y, x),),
                        )
                    )
                for y in range(y0, y1 + 1):
                    for x in (x0 - 1, x1 + 1):
                        if 0 <= y < h and 0 <= x < w and int(struct_m[y, x]) in (0, 4):
                            short_hit = (y, x)
                            break
                    if short_hit:
                        break
                if short_hit:
                    y, x = short_hit
                    out.append(
                        OpeningViolation(
                            code="OPENING_SHORT_SIDE_FREE",
                            message=f"{label} opening at ({y0}:{y1},{x0}:{x1}): "
                            f"nearby indoor/outdoor cell at ({y},{x}) may need review",
                            opening_label=label,
                            cc_id=cc,
                            orient=orient,
                            bbox=(y0, y1, x0, x1),
                            cells=((y, x),),
                        )
                    )
            else:
                for y in range(y0, y1 + 1):
                    for x in (x0 - 1, x1 + 1):
                        if 0 <= y < h and 0 <= x < w and int(struct_m[y, x]) == 1:
                            long_hit = (y, x)
                            break
                    if long_hit:
                        break
                if long_hit:
                    y, x = long_hit
                    out.append(
                        OpeningViolation(
                            code="OPENING_LONG_SIDE_WALL",
                            message=f"{label} opening at ({y0}:{y1},{x0}:{x1}): "
                            f"nearby wall at ({y},{x}) may need review",
                            opening_label=label,
                            cc_id=cc,
                            orient=orient,
                            bbox=(y0, y1, x0, x1),
                            cells=((y, x),),
                        )
                    )
                for x in range(x0, x1 + 1):
                    for y in (y0 - 1, y1 + 1):
                        if 0 <= y < h and 0 <= x < w and int(struct_m[y, x]) in (0, 4):
                            short_hit = (y, x)
                            break
                    if short_hit:
                        break
                if short_hit:
                    y, x = short_hit
                    out.append(
                        OpeningViolation(
                            code="OPENING_SHORT_SIDE_FREE",
                            message=f"{label} opening at ({y0}:{y1},{x0}:{x1}): "
                            f"nearby indoor/outdoor cell at ({y},{x}) may need review",
                            opening_label=label,
                            cc_id=cc,
                            orient=orient,
                            bbox=(y0, y1, x0, x1),
                            cells=((y, x),),
                        )
                    )
    return out


def enforce_opening_adjacency(
    struct_m: np.ndarray,
    free_pref: np.ndarray,
) -> list[str]:
    """
    Mutate struct_m like legacy final_step04: long sides wall->free_pref, short free->wall.
    Returns log lines (one per changed component).
    """
    out = struct_m
    logs: list[str] = []

    for opening_val, label in ((2, "window"), (3, "door")):
        ncc, labels = connected_components_4(out == opening_val)
        for cc in range(1, ncc):
            ys, xs = np.where(labels == cc)
            if ys.size == 0:
                continue
            y0, y1 = int(ys.min()), int(ys.max())
            x0, x1 = int(xs.min()), int(xs.max())
            bh = y1 - y0 + 1
            bw = x1 - x0 + 1
            orient = "H" if bw >= bh else "V"
            changes_long = 0
            changes_short = 0

            if orient == "H":
                for x in range(x0, x1 + 1):
                    for y in (y0 - 1, y1 + 1):
                        if 0 <= y < out.shape[0] and 0 <= x < out.shape[1] and out[y, x] == 1:
                            out[y, x] = int(free_pref[y, x])
                            changes_long += 1
                for y in range(y0, y1 + 1):
                    for x in (x0 - 1, x1 + 1):
                        if 0 <= y < out.shape[0] and 0 <= x < out.shape[1] and out[y, x] in (0, 4):
                            out[y, x] = 1
                            changes_short += 1
            else:
                for y in range(y0, y1 + 1):
                    for x in (x0 - 1, x1 + 1):
                        if 0 <= y < out.shape[0] and 0 <= x < out.shape[1] and out[y, x] == 1:
                            out[y, x] = int(free_pref[y, x])
                            changes_long += 1
                for x in range(x0, x1 + 1):
                    for y in (y0 - 1, y1 + 1):
                        if 0 <= y < out.shape[0] and 0 <= x < out.shape[1] and out[y, x] in (0, 4):
                            out[y, x] = 1
                            changes_short += 1

            if changes_long or changes_short:
                logs.append(
                    f"{label}[cc={cc}] orient={orient} bbox=({y0}:{y1},{x0}:{x1}) "
                    f"long_side_wall_to_free={changes_long} short_side_free_to_wall={changes_short}"
                )
    return logs
