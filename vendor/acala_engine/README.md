# acala_engine – Deterministic Alarm Planning Engine

Takes a floorplan **matrix** (2D grid of cell types) and produces a full **InstallationProposal** with zones and device placements (panel, keyboard, magnetics, PIR, sirens).

## Quick start

```python
from acala_engine import build_scenario, make_element, make_room, plan_installation

# Build a Scenario from your matrix (the parallel project provides this)
scenario = build_scenario(
    cells=matrix,          # List[List[int]]: -1=outdoor, 0=indoor, 1=wall, 2=door, 3=window, 4=prohibited
    cell_size_m=0.5,       # meters per cell edge
    security_level="optimal",  # "min" | "optimal" | "max"
    rooms=[
        make_room(id="r1", cells=[(2,1),(2,2),(3,1),(3,2)], room_type="bedroom"),
    ],
    elements=[
        make_element(id="e1", element_type="main_entry", position=(1, 4)),
        make_element(id="e2", element_type="electric_board", position=(3, 2)),
        make_element(id="e3", element_type="heat_source", position=(5, 4)),
    ],
)

# Run the planner
proposal = plan_installation(scenario)

# proposal.devices  → List[DevicePlacement] with panel, keyboard, magnetics, PIRs, sirens
# proposal.zones    → List[Zone] with red and prohibited zones
# Each device has .reasons (explainable) and .is_out_of_standard
```

## Serialize / deserialize proposals

```python
from acala_engine import installation_to_json, installation_from_json

json_str = installation_to_json(proposal)
restored = installation_from_json(json_str)
```

## Debug rendering (ASCII)

```python
from acala_engine import render_scenario

print(render_scenario(scenario, zones=proposal.zones, devices=proposal.devices))
```

## Input contract

The engine expects a `Scenario` with:

| Field | Type | Description |
|-------|------|-------------|
| `cells` | `List[List[int]]` | 2D matrix with CellType values: -1=outdoor, 0=indoor, 1=wall, 2=door, 3=window, 4=prohibited |
| `cell_size_m` | `float` | Physical size of one cell edge in meters |
| `security_level` | `str` or `SecurityLevel` | `"min"` / `"optimal"` / `"max"` |
| `rooms` | `List[Room]` | Optional room definitions (cells + type) |
| `elements` | `List[MapElement]` | Semantic markers: `main_entry`, `electric_board`, `heat_source`, `cold_source` |

Key rules:
- **Doors/windows are structural**: encoded in the `cells` matrix as values 2/3, NOT as elements
- **Main entry is semantic**: an element of type `"main_entry"` that must sit on a door cell (value 2)
- **Outdoor ring**: exterior doors/windows must touch at least one outdoor cell (-1) to generate red zones
- **Rooms avoid walls/outdoor**: room cell lists must not reference wall (1) or outdoor (-1) cells

## Output: InstallationProposal

| Field | Type | Description |
|-------|------|-------------|
| `devices` | `List[DevicePlacement]` | Panel, keyboard, magnetics, PIR, sirens with positions, reasons |
| `zones` | `List[Zone]` | Red (must-cover) and prohibited (no-device) zones |
| `grid_map`, `rooms`, `elements` | — | Echoed from input |

## Security profiles

| Profile | Magnetics | PIR door-anchor | Indoor siren | Outdoor siren |
|---------|-----------|-----------------|--------------|---------------|
| **min** | Main entry only | Yes | Yes | No |
| **optimal** | All exterior doors | Yes | Yes | Yes |
| **max** | All doors + windows | No | Yes | Yes |

## Project structure

```
src/acala_engine/
  __init__.py          # public API
  model.py             # enums + dataclasses (the contract)
  scenario_builder.py  # build_scenario(), make_element(), make_room()
  grid_utils.py        # spatial primitives (neighbors, flood fill, radius)
  zones.py             # red + prohibited zone generation
  alarm_rules.py       # per-profile rule configuration
  engine_alarm.py      # main planner: Scenario → InstallationProposal
  debug_render.py      # ASCII renderer
  io_json.py           # proposal serialization (to/from JSON)
tests/
  test_model.py
  test_grid_utils.py
  test_zones.py
  test_engine_alarm.py
  test_scenario_builder.py
  test_io_json.py
docs/
  model.md             # full type documentation
  alarm_engine.md      # engine behaviour spec
```

## Running tests

```bash
pip install pytest
cd export/acala_engine
pytest tests/ -v
```
