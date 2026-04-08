"""
JSON serialization / deserialization for InstallationProposal.

This module handles only the OUTPUT side: converting proposals to/from JSON.
Input (matrix → Scenario) is handled by the consuming project.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .model import (
    CellType,
    GridMap,
    Room,
    Zone,
    MapElement,
    DevicePlacement,
    InstallationProposal,
    GridCoord,
    ZoneType,
    RoomType,
    SecurityLevel,
    ProductType,
    MapElementType,
    DeviceType,
)


def _enum_to_str(value) -> str:
    return None if value is None else value.value


def _str_to_enum(enum_cls, value: str):
    return enum_cls(value)


def _coords_from_list(coords: List[List[int]]) -> List[GridCoord]:
    return [(int(r), int(c)) for (r, c) in coords]


# ---------- Proposal → dict / JSON ----------

def installation_to_dict(installation: InstallationProposal) -> Dict[str, Any]:
    """Convert InstallationProposal to a pure-JSON-serialisable dict."""
    gm = installation.grid_map

    return {
        "product_type": _enum_to_str(installation.product_type),
        "security_level": _enum_to_str(installation.security_level),
        "grid_map": {
            "height": gm.height,
            "width": gm.width,
            "cell_size_m": gm.cell_size_m,
            "origin_m": list(gm.origin_m),
            "cells": gm.cells,
        },
        "rooms": [
            {
                "id": r.id,
                "room_type": _enum_to_str(r.room_type),
                "is_critical": r.is_critical,
                "cells": [list(c) for c in r.cells],
            }
            for r in installation.rooms
        ],
        "zones": [
            {
                "id": z.id,
                "zone_type": _enum_to_str(z.zone_type),
                "cells": [list(c) for c in z.cells],
            }
            for z in installation.zones
        ],
        "elements": [
            {
                "id": e.id,
                "element_type": _enum_to_str(e.element_type),
                "room_id": e.room_id,
                "cells": [list(c) for c in e.cells],
            }
            for e in installation.elements
        ],
        "devices": [
            {
                "id": d.id,
                "device_type": _enum_to_str(d.device_type),
                "room_id": d.room_id,
                "cell": list(d.cell),
                "orientation_deg": d.orientation_deg,
                "coverage_radius_cells": d.coverage_radius_cells,
                "coverage_angle_deg": d.coverage_angle_deg,
                "reasons": list(d.reasons),
                "is_out_of_standard": d.is_out_of_standard,
            }
            for d in installation.devices
        ],
    }


def installation_to_json(installation: InstallationProposal, *, indent: int = 2) -> str:
    """Convert InstallationProposal directly to a JSON string."""
    data = installation_to_dict(installation)
    return json.dumps(data, indent=indent, sort_keys=False)


# ---------- dict / JSON → Proposal ----------

def installation_from_dict(data: Dict[str, Any]) -> InstallationProposal:
    """Reconstruct InstallationProposal from a dict (inverse of installation_to_dict)."""
    grid = data["grid_map"]
    grid_map = GridMap(
        cells=[[int(v) for v in row] for row in grid["cells"]],
        cell_size_m=float(grid["cell_size_m"]),
        height=int(grid["height"]),
        width=int(grid["width"]),
        origin_m=(float(grid["origin_m"][0]), float(grid["origin_m"][1])),
    )

    rooms = [
        Room(
            id=r["id"],
            cells=_coords_from_list(r["cells"]),
            room_type=_str_to_enum(RoomType, r["room_type"]),
            is_critical=bool(r["is_critical"]),
        )
        for r in data.get("rooms", [])
    ]

    zones = [
        Zone(
            id=z["id"],
            zone_type=_str_to_enum(ZoneType, z["zone_type"]),
            cells=_coords_from_list(z["cells"]),
        )
        for z in data.get("zones", [])
    ]

    elements = [
        MapElement(
            id=e["id"],
            element_type=_str_to_enum(MapElementType, e["element_type"]),
            cells=_coords_from_list(e["cells"]),
            room_id=e.get("room_id"),
        )
        for e in data.get("elements", [])
    ]

    devices = [
        DevicePlacement(
            id=d["id"],
            device_type=_str_to_enum(DeviceType, d["device_type"]),
            cell=tuple(d["cell"]),
            room_id=d.get("room_id"),
            orientation_deg=d.get("orientation_deg"),
            coverage_radius_cells=d.get("coverage_radius_cells"),
            coverage_angle_deg=d.get("coverage_angle_deg"),
            reasons=list(d.get("reasons", [])),
            is_out_of_standard=bool(d.get("is_out_of_standard", False)),
        )
        for d in data.get("devices", [])
    ]

    return InstallationProposal(
        product_type=_str_to_enum(ProductType, data["product_type"]),
        security_level=_str_to_enum(SecurityLevel, data["security_level"]),
        grid_map=grid_map,
        rooms=rooms,
        zones=zones,
        elements=elements,
        devices=devices,
    )


def installation_from_json(raw: str) -> InstallationProposal:
    """Parse InstallationProposal from a JSON string."""
    data = json.loads(raw)
    return installation_from_dict(data)
