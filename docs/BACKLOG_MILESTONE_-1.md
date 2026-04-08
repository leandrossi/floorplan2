# BACKLOG_MILESTONE_-1.md

## Title
Execution Backlog — Milestone -1

## Purpose
This file translates **Milestone -1** into a practical execution backlog for a **one-person project using Cursor**.

It is not a strategy document.
It is an **implementation document**.

Its job is to answer:

- what to build first
- what to build next
- how small each step should be
- what each task depends on
- how to know when each task is done
- what to ask Cursor to do

---

## How to Use This Backlog
Work through tasks in order.

For each task:
1. read the goal
2. check dependencies
3. ask Cursor to implement only that task
4. run the related tests
5. inspect output if needed
6. mark task complete
7. commit before moving on if stable

### Important rule
Do not ask Cursor for large vague tasks like:
- "build the planner"
- "implement the whole milestone"

Always ask for one small task at a time.

---

## Milestone Goal
Build a first working version of:

**synthetic matrix -> zones -> alarm proposal**

This backlog supports only **Milestone -1**.
It does not include real floorplan ingestion yet.

---

# Phase 0 — Project skeleton

## Task P0-01 — Create repository folders
### Goal
Create the base folder structure required for the milestone.

### Dependencies
None

### Action
Create:
- `docs/`
- `data/fixtures/synthetic/`
- `data/expected/`
- `src/`
- `scripts/`
- `tests/`
- `outputs/synthetic_debug/`

### Done when
- folders exist
- repo structure matches milestone docs

### Cursor prompt
```text
Create the base project folders for the MVP:
docs, data/fixtures/synthetic, data/expected, src, scripts, tests, outputs/synthetic_debug.
Do not add extra folders yet.
```

---

## Task P0-02 — Add core docs to repo
### Goal
Place the planning documents inside `docs/`.

### Dependencies
P0-01

### Action
Make sure these files exist in `docs/`:
- `PROJECT_PLAN.md`
- `MILESTONE_-1.md`
- `ARCHITECTURE.md`
- `TEST_STRATEGY_MILESTONE_-1.md`

### Done when
- all planning docs are in repo
- file names are stable

### Cursor prompt
```text
Ensure the docs folder contains the planning files:
PROJECT_PLAN.md, MILESTONE_-1.md, ARCHITECTURE.md, TEST_STRATEGY_MILESTONE_-1.md.
Do not modify their content.
```

---

# Phase 1 — Core model and fixture schema

## Task P1-01 — Create `src/model.py` with minimal enums
### Goal
Define the smallest set of enums needed to represent fixtures and proposals.

### Dependencies
P0-01

### Action
Create enums for:
- cell types
- room types
- element types
- zone types
- device types
- security levels

### Done when
- enums exist
- names align with milestone docs
- no business logic exists yet

### Cursor prompt
```text
Create src/model.py with minimal Python enums for:
CellType, RoomType, ElementType, ZoneType, DeviceType, SecurityLevel.
Keep it simple and aligned with the milestone docs.
Do not add planning logic yet.
```

---

## Task P1-02 — Add minimal dataclasses or models
### Goal
Create the minimum internal data structures.

### Dependencies
P1-01

### Action
Add minimal classes for:
- Room
- Element
- Zone
- DevicePlacement
- InstallationProposal
- Scenario

### Done when
- the core objects exist
- fields are enough to load a fixture and return a proposal
- models are readable and small

### Cursor prompt
```text
Extend src/model.py with minimal dataclasses or simple Pydantic models for:
Room, Element, Zone, DevicePlacement, InstallationProposal, and Scenario.
Keep the schema small and practical for Milestone -1.
```

---

## Task P1-03 — Create `tests/test_model.py`
### Goal
Protect the model before building the loader.

### Dependencies
P1-02

### Action
Add tests for:
- valid enum usage
- invalid enum handling if applicable
- basic object creation
- basic proposal creation

### Done when
- tests run
- model file is importable
- invalid values fail clearly if validation is implemented

### Cursor prompt
```text
Create tests/test_model.py with basic tests for the models and enums in src/model.py.
Focus on simple object creation and invalid value handling where relevant.
```

---

## Task P1-04 — Create fixture schema example in docs or comments
### Goal
Freeze the first minimal fixture shape before writing the loader.

### Dependencies
P1-02

### Action
Create one small schema example showing:
- width
- height
- cell_size_m
- cells
- rooms
- elements
- security_level
- notes

### Done when
- there is one agreed example shape
- loader implementation can follow it

