# MILESTONE_-1.md

## Title
Synthetic Matrix Prototype

## Status
Current milestone

## Purpose
This milestone exists to validate the **core alarm planning engine** before working on real floorplan ingestion.

At this stage:
- we do **not** upload or parse real floorplans
- we do **not** build OCR or computer vision yet
- we do **not** optimize UI workflows yet

Instead, we manually create **synthetic residential matrices** and prove that the system can generate a coherent installation proposal from a structured input.

The main question to answer in this milestone is:

> If the matrix and semantic elements are already correct, can the planner generate a useful alarm installation proposal?

If the answer is no, then there is no reason to invest time in floorplan parsing yet.

---

## Primary Goal
Build a first working version of the planning pipeline:

**synthetic matrix -> rooms/zones/elements -> alarm proposal**

---

## Success Criteria
This milestone is successful if the project can:

1. load synthetic scenarios from JSON fixtures
2. represent walls, indoor/outdoor space, doors, windows, and key elements
3. generate zones from those inputs
4. produce an installation proposal for:
   - `min`
   - `optimal`
   - `max`
5. explain why each device was placed
6. avoid obvious invalid placements
7. run a small regression suite on all synthetic scenarios

---

## Out of Scope
The following items are explicitly out of scope for Milestone -1:

- real floorplan upload
- image processing
- PDF parsing
- OCR
- wall detection from image
- automatic room classification from floorplan text
- complex UI/editor
- production deployment
- advanced optimization beyond a reasonable deterministic heuristic

---

## Deliverables
By the end of this milestone, the repo should contain:

- a stable synthetic scenario format
- a scenario loader
- core model validation
- matrix/grid helper functions
- zone generation logic
- alarm placement engine v1
- visual debug output for scenarios
- regression tests for all scenarios
- one Markdown summary of results and known limitations

---

## Recommended Repository Structure
```text
project-root/
├─ docs/
│  ├─ PROJECT_PLAN.md
│  ├─ MILESTONE_-1.md
│  ├─ ARCHITECTURE.md
│  └─ TEST_STRATEGY.md
├─ data/
│  └─ fixtures/
│     ├─ synthetic/
│     │  ├─ studio_apartment.json
│     │  ├─ apartment_1br.json
│     │  ├─ apartment_2br.json
│     │  ├─ house_small_front_back.json
│     │  ├─ house_window_heavy.json
│     │  ├─ house_open_plan.json
│     │  ├─ house_corridor.json
│     │  └─ house_irregular.json
│     └─ expected/
│        ├─ studio_apartment.expected.json
│        ├─ apartment_1br.expected.json
│        └─ ...
├─ src/
│  ├─ model.py
│  ├─ io_json.py
│  ├─ grid_utils.py
│  ├─ zones.py
│  ├─ engine_alarm.py
│  ├─ scoring.py
│  └─ debug_render.py
├─ scripts/
│  ├─ run_fixture.py
│  ├─ render_fixture.py
│  └─ benchmark_synthetic.py
├─ tests/
│  ├─ test_model.py
│  ├─ test_io_json.py
│  ├─ test_grid_utils.py
│  ├─ test_zones.py
│  ├─ test_engine_alarm.py
│  └─ test_regression_synthetic.py
└─ outputs/
   └─ synthetic_debug/
```

---

## Functional Scope

### Input
Input will be a hand-authored JSON fixture representing:
- grid dimensions
- cell size in meters
- cell types
- rooms
- semantic elements
- security level

### Processing
The pipeline should:
1. load fixture
2. validate structure
3. build internal matrix/grid
4. generate zones
5. generate candidate placements
6. score candidates
7. produce final proposal
8. render a debug output

### Output
The output should include:
- `InstallationProposal`
- list of device placements
- reasons for each placement
- optional warnings
- out-of-standard flags where needed
- rendered matrix image or text map for debugging

---

## Device Scope for Milestone -1
The first version should support these device types:

- Panel
- Keyboard
- Magnetic sensor
- PIR
- PIRCam
- Indoor siren
- Outdoor siren

Do not add extra device families in this milestone unless needed to unblock core logic.

---

## Security Profiles
The milestone must support three security profiles:

### Min
Minimal viable protection with low device count.

### Optimal
Balanced recommendation for normal residential use.

