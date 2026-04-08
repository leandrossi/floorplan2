# Alarm engine behaviour (Milestone -1)

This document describes the **exact behaviour** of the alarm planning engine: zones, magnetics, PIRs, and sirens. It complements `ARCHITECTURE.md` and is the reference for rules in `src/acala_core/alarm_rules.py` and `engine_alarm.py`.

---

## Pipeline overview

1. **Load fixture** → `Scenario` (grid, rooms, elements).
2. **Build zones** → red zones (from exterior openings), prohibited zones (heat/cold sources).
3. **Place devices** → panel, keyboard, magnetics, then suppress red for covered openings, then PIRs, then suppress red for PIR coverage, then sirens.
4. **Return** → `InstallationProposal` (zones + devices).

All behaviour is **deterministic** and **profile-dependent** via `SecurityLevel`: `min`, `optimal`, `max`.

---

## Red zones

- **Definition**: Indoor cells reachable from an **exterior** door or window (a door/window cell that has at least one 4-neighbour that is OUTDOOR). Red zones are built by BFS from each such opening over INDOOR/DOOR/WINDOW cells; walls block propagation.
- **Purpose**: Areas that “must be covered” by either a magnetic (on the opening) or a PIR (motion coverage). Coverage is enforced by **per-cell magnetic suppression** and **PIR coverage suppression** (see below).
- **No red from interior doors**: Only openings that touch OUTDOOR generate red.

---

## Prohibited zones

- **Definition**: Cells within a radius of **heat_source** and **cold_source** elements (from the fixture). Devices must not be placed in prohibited cells (except the outdoor siren, which is on a wall).
- **Purpose**: Avoid placing PIRs/panel/keyboard near radiators, AC units, etc.

---

## Magnetics

- **Where**: One magnetic per **exterior opening group** (4-connected door or window cells). Placed on a single “representative” cell of that group (e.g. top-most for vertical strips, left-most for horizontal).
- **Cell constraint**: Magnetics are placed on DOOR or WINDOW cells only.
- **Profile rules** (from `MagneticRules`):
  - **MIN**: `protect_main_entry_only=True` → only the opening group containing the main_entry door gets a magnetic.
  - **OPTIMAL**: `protect_all_doors=True`, `protect_windows=False` → all exterior doors, no windows.
  - **MAX**: `protect_all_doors=True`, `protect_windows=True` → all exterior doors and exterior windows.
- **Suppression**: After placing magnetics, red zone cells that lie within `suppression_radius_m` of **any covered opening cell** are removed from red zones (per-cell: only red near a covered opening is cleared). Prohibited zones are unchanged.

---

## PIRs (motion)

- **Where**: Indoor cells only, wall-adjacent (candidates are INDOOR cells with at least one WALL neighbour). Placement is **component-aware**: coverage is computed per indoor connectivity component (walls and indoor doors block propagation).
- **Coverage**: 8 m nominal radius in **cells** (Chebyshev distance), within the same indoor component; walls block. Used both for “how much red does this candidate cover?” and for “which red cells do we remove after placing a PIR?”.
- **Profile rules** (from `PirRules`):
  - **MIN / OPTIMAL**: `protect_unmagnetized_doors=True` → force one PIR anchored at each **exterior door** that has **no** magnetic (door-anchored PIRs placed first).
  - **MAX**: `protect_unmagnetized_doors=False` → no forced door-anchored PIRs; only greedy coverage.
- **Placement order**: (1) Door-anchored PIRs for un-magnetized exterior doors (if enabled). (2) Greedy: repeatedly pick the wall-adjacent candidate that covers the most remaining red; corner candidates (near red bbox corners) are preferred when scores tie. Stops when no red remains or no candidate improves coverage.

---

## Sirens

- **Indoor siren**
  - **Rule**: Placed on the **same cell as the panel** (same room).
  - **Cell**: Must be INDOOR. Only placed if `SirenRules.place_indoor` is True (all profiles today).
- **Outdoor siren**
  - **Rule**: Placed on a **façade wall** cell: WALL cell that has at least one 4-neighbour OUTDOOR. Search starts from the main entry door: prefer a wall cell to the **left** of the outward normal, then **right**.
  - **Cell**: Must be WALL and outdoor-adjacent. Only placed if `SirenRules.place_outdoor` is True.
- **Profile rules** (from `SirenRules`):
  - **MIN**: `place_indoor=True`, `place_outdoor=False` → indoor siren only.
  - **OPTIMAL / MAX**: `place_indoor=True`, `place_outdoor=True` → indoor + outdoor.

---

## Profile matrix (summary)

| Profile   | Magnetics              | PIR door-anchor | Indoor siren | Outdoor siren |
|----------|------------------------|------------------|--------------|---------------|
| **min**  | Main entry only        | Yes              | Yes          | No            |
| **optimal** | All exterior doors  | Yes              | Yes          | Yes           |
| **max**  | All doors + windows    | No               | Yes          | Yes           |

Suppression radius for magnetics: 2.0 m for all profiles. PIR radius: 8.0 m, FOV 90° (used for component coverage).

---

## Other devices

- **Panel**: Placed on an INDOOR, non-prohibited cell at or 4-adjacent to the electric_board; fallback first valid indoor cell.
- **Keyboard**: Placed on an INDOOR, non-prohibited cell at or 4-adjacent to the main entry door; fallback first valid indoor cell.

---

## Related files

- `src/acala_core/alarm_rules.py` — `MagneticRules`, `PirRules`, `SirenRules`, `ALARM_RULES`.
- `src/acala_core/engine_alarm.py` — placement and suppression implementation.
- `src/acala_core/zones.py` — red and prohibited zone generation.
- `docs/ARCHITECTURE.md` — overall MVP architecture.
