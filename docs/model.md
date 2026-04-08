# Model – Data structures and enums

This document explains every type in `src/acala_core/model.py`. Use it for daily reading or export to PDF. Section headings match the code symbols so you can jump between doc and code quickly.

---

## model.CellType

**What it is:** Integer enum that defines the meaning of each cell value in the grid matrix.

**Values:**

| Value | Name       | Meaning |
|-------|------------|---------|
| -1    | OUTDOOR    | Outside the building. In synthetic fixtures this often forms a perimeter ring so façade doors/windows can “see” the outside. |
| 0     | INDOOR     | Walkable indoor space. |
| 1     | WALL       | Wall or solid obstacle. |
| 2     | DOOR       | Door opening (always represented structurally in the matrix, not as an element type). |
| 3     | WINDOW     | Window opening (always represented structurally in the matrix, not as an element type). |
| 4     | PROHIBITED | Indoor cell where devices must not be installed (e.g. near heat/cold). |

**Why:** Keeps the raw matrix as a simple 2D list of integers while giving each number a clear semantic name. All algorithms that read the grid use these constants instead of magic numbers. For Milestone -1, “exterior openings” are detected purely from `CellType.DOOR` / `CellType.WINDOW` cells that are 4-neighbour adjacent to at least one `OUTDOOR` cell; red zones are then expanded from those openings.

**Code location:** `model.py` – `class CellType(IntEnum)`.

---

## model.ZoneType

**What it is:** Logical classification of “areas of interest” over the grid (red / gray / prohibited).

**Values:**

- **RED** – Must be covered by at least one sensor (unsafe area, e.g. in front of an exterior-accessible door/window). Built from structural openings that are adjacent to `OUTDOOR` and expanded through connected indoor cells only (wall-aware flood fill with a bounded radius).
- **GRAY** – Nice to cover but not strictly required.
- **PROHIBITED** – Valid indoor space where devices must not be placed (e.g. around stoves, fridges). Built around heat/cold sources.

**Why:** The rule engine reasons at the zone level (“all RED zones must be inside a PIR coverage cone, and PROHIBITED must stay device-free”) instead of cell-by-cell. Matches the red/gray/prohibited concepts from the ACALA spec.

**Code location:** `model.py` – `class ZoneType(Enum)`.

---

## model.RoomType

**What it is:** Semantic label for a room (kitchen, bedroom, hall, etc.).

**Values:** UNKNOWN, KITCHEN, DEPOSIT, LAUNDRY, LIVING, BEDROOM, BATHROOM, GARDEN, OFFICE, HALL, CORRIDOR.

**Usage:** Attached to each `Room`. Used by product-specific rules (e.g. “exclude bathrooms from certain sensor rules”, “panel preferred in deposit/laundry”).

**Code location:** `model.py` – `class RoomType(Enum)`.

---

## model.SecurityLevel

**What it is:** Global security profile for one installation proposal.

**Values:** MAX, OPTIMAL, MIN (from the spec).

**Why:** The alarm (and later smoke) rule engine uses this to decide how many devices to place and where (e.g. MAX = magnetics on all exterior openings + full red-zone coverage; MIN = only people’s paths).

**Code location:** `model.py` – `class SecurityLevel(Enum)`.

---

## model.ProductType

**What it is:** Which logical product the proposal is for.

**Values:** ALARM, SMOKE.

**Why:** Same grid and same rooms/zones can feed different rule engines; this flag tells the consumer what kind of proposal they are looking at.

**Code location:** `model.py` – `class ProductType(Enum)`.

---

## model.MapElementType

**What it is:** Types of static elements that can be drawn on the floorplan.

**Values:** DOOR, WINDOW, ELECTRIC_BOARD, HEAT_SOURCE, COLD_SOURCE, FURNITURE, WIFI_AP.

**Examples / conventions:**

- **DOOR (main entry only)** – fixtures use `type: "main_entry"` for the front door; this is mapped to `MapElementType.DOOR` with `is_main_entry=True` and must sit on a `"door"` cell in the matrix. Other doors are structural only (encoded as `CellType.DOOR`) and must *not* appear as elements.
- **WINDOW** – reserved for future semantic tagging; for now all windows are structural only (`CellType.WINDOW`), not elements.
- ELECTRIC_BOARD → preferred panel location.
- HEAT_SOURCE / COLD_SOURCE → used to build prohibited zones (e.g. 50 cm around stove).
- FURNITURE, WIFI_AP → optional; can be used for “no install here” or WiFi mapping later.

