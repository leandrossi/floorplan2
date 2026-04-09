"""
Zone generation logic (Milestone -1).

Current capabilities:
- build red zones for exterior-accessible doors and windows
- build prohibited zones around heat/cold sources
"""

from __future__ import annotations

from typing import List, Set

from .grid_utils import (
    flood_fill_opening_group,
    is_interior_opening_to_outdoor,
    iter_neighbors_4,
    radius_expand,
)
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

    For every connected group of DOOR/WINDOW cells that reaches OUTDOOR on one
    side, seed a BFS from the INDOOR cells adjacent to the *interior* edge of
    that group.  This handles openings that are 1-cell, 2-cell, or N-cell thick
    (common in rasterized floorplans where a wall+window occupies several rows).

    Expansion is wall-aware: only INDOOR cells within ``influence_depth_m``
    (Chebyshev from the nearest group cell) are included.
    """
    grid = scenario.grid_map
    radius_cells = influence_depth_m / grid.cell_size_m

    zones: List[Zone] = []
    red_index = 1
    processed_openings: Set[GridCoord] = set()

    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if coord in processed_openings:
                continue
            if not _is_exterior_opening_cell(scenario, coord):
                continue

            group, _ext_edge, interior_seeds = flood_fill_opening_group(grid, coord)
            processed_openings.update(group)

            if not interior_seeds:
                continue

            group_set = set(group)

            def _min_chebyshev_to_group(cr: int, cc: int) -> float:
                return min(
                    max(abs(cr - gr), abs(cc - gc)) for gr, gc in group_set
                )

            red_cells: Set[GridCoord] = set()
            visited: Set[GridCoord] = set()
            queue = list(interior_seeds)

            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)

                cr, cc = cur
                if _min_chebyshev_to_group(cr, cc) > radius_cells:
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