### Cursor prompt
```text
Add a minimal fixture schema example, either in docs or as a reference comment in src/io_json.py,
showing the expected fields for Milestone -1 synthetic fixtures.
Keep it small and consistent with the architecture docs.
```

---

# Phase 2 — Fixture loading and validation

## Task P2-01 — Create `src/io_json.py` with fixture loader
### Goal
Load a fixture JSON file from disk.

### Dependencies
P1-02
P1-04

### Action
Add:
- `load_fixture(path)`
- raw JSON loading
- conversion into Scenario model

### Done when
- a valid fixture can be loaded into internal objects
- loader is readable
- no export yet

### Cursor prompt
```text
Create src/io_json.py with a load_fixture(path) function.
It should load a synthetic fixture JSON from disk and convert it into the internal Scenario model.
Keep it simple and local-file based.
```

---

## Task P2-02 — Add fixture validation
### Goal
Reject malformed fixtures early.

### Dependencies
P2-01

### Action
Validate:
- required fields exist
- width/height are positive
- cell matrix dimensions match width/height
- security level is valid
- element coordinates are inside bounds

### Done when
- malformed fixtures fail with readable errors
- valid fixtures still load successfully

### Cursor prompt
```text
Add validation to src/io_json.py for synthetic fixtures:
required fields, positive dimensions, cells matrix shape, valid security level, and in-bounds element coordinates.
Raise clear errors.
```

---

## Task P2-03 — Create `tests/test_io_json.py`
### Goal
Protect the loader and validation behavior.

### Dependencies
P2-02

### Action
Add tests for:
- valid fixture load
- missing field
- invalid dimensions
- invalid security profile
- out-of-bounds element

### Done when
- loader tests pass
- invalid fixtures fail for the correct reason

### Cursor prompt
```text
Create tests/test_io_json.py covering valid fixture loading and common invalid fixture cases:
missing field, mismatched dimensions, invalid security profile, and out-of-bounds element coordinates.
```

---

## Task P2-04 — Create first fixture `studio_apartment.json`
### Goal
Have the first end-to-end input file.

### Dependencies
P2-02

### Action
Create a very small realistic synthetic fixture.

### Done when
- fixture loads successfully
- fixture is easy to understand
- it includes at least:
  - walls
  - indoor/outdoor
  - main entry
  - one window
  - electric board
  - one heat source

### Cursor prompt
```text
Create data/fixtures/synthetic/studio_apartment.json as the first synthetic residential fixture.
Keep it small but realistic. Include walls, indoor/outdoor cells, a main entry, one window, an electric board, and one heat source.
```

---

## Task P2-05 — Create second fixture `apartment_1br.json`
### Goal
Add a second scenario before building planner logic.

### Dependencies
P2-04

### Action
Create a slightly more complex apartment fixture.

### Done when
- fixture loads successfully
- layout differs from studio
- includes multiple rooms and windows

### Cursor prompt
```text
Create data/fixtures/synthetic/apartment_1br.json as a second synthetic fixture.
Make it slightly more complex than the studio and include multiple rooms and windows.
```

---

# Phase 3 — Grid utilities and debugging support

## Task P3-01 — Create `src/grid_utils.py` with bounds helpers
### Goal
Build the most basic grid operations.

### Dependencies
P2-02

### Action
Add helpers like:
- `is_inside(...)`
- `get_cell(...)`
- `iter_neighbors(...)`

### Done when
- basic spatial helpers exist
- helpers are independent of planner logic

### Cursor prompt
```text
Create src/grid_utils.py with basic grid helper functions:
is_inside, get_cell, and iter_neighbors.
Keep these utilities generic and independent from alarm business logic.
```

---

## Task P3-02 — Add adjacency and opening helpers
### Goal
Enable exterior-opening logic.

### Dependencies
P3-01

### Action
Add helpers for:
- indoor/outdoor adjacency
- checking if a door/window is adjacent to outdoor cells
- simple radius expansion

### Done when
- exterior opening checks work
- helper functions are testable

### Cursor prompt
```text
Extend src/grid_utils.py with helpers for indoor/outdoor adjacency,
detecting whether an opening is exterior, and basic radius expansion.
Keep the functions simple and testable.
```

---

## Task P3-03 — Create `tests/test_grid_utils.py`
### Goal
Protect spatial helper behavior.

### Dependencies
P3-02

### Action
Test:
- bounds
- neighbors
- exterior opening detection
- radius behavior

### Done when
- basic spatial logic is covered
- helpers behave correctly on edges and corners

