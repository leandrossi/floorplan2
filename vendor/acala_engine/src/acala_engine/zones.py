"""
Zone generation logic (Milestone -1).

Current capabilities:
- build red zones for exterior-accessible doors and windows
- build prohibited zones around heat/cold sources
"""

from __future__ import annotations

from typing import List, Set

from .grid_utils import is_interior_opening_to_outdoor, radius_expand, iter_neighbors_4
from .model import (
    CellType,
    GridCoord,
    MapElement,
    MapElementType,
    Scenario,
    Zone,
    ZoneType,
)


def _is_exterior_opening_cell(scenario: Scenario, coord: GridCoord) -> bool:
    """True if coord is a DOOR/WINDOW cell that is adjacent to outdoor."""
    return is_interior_opening_to_outdoor(scenario.grid_map, coord)


def build_red_zones_for_exterior_openings(
    scenario: Scenario,
    *,
    influence_depth_m: float = 2.0,
) -> List[Zone]:
    """
    Generate red zones for exterior-accessible windows and doors.

    - For every DOOR / WINDOW cell that touches outdoor on the other side,
      we create a small red zone inside the dwelling.
    - The red zone covers indoor cells within `influence_depth_m` of the opening,
      but expansion is *wall-aware*: it only flows through indoor cells and
      cannot "leak" through walls into other rooms.
    """
    grid = scenario.grid_map
    radius_cells = influence_depth_m / grid.cell_size_m

    zones: List[Zone] = []
    red_index = 1

    # Iterate over all cells; doors/windows live in the matrix, not elements.
    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if not _is_exterior_opening_cell(scenario, coord):
                continue

            red_cells: Set[GridCoord] = set()

            # Start from indoor neighbours just inside the opening.
            r0, c0 = coord
            start_cells: List[GridCoord] = []
            for n in iter_neighbors_4(grid, coord):
                nr, nc = n
                if CellType(grid.cells[nr][nc]) is CellType.INDOOR:
                    # Chebyshev distance limit, same as radius_expand.
                    if max(abs(nr - r0), abs(nc - c0)) <= radius_cells:
                        start_cells.append(n)

            if not start_cells:
                continue

            visited: Set[GridCoord] = set()
            queue: List[GridCoord] = list(start_cells)

            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)

                cr, cc = cur
                # Respect radius limit from the opening.
                if max(abs(cr - r0), abs(cc - c0)) > radius_cells:
                    continue

                if CellType(grid.cells[cr][cc]) is not CellType.INDOOR:
                    continue

                red_cells.add(cur)

                for n in iter_neighbors_4(grid, cur):
                    if n in visited:
                        continue
                    nr, nc = n
                    if CellType(grid.cells[nr][nc]) is not CellType.INDOOR:
                        continue
                    queue.append(n)

            if not red_cells:
                continue

            zone = Zone(
                id=f"zone_red_{red_index}",
                zone_type=ZoneType.RED,
                cells=sorted(red_cells),
            )
            zones.append(zone)
            red_index += 1

    return zones


def build_prohibited_zones_around_hazards(
    scenario: Scenario,
    *,
    radius_m: float = 0.5,
) -> List[Zone]:
    """
    Generate prohibited zones around heat/cold sources.

    - Uses MapElementType.HEAT_SOURCE and MapElementType.COLD_SOURCE as centers.
    - Expands a simple radius in grid cells (no wall-awareness yet).
    - Marks indoor and already-prohibited cells within that radius as part
      of a PROHIBITED zone.
    """
    grid = scenario.grid_map
    radius_cells = radius_m / grid.cell_size_m

    zones: List[Zone] = []
    prohib_index = 1

    for elem in scenario.elements:
        if elem.element_type not in (MapElementType.HEAT_SOURCE, MapElementType.COLD_SOURCE):
            continue
        if not elem.cells:
            continue

        zone_cells: Set[GridCoord] = set()
        for center in elem.cells:
            for coord in radius_expand(grid, center, radius_cells=radius_cells):
                ct = CellType(grid.cells[coord[0]][coord[1]])
                if ct not in (CellType.INDOOR, CellType.PROHIBITED):
                    continue
                zone_cells.add(coord)

        if not zone_cells:
            continue

        zone = Zone(
            id=f"zone_prohibited_{prohib_index}",
            zone_type=ZoneType.PROHIBITED,
            cells=sorted(zone_cells),
        )
        zones.append(zone)
        prohib_index += 1

    return zones

