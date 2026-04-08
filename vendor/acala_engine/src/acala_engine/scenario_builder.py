"""
Scenario builder: construct a Scenario from raw matrix data.

The parallel project produces the matrix (cells, rooms, elements).
This module provides a clean way to assemble a Scenario without
needing the old fixture JSON format.
"""

from __future__ import annotations

from typing import List, Optional

from .model import (
    CellType,
    GridCoord,
    GridMap,
    MapElement,
    MapElementType,
    Room,
    RoomType,
    Scenario,
    SecurityLevel,
)


def build_scenario(
    *,
    cells: List[List[int]],
    cell_size_m: float,
    security_level: str | SecurityLevel = "optimal",
    rooms: Optional[List[Room]] = None,
    elements: Optional[List[MapElement]] = None,
    fixture_name: str = "from_matrix",
    notes: str = "",
) -> Scenario:
    """
    Build a Scenario from a raw integer matrix and optional metadata.

    Args:
        cells: 2D list of ints matching CellType values.
                -1=outdoor, 0=indoor, 1=wall, 2=door, 3=window, 4=prohibited.
        cell_size_m: Physical size of one cell edge in meters.
        security_level: "min" / "optimal" / "max" or SecurityLevel enum.
        rooms: Pre-built Room list. Pass None/[] if not available.
        elements: Pre-built MapElement list (main_entry, electric_board,
                  heat_source, cold_source). Pass None/[] if not available.
        fixture_name: Human label for the scenario.
        notes: Optional free-text.

    Returns:
        A ready-to-plan Scenario.

    Raises:
        ValueError: If cells dimensions are inconsistent.
    """
    if not cells or not cells[0]:
        raise ValueError("cells matrix must be non-empty")

    height = len(cells)
    width = len(cells[0])
    if any(len(row) != width for row in cells):
        raise ValueError("All rows in cells must have the same width")

    if isinstance(security_level, str):
        security_level = SecurityLevel(security_level)

    grid_map = GridMap(
        cells=cells,
        cell_size_m=cell_size_m,
        height=height,
        width=width,
        origin_m=(0.0, 0.0),
    )

    return Scenario(
        fixture_name=fixture_name,
        cell_size_m=cell_size_m,
        width=width,
        height=height,
        security_level=security_level,
        grid_map=grid_map,
        rooms=rooms or [],
        elements=elements or [],
        notes=notes,
    )


def make_element(
    *,
    id: str,
    element_type: str | MapElementType,
    position: GridCoord,
    room_id: Optional[str] = None,
    is_main_entry: bool = False,
) -> MapElement:
    """
    Convenience to create a MapElement from simple args.

    element_type can be a string ("main_entry", "electric_board",
    "heat_source", "cold_source") or a MapElementType enum.
    """
    if isinstance(element_type, str):
        mapping = {
            "main_entry": MapElementType.DOOR,
            "electric_board": MapElementType.ELECTRIC_BOARD,
            "heat_source": MapElementType.HEAT_SOURCE,
            "cold_source": MapElementType.COLD_SOURCE,
        }
        et = mapping.get(element_type.strip().lower().replace(" ", "_"))
        if et is None:
            raise ValueError(f"Unknown element type: {element_type!r}")
        if element_type.strip().lower().replace(" ", "_") == "main_entry":
            is_main_entry = True
    else:
        et = element_type

    return MapElement(
        id=id,
        element_type=et,
        cells=[position],
        room_id=room_id,
        is_main_entry=is_main_entry,
    )


def make_room(
    *,
    id: str,
    cells: List[GridCoord],
    room_type: str | RoomType = "unknown",
    is_critical: bool = True,
) -> Room:
    """Convenience to create a Room from simple args."""
    if isinstance(room_type, str):
        try:
            rt = RoomType(room_type)
        except ValueError:
            rt = RoomType.UNKNOWN
    else:
        rt = room_type

    return Room(id=id, cells=cells, room_type=rt, is_critical=is_critical)
