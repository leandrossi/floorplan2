"""
Exterior margin padding for cell-level structure grids (0 ext, 1 wall, 2 win, 3 door, 4 int).

When the floorplan raster touches the matrix border, openings and walls can have their
bbox \"long\" face pointing outside the grid (no neighbor). This module adds rows/columns
of exterior (0) so long faces can face free space, using one union padding pass (no
duplicate columns from overlapping rules).

Conceptual / heuristic: same long/short convention as ``opening_adjacency`` for 2/3;
walls (1) use local neighbor counts to pick long normals (horizontal segment → up/down).
"""
from __future__ import annotations

import numpy as np

from opening_adjacency import iter_opening_cc_boxes


def _opening_long_side_border_padding(struct: np.ndarray) -> tuple[int, int, int, int]:
    """(pad_top, pad_bottom, pad_left, pad_right) if long side of opening bbox lies on grid edge."""
    h, w = struct.shape
    pt = pb = pl = pr = 0
    for opening_val in (2, 3):
        for _cc, y0, y1, x0, x1 in iter_opening_cc_boxes(struct, opening_val):
            bh = y1 - y0 + 1
            bw = x1 - x0 + 1
            orient = "H" if bw >= bh else "V"
            if orient == "H":
                if y0 == 0:
                    pt = max(pt, 1)
                if y1 == h - 1:
                    pb = max(pb, 1)
            else:
                if x0 == 0:
                    pl = max(pl, 1)
                if x1 == w - 1:
                    pr = max(pr, 1)
    return pt, pb, pl, pr


def _wall_long_face_border_padding(struct: np.ndarray) -> tuple[int, int, int, int]:
    """
    For each wall cell, estimate segment orientation; long faces are the two normals
    orthogonal to the segment. If a long face is out of bounds, request padding on that side.
    Ties / isolated wall cells consider all four directions.
    """
    h, w = struct.shape
    pt = pb = pl = pr = 0
    s = struct
    ys, xs = np.where(s == 1)
    for r, c in zip(ys.tolist(), xs.tolist()):
        left_w = c > 0 and int(s[r, c - 1]) == 1
        right_w = c < w - 1 and int(s[r, c + 1]) == 1
        up_w = r > 0 and int(s[r - 1, c]) == 1
        down_w = r < h - 1 and int(s[r + 1, c]) == 1
        horiz = (1 if left_w else 0) + (1 if right_w else 0)
        vert = (1 if up_w else 0) + (1 if down_w else 0)
        if horiz > vert:
            long_dirs = ((-1, 0), (1, 0))
        elif vert > horiz:
            long_dirs = ((0, -1), (0, 1))
        else:
            long_dirs = ((-1, 0), (1, 0), (0, -1), (0, 1))
        for dr, dc in long_dirs:
            nr, nc = r + dr, c + dc
            if nr < 0:
                pt = max(pt, 1)
            elif nr >= h:
                pb = max(pb, 1)
            elif nc < 0:
                pl = max(pl, 1)
            elif nc >= w:
                pr = max(pr, 1)
    return pt, pb, pl, pr


def compute_exterior_border_padding(struct: np.ndarray) -> tuple[int, int, int, int]:
    """
    Union of padding required so opening long sides and wall long faces are not clipped
    by the grid border (single pass totals per edge).
    """
    s = np.asarray(struct, dtype=np.uint8)
    if s.ndim != 2:
        raise ValueError("struct must be 2D")
    ot, ob, ol, or_ = _opening_long_side_border_padding(s)
    wt, wb, wl, wr = _wall_long_face_border_padding(s)
    return max(ot, wt), max(ob, wb), max(ol, wl), max(or_, wr)


def apply_struct_exterior_padding(
    struct: np.ndarray,
    room_out: np.ndarray,
    free_pref: np.ndarray,
    pads: tuple[int, int, int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pad struct (0), rooms (0), free_pref (0) with the same geometry."""
    pt, pb, pl, pr = pads
    if pt == pb == pl == pr == 0:
        return struct, room_out, free_pref
    struct_p = np.pad(struct, ((pt, pb), (pl, pr)), constant_values=0)
    room_p = np.pad(room_out, ((pt, pb), (pl, pr)), constant_values=0)
    free_p = np.pad(free_pref, ((pt, pb), (pl, pr)), constant_values=0)
    return struct_p, room_p, free_p


def pad_struct_grids_in_place(
    struct: np.ndarray,
    room_out: np.ndarray,
    free_pref: np.ndarray,
    *,
    max_passes: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int, int, int], list[str]]:
    """
    Repeatedly pad until no border demands or max_passes. Returns padded arrays,
    cumulative pads (sum per edge), and log lines.
    """
    logs: list[str] = []
    total_pt = total_pb = total_pl = total_pr = 0
    s, r, f = struct, room_out, free_pref
    for pass_i in range(max_passes):
        pt, pb, pl, pr = compute_exterior_border_padding(s)
        if pt == pb == pl == pr == 0:
            break
        logs.append(
            f"exterior_border_pad pass={pass_i + 1} top={pt} bottom={pb} left={pl} right={pr}"
        )
        s, r, f = apply_struct_exterior_padding(s, r, f, (pt, pb, pl, pr))
        total_pt += pt
        total_pb += pb
        total_pl += pl
        total_pr += pr
    return s, r, f, (total_pt, total_pb, total_pl, total_pr), logs