### Max
High-coverage recommendation with more perimeter protection and more detection redundancy.

---

## Synthetic Scenario Set
Start with these 8 base scenarios.

### 1. Studio apartment
Small open space with one main entry and limited windows.

### 2. 1-bedroom apartment
Basic separated bedroom plus living area.

### 3. 2-bedroom apartment
A more realistic apartment layout with multiple windows.

### 4. Small house with front and back door
Useful to test circulation and dual-entry logic.

### 5. Window-heavy perimeter house
Useful to stress perimeter logic and sensor count.

### 6. Open-plan house
Useful to test large visible spaces and PIR/PIRCam logic.

### 7. Corridor-heavy house
Useful to test choke-point and circulation coverage.

### 8. Irregular-shaped house
Useful to test geometry edge cases.

---

## Synthetic Fixture Requirements
Each fixture should contain at minimum:

- `fixture_name`
- `cell_size_m`
- `width`
- `height`
- `cells`
- `rooms`
- `elements`
- `security_level`
- `notes`

### Minimum cell categories
At minimum support:
- outdoor
- indoor
- wall
- door
- window
- prohibited

### Minimum semantic elements
At minimum support:
- electric_board
- heat_source
- cold_source
- main_entry

---

## Suggested JSON Shape
This is a suggested direction, not a frozen final schema.

```json
{
  "fixture_name": "studio_apartment",
  "cell_size_m": 0.1,
  "width": 20,
  "height": 15,
  "security_level": "optimal",
  "cells": [
    ["outdoor", "outdoor", "wall", "..."],
    ["outdoor", "indoor", "indoor", "..."]
  ],
  "rooms": [
    {
      "id": "room_1",
      "name": "living_sleeping_area",
      "room_type": "living_room",
      "cells": [[2, 3], [2, 4], [3, 4]]
    }
  ],
  "elements": [
    {
      "type": "main_entry",
      "position": [5, 2]
    },
    {
      "type": "electric_board",
      "position": [4, 2]
    },
    {
      "type": "window",
      "position": [12, 1]
    },
    {
      "type": "heat_source",
      "position": [14, 10]
    }
  ],
  "notes": "Simple synthetic studio for first-pass validation."
}
```

---

## Core Tasks

### Task Group A — Model and schema
#### Goal
Make sure the scenario structure and proposal structure are stable enough to build on.

#### Tasks
- review and stabilize the core Python model
- define missing enums if needed
- implement fixture validation
- implement proposal serialization
- create 2 example fixtures first before creating all 8

#### Done when
- fixtures load successfully
- invalid fixtures fail cleanly
- proposal object can be serialized

---

### Task Group B — Grid utilities
#### Goal
Provide reliable helpers for matrix operations.

#### Tasks
- grid creation helpers
- bounds validation
- neighborhood utilities
- indoor/outdoor adjacency checks
- wall occlusion helpers
- fixture pretty-printer or renderer

#### Done when
- all fixtures can be loaded and rendered
- coordinate bugs are under control
- debugging a scenario is fast

---

### Task Group C — Zone generation
#### Goal
Convert structural input into actionable alarm planning zones.

#### Tasks
- create red-zone logic from exterior openings
- create prohibited logic around heat/cold/problem areas
- create optional gray-zone logic for secondary desirability
- render zones for visual review

#### Done when
- each fixture produces zones without crashing
- zones visually match expectations
- prohibited zones do not leak outside reasonable areas

---

### Task Group D — Alarm placement engine v1
#### Goal
Place core alarm devices deterministically.

#### Tasks
- define hard constraints by device type
- generate candidate positions
- score candidates
- choose final placements
- attach reasoning strings
- support min / optimal / max

#### Done when
- each fixture produces a coherent proposal
- major invalid placements are blocked
- proposals differ sensibly by security profile

---

### Task Group E — Regression and benchmark harness
#### Goal
Protect progress and make iteration safe.

#### Tasks
- create expected-output summaries
- build a benchmark runner
- compare proposal metrics across fixtures
- store debug renders
- document known limitations

#### Done when
- all fixtures run from one command
- regressions are visible
- rule changes can be validated quickly

---

## Initial Implementation Order
Use this exact build order to reduce rework:

1. create 2 minimal fixtures
2. finalize the minimal fixture schema
3. implement loader + validation
4. implement grid render/debug tools
5. implement zone generation
6. implement panel/keyboard placement
7. implement magnetic placement
8. implement PIR/PIRCam placement
9. implement siren placement
10. expand to all 8 fixtures
11. freeze first regression baseline

---

## Testing Strategy

### Test Layer 1 — Unit tests
Write focused tests for:
- model validation
- fixture loading
- coordinate bounds
- adjacency logic
- simple zone logic
- scoring helpers

### Test Layer 2 — Scenario tests
For each synthetic fixture, verify:
- no crash
- valid proposal object
- expected device types appear
- no device placed inside wall/outdoor/prohibited cells unless explicitly flagged

### Test Layer 3 — Visual review
For each fixture and security level:
- render matrix
- render zones
- render final placements
- manually inspect whether the result is coherent

### Test Layer 4 — Regression tests
Save a baseline summary such as:
- number of devices by type
- red-zone coverage %
- warnings count
- out-of-standard count

The exact positions may evolve, but core metrics should remain stable or improve.

---

## Acceptance Tests
Milestone -1 should not be marked complete until all of the following are true:

- at least 8 synthetic fixtures exist
- all fixtures load successfully
- all fixtures produce a proposal for min / optimal / max
- panel placement works in a reasonable way
- keyboard placement works in a reasonable way
- opening/perimeter logic is present
- PIR or PIRCam logic covers intrusion paths in basic cases
- prohibited placements are blocked or explicitly flagged
- one benchmark command runs the full synthetic suite
- results are documented in a summary file

---

## Exit Criteria
This milestone is complete when:

1. the planner works on synthetic matrices
2. the synthetic suite is stable
3. the project has enough confidence to start assisted real-floorplan input
4. future work can be measured against a baseline

If any of these are missing, do not move to the next milestone.

---

## Known Risks

### Risk 1
The planner produces outputs but they are not commercially sensible.

**Mitigation:** keep fixtures realistic and review outputs critically.

### Risk 2
Schema churn slows development.

**Mitigation:** freeze a minimal schema early, then extend only if necessary.

### Risk 3
Too much time is spent on optimization too early.

**Mitigation:** prefer deterministic, readable heuristics first.

### Risk 4
Synthetic fixtures become too artificial and stop representing real homes.

**Mitigation:** make scenarios resemble real residential patterns and add edge cases intentionally.

---

## Cursor Workflow Recommendation
Because this is a one-person project using Cursor as an AI agent, each task should be executed in very small slices.

Recommended loop:
1. pick one task
2. ask Cursor to implement it
3. run tests immediately
4. inspect the output
5. commit when stable

### Good examples of task slicing
- "Implement fixture loader validation only"
- "Add red-zone generation from windows adjacent to outdoor cells"
- "Add keyboard candidate scoring near main entry"
- "Render matrix and placements to PNG for synthetic fixtures"

Avoid asking Cursor for large vague tasks like:
- "Build the whole planner"

---

## Suggested Commands
These are placeholders; adapt them to your actual tooling.

```bash
python scripts/run_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/render_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/benchmark_synthetic.py
pytest tests/
```

---

## Recommended First Week Backlog

### Day 1
- create `MILESTONE_-1.md`
- create 2 synthetic fixtures
- create loader and basic validation

### Day 2
- implement grid renderer/debug output
- validate coordinates and cell categories

### Day 3
- implement first red/prohibited zone logic
- render zones for 2 fixtures

### Day 4
- implement panel and keyboard placement
- add first scenario tests

### Day 5
- implement magnetic placement
- run first end-to-end synthetic benchmark

### Day 6
- refine scoring and reasons
- fix edge-case bugs

### Day 7
- freeze baseline
- write summary of milestone progress

---

## Definition of Done
Milestone -1 is done when the synthetic planning engine is real, testable, repeatable, and useful enough to justify starting work on real floorplan ingestion.

---

## Next Milestone
Once Milestone -1 is complete, the next step is:

**Milestone 0 — Solo MVP Definition**

That milestone should use the results of this synthetic prototype to freeze:
- device scope
- planning rules
- acceptance thresholds
- what real-floorplan support should look like in the first assisted version