### Cursor prompt
```text
Create tests/test_grid_utils.py to cover bounds checks, neighbor logic, exterior opening detection, and radius expansion behavior.
Use small synthetic grid examples in the tests.
```

---

## Task P3-04 — Create `src/debug_render.py` with simple matrix render
### Goal
Make the matrix visible for debugging.

### Dependencies
P2-04
P2-05

### Action
Implement a minimal renderer:
- ASCII or simple image
- show walls, indoor/outdoor, doors/windows, elements

### Done when
- first fixtures can be rendered
- output helps inspect mistakes quickly

### Cursor prompt
```text
Create src/debug_render.py with a very simple matrix renderer for synthetic fixtures.
ASCII output is acceptable for the MVP.
Render walls, indoor/outdoor cells, openings, and semantic elements.
```

---

## Task P3-05 — Create `scripts/render_fixture.py`
### Goal
Render a fixture from the command line.

### Dependencies
P3-04
P2-01

### Action
Add a script to load and render a fixture.

### Done when
- one command produces a debug render for a fixture
- script is simple and readable

### Cursor prompt
```text
Create scripts/render_fixture.py that loads a synthetic fixture and renders it using src/debug_render.py.
Keep the script simple and CLI-based.
```

---

# Phase 4 — Zone generation

## Task P4-01 — Create `src/zones.py` with red-zone generation
### Goal
Generate the first meaningful planning zones.

### Dependencies
P3-02
P2-04
P2-05

### Action
Build red zones from exterior-accessible openings.

### Done when
- doors/windows adjacent to outdoor space generate red influence
- zones stay inside valid grid area

### Cursor prompt
```text
Create src/zones.py with initial red-zone generation logic based on exterior-accessible doors and windows.
Keep the logic deterministic and easy to inspect.
```

---

## Task P4-02 — Add prohibited-zone generation
### Goal
Prevent bad placements around hazards.

### Dependencies
P4-01

### Action
Generate prohibited zones around:
- heat sources
- cold sources if present

### Done when
- prohibited zones appear around hazard elements
- zone expansion is configurable or at least centralized

### Cursor prompt
```text
Extend src/zones.py with prohibited-zone generation around heat_source and cold_source elements.
Keep the radius simple and centralized for easy tuning.
```

---

## Task P4-03 — Create `tests/test_zones.py`
### Goal
Protect early zone logic.

### Dependencies
P4-02

### Action
Test:
- red zones from entry/window
- prohibited zones from heat source
- zones stay within bounds

### Done when
- zone logic has unit-level coverage
- obvious zone regressions are catchable

### Cursor prompt
```text
Create tests/test_zones.py covering red-zone generation from openings, prohibited-zone generation from heat sources, and zone bound safety.
Use small synthetic scenarios in the tests.
```

---

## Task P4-04 — Extend debug render to show zones
### Goal
Make zone logic visually inspectable.

### Dependencies
P4-02
P3-04

### Action
Render:
- red zones
- prohibited zones

### Done when
- zone overlays are visible in debug output
- studio and 1br fixtures can show zones clearly

### Cursor prompt
```text
Extend src/debug_render.py so it can display red zones and prohibited zones in the debug output for synthetic fixtures.
Keep the rendering simple and readable.
```

---

# Phase 5 — Alarm planning engine v1

## Task P5-01 — Create `src/engine_alarm.py` with planner entrypoint
### Goal
Create the main planning function.

### Dependencies
P4-02
P1-02

### Action
Add:
- `plan_installation(scenario)`

At first it can return a very simple empty or placeholder proposal structure.

### Done when
- the planner entrypoint exists
- end-to-end orchestration can start

### Cursor prompt
```text
Create src/engine_alarm.py with a plan_installation(scenario) entrypoint.
For now it can return a minimal InstallationProposal placeholder structure so later tasks can build on it.
```

---

## Task P5-02 — Add panel placement
### Goal
Place the control panel in a basic reasonable way.

### Dependencies
P5-01

### Action
Use simple rule:
- prefer near electric board
- stay indoors
- avoid prohibited cells

### Done when
- valid panel placement is added to proposal
- proposal includes reason text

### Cursor prompt
```text
Extend src/engine_alarm.py to place a panel using simple MVP rules:
prefer near electric_board, stay indoors, avoid prohibited cells.
Add a readable reason string to the placement.
```

---

## Task P5-03 — Add keyboard placement
### Goal
Place the keyboard near the main entry.

### Dependencies
P5-02

### Action
Use simple rule:
- near main entry
- indoors
- not on prohibited cells
- not colliding with wall/outdoor

