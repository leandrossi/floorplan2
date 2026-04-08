"""
acala_engine – Deterministic alarm planning engine.

Input:  Scenario (matrix + rooms + elements + security level)
Output: InstallationProposal (zones + device placements with reasons)

Usage:
    from acala_engine import build_scenario, plan_installation

    scenario = build_scenario(cells=matrix, cell_size_m=0.5, security_level="optimal")
    proposal = plan_installation(scenario)
"""

from .model import (  # noqa: F401
    CellType,
    ZoneType,
    RoomType,
    SecurityLevel,
    ProductType,
    MapElementType,
    DeviceType,
    GridCoord,
    GridMap,
    Room,
    Zone,
    MapElement,
    DevicePlacement,
    InstallationProposal,
    Scenario,
)
from .engine_alarm import plan_installation  # noqa: F401
from .scenario_builder import build_scenario, make_element, make_room  # noqa: F401
from .io_json import (  # noqa: F401
    installation_to_dict,
    installation_to_json,
    installation_from_dict,
    installation_from_json,
)
from .debug_render import render_grid, render_scenario  # noqa: F401

__all__ = [
    # Enums
    "CellType",
    "ZoneType",
    "RoomType",
    "SecurityLevel",
    "ProductType",
    "MapElementType",
    "DeviceType",
    # Data structures
    "GridCoord",
    "GridMap",
    "Room",
    "Zone",
    "MapElement",
    "DevicePlacement",
    "InstallationProposal",
    "Scenario",
    # Engine
    "plan_installation",
    # Scenario construction
    "build_scenario",
    "make_element",
    "make_room",
    # Serialization
    "installation_to_dict",
    "installation_to_json",
    "installation_from_dict",
    "installation_from_json",
    # Debug
    "render_grid",
    "render_scenario",
]
