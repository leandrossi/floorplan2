"""
Data model for floorplan grid, rooms, zones, map elements, and installation proposals.

All types here are the single source of truth for the matrix encoding and
the structure returned by the alarm/smoke rule engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import List, Optional, Tuple


class CellType(IntEnum):
    """
    Integer encoding for each grid cell.
    Stored in GridMap.cells; use this enum to interpret values.
    """
    OUTDOOR = -1     # outside the building
    INDOOR = 0       # walkable indoor space
    WALL = 1         # wall or solid obstacle
    DOOR = 2         # door opening
    WINDOW = 3       # window opening
    PROHIBITED = 4   # indoor cell where devices must not be installed


class ZoneType(Enum):
    """Logical categories of areas used by the rule engines."""
    RED = "red"                   # must be covered (unsafe)
    GRAY = "gray"                 # nice-to-cover, not mandatory
    PROHIBITED = "prohibited"     # must not place devices here


class RoomType(Enum):
    """Semantic classification of rooms (matches spec list of environments)."""
    UNKNOWN = "unknown"
    KITCHEN = "kitchen"
    DEPOSIT = "deposit"
    LAUNDRY = "laundry"
    LIVING = "living"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    GARDEN = "garden"
    OFFICE = "office"
    HALL = "hall"
    CORRIDOR = "corridor"


class SecurityLevel(Enum):
    """Global security profile for one installation (max / optimal / min)."""
    MAX = "max"
    OPTIMAL = "optimal"
    MIN = "min"


class ProductType(Enum):
    """Which product the proposal is for (alarm vs smoke)."""
    ALARM = "alarm"
    SMOKE = "smoke"


class MapElementType(Enum):
    """Static elements on the map that influence placement rules."""
    DOOR = "door"
    WINDOW = "window"
    ELECTRIC_BOARD = "electric_board"
    HEAT_SOURCE = "heat_source"
    COLD_SOURCE = "cold_source"
    FURNITURE = "furniture"
    WIFI_AP = "wifi_ap"


class DeviceType(Enum):
    """Installable device types (panel, sensors, sirens, etc.)."""
    PANEL = "panel"
    KEYBOARD = "keyboard"
    PIR = "pir"
    PIRCAM = "pircam"
    MAGNETIC = "magnetic"
    SIREN_INDOOR = "siren_indoor"
    SIREN_OUTDOOR = "siren_outdoor"
    SMOKE_SENSOR = "smoke_sensor"


# (row, col) in grid indices
GridCoord = Tuple[int, int]


@dataclass
class GridMap:
    """Discrete floorplan matrix and its physical scale."""
    cells: List[List[int]]       # values from CellType
    cell_size_m: float            # meters per cell side
    height: int
    width: int
    origin_m: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Room:
    """One connected indoor region with optional type and criticality."""
    id: str
    cells: List[GridCoord]
    room_type: RoomType = RoomType.UNKNOWN
    is_critical: bool = True


@dataclass
class Zone:
    """Red / gray / prohibited region used by rule engines."""
    id: str
    zone_type: ZoneType
    cells: List[GridCoord]


@dataclass
class MapElement:
    """Semantic element on the map (door, window, electric board, heat source, etc.)."""
    id: str
    element_type: MapElementType
    cells: List[GridCoord]
    room_id: Optional[str] = None
    # True when this element is the main entry door for the dwelling.
    is_main_entry: bool = False


@dataclass
class DevicePlacement:
    """One proposed device location with optional coverage and explanation."""
    id: str
    device_type: DeviceType
    cell: GridCoord
    room_id: Optional[str] = None
    orientation_deg: Optional[float] = None
    coverage_radius_cells: Optional[float] = None
    coverage_angle_deg: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    is_out_of_standard: bool = False


@dataclass
class InstallationProposal:
    """Full result of running the planner for one product on one map."""
    product_type: ProductType
    security_level: SecurityLevel
    grid_map: GridMap
    rooms: List[Room]
    zones: List[Zone]
    elements: List[MapElement]
    devices: List[DevicePlacement]


@dataclass
class Scenario:
    """
    One planning input fixture: grid + rooms + elements + global settings.

    This is what synthetic JSON fixtures load into before zone generation
    and device planning run.
    """
    fixture_name: str
    cell_size_m: float
    width: int
    height: int
    security_level: SecurityLevel
    grid_map: GridMap
    rooms: List[Room]
    elements: List[MapElement]
    notes: str = ""