### Done when
- keyboard placement exists when main entry exists
- reason text is included

### Cursor prompt
```text
Extend src/engine_alarm.py to place a keyboard near the main_entry using simple MVP rules.
Keep it indoors and avoid prohibited or invalid cells.
Add a readable reason string.
```

---

## Task P5-04 — Add magnetic sensor placement
### Goal
Protect relevant openings.

### Dependencies
P5-03

### Action
Add magnetic sensors to selected exterior openings based on security level.

### Done when
- opening logic affects magnetic count
- min/optimal/max differ in a sensible way

### Cursor prompt
```text
Extend src/engine_alarm.py to place magnetic sensors on relevant exterior openings.
Use security_level to vary the number or strictness of placements for min, optimal, and max.
```

---

## Task P5-05 — Add first motion device placement
### Goal
Place PIR or PIRCam devices using simple zone-driven logic.

### Dependencies
P5-04
P4-02

### Action
Use simple heuristic:
- prefer cells covering red zones
- avoid prohibited cells
- avoid walls/outdoor
- do not overcomplicate orientation at first

### Done when
- at least one motion strategy exists on basic fixtures
- proposal remains coherent

### Cursor prompt
```text
Extend src/engine_alarm.py with first-pass motion device placement logic using simple zone-driven heuristics.
Prefer coverage of red zones, avoid prohibited cells, and keep the logic readable.
Do not overcomplicate orientation yet.
```

---

## Task P5-06 — Add siren placement
### Goal
Add indoor and outdoor siren support.

### Dependencies
P5-05

### Action
Use very simple rules:
- indoor siren in central or useful indoor area
- outdoor siren near perimeter/main façade area if representable

### Done when
- sirens appear in proposal
- no obviously invalid siren placement

### Cursor prompt
```text
Extend src/engine_alarm.py to place an indoor siren and, if supported by the fixture, an outdoor siren using simple MVP rules.
Keep the logic deterministic and readable.
```

---

## Task P5-07 — Add warnings and out-of-standard flags
### Goal
Expose planner limitations explicitly.

### Dependencies
P5-06

### Action
Add:
- warnings list
- out-of-standard flags for problematic placements or missing assumptions

### Done when
- proposal can communicate imperfect cases
- planner is more transparent

### Cursor prompt
```text
Extend the proposal generation in src/engine_alarm.py to include warnings and out-of-standard flags where the planner cannot meet ideal conditions.
Keep the output simple and readable.
```

---

## Task P5-08 — Create `tests/test_engine_alarm.py`
### Goal
Protect the first planner behaviors.

### Dependencies
P5-07

### Action
Test:
- panel exists
- keyboard exists when main entry exists
- no placements on walls/outdoor
- prohibited placements blocked or flagged
- security profile changes output

### Done when
- planner has basic automated protection
- major regressions can be caught

### Cursor prompt
```text
Create tests/test_engine_alarm.py to cover initial planner behavior:
panel placement, keyboard placement near entry, avoiding wall/outdoor cells, handling prohibited cells, and profile-sensitive output differences.
```

---

# Phase 6 — End-to-end scripts and synthetic expansion

## Task P6-01 — Create `scripts/run_fixture.py`
### Goal
Run one synthetic fixture end to end.

### Dependencies
P5-07
P2-01
P3-04

### Action
Script should:
- load fixture
- run planner
- save proposal JSON
- optionally save render

### Done when
- one command runs the full MVP pipeline for a fixture

### Cursor prompt
```text
Create scripts/run_fixture.py that loads one synthetic fixture, runs the planner, saves proposal JSON, and optionally saves a debug render.
Keep the CLI simple.
```

---

## Task P6-02 — Expand synthetic fixture set to all 8 base cases
### Goal
Build the milestone benchmark set.

### Dependencies
P6-01

### Action
Add:
- `apartment_2br.json`
- `house_small_front_back.json`
- `house_window_heavy.json`
- `house_open_plan.json`
- `house_corridor.json`
- `house_irregular.json`

### Done when
- all 8 fixtures exist
- all fixtures load successfully

### Cursor prompt
```text
Create the remaining synthetic fixtures for Milestone -1:
apartment_2br, house_small_front_back, house_window_heavy, house_open_plan, house_corridor, and house_irregular.
Keep them realistic enough for residential planning tests.
```

---

## Task P6-03 — Run manual visual review on all fixtures
### Goal
Catch obvious spatial mistakes before baseline freeze.

### Dependencies
P6-02
P4-04
P6-01

### Action
Render each fixture and review:
- structure
- zones
- placements

