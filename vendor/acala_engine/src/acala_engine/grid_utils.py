"""
Generic grid helper functions operating on GridMap + CellType.

No alarm business rules live here; only reusable spatial logic.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Iterator, List, Set, Tuple

from .model import CellType, GridCoord, GridMap


def is_inside(grid: GridMap, coord: GridCoord) -> bool:
    """Return True if coord is inside the grid bounds."""
    r, c = coord
    return 0 <= r < grid.height and 0 <= c < grid.width


def get_cell(grid: GridMap, coord: GridCoord) -> int:
    """
    Return the raw cell value at coord.

    Caller can wrap it as CellType(...) if needed.
    """
    if not is_inside(grid, coord):
        raise IndexError(f"coord {coord} outside grid bounds {grid.height}x{grid.width}")
    r, c = coord
    return grid.cells[r][c]


def iter_neighbors_4(grid: GridMap, coord: GridCoord) -> Iterator[GridCoord]:
    """Yield 4-connected neighbours (up, down, left, right) inside bounds."""
    r, c = coord
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < grid.height and 0 <= nc < grid.width:
            yield (nr, nc)


def is_outdoor_adjacent(grid: GridMap, coord: GridCoord) -> bool:
    """
    True if any 4-neighbour of coord is an OUTDOOR cell.
    """
    for n in iter_neighbors_4(grid, coord):
        if CellType(get_cell(grid, n)) is CellType.OUTDOOR:
            return True
    return False


def is_interior_opening_to_outdoor(grid: GridMap, coord: GridCoord) -> bool:
    """
    True if coord is a DOOR/WINDOW cell and is adjacent to OUTDOOR.
    """
    cell_type = CellType(get_cell(grid, coord))
    if cell_type not in (CellType.DOOR, CellType.WINDOW):
        return False
    return is_outdoor_adjacent(grid, coord)


def radius_expand(
    grid: GridMap,
    center: GridCoord,
    radius_cells: float,
    *,
    include_center: bool = True,
) -> List[GridCoord]:
    """
    Return all coords within a Chebyshev radius (square) around center.

    This is intentionally simple for Milestone -1: it does not consider walls,
    only raw grid distance in cells.
    """
    max_delta = int(radius_cells)
    if max_delta < 0:
        return []

    out: List[GridCoord] = []
    cr, cc = center
    for dr in range(-max_delta, max_delta + 1):
        for dc in range(-max_delta, max_delta + 1):
            if not include_center and dr == 0 and dc == 0:
                continue
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < grid.height and 0 <= nc < grid.width:
                out.append((nr, nc))
    return out


def flood_fill_indoor_component(grid: GridMap, start: GridCoord) -> List[GridCoord]:
    """
    Return all connected INDOOR cells reachable from start (4-connected).

    If start is not INDOOR, returns [].
    """
    if not is_inside(grid, start):
        return []
    if CellType(get_cell(grid, start)) is not CellType.INDOOR:
        return []

    visited: Set[GridCoord] = set()
    q: deque[GridCoord] = deque([start])
    visited.add(start)

    while q:
        cur = q.popleft()
        for n in iter_neighbors_4(grid, cur):
            if n in visited:
                continue
            if CellType(get_cell(grid, n)) is not CellType.INDOOR:
                continue
            visited.add(n)
            q.append(n)

    return sorted(visited)


def find_all_indoor_components(grid: GridMap) -> List[List[GridCoord]]:
    """
    Find all 4-connected components of INDOOR cells in the grid.

    Returns a list of components, each component being a sorted list of coords.
    """
    visited: Set[GridCoord] = set()
    components: List[List[GridCoord]] = []

    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if coord in visited:
                continue
            if CellType(grid.cells[r][c]) is not CellType.INDOOR:
                continue
            comp = flood_fill_indoor_component(grid, coord)
            if not comp:
                continue
            visited.update(comp)
            components.append(comp)

    return components