**Code location:** `model.py` – `class MapElementType(Enum)`.

---

## model.DeviceType

**What it is:** Types of devices that can be installed.

**Values:** PANEL, KEYBOARD, PIR, PIRCAM, MAGNETIC, SIREN_INDOOR, SIREN_OUTDOOR, SMOKE_SENSOR.

**Why:** Matches the spec device list. Used in `DevicePlacement` so the UI and rules know what each proposed position is for.

- **MAGNETIC** – protects exterior openings. The planner groups structural doors/windows into opening strips and places at most one MAGNETIC per strip (e.g. one per multi-cell window), with behaviour driven by `SecurityLevel`. Red suppression for magnetics is **per-cell**: only red cells within a small radius of the covered opening are removed; red created by other openings in the same zone is preserved until covered by another device.
- **PIR / PIRCAM** – treated as one logical motion family in Milestone -1. They are **wall-mounted, corner-preferred** motion sensors with a nominal **8 m radius** and **90° field of view**. Coverage is computed on a grid as:
  - wall-aware BFS over `INDOOR` cells only (walls and indoor doors block propagation),
  - limited by Chebyshev radius (~8 m),
  - restricted to the PIR’s indoor connectivity component (no “seeing” through walls into other rooms).
  The alarm engine places as few PIRs as possible (greedy set cover) while ensuring **no RED cells remain after magnetics + PIRs** for the chosen `SecurityLevel`.

**Code location:** `model.py` – `class DeviceType(Enum)`.

---

## model.GridMap

**What it is:** The main matrix representation of the floorplan plus its physical scale.

**Fields:**

| Field         | Type              | Meaning |
|---------------|-------------------|---------|
| cells         | List[List[int]]   | 2D array of CellType values. |
| cell_size_m   | float             | Physical size of one cell in meters. |
| height        | int               | Number of rows. |
| width         | int               | Number of columns. |
| origin_m      | (float, float)    | Optional physical origin (x, y) in meters. |

**How it’s used:** All higher-level logic (rooms, zones, device positions) works in grid coordinates (row, col). `cell_size_m` is used to convert real-world distances (e.g. “1.5 m from door”) into cell counts.

**Code location:** `model.py` – `@dataclass class GridMap`.

---

## model.Room

**What it is:** One connected indoor area (one “room” or open region).

**Fields:**

| Field      | Type           | Meaning |
|------------|----------------|---------|
| id         | str            | Stable identifier (e.g. room_1). |
| cells      | List[GridCoord]| All grid coordinates in this room. |
| room_type  | RoomType       | Semantic type (living, bedroom, etc.). |
| is_critical| bool           | If False, “non-critical room” – algorithm may only cover the entrance. |

**Why:** Lets the rule engine apply different behaviour per room and lets the UI show rooms clearly. Non-critical rooms reduce device count while still protecting entry points.

**Code location:** `model.py` – `@dataclass class Room`.

---

## model.Zone

**What it is:** A set of cells that form a red, gray, or prohibited region.

**Fields:** id (str), zone_type (ZoneType), cells (List[GridCoord]).

**How it’s used:** Alarm/smoke rules check that every RED zone is covered, and that no device is placed inside a PROHIBITED zone.

**Code location:** `model.py` – `@dataclass class Zone`.

---

## model.MapElement

**What it is:** A semantic element placed on the map (door, window, electric board, stove, etc.).

**Fields:**

| Field         | Type             | Meaning |
|---------------|------------------|---------|
| id            | str              | Stable identifier. |
| element_type  | MapElementType   | What kind of element. |
| cells         | List[GridCoord]  | Grid cells this element occupies. |
| room_id       | str or None      | Optional link to a Room. |
| is_main_entry | bool             | True if this is the main entry door for the dwelling. |

**Why:** Decouples “things the user or operator marks on the plan” from the raw grid. Rules use elements (e.g. “front door”, “electric board”) to decide where to place devices.

**Code location:** `model.py` – `@dataclass class MapElement`.

---

## model.DevicePlacement

**What it is:** One proposed device location on the grid.