### Done when
- obvious geometry or placement mistakes are fixed
- fixture set feels realistic enough for milestone

### Cursor prompt
```text
Help me review the synthetic fixture outputs visually.
I will run the renderer on each fixture and we will inspect structure, zones, and placements for obvious errors before freezing a baseline.
```

---

# Phase 7 — Regression harness and milestone freeze

## Task P7-01 — Create `tests/test_regression_synthetic.py`
### Goal
Protect against accidental planner degradation.

### Dependencies
P6-02
P5-08

### Action
Create regression tests using stable metrics like:
- device counts by type
- warnings count
- out-of-standard count
- proposal existence

### Done when
- rule changes can be compared to baseline behavior
- exact coordinates are not over-frozen too early

### Cursor prompt
```text
Create tests/test_regression_synthetic.py using stable regression metrics for the synthetic fixtures:
device counts by type, warnings count, out-of-standard count, and proposal existence.
Do not freeze exact coordinates too aggressively yet.
```

---

## Task P7-02 — Create `scripts/benchmark_synthetic.py`
### Goal
Run the full synthetic suite and summarize results.

### Dependencies
P7-01
P6-02

### Action
Script should:
- iterate over all fixtures
- run all profiles if supported
- save summary metrics

### Done when
- one command runs the synthetic benchmark suite
- result summary is easy to inspect

### Cursor prompt
```text
Create scripts/benchmark_synthetic.py to run the full synthetic fixture suite,
execute the planner, and summarize benchmark metrics in a readable output file or terminal summary.
```

---

## Task P7-03 — Freeze first baseline outputs
### Goal
Create the first milestone reference point.

### Dependencies
P7-02
P6-03

### Action
Save:
- proposal summaries
- benchmark summary
- selected debug renders

### Done when
- the project has a baseline for future rule changes
- milestone results are reviewable

### Cursor prompt
```text
Help me define and save the first synthetic benchmark baseline:
proposal summaries, benchmark metrics, and selected debug outputs for Milestone -1.
Keep the baseline practical and not too brittle.
```

---

## Task P7-04 — Write milestone summary
### Goal
Document what was achieved and what remains weak.

### Dependencies
P7-03

### Action
Create a short milestone report with:
- completed scope
- passing fixtures
- open limitations
- readiness for Milestone 0

### Done when
- milestone has a closing summary
- next step is clear

### Cursor prompt
```text
Create a short Milestone -1 summary report describing:
what was completed, which synthetic fixtures pass, known limitations, and whether the project is ready to move to Milestone 0.
```

---

# Priority Order Summary

## Highest priority tasks
Do these first:
1. P0-01
2. P1-01
3. P1-02
4. P2-01
5. P2-02
6. P2-04
7. P2-05
8. P3-01
9. P3-02
10. P4-01
11. P4-02
12. P5-01
13. P5-02
14. P5-03

These are the tasks needed to get the first end-to-end planner shape.

---

# Daily Execution Recommendation

## Day 1
- P0-01
- P1-01
- P1-02
- P1-03

## Day 2
- P1-04
- P2-01
- P2-02
- P2-03

## Day 3
- P2-04
- P2-05
- P3-01
- P3-02

## Day 4
- P3-03
- P3-04
- P3-05
- P4-01

## Day 5
- P4-02
- P4-03
- P4-04
- P5-01

## Day 6
- P5-02
- P5-03
- P5-04
- P5-05

## Day 7
- P5-06
- P5-07
- P5-08
- P6-01

This is only a suggested sequence, not a strict deadline.

---

# Rules for Task Sizing
Every task in this backlog should be:

- small enough to implement in one focused Cursor request
- testable immediately after implementation
- independent enough to debug without chaos
- meaningful enough to move the project forward

If a task feels too large, split it before asking Cursor to implement it.

---

# Definition of Backlog Completion
This backlog is considered complete when:

- all tasks required for Milestone -1 are done
- all 8 synthetic fixtures exist
- planner works end to end
- synthetic benchmark can run
- baseline is frozen
- milestone summary is written

At that point, the project is ready to transition into **Milestone 0**.

---

# Related Documents
Use this backlog together with:
- `PROJECT_PLAN.md`
- `MILESTONE_-1.md`
- `ARCHITECTURE.md`
- `TEST_STRATEGY_MILESTONE_-1.md`

---

# Final Recommendation
Do not optimize for elegance during this milestone.

Optimize for:
- working code
- visible outputs
- safe iteration
- small Cursor tasks
- fast feedback

That is the best way to get a real MVP moving.
