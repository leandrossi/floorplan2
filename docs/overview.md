# ACALA Core – Overview

MVP for automated residential alarm installation from a floorplan: **image → matrix → rooms/zones → device placement**.

## What this repo does (MVP)

1. **Matrix representation** – Floorplan image is turned into a grid where each cell has a type: outdoor, indoor, wall, door, window, prohibited.
2. **Rooms and zones** – Indoor cells are grouped into rooms; red/gray/prohibited zones are built purely from the matrix (doors/windows as `CellType` values, hazards as elements). Red zones come from exterior-accessible openings and expand through indoor connectivity while respecting walls.
3. **Installation proposal** – Rule engine places panel, keyboard, magnetics, PIR/PIRCAM, sirens according to a chosen security level (max / optimal / min).

No auth, no CRUD, no AR in this phase – only the core logic and data structures needed to test the concept.

## Core conventions / invariants

These are enforced by validations in `io_json.load_fixture` and used across the engine:

- **Doors/windows are structural** – they must be encoded only in the `cells` matrix (`CellType.DOOR` / `CellType.WINDOW`), never as `MapElementType.DOOR` / `MapElementType.WINDOW` elements.
- **Main entry is semantic** – fixtures tag one `elements[].type == "main_entry"`; it maps to `MapElementType.DOOR` with `is_main_entry=True` and must sit on a `"door"` cell.
- **Outdoor ring for façades** – any door/window that should create a red zone must touch at least one `OUTDOOR` neighbour in the matrix; most synthetic fixtures use an outdoor perimeter ring.
- **Rooms avoid walls/outdoor** – room cell lists may only reference indoor-ish cells (indoor, door, window, hazards), never `OUTDOOR` or `WALL`.
- **Red zones are wall-aware** – red influence from exterior openings is computed via an indoor-only flood fill limited by a radius; it cannot jump through walls into other rooms.
- **Magnetics clear their openings (locally)** – when a magnetic is placed on an exterior door/window group, only the red cells within a small radius around that structural opening are removed. Red produced by other openings in the same zone (e.g. windows in the same room) survives until covered by another device.
- **PIR/PIRCAM coverage is component-based and wall-blocked** – motion devices are wall-mounted and corner-preferred. Their coverage is modelled as an ~8 m Chebyshev radius over indoor cells only, restricted to the PIR’s indoor connectivity component (computed from the grid). Walls and indoor doors break components, so a PIR in a corridor cannot “see” into a bedroom behind a door.
- **No RED left after devices** – for alarm planning, the combination of magnetics + PIR/PIRCAM must eliminate all RED cells for the chosen `SecurityLevel` (MIN/OPTIMAL/MAX). The engine uses a greedy, corner-first set cover over candidate PIR locations to achieve this with as few devices as possible.

## Docs (export to PDF for reading)

| Document | Content |
|----------|---------|
| [model.md](model.md) | Full explanation of every type in `model.py` (enums, GridMap, Room, Zone, MapElement, DevicePlacement, InstallationProposal, Scenario). |
| overview.md | This file – high-level picture. |
| scripts/render_fixture.py | CLI to render fixtures as ASCII, with original grid, raw zones, and device proposals per security profile. |
| scripts/debug_pir_steps.py | Debug CLI that shows step-by-step PIR placement: ASCII + red stats after each PIR, useful to understand coverage behaviour on a given fixture. |

Future: `alarm_engine.md`, `grid_utils.md`, `io_json.md` as we add those modules.

## Code layout

```
src/acala_core/
  __init__.py      # re-exports core model types (and later, planner entrypoints)
  model.py         # enums + dataclasses: grid, rooms, zones, elements, devices, Scenario, proposal
  io_json.py       # JSON I/O: synthetic fixtures -> Scenario, proposals <-> JSON
  grid_utils.py    # generic grid helpers (bounds, neighbours, components, simple radius)
  debug_render.py  # ASCII renderer for GridMap / Scenario (for fast visual debugging)
  zones.py         # zone generation (currently: red zones from exterior-accessible openings)
  engine_alarm.py  # alarm planner entrypoint: Scenario -> InstallationProposal (zones now, devices next)
docs/
  overview.md
  model.md
scripts/
  render_fixture.py  # (next) CLI to load a fixture and print/render it
```

## How to read the code

- **model.py** – Single source of truth for the matrix encoding and the shape of an installation result. Start here; the rest of the code uses these types.
- **docs/model.md** – One section per symbol (`model.CellType`, `model.GridMap`, etc.). Use it to understand each type and to generate a PDF for offline reading.