**Fields:**

| Field                   | Type           | Meaning |
|-------------------------|----------------|---------|
| id                      | str            | Identifier (e.g. dev_panel_1). |
| device_type             | DeviceType     | Panel, PIR, magnetic, etc. |
| cell                    | GridCoord      | (row, col) where to install. |
| room_id                 | str or None    | Which room this is in. |
| orientation_deg         | float or None  | For PIR/PIRCAM: direction the sensor points (not strictly needed for Milestone -1, but kept for completeness). |
| coverage_radius_cells   | float or None  | For sensors: coverage radius in cells (PIR/PIRCAM use ~8 m / cell_size_m). |
| coverage_angle_deg      | float or None  | For sensors: opening angle (PIR/PIRCAM use 90°). |
| reasons                 | List[str]      | Short explanation of why this position was chosen. |
| is_out_of_standard      | bool           | True if placement violates rules but is accepted. |

**Why:** `reasons` keeps the system explainable (no black box). `is_out_of_standard` matches the “Out of standard” flag in the spec when the user keeps a non-compliant position.

Examples of `reasons` used in the alarm engine:

- `["panel", "near_electric_board"]`
- `["keyboard", "near_main_entry"]`
- `["magnetic", "on_exterior_opening"]`, optionally with `["on_main_entry"]`, `["on_exterior_door"]`, or `["on_exterior_window"]`
- `["pir", "cover_red_zone"]` or `["pir", "cover_red_zone", "protect_exterior_door"]` for door-anchored motion protecting an un-magnetized exterior door.

**Code location:** `model.py` – `@dataclass class DevicePlacement`.

---

## model.InstallationProposal

**What it is:** The full result of running the planner for one product (alarm or smoke) on one map.

**Fields:**

| Field           | Type                  | Meaning |
|-----------------|-----------------------|---------|
| product_type    | ProductType           | ALARM or SMOKE. |
| security_level  | SecurityLevel         | MAX / OPTIMAL / MIN. |
| grid_map        | GridMap               | The matrix the proposal is based on. |
| rooms           | List[Room]            | Detected or annotated rooms. |
| zones           | List[Zone]            | Red/gray/prohibited zones. |
| elements        | List[MapElement]      | Doors, windows, electric board, etc. |
| devices         | List[DevicePlacement] | Proposed device positions with reasons. |

**How it’s used:** This is the main object returned by the backend and consumed by the app (and later AR). Serialise to JSON for storage or API responses.

**Code location:** `model.py` – `@dataclass class InstallationProposal`.

---

## model.Scenario

**What it is:** One complete planning input fixture: the grid, rooms, semantic elements, and global settings loaded from a synthetic JSON file.

**Fields:**

| Field          | Type              | Meaning |
|----------------|-------------------|---------|
| fixture_name   | str               | Human-readable identifier of the fixture. |
| cell_size_m    | float             | Physical size of one cell in meters (copied from the JSON). |
| width          | int               | Number of columns in the grid. |
| height         | int               | Number of rows in the grid. |
| security_level | SecurityLevel     | Selected profile (MIN / OPTIMAL / MAX). |
| grid_map       | GridMap           | Matrix representation of the layout (with CellType values). |
| rooms          | List[Room]        | Rooms defined in the fixture. Room cells must never reference `OUTDOOR` or `WALL` cells; they may include indoor, door, window, and hazard tiles. |
| elements       | List[MapElement]  | Elements defined in the fixture (main entry door, electric board, heat/cold sources, etc.). Doors/windows as element types are rejected except for the semantic `main_entry`. |
| notes          | str               | Optional free-text notes from the fixture. |

**How it’s used:** `Scenario` is what the planner core consumes for Milestone -1. Fixtures are loaded from JSON into `Scenario`, then zone generation and device placement run on top of it.

**Code location:** `model.py` – `@dataclass class Scenario`.

---

## GridCoord

**What it is:** Type alias for a grid coordinate: `Tuple[int, int]` meaning `(row, col)`.

**Usage:** Used in `Room.cells`, `Zone.cells`, `MapElement.cells`, and `DevicePlacement.cell` so it’s clear when a value is a grid index rather than a physical (x, y) in meters.

**Code location:** `model.py` – `GridCoord = Tuple[int, int]`.
