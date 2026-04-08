"""
Debug rendering for synthetic fixtures and planner inputs.

ASCII-based, intentionally simple and dependency-free.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from .model import (
    CellType,
    GridCoord,
    GridMap,
    MapElement,
    MapElementType,
    Scenario,
    DevicePlacement,
    DeviceType,
    Zone,
    ZoneType,
)


_CELL_CHAR = {
    CellType.OUTDOOR: " ",
    CellType.INDOOR: ".",
    CellType.WALL: "#",
    CellType.DOOR: "D",
    CellType.WINDOW: "W",
    CellType.PROHIBITED: "X",
}

_ELEMENT_CHAR = {
    MapElementType.DOOR: "D",
    MapElementType.WINDOW: "W",
    MapElementType.ELECTRIC_BOARD: "E",
    MapElementType.HEAT_SOURCE: "H",
    MapElementType.COLD_SOURCE: "C",
    MapElementType.FURNITURE: "F",
    MapElementType.WIFI_AP: "@",
}

_ZONE_CHAR = {
    ZoneType.RED: "R",
    ZoneType.PROHIBITED: "X",
}

_DEVICE_CHAR = {
    DeviceType.PANEL: "P",
    DeviceType.KEYBOARD: "K",
    DeviceType.MAGNETIC: "M",
    DeviceType.PIR: "I",
    DeviceType.PIRCAM: "C",
    DeviceType.SIREN_INDOOR: "S",
    DeviceType.SIREN_OUTDOOR: "O",
    DeviceType.SMOKE_SENSOR: "S",
}


def _base_char_for_cell(grid: GridMap, coord: GridCoord) -> str:
    ct = CellType(grid.cells[coord[0]][coord[1]])
    return _CELL_CHAR.get(ct, "?")


def _overlay_elements(base: List[List[str]], elements: Sequence[MapElement]) -> None:
    for elem in elements:
        ch = _ELEMENT_CHAR.get(elem.element_type)
        if ch is None:
            continue
        for (r, c) in elem.cells:
            if 0 <= r < len(base) and 0 <= c < len(base[0]):
                base[r][c] = ch


def _overlay_zones(base: List[List[str]], zones: Sequence[Zone]) -> None:
    for zone in zones:
        ch = _ZONE_CHAR.get(zone.zone_type)
        if ch is None:
            continue
        for (r, c) in zone.cells:
            if 0 <= r < len(base) and 0 <= c < len(base[0]):
                base[r][c] = ch


def _overlay_devices(base: List[List[str]], devices: Sequence[DevicePlacement]) -> None:
    for dev in devices:
        ch = _DEVICE_CHAR.get(dev.device_type)
        if ch is None:
            continue
        r, c = dev.cell
        if 0 <= r < len(base) and 0 <= c < len(base[0]):
            base[r][c] = ch


def render_grid(
    grid: GridMap,
    *,
    elements: Optional[Sequence[MapElement]] = None,
    zones: Optional[Sequence[Zone]] = None,
    devices: Optional[Sequence[DevicePlacement]] = None,
) -> str:
    """
    Render the raw grid (and optionally elements, zones, and devices) as ASCII.

    Legend (MVP):
      ' ' : outdoor
      '#' : wall
      '.' : indoor
      'D' : door
      'W' : window
      'X' : prohibited cell or prohibited zone
      'E' : electric board element
      'H' : heat source element
      'C' : cold source element
      'P' : panel device
      'K' : keyboard device
      'M' : magnetic contact on opening
      'I' : PIR motion sensor
    """
    rows = grid.height
    cols = grid.width

    canvas: List[List[str]] = [
        [_base_char_for_cell(grid, (r, c)) for c in range(cols)]
        for r in range(rows)
    ]

    if elements:
        _overlay_elements(canvas, elements)
    if zones:
        _overlay_zones(canvas, zones)
    if devices:
        _overlay_devices(canvas, devices)

    return "\n".join("".join(row) for row in canvas)


def render_scenario(
    scenario: Scenario,
    *,
    zones: Optional[Sequence[Zone]] = None,
    devices: Optional[Sequence[DevicePlacement]] = None,
) -> str:
    """Convenience wrapper to render a complete Scenario (optionally with zones)."""
    header = (
        f"fixture={scenario.fixture_name}  "
        f"size={scenario.width}x{scenario.height}  "
        f"security={scenario.security_level.value}"
    )
    body = render_grid(
        scenario.grid_map,
        elements=scenario.elements,
        zones=zones,
        devices=devices,
    )
    return header + "\n" + body

