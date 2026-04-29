"""
Topological validation of final structure grids (0=ext, 1=wall, 2=win, 3=door, 4=int).

Run on ``effective_struct`` after wizard patches (same matrix step05 uses).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from opening_adjacency import connected_components_4, iter_opening_cc_boxes, scan_opening_adjacency_violations

_EXTERIOR = 0
_WALL = 1
_WINDOW = 2
_DOOR = 3
_INTERIOR = 4


@dataclass
class TopologyOptions:
    """Toggle stricter checks. R4 is off by default (see module docstring)."""

    r4_interior_reachable_without_wall: bool = False
    """If True, flag interior cells reachable from map border through non-wall cells.
    This is True for almost all real floorplans that have a door to the outside; keep False."""

    max_sample_cells_per_issue: int = 6


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str  # "error" | "warning"
    cells: tuple[tuple[int, int], ...] = ()


@dataclass
class TopologyValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)


@dataclass
class ValidationCheckItem:
    """Single row for UI checklist; detail matches validate_grid_for_alarm strings."""

    id: str
    label: str
    ok: bool
    blocks_proposal: bool
    detail: str | None = None


def _neighbor4(h: int, w: int, r: int, c: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            out.append((nr, nc))
    return out


def _check_r1_interior_adjacent_exterior(struct: np.ndarray, max_cells: int) -> list[ValidationIssue]:
    h, w = struct.shape
    bad: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if int(struct[r, c]) != _INTERIOR:
                continue
            for nr, nc in _neighbor4(h, w, r, c):
                if int(struct[nr, nc]) == _EXTERIOR:
                    bad.append((r, c))
                    break
            if len(bad) >= max_cells:
                break
        if len(bad) >= max_cells:
            break
    if not bad:
        return []
    sample = tuple(bad[:max_cells])
    extra = len(bad) - len(sample) if len(bad) > max_cells else 0
    msg = (
        "[INT_EXT_ADJ] Indoor cells cannot touch outdoor cells directly. "
        f"Examples (row,col): {sample}"
    )
    if extra > 0:
        msg += f" … (+{extra} more)"
    return [ValidationIssue(code="INT_EXT_ADJ", message=msg, severity="error", cells=sample)]


def _check_r3_exterior_islands(struct: np.ndarray, max_cc_report: int) -> list[ValidationIssue]:
    """Exterior CC that does not touch grid border (courtyard / hole)."""
    h, w = struct.shape
    ncc, labels = connected_components_4(struct == _EXTERIOR)
    issues: list[ValidationIssue] = []
    for cc in range(1, ncc):
        ys, xs = np.where(labels == cc)
        if ys.size == 0:
            continue
        touches = bool(np.any(ys == 0) or np.any(ys == h - 1) or np.any(xs == 0) or np.any(xs == w - 1))
        if touches:
            continue
        area = int(ys.size)
        rep = (int(ys[0]), int(xs[0]))
        issues.append(
            ValidationIssue(
                code="EXTERIOR_ISLAND",
                message=f"[EXTERIOR_ISLAND] Outdoor area does not connect to the outside edge "
                f"(area≈{area} cells, example {rep}). Check if a patio or hole was marked incorrectly.",
                severity="error",
                cells=(rep,),
            )
        )
        if len(issues) >= max_cc_report:
            break
    return issues


def _check_r4_flood_non_wall(
    struct: np.ndarray, max_cells: int,
) -> list[ValidationIssue]:
    """
    Flood from border through cells != wall. Interior cells in the flood are flagged.
    Off by default in production (doors connect outside to inside).
    """
    h, w = struct.shape
    walk = struct != _WALL
    vis = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for c in range(w):
        for r in (0, h - 1):
            if walk[r, c] and not vis[r, c]:
                vis[r, c] = True
                q.append((r, c))
    for r in range(h):
        for c in (0, w - 1):
            if walk[r, c] and not vis[r, c]:
                vis[r, c] = True
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for nr, nc in _neighbor4(h, w, r, c):
            if walk[nr, nc] and not vis[nr, nc]:
                vis[nr, nc] = True
                q.append((nr, nc))
    bad_mask = (struct == _INTERIOR) & vis
    if not np.any(bad_mask):
        return []
    ys, xs = np.where(bad_mask)
    coords = list(zip(ys.tolist(), xs.tolist()))[:max_cells]
    sample = tuple((int(r), int(c)) for r, c in coords)
    total = int(bad_mask.sum())
    msg = (
        f"[INTERIOR_LEAKS_TO_BORDER] {total} indoor cells can be reached from the map edge without crossing a wall "
        f"(strict mode; common in plans with doors). Example: {sample}"
    )
    return [ValidationIssue(code="INTERIOR_LEAKS_TO_BORDER", message=msg, severity="error", cells=sample)]


def _check_opening_orphans(struct: np.ndarray) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    h, w = struct.shape
    for opening_val, label in ((_WINDOW, "window"), (_DOOR, "door")):
        for cc, y0, y1, x0, x1 in iter_opening_cc_boxes(struct, opening_val):
            ok = False
            for r in range(y0, y1 + 1):
                for c in range(x0, x1 + 1):
                    for nr, nc in _neighbor4(h, w, r, c):
                        v = int(struct[nr, nc])
                        if v in (_EXTERIOR, _INTERIOR):
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                issues.append(
                    ValidationIssue(
                        code="OPENING_NO_ADJACENT_FREE",
                        message=f"[OPENING_NO_ADJACENT_FREE] {label} cc={cc} bbox=({y0}:{y1},{x0}:{x1}) "
                        f"without a directly adjacent outdoor or indoor cell.",
                        severity="error",
                        cells=((y0, x0),),
                    )
                )
    return issues


def _check_interior_exists(struct: np.ndarray) -> list[ValidationIssue]:
    if not np.any(struct == _INTERIOR):
        return [
            ValidationIssue(
                code="NO_INTERIOR",
                message="[NO_INTERIOR] No indoor cells were found in the matrix.",
                severity="error",
                cells=(),
            )
        ]
    return []


def validate_topology(
    struct: np.ndarray,
    *,
    options: TopologyOptions | None = None,
) -> TopologyValidationResult:
    s = np.asarray(struct, dtype=np.uint8)
    if s.ndim != 2:
        raise ValueError("struct must be 2D")
    opts = options or TopologyOptions()
    mx = max(1, opts.max_sample_cells_per_issue)

    res = TopologyValidationResult()
    res.errors.extend(_check_interior_exists(s))
    res.errors.extend(_check_r1_interior_adjacent_exterior(s, mx))
    res.errors.extend(_check_r3_exterior_islands(s, max_cc_report=5))

    # Aperturas largo/corto: step04 intenta corregir; aquí solo advertimos (evita falsos positivos vs enforce).
    for v in scan_opening_adjacency_violations(s):
        res.warnings.append(
            ValidationIssue(
                code=v.code,
                message=f"[{v.code}] {v.message}",
                severity="warning",
                cells=v.cells,
            )
        )
    res.errors.extend(_check_opening_orphans(s))

    if opts.r4_interior_reachable_without_wall:
        res.errors.extend(_check_r4_flood_non_wall(s, mx))

    return res


def _struct_patch_errors(approved: dict, h: int, w: int) -> list[str]:
    errs: list[str] = []
    for i, p in enumerate(approved.get("struct_patch") or []):
        if not all(k in p for k in ("r", "c", "v")):
            errs.append(f"struct_patch[{i}] needs r, c, v")
            continue
        r, c, v = int(p["r"]), int(p["c"]), int(p["v"])
        if not (0 <= r < h and 0 <= c < w):
            errs.append(f"struct_patch[{i}] out of bounds")
        elif v not in range(5):
            errs.append(f"struct_patch[{i}] v must be 0..4")
    return errs


def _main_cell_errors(struct: np.ndarray, me: object, h: int, w: int) -> list[str]:
    if me is None:
        return []
    if not isinstance(me, (list, tuple)) or len(me) != 2:
        return ["main_entry must be [row, col] or null"]
    r, c = int(me[0]), int(me[1])
    if not (0 <= r < h and 0 <= c < w):
        return [f"main_entry ({r},{c}) out of bounds"]
    if int(struct[r, c]) != _DOOR:
        return [f"main_entry must be on a door cell (struct=3), got {int(struct[r, c])}"]
    return []


def _board_cell_errors(struct: np.ndarray, eb: object, h: int, w: int) -> list[str]:
    if eb is None:
        return []
    if not isinstance(eb, (list, tuple)) or len(eb) != 2:
        return ["electric_board must be [row, col] or null"]
    r, c = int(eb[0]), int(eb[1])
    if not (0 <= r < h and 0 <= c < w):
        return [f"electric_board ({r},{c}) out of bounds"]
    if int(struct[r, c]) != _INTERIOR:
        return [
            f"electric_board must be on interior (struct=4), got {int(struct[r, c])}"
        ]
    return []


def build_validation_checklist(
    struct: np.ndarray,
    approved: dict | None,
    *,
    require_markers: bool = True,
    main_entry_must_touch_exterior: bool = True,
    topology_options: TopologyOptions | None = None,
) -> list[ValidationCheckItem]:
    """
    Ordered checklist for UI: each row ok/fail; ``blocks_proposal`` matches step05 / wizard gating.
    Mirrors ``validate_approved`` gate: if markers required but missing, skip patch/placement rows
    (same as review_bundle_io early return).
    """
    s = np.asarray(struct, dtype=np.uint8)
    h, w = s.shape
    ap = approved or {}
    me, eb = ap.get("main_entry"), ap.get("electric_board")
    items: list[ValidationCheckItem] = []

    if require_markers:
        items.append(
            ValidationCheckItem(
                id="marker_main",
                label="Front door marker is placed",
                ok=me is not None,
                blocks_proposal=True,
                detail=None
                if me is not None
                else "main_entry is required (pick a door cell)",
            )
        )
        items.append(
            ValidationCheckItem(
                id="marker_board",
                label="Electrical board marker is placed",
                ok=eb is not None,
                blocks_proposal=True,
                detail=None
                if eb is not None
                else "electric_board is required (pick an interior cell)",
            )
        )

    marker_gate_ok = not require_markers or (me is not None and eb is not None)

    if marker_gate_ok:
        pe = _struct_patch_errors(ap, h, w)
        items.append(
            ValidationCheckItem(
                id="struct_patches",
                label="Matrix edits are valid",
                ok=len(pe) == 0,
                blocks_proposal=True,
                detail=None if not pe else " · ".join(pe),
            )
        )

        if me is not None:
            m_err = _main_cell_errors(s, me, h, w)
            items.append(
                ValidationCheckItem(
                    id="main_door_cell",
                    label="Front door is on a Door cell",
                    ok=len(m_err) == 0,
                    blocks_proposal=True,
                    detail=None if not m_err else m_err[0],
                )
            )
        if eb is not None:
            b_err = _board_cell_errors(s, eb, h, w)
            items.append(
                ValidationCheckItem(
                    id="board_interior",
                    label="Electrical board is on an Interior cell",
                    ok=len(b_err) == 0,
                    blocks_proposal=True,
                    detail=None if not b_err else b_err[0],
                )
            )

        if main_entry_must_touch_exterior and me is not None:
            main_ex_ok = True
            main_ex_detail: str | None = None
            if isinstance(me, (list, tuple)) and len(me) == 2:
                r, c = int(me[0]), int(me[1])
                if 0 <= r < h and 0 <= c < w:
                    touches = any(
                        int(s[nr, nc]) == _EXTERIOR for nr, nc in _neighbor4(h, w, r, c)
                    )
                    if not touches:
                        main_ex_ok = False
                        main_ex_detail = (
                            "[MAIN_ENTRY_NO_EXTERIOR] Front door must be on a Door cell with "
                            "an Outdoor cell directly next to it."
                        )
            items.append(
                ValidationCheckItem(
                    id="main_entry_exterior",
                    label="Front door has an Outdoor cell next to it",
                    ok=main_ex_ok,
                    blocks_proposal=True,
                    detail=main_ex_detail,
                )
            )

    topo = validate_topology(s, options=topology_options)
    by_code: dict[str, list[ValidationIssue]] = {}
    for iss in topo.errors:
        by_code.setdefault(iss.code, []).append(iss)

    def _one(code: str, label: str) -> None:
        group = by_code.get(code, [])
        items.append(
            ValidationCheckItem(
                id=code.lower(),
                label=label,
                ok=len(group) == 0,
                blocks_proposal=True,
                detail=None if not group else group[0].message,
            )
        )

    _one("NO_INTERIOR", "The plan includes indoor space")
    _one("INT_EXT_ADJ", "Indoor cells are separated from outdoor cells")
    _one("EXTERIOR_ISLAND", "Outdoor areas connect to the outside edge")
    orphans = by_code.get("OPENING_NO_ADJACENT_FREE", [])
    items.append(
        ValidationCheckItem(
            id="opening_adjacent_free",
            label="Doors and windows touch indoor or outdoor space",
            ok=len(orphans) == 0,
            blocks_proposal=True,
            detail=None if not orphans else orphans[0].message,
        )
    )
    if topology_options and topology_options.r4_interior_reachable_without_wall:
        _one(
            "INTERIOR_LEAKS_TO_BORDER",
            "Indoor cells are not reachable from the map edge without a wall",
        )

    open_warns = [w for w in topo.warnings if w.code.startswith("OPENING_")]
    items.append(
        ValidationCheckItem(
            id="opening_geometry",
            label="Door and window surrounding walls look reasonable",
            ok=len(open_warns) == 0,
            blocks_proposal=False,
            detail=None if not open_warns else " · ".join(w.message for w in open_warns),
        )
    )

    return items


def collect_validation_highlight_cells(
    struct: np.ndarray,
    approved: dict | None,
    *,
    require_markers: bool = True,
    main_entry_must_touch_exterior: bool = True,
    topology_options: TopologyOptions | None = None,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]]]:
    """
    Sets of ``(row, col)`` for map overlay:
    blocking errors and opening/wall warnings.
    Same gates as :func:`build_validation_checklist` for marker/placement extras.
    """
    s = np.asarray(struct, dtype=np.uint8)
    h, w = s.shape
    ap = approved or {}
    err_cells: set[tuple[int, int]] = set()
    warn_short: set[tuple[int, int]] = set()
    warn_long_wall: set[tuple[int, int]] = set()

    topo = validate_topology(s, options=topology_options)
    for iss in topo.errors:
        err_cells.update(iss.cells)
    for iss in topo.warnings:
        if iss.code == "OPENING_LONG_SIDE_WALL":
            warn_long_wall.update(iss.cells)
        else:
            warn_short.update(iss.cells)

    me, eb = ap.get("main_entry"), ap.get("electric_board")
    marker_gate_ok = not require_markers or (me is not None and eb is not None)

    if marker_gate_ok:
        if me is not None and isinstance(me, (list, tuple)) and len(me) == 2:
            r, c = int(me[0]), int(me[1])
            if 0 <= r < h and 0 <= c < w and int(s[r, c]) != _DOOR:
                err_cells.add((r, c))
        if eb is not None and isinstance(eb, (list, tuple)) and len(eb) == 2:
            r, c = int(eb[0]), int(eb[1])
            if 0 <= r < h and 0 <= c < w and int(s[r, c]) != _INTERIOR:
                err_cells.add((r, c))
        if main_entry_must_touch_exterior and me is not None and isinstance(me, (list, tuple)) and len(me) == 2:
            r, c = int(me[0]), int(me[1])
            if 0 <= r < h and 0 <= c < w and int(s[r, c]) == _DOOR:
                touches = any(
                    int(s[nr, nc]) == _EXTERIOR for nr, nc in _neighbor4(h, w, r, c)
                )
                if not touches:
                    err_cells.add((r, c))

    warn_short -= err_cells
    warn_long_wall -= err_cells
    return err_cells, warn_short, warn_long_wall


def validate_grid_for_alarm(
    struct: np.ndarray,
    approved: dict | None,
    *,
    require_markers: bool = True,
    main_entry_must_touch_exterior: bool = True,
    topology_options: TopologyOptions | None = None,
) -> tuple[list[str], list[str]]:
    """
    Merge marker/patch validation with topology rules (same rules as ``review_bundle_io.validate_approved``).

    Returns (errors, warnings) as human-readable strings for UI / reports.
    """
    s = np.asarray(struct, dtype=np.uint8)
    items = build_validation_checklist(
        s,
        approved,
        require_markers=require_markers,
        main_entry_must_touch_exterior=main_entry_must_touch_exterior,
        topology_options=topology_options,
    )
    errors: list[str] = []
    warnings: list[str] = []
    for it in items:
        if it.ok:
            continue
        msg = it.detail if it.detail else it.label
        if it.blocks_proposal:
            errors.append(msg)
        else:
            warnings.append(msg)
    return errors, warnings
