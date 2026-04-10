"""
Alarm planning engine v1 (Milestone -1).

Current behavior:
- Scenario -> zones (red + prohibited)
- Scenario -> InstallationProposal with panel + keyboard placement (devices list will grow later)
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Set, Tuple
import math

from .model import (
    CellType,
    DevicePlacement,
    DeviceType,
    GridCoord,
    InstallationProposal,
    MapElement,
    MapElementType,
    ProductType,
    Scenario,
    SecurityLevel,
    Zone,
    ZoneType,
)
from .zones import (
    build_prohibited_zones_around_hazards,
    build_red_zones_for_exterior_openings,
)
from .grid_utils import (
    capped_radius_cells,
    find_all_indoor_components,
    flood_fill_opening_group,
    is_interior_opening_to_outdoor,
    is_outdoor_adjacent,
    iter_neighbors_4,
    radius_expand,
)
from .alarm_rules import ALARM_RULES, MagneticRules, PirRules, SirenRules


def plan_installation(
    scenario: Scenario,
    *,
    product_type: ProductType = ProductType.ALARM,
    security_level: SecurityLevel | None = None,
) -> InstallationProposal:
    """
    Main planner entrypoint for Milestone -1.

    Current behavior:
    - builds red zones for exterior-accessible doors/windows
    - builds prohibited zones around heat/cold sources
    - places a panel near the electric board when possible
    - returns an InstallationProposal with zones and at least one device (panel)
    """
    if security_level is None:
        security_level = scenario.security_level

    red_zones: List[Zone] = build_red_zones_for_exterior_openings(scenario)
    prohibited_zones: List[Zone] = build_prohibited_zones_around_hazards(scenario)
    zones: List[Zone] = [*red_zones, *prohibited_zones]

    devices: List[DevicePlacement] = []
    _place_panel(scenario, zones, devices)
    _place_keyboard(scenario, zones, devices)
    covered_openings = _place_magnetics(scenario, zones, devices, security_level)

    if covered_openings:
        zones = _suppress_red_zones_for_covered_openings(
            scenario, zones, covered_openings, security_level
        )

    _place_pirs(scenario, zones, devices, security_level)
    zones = _suppress_red_zones_covered_by_pirs(
        scenario, zones, devices, security_level
    )

    _place_sirens(scenario, zones, devices, security_level)

    proposal = InstallationProposal(
        product_type=product_type,
        security_level=security_level,
        grid_map=scenario.grid_map,
        rooms=scenario.rooms,
        zones=zones,
        elements=scenario.elements,
        devices=devices,
    )
    return proposal


def _first_element_of_type(
    elements: List[MapElement],
    element_type: MapElementType,
) -> Optional[MapElement]:
    for e in elements:
        if e.element_type is element_type:
            return e
    return None


def _collect_prohibited_cells(zones: List[Zone]) -> Set[GridCoord]:
    cells: Set[GridCoord] = set()
    for z in zones:
        if z.zone_type is ZoneType.PROHIBITED:
            cells.update(z.cells)
    return cells


def _place_panel(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
) -> None:
    """
    Place the panel:
    - prefer an indoor, non-prohibited cell at / near the electric board
    - otherwise, fall back to the first indoor, non-prohibited cell in the grid
    """
    grid = scenario.grid_map
    cells = grid.cells

    prohibited_cells = _collect_prohibited_cells(zones)

    def is_valid(coord: GridCoord) -> bool:
        r, c = coord
        if not (0 <= r < grid.height and 0 <= c < grid.width):
            return False
        if CellType(cells[r][c]) is not CellType.INDOOR:
            return False
        if coord in prohibited_cells:
            return False
        return True

    # 1) Try to place at or next to the electric board
    board = _first_element_of_type(scenario.elements, MapElementType.ELECTRIC_BOARD)
    candidate: Optional[GridCoord] = None

    if board and board.cells:
        for coord in board.cells:
            if is_valid(coord):
                candidate = coord
                break
        # Try 4-neighbours around the board if direct cell is unusable
        if candidate is None:
            r0, c0 = board.cells[0]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                coord = (r0 + dr, c0 + dc)
                if is_valid(coord):
                    candidate = coord
                    break

    # 2) Fallback: first indoor, non-prohibited cell in the grid
    if candidate is None:
        for r in range(grid.height):
            for c in range(grid.width):
                if is_valid((r, c)):
                    candidate = (r, c)
                    break
            if candidate is not None:
                break

    if candidate is None:
        return

    reasons = ["panel", "near_electric_board" if board else "fallback_first_indoor"]
    devices.append(
        DevicePlacement(
            id="dev_panel_1",
            device_type=DeviceType.PANEL,
            cell=candidate,
            room_id=None,
            reasons=reasons,
            is_out_of_standard=False,
        )
    )


def _place_keyboard(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
) -> None:
    """
    Place the keyboard near the main entry door, indoors and outside prohibited zones.
    """
    grid = scenario.grid_map
    cells = grid.cells

    prohibited_cells = _collect_prohibited_cells(zones)

    def is_valid(coord: GridCoord) -> bool:
        r, c = coord
        if not (0 <= r < grid.height and 0 <= c < grid.width):
            return False
        if CellType(cells[r][c]) is not CellType.INDOOR:
            return False
        if coord in prohibited_cells:
            return False
        return True

    # Find main entry element (door with is_main_entry=True)
    main_entries = [
        e
        for e in scenario.elements
        if e.element_type is MapElementType.DOOR and e.is_main_entry
    ]
    if not main_entries:
        return

    main = main_entries[0]
    if not main.cells:
        return

    # For thick openings, flood through the door group to find interior-side seeds.
    _kb_group, _kb_ext, kb_interior_seeds = flood_fill_opening_group(grid, main.cells[0])
    candidate: Optional[GridCoord] = None
    for seed in kb_interior_seeds:
        if is_valid(seed):
            candidate = seed
            break
    # Fallback: try direct 4-neighbours of the element cell.
    if candidate is None:
        r0, c0 = main.cells[0]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            coord = (r0 + dr, c0 + dc)
            if is_valid(coord):
                candidate = coord
                break

    if candidate is None:
        for r in range(grid.height):
            for c in range(grid.width):
                if is_valid((r, c)):
                    candidate = (r, c)
                    break
            if candidate is not None:
                break

    if candidate is None:
        return

    reasons = ["keyboard", "near_main_entry"]
    devices.append(
        DevicePlacement(
            id="dev_keyboard_1",
            device_type=DeviceType.KEYBOARD,
            cell=candidate,
            room_id=None,
            reasons=reasons,
            is_out_of_standard=False,
        )
    )


class _OpeningGroup:
    def __init__(self, cells: List[GridCoord], kind: str, representative: GridCoord, is_main_entry: bool) -> None:
        self.cells = cells
        self.kind = kind  # "door" or "window"
        self.representative = representative
        self.is_main_entry = is_main_entry


def _collect_exterior_opening_groups(
    scenario: Scenario,
) -> List[_OpeningGroup]:
    """
    Group exterior doors/windows (structural cells) into contiguous opening groups.

    Uses flood_fill_opening_group to handle multi-pixel-thick openings: the full
    connected DOOR/WINDOW component is collected even when only the outermost row
    touches OUTDOOR.

    Each group has:
    - cells: all door/window coords in the group (4-connected)
    - kind: "door" or "window" (based on CellType of the exterior edge)
    - representative: cell on the *interior* edge of the group (closest to INDOOR),
      matching real-world magnetic sensor placement on the inside frame
    - is_main_entry: True if the group contains the main_entry cell
    """
    grid = scenario.grid_map
    cells = grid.cells

    main_entry_cell: Optional[GridCoord] = None
    main_entries = [
        e
        for e in scenario.elements
        if e.element_type is MapElementType.DOOR and e.is_main_entry and e.cells
    ]
    if main_entries:
        main_entry_cell = main_entries[0].cells[0]

    groups: List[_OpeningGroup] = []
    visited: Set[GridCoord] = set()

    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if coord in visited:
                continue
            if not is_interior_opening_to_outdoor(grid, coord):
                continue

            group_cells, ext_edge, interior_seeds = flood_fill_opening_group(grid, coord)
            visited.update(group_cells)

            if not group_cells:
                continue
            if not ext_edge:
                continue

            ct0 = CellType(cells[ext_edge[0][0]][ext_edge[0][1]])
            kind = "door" if ct0 is CellType.DOOR else "window"

            # Representative: prefer a cell adjacent to INDOOR (interior edge).
            # This is where a magnetic sensor physically sits (inside frame).
            interior_edge = [
                gc for gc in group_cells
                if any(
                    CellType(cells[nr][nc]) is CellType.INDOOR
                    for nr, nc in [(gc[0]-1, gc[1]), (gc[0]+1, gc[1]),
                                   (gc[0], gc[1]-1), (gc[0], gc[1]+1)]
                    if 0 <= nr < grid.height and 0 <= nc < grid.width
                )
            ]
            rep_pool = interior_edge if interior_edge else group_cells

            rows = {r for (r, _) in rep_pool}
            cols = {c for (_, c) in rep_pool}
            if len(cols) == 1 and len(rows) > 1:
                rep = min(rep_pool, key=lambda rc: (rc[0], rc[1]))
            elif len(rows) == 1 and len(cols) > 1:
                rep = min(rep_pool, key=lambda rc: (rc[1], rc[0]))
            else:
                rep = min(rep_pool, key=lambda rc: (rc[0], rc[1]))

            group_set = set(group_cells)
            is_main = main_entry_cell is not None and main_entry_cell in group_set
            groups.append(_OpeningGroup(group_cells, kind, rep, is_main))

    return groups


def _place_magnetics(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
    security_level: SecurityLevel,
) -> Set[GridCoord]:
    """
    Place magnetic sensors on exterior openings, varying by security level:

    - MIN: main entry door only (if exterior).
    - OPTIMAL: all exterior doors.
    - MAX: all exterior doors + exterior windows.

    Magnetics are placed directly on the opening cell.
    """
    grid = scenario.grid_map
    cells = grid.cells

    groups = _collect_exterior_opening_groups(scenario)

    # Choose which groups to protect based on security_level using MagneticRules.
    rules: MagneticRules = ALARM_RULES[security_level]["magnetic"]  # type: ignore[assignment]
    chosen: List[_OpeningGroup] = []
    if rules.protect_main_entry_only:
        chosen = [g for g in groups if g.is_main_entry]
    else:
        door_groups = [g for g in groups if g.kind == "door"]
        window_groups = [g for g in groups if g.kind == "window"] if rules.protect_windows else []
        if rules.protect_all_doors:
            chosen = [*door_groups, *window_groups]
        else:
            # Fallback: if neither main-entry-only nor all-doors is requested, treat as no openings.
            chosen = []

    if not chosen:
        return set()

    covered_cells: Set[GridCoord] = set()

    # Place magnetics for each chosen group.
    for idx, group in enumerate(sorted(chosen, key=lambda g: (g.representative[0], g.representative[1]))):
        coord = group.representative
        r, c = coord
        ct = CellType(cells[r][c])
        base_reasons = ["magnetic", "on_exterior_opening"]
        if group.is_main_entry:
            base_reasons.append("on_main_entry")
        elif ct is CellType.DOOR:
            base_reasons.append("on_exterior_door")
        elif ct is CellType.WINDOW:
            base_reasons.append("on_exterior_window")

        devices.append(
            DevicePlacement(
                id=f"dev_magnetic_{idx + 1}",
                device_type=DeviceType.MAGNETIC,
                cell=coord,
                room_id=None,
                reasons=base_reasons,
                is_out_of_standard=False,
            )
        )

        covered_cells.update(group.cells)

    return covered_cells


def _suppress_red_zones_for_covered_openings(
    scenario: Scenario,
    zones: List[Zone],
    covered_openings: Set[GridCoord],
    security_level: SecurityLevel,
) -> List[Zone]:
    """
    Drop red zones whose influence comes from openings that now have magnetic contacts.

    Heuristic: any RED zone that contains at least one covered opening cell is removed.
    Prohibited zones are preserved.
    """
    if not covered_openings:
        return zones

    grid = scenario.grid_map
    cells = grid.cells

    # Use the same suppression radius as defined in MagneticRules for this profile.
    rules: MagneticRules = ALARM_RULES[security_level]["magnetic"]  # type: ignore[assignment]
    radius_cells = capped_radius_cells(grid, rules.suppression_radius_m, max_grid_fraction=0.15)
    influenced: Set[GridCoord] = set()
    for opening in covered_openings:
        for coord in radius_expand(grid, opening, radius_cells=radius_cells, include_center=True):
            r, c = coord
            if CellType(cells[r][c]) is CellType.INDOOR or coord == opening:
                influenced.add(coord)

    result: List[Zone] = []
    for z in zones:
        if z.zone_type is not ZoneType.RED:
            result.append(z)
            continue
        # Remove only the cells influenced by covered openings; keep the rest of the zone.
        remaining_cells = [c for c in z.cells if c not in influenced]
        if not remaining_cells:
            continue
        result.append(Zone(id=z.id, zone_type=ZoneType.RED, cells=remaining_cells))
    return result


def _suppress_red_zones_covered_by_pirs(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
    security_level: SecurityLevel,
) -> List[Zone]:
    """Remove red zone cells that fall inside any placed PIR's coverage.

    Coverage is computed with the same wall-aware geometry used in _place_pirs:
    - BFS over indoor cells only (walls block propagation)
    - within 8 m Chebyshev radius
    - within the 90° FOV defined by the PIR orientation(s)
    """
    grid = scenario.grid_map
    cells = grid.cells
    cell_size = grid.cell_size_m
    pir_rules: PirRules = ALARM_RULES[security_level]["pir"]  # type: ignore[assignment]
    radius_cells = capped_radius_cells(grid, pir_rules.radius_m, max_grid_fraction=1.0)

    # Build indoor connectivity components once for the grid.
    component_ids_by_coord: Dict[GridCoord, int] = {}
    components = find_all_indoor_components(grid)
    for comp_idx, comp in enumerate(components):
        for coord in comp:
            component_ids_by_coord[coord] = comp_idx

    influenced: Set[GridCoord] = set()
    for d in devices:
        if d.device_type is not DeviceType.PIR:
            continue
        pir_comp = component_ids_by_coord.get(d.cell)
        influenced |= _pir_coverage_component_radius(
            grid, cells, d.cell, radius_cells, component_ids_by_coord, pir_comp
        )

    result: List[Zone] = []
    for z in zones:
        if z.zone_type is not ZoneType.RED:
            result.append(z)
            continue
        remaining = [c for c in z.cells if c not in influenced]
        if not remaining:
            continue
        result.append(Zone(id=z.id, zone_type=ZoneType.RED, cells=remaining))
    return result


def _room_id_for_coord(scenario: Scenario, coord: GridCoord) -> Optional[str]:
    """Return the room id for coord if it belongs to a Room, otherwise None."""
    for room in scenario.rooms:
        if coord in room.cells:
            return room.id
    return None


def _place_sirens(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
    security_level: SecurityLevel,
) -> None:
    """
    Place indoor and outdoor sirens according to SirenRules.

    - Indoor siren: placed in the same room/component as the panel (for MVP, on the
      same cell as the panel).
    - Outdoor siren: placed on a wall cell on the façade next to the main entry
      door, preferring the left side, then the right side if left is unavailable.
    """
    rules: SirenRules = ALARM_RULES[security_level]["siren"]  # type: ignore[assignment]

    grid = scenario.grid_map
    cells = grid.cells

    # Find panel device.
    panels = [d for d in devices if d.device_type is DeviceType.PANEL]
    panel: Optional[DevicePlacement] = panels[0] if panels else None

    # Indoor siren: same cell as panel for MVP, if configured.
    if rules.place_indoor and panel is not None:
        sirens_indoor = [d for d in devices if d.device_type is DeviceType.SIREN_INDOOR]
        if not sirens_indoor:
            devices.append(
                DevicePlacement(
                    id="dev_siren_indoor_1",
                    device_type=DeviceType.SIREN_INDOOR,
                    cell=panel.cell,
                    room_id=_room_id_for_coord(scenario, panel.cell),
                    orientation_deg=None,
                    coverage_radius_cells=None,
                    coverage_angle_deg=None,
                    reasons=["siren_indoor", "same_room_as_panel"],
                    is_out_of_standard=False,
                )
            )

    # Outdoor siren: façade wall next to main entry, left first then right.
    if rules.place_outdoor:
        main_entries = [
            e
            for e in scenario.elements
            if e.element_type is MapElementType.DOOR and e.is_main_entry and e.cells
        ]
        if main_entries:
            main = main_entries[0]
            door_cell = main.cells[0]

            # For thick openings, flood to find an exterior-edge cell in the group.
            group, ext_edge, _seeds = flood_fill_opening_group(grid, door_cell)
            anchor = ext_edge[0] if ext_edge else door_cell
            dr0, dc0 = anchor

            outward: Optional[GridCoord] = None
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = dr0 + dr, dc0 + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    if CellType(cells[nr][nc]) is CellType.OUTDOOR:
                        outward = (nr, nc)
                        break

            if outward is not None:
                or_, oc = outward
                dr_out, dc_out = or_ - dr0, oc - dc0

                # Left/right directions are perpendicular to outward normal.
                left_dir = (-dc_out, dr_out)
                right_dir = (dc_out, -dr_out)

                def find_siren_wall(direction: Tuple[int, int]) -> Optional[GridCoord]:
                    drd, dcd = direction
                    # Search a few cells along the façade line.
                    for k in range(1, max(grid.width, grid.height)):
                        nr, nc = dr0 + drd * k, dc0 + dcd * k
                        if not (0 <= nr < grid.height and 0 <= nc < grid.width):
                            break
                        ct = CellType(cells[nr][nc])
                        if ct is CellType.WALL and is_outdoor_adjacent(grid, (nr, nc)):
                            return (nr, nc)
                        # Stop if we leave the wall band.
                        if ct is not CellType.WALL:
                            break
                    return None

                target = find_siren_wall(left_dir)
                if target is None:
                    target = find_siren_wall(right_dir)

                if target is not None:
                    # Avoid duplicating outdoor sirens.
                    existing_outdoor = [
                        d for d in devices if d.device_type is DeviceType.SIREN_OUTDOOR
                    ]
                    if not existing_outdoor:
                        devices.append(
                            DevicePlacement(
                                id="dev_siren_outdoor_1",
                                device_type=DeviceType.SIREN_OUTDOOR,
                                cell=target,
                                room_id=None,
                                orientation_deg=None,
                                coverage_radius_cells=None,
                                coverage_angle_deg=None,
                                reasons=["siren_outdoor", "near_main_entry_façade"],
                                is_out_of_standard=False,
                            )
                        )


def _pir_coverage_wall_aware(
    grid,
    cells,
    pir_coord: GridCoord,
    radius_cells: float,
    half_fov_rad: float,
    orientations: List[Tuple[float, float]],
) -> Set[GridCoord]:
    """
    Return set of INDOOR cells covered by a PIR at pir_coord with given look directions.
    Wall-aware: only cells reachable by 4-connected INDOOR path from PIR, within radius
    and within FOV of at least one orientation.
    """
    pr, pc = pir_coord
    covered: Set[GridCoord] = set()
    visited: Set[GridCoord] = set()
    queue: List[GridCoord] = [pir_coord]
    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        cr, cc = cur
        if CellType(cells[cr][cc]) is not CellType.INDOOR:
            continue
        if max(abs(cr - pr), abs(cc - pc)) > radius_cells:
            continue
        # Check if direction from PIR to cell is within FOV of any orientation.
        dr, dc = cr - pr, cc - pc
        if dr == 0 and dc == 0:
            pass  # PIR cell itself: include by continuing to neighbours
        else:
            vx, vy = float(dr), float(dc)
            vnorm = math.hypot(vx, vy)
            if vnorm > 0:
                vx, vy = vx / vnorm, vy / vnorm
                in_fov = False
                for ox, oy in orientations:
                    dot = ox * vx + oy * vy
                    dot = max(-1.0, min(1.0, dot))
                    if math.acos(dot) <= half_fov_rad:
                        in_fov = True
                        break
                if not in_fov:
                    continue
        covered.add(cur)
        for n in iter_neighbors_4(grid, cur):
            if n not in visited:
                queue.append(n)
    return covered


def _pir_coverage_component_radius(
    grid,
    cells,
    pir_coord: GridCoord,
    radius_cells: float,
    component_ids_by_coord: Dict[GridCoord, int],
    component_id: Optional[int],
) -> Set[GridCoord]:
    """
    Wall-aware coverage for a PIR based purely on radius within an indoor component.

    - BFS over INDOOR cells only (walls block propagation)
    - within Chebyshev radius

    This intentionally ignores fine-grained FOV and approximates a typical corner PIR in a
    small/medium room as covering the whole indoor component within range.
    """
    pr, pc = pir_coord
    covered: Set[GridCoord] = set()
    visited: Set[GridCoord] = set()
    queue: List[GridCoord] = [pir_coord]

    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)

        cr, cc = cur
        if CellType(cells[cr][cc]) is not CellType.INDOOR:
            continue

        # Restrict coverage to the same indoor connectivity component.
        if component_id is not None:
            cell_comp = component_ids_by_coord.get((cr, cc))
            if cell_comp != component_id:
                continue

        if max(abs(cr - pr), abs(cc - pc)) > radius_cells:
            continue

        covered.add(cur)
        for n in iter_neighbors_4(grid, cur):
            if n not in visited:
                queue.append(n)

    return covered


def _window_beyond_wall_from_indoor(
    cells,
    grid,
    indoor_r: int,
    indoor_c: int,
    wall_r: int,
    wall_c: int,
) -> bool:
    """
    True if the cell one step past the wall (away from the indoor cell) is WINDOW.

    Detects the thin wall between interior and the window strip in rasterised plans:
    a corner with this wall counts as a "window jamb" corner, not two real room walls.
    """
    dr = wall_r - indoor_r
    dc = wall_c - indoor_c
    if abs(dr) + abs(dc) != 1:
        return False
    br, bc = wall_r + dr, wall_c + dc
    if not (0 <= br < grid.height and 0 <= bc < grid.width):
        return False
    return CellType(cells[br][bc]) is CellType.WINDOW


def _is_real_room_wall_corner_pir(
    cells,
    grid,
    coord: GridCoord,
    wall_neighbours: List[GridCoord],
) -> bool:
    """Indoor cell with 2+ wall neighbours and none of them is a window-jamb wall."""
    if len(wall_neighbours) < 2:
        return False
    r, c = coord
    for wr, wc in wall_neighbours:
        if _window_beyond_wall_from_indoor(cells, grid, r, c, wr, wc):
            return False
    return True


def _pir_coverage_quadrant(
    grid,
    cells,
    pir_coord: GridCoord,
    radius_cells: float,
    wall_neighbours: List[GridCoord],
) -> Set[GridCoord]:
    """
    Wall-aware coverage for a corner PIR using a 90-degree quadrant aligned with the walls.

    - BFS over indoor cells only (walls block propagation)
    - within Chebyshev radius
    - constrained to the open quadrant defined by the two adjacent walls
    """
    pr, pc = pir_coord

    # Determine open signs for row/col relative to the PIR (which quadrant is "inside" the room).
    dr_sign = 0  # +1 => dr >= 0, -1 => dr <= 0, 0 => unconstrained
    dc_sign = 0  # +1 => dc >= 0, -1 => dc <= 0, 0 => unconstrained
    for wr, wc in wall_neighbours:
        if wr == pr - 1:  # wall directly above -> room is below
            dr_sign = 1
        elif wr == pr + 1:  # wall below -> room is above
            dr_sign = -1
        if wc == pc - 1:  # wall left -> room is to the right
            dc_sign = 1
        elif wc == pc + 1:  # wall right -> room is to the left
            dc_sign = -1

    covered: Set[GridCoord] = set()
    visited: Set[GridCoord] = set()
    queue: List[GridCoord] = [pir_coord]

    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)

        cr, cc = cur
        if CellType(cells[cr][cc]) is not CellType.INDOOR:
            continue

        if max(abs(cr - pr), abs(cc - pc)) > radius_cells:
            continue

        dr = cr - pr
        dc = cc - pc
        # Enforce quadrant constraints: stay on same side of each wall.
        if dr_sign != 0 and dr_sign * dr < 0:
            continue
        if dc_sign != 0 and dc_sign * dc < 0:
            continue

        covered.add(cur)
        for n in iter_neighbors_4(grid, cur):
            if n not in visited:
                queue.append(n)

    return covered


def _red_bbox(red: Set[GridCoord]) -> Tuple[int, int, int, int]:
    """Axis-aligned bounding box for a non-empty set of red cells."""
    rs = [r for r, _ in red]
    cs = [c for _, c in red]
    return min(rs), max(rs), min(cs), max(cs)


def _is_red_corner_candidate(coord: GridCoord, red: Set[GridCoord], tol: int = 1) -> bool:
    """
    True if coord lies near one of the four corners of the red bounding box.

    This is our general definition of a "corner" placement for motion coverage:
    prioritise candidates close to the extrema of the remaining red blob.
    """
    if not red:
        return False
    r, c = coord
    rmin, rmax, cmin, cmax = _red_bbox(red)
    corners = [
        (rmin, cmin),
        (rmin, cmax),
        (rmax, cmin),
        (rmax, cmax),
    ]
    for cr, cc in corners:
        if abs(r - cr) <= tol and abs(c - cc) <= tol:
            return True
    return False


def _prefer_window_tie_by_target_axis(
    grid_height: int,
    grid_width: int,
    group_set: Set[GridCoord],
    interior_edge: List[GridCoord],
    mean_indoor_r: float,
    mean_indoor_c: float,
    cand: GridCoord,
    incumbent: GridCoord,
    opening_cheb_dist: Callable[[GridCoord], float],
) -> bool:
    """
    When two window-anchored candidates tie on red coverage, prefer the row/col closest
    to the first interior line past the opening (e.g. r = opening_rmax + 1 under a top
    lintel), not the farthest row inside the local radius (which also ties coverage).
    """
    if not interior_edge or not group_set:
        return False
    rs = [r for r, _ in group_set]
    cs = [c for _, c in group_set]
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    hspan = cmax - cmin
    vspan = rmax - rmin
    er = sum(r for r, _ in interior_edge) / len(interior_edge)
    ec = sum(c for _, c in interior_edge) / len(interior_edge)
    cr, cc = cand
    ir, ic = incumbent

    if hspan >= vspan:
        if er < mean_indoor_r:
            target_r = min(rmax + 1, grid_height - 1)
        elif er > mean_indoor_r:
            target_r = max(rmin - 1, 0)
        else:
            return False
        dc = abs(cr - target_r)
        di = abs(ir - target_r)
        if dc < di:
            return True
        if dc > di:
            return False
        # Same distance to lintel row: prefer farther from the opening along the wall
        # (room corner) instead of the jamb-adjacent cell with identical coverage.
        return opening_cheb_dist(cand) > opening_cheb_dist(incumbent)
    if vspan > hspan:
        if ec < mean_indoor_c:
            target_c = min(cmax + 1, grid_width - 1)
        elif ec > mean_indoor_c:
            target_c = max(cmin - 1, 0)
        else:
            return False
        dc = abs(cc - target_c)
        di = abs(ic - target_c)
        if dc < di:
            return True
        if dc > di:
            return False
        return opening_cheb_dist(cand) > opening_cheb_dist(incumbent)
    return False


def _place_pirs(
    scenario: Scenario,
    zones: List[Zone],
    devices: List[DevicePlacement],
    security_level: SecurityLevel,
) -> None:
    """
    Place PIR/PIRCAM-style motion devices (DeviceType.PIR) to clear remaining red zones.

    - Use a parameterised radius / field-of-view.
    - Only place sensors on indoor cells adjacent to walls (wall-mounted), preferring corners.
    - Greedy cover: repeatedly pick the wall candidate that covers the most remaining red cells
      until no red remains or no candidate improves coverage.

    If magnetics already removed all red zones, this function places no PIRs for any profile.
    """
    grid = scenario.grid_map
    cells = grid.cells
    cell_size = grid.cell_size_m

    pir_rules: PirRules = ALARM_RULES[security_level]["pir"]  # type: ignore[assignment]

    # Build indoor connectivity components once for the grid.
    component_ids_by_coord: Dict[GridCoord, int] = {}
    components = find_all_indoor_components(grid)
    for comp_idx, comp in enumerate(components):
        for coord in comp:
            component_ids_by_coord[coord] = comp_idx

    # Collect remaining red cells after magnetic suppression.
    remaining_red: Set[GridCoord] = {
        coord
        for z in zones
        if z.zone_type is ZoneType.RED
        for coord in z.cells
    }
    if not remaining_red:
        return

    # Motion geometry config (shared for PIR/PIRCAM).
    fov_deg = pir_rules.fov_deg
    radius_cells = capped_radius_cells(grid, pir_rules.radius_m, max_grid_fraction=1.0)
    half_fov_rad = math.radians(fov_deg / 2.0)

    # Build wall-adjacent indoor candidates, track their wall neighbours and corners (2+).
    candidates: List[GridCoord] = []
    wall_neighbours_by_coord: Dict[GridCoord, List[GridCoord]] = {}
    is_corner: Dict[GridCoord, bool] = {}

    for r in range(grid.height):
        for c in range(grid.width):
            if CellType(cells[r][c]) is not CellType.INDOOR:
                continue
            wall_neighbours = []
            for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    if CellType(cells[nr][nc]) is CellType.WALL:
                        wall_neighbours.append((nr, nc))
            if not wall_neighbours:
                continue
            coord = (r, c)
            candidates.append(coord)
            wall_neighbours_by_coord[coord] = wall_neighbours
            is_corner[coord] = len(wall_neighbours) >= 2

    if not candidates:
        return

    _indoor_cells = [
        (r, c)
        for r in range(grid.height)
        for c in range(grid.width)
        if CellType(cells[r][c]) is CellType.INDOOR
    ]
    if _indoor_cells:
        mean_indoor_r = sum(r for r, _ in _indoor_cells) / len(_indoor_cells)
        mean_indoor_c = sum(c for _, c in _indoor_cells) / len(_indoor_cells)
    else:
        mean_indoor_r = grid.height * 0.5
        mean_indoor_c = grid.width * 0.5

    # Orientations: into-room normal per adjacent wall. Corners get multiple (wider effective FOV).
    def orientations_for_cell(coord: GridCoord) -> List[Tuple[float, float]]:
        r, c = coord
        out: List[Tuple[float, float]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid.height and 0 <= nc < grid.width:
                if CellType(cells[nr][nc]) is CellType.WALL:
                    if dr == -1:
                        out.append((1.0, 0.0))
                    elif dr == 1:
                        out.append((-1.0, 0.0))
                    elif dc == -1:
                        out.append((0.0, 1.0))
                    elif dc == 1:
                        out.append((0.0, -1.0))
        if not out:
            return [(1.0, 0.0)]
        # Dedupe by normalized direction (keep unique look directions).
        seen: Set[Tuple[float, float]] = set()
        unique: List[Tuple[float, float]] = []
        for ox, oy in out:
            n = math.hypot(ox, oy)
            if n == 0:
                continue
            key = (round(ox / n, 6), round(oy / n, 6))
            if key not in seen:
                seen.add(key)
                unique.append((ox / n, oy / n))
        return unique if unique else [(1.0, 0.0)]

    # Precompute wall-aware coverage for each candidate using component+radius (walls block).
    coverage_cache: Dict[GridCoord, Set[GridCoord]] = {}
    for coord in candidates:
        pir_comp = component_ids_by_coord.get(coord)
        coverage_cache[coord] = _pir_coverage_component_radius(
            grid, cells, coord, radius_cells, component_ids_by_coord, pir_comp
        )

    used_coords: Set[GridCoord] = set()

    def _append_pir(coord: GridCoord, reasons: List[str]) -> None:
        pir_index = len([d for d in devices if d.device_type is DeviceType.PIR]) + 1
        devices.append(
            DevicePlacement(
                id=f"dev_pir_{pir_index}",
                device_type=DeviceType.PIR,
                cell=coord,
                room_id=None,
                orientation_deg=None,
                coverage_radius_cells=radius_cells,
                coverage_angle_deg=fov_deg,
                reasons=reasons,
                is_out_of_standard=False,
            )
        )

    # Phase A/B: opening-anchored PIR placement.
    # First try same-wall candidates (adjacent to the opening group), preferring
    # corner/extreme anchors. If not enough, expand to local candidates near the opening.
    opening_groups: List[Tuple[Set[GridCoord], List[GridCoord], str]] = []
    og_visited: Set[GridCoord] = set()
    for r in range(grid.height):
        for c in range(grid.width):
            coord = (r, c)
            if coord in og_visited:
                continue
            if not is_interior_opening_to_outdoor(grid, coord):
                continue
            group, ext_edge, _seeds = flood_fill_opening_group(grid, coord)
            og_visited.update(group)
            if not group or not ext_edge:
                continue
            group_set = set(group)
            interior_edge = [
                gc
                for gc in group
                if any(
                    CellType(cells[nr][nc]) is CellType.INDOOR
                    for nr, nc in [(gc[0] - 1, gc[1]), (gc[0] + 1, gc[1]), (gc[0], gc[1] - 1), (gc[0], gc[1] + 1)]
                    if 0 <= nr < grid.height and 0 <= nc < grid.width
                )
            ]
            kind = "door" if any(CellType(cells[gr][gc]) is CellType.DOOR for gr, gc in group) else "window"
            opening_groups.append((group_set, interior_edge, kind))

    influence_cells = capped_radius_cells(grid, 2.0, max_grid_fraction=0.15)
    local_max_dist = max(3.0, min(12.0, radius_cells / 4.0))

    def _min_dist_to_group(coord: GridCoord, group_set: Set[GridCoord]) -> float:
        cr, cc = coord
        return min(max(abs(cr - gr), abs(cc - gc)) for gr, gc in group_set)

    for group_set, interior_edge, kind in opening_groups:
        if not remaining_red:
            break
        group_red: Set[GridCoord] = {
            rc for rc in remaining_red if _min_dist_to_group(rc, group_set) <= influence_cells
        }
        if not group_red:
            continue

        endpoints: List[GridCoord] = []
        if interior_edge:
            rows = [r for r, _ in interior_edge]
            cols = [c for _, c in interior_edge]
            if (max(rows) - min(rows)) >= (max(cols) - min(cols)):
                endpoints = [min(interior_edge, key=lambda x: x[0]), max(interior_edge, key=lambda x: x[0])]
            else:
                endpoints = [min(interior_edge, key=lambda x: x[1]), max(interior_edge, key=lambda x: x[1])]

        def _endpoint_dist(cand: GridCoord) -> float:
            if not endpoints:
                return 9999.0
            cr, cc = cand
            return min(abs(cr - er) + abs(cc - ec) for er, ec in endpoints)

        # Only protect indoor components directly adjacent to this opening.
        adjacent_comps: Set[int] = set()
        for gr, gc in group_set:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    if CellType(cells[nr][nc]) is CellType.INDOOR:
                        ac = component_ids_by_coord.get((nr, nc))
                        if ac is not None:
                            adjacent_comps.add(ac)

        comp_red: Dict[int, Set[GridCoord]] = {}
        for rc in group_red:
            cid = component_ids_by_coord.get(rc)
            if cid is not None and cid in adjacent_comps:
                comp_red.setdefault(cid, set()).add(rc)

        reason_tag = "protect_exterior_door" if kind == "door" else "protect_exterior_window"

        for cid, cr_set in comp_red.items():
            cr_set = cr_set & remaining_red
            if not cr_set:
                continue

            comp_cands = [
                c for c in candidates
                if c not in used_coords
                and component_ids_by_coord.get(c) == cid
            ]
            if not comp_cands:
                continue

            best_any = max(comp_cands, key=lambda c: len(coverage_cache[c] & cr_set))
            best_any_score = len(coverage_cache[best_any] & cr_set)
            if best_any_score == 0:
                continue

            chosen: Optional[GridCoord] = None

            # Priority 1: corner — prefer two real room walls (no window-jamb wall); else any corner.
            corner_cands = [c for c in comp_cands if is_corner.get(c, False)]
            if corner_cands:
                real_corner_cands = [
                    c
                    for c in corner_cands
                    if _is_real_room_wall_corner_pir(cells, grid, c, wall_neighbours_by_coord.get(c, []))
                ]

                def _corner_key_near_opening(c: GridCoord) -> Tuple[int, float]:
                    return (len(coverage_cache[c] & cr_set), -_endpoint_dist(c))

                def _corner_key_real_wall_preferred(c: GridCoord) -> Tuple[int, float, float]:
                    """
                    Among equal coverage: stay in the same wall band as the opening (min perpendicular
                    offset), then move along that wall away from the glazing (max Chebyshev distance
                    to the opening group). Avoids picking a far corner on another wall (e.g. row 42)
                    or a jamb-adjacent real corner on the window end.
                    """
                    cov = len(coverage_cache[c] & cr_set)
                    cr, cc = c
                    if not interior_edge:
                        return (cov, 0.0, _min_dist_to_group(c, group_set))
                    rows_ie = [r for r, _ in interior_edge]
                    cols_ie = [c for _, c in interior_edge]
                    row_span = max(rows_ie) - min(rows_ie)
                    col_span = max(cols_ie) - min(cols_ie)
                    # Horizontal glazing (wider along cols): depth into room is along rows.
                    # Vertical glazing: depth is along cols.
                    if col_span > row_span:
                        med_r = sum(rows_ie) / len(rows_ie)
                        perp_off = abs(float(cr) - med_r)
                    else:
                        med_c = sum(cols_ie) / len(cols_ie)
                        perp_off = abs(float(cc) - med_c)
                    return (cov, -perp_off, _min_dist_to_group(c, group_set))

                if real_corner_cands:
                    best_corner = max(real_corner_cands, key=_corner_key_real_wall_preferred)
                    corner_score = len(coverage_cache[best_corner] & cr_set)
                    if corner_score >= 0.60 * best_any_score:
                        chosen = best_corner
                    else:
                        # Real corners exist but none reach 60 % — fall back to window-jamb corners.
                        best_any_corner = max(corner_cands, key=_corner_key_near_opening)
                        ac_score = len(coverage_cache[best_any_corner] & cr_set)
                        if ac_score >= 0.60 * best_any_score:
                            chosen = best_any_corner
                else:
                    best_corner = max(corner_cands, key=_corner_key_near_opening)
                    corner_score = len(coverage_cache[best_corner] & cr_set)
                    if corner_score >= 0.60 * best_any_score:
                        chosen = best_corner

            # Priority 2: on-wall of opening (adjacent to opening group).
            if chosen is None:
                on_wall = [
                    c for c in comp_cands
                    if any(
                        (nr, nc) in group_set
                        for nr, nc in [(c[0]-1, c[1]), (c[0]+1, c[1]),
                                       (c[0], c[1]-1), (c[0], c[1]+1)]
                        if 0 <= nr < grid.height and 0 <= nc < grid.width
                    )
                ]
                if on_wall:
                    best_wall = max(on_wall, key=lambda c: (
                        len(coverage_cache[c] & cr_set), -_endpoint_dist(c)
                    ))
                    wall_score = len(coverage_cache[best_wall] & cr_set)
                    if wall_score >= 0.60 * best_any_score:
                        chosen = best_wall

            # Priority 3: max coverage anywhere in component.
            if chosen is None:
                chosen = best_any

            used_coords.add(chosen)
            covered_now = coverage_cache[chosen] & cr_set
            remaining_red -= covered_now
            _append_pir(chosen, ["pir", "cover_red_zone", "local_opening_fallback", reason_tag])

    # Phase C) Global greedy for any residual red not solved by opening-anchored strategy.
    while remaining_red:
        best_coord: Optional[GridCoord] = None
        best_score = 0
        # First, restrict to "red-corner" candidates if any of them can still see red.
        corner_candidates: List[GridCoord] = []
        if remaining_red:
            for coord in candidates:
                if coord in used_coords:
                    continue
                if not _is_red_corner_candidate(coord, remaining_red):
                    continue
                if coverage_cache[coord] & remaining_red:
                    corner_candidates.append(coord)

        active_candidates = corner_candidates if corner_candidates else candidates

        for coord in active_candidates:
            if coord in used_coords:
                continue
            cov = coverage_cache[coord]
            score = len(cov & remaining_red)
            if score == 0:
                continue
            coord_is_corner = is_corner.get(coord, False)
            best_is_corner = is_corner.get(best_coord, False) if best_coord is not None else False
            if (
                best_coord is None
                or score > best_score
                or (score == best_score and coord_is_corner and not best_is_corner)
            ):
                best_coord = coord
                best_score = score

        if best_coord is None or best_score == 0:
            break  # no improvement possible

        used_coords.add(best_coord)
        # Newly covered red cells: use the same wall-aware coverage geometry.
        newly_covered: Set[GridCoord] = coverage_cache[best_coord] & remaining_red
        remaining_red -= newly_covered

        _append_pir(best_coord, ["pir", "cover_red_zone", "global_fallback"])

        if not remaining_red:
            break

