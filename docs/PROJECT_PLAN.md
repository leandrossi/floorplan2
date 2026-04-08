# Home Alarm Auto-Planning Project Plan

## Document Purpose
This file is the **master project plan** for the complete project.

It is not only for Milestone -1.
It defines the full roadmap from synthetic planning prototypes to real floorplan support and later automation.

At the current stage, execution focus is on **Milestone -1**, but the structure of this document covers the entire project so it can be used in Cursor as the main source of truth.

---

## Project Vision
Build a system that makes residential alarm installations much easier by:

1. reading or constructing a property layout,
2. converting that layout into a structured matrix/grid model,
3. identifying relevant planning elements,
4. applying alarm installation logic,
5. outputting a justified installation proposal with the required devices and placements.

---

## Core Product Strategy
The project should be built as two connected systems:

### 1. Core Planner
Input:
- synthetic matrix, or
- manually defined matrix, or
- later, matrix generated from a real floorplan

Output:
- installation proposal
- device placements
- reasoning / constraints / warnings

### 2. Floorplan Ingestion Layer
Input:
- real floorplan image or PDF

Output:
- matrix and semantic elements for the planner

### Strategic rule
For a solo project, the correct approach is to build the **Core Planner first** and only later add real floorplan ingestion.

---

## Working Reality
- One-person project
- Main coding environment: Cursor
- Cursor is used as an AI coding agent/copilot
- The plan should optimize for:
  - fast iteration
  - small implementation loops
  - low dependency risk
  - strong regression testing
  - clear milestone gates

---

## Recommended File Type

### Best choice: `.md`
Markdown is the best format for this project document because:
- Cursor reads and edits Markdown very well
- easy to version in Git
- ideal for milestones, backlog, checklists, architecture notes, prompts, and implementation guidance
- readable by both humans and AI agents
- easy to split later into milestone-specific documents

### Recommendation
Use this file in the repository as:

`docs/PROJECT_PLAN.md`

---

# Full Project Roadmap

## Roadmap Summary
The full project is organized into these milestones:

- **Milestone -1** — Synthetic Matrix Prototype
- **Milestone 0** — Solo MVP Definition
- **Milestone 1** — Core Model and JSON Contract
- **Milestone 2** — Grid Utilities and Scenario Builder
- **Milestone 3** — Zone Generation
- **Milestone 4** — Alarm Placement Engine v1
- **Milestone 5** — Benchmark Harness and Regression Suite
- **Milestone 6** — Assisted Real Floorplan Input
- **Milestone 7** — Real Plan Validation
- **Milestone 8** — Automation Upgrade Path

### Current execution focus
At this moment, development should focus on:

**Milestone -1 — Synthetic Matrix Prototype**

That is the first build milestone, but the rest of the milestones are already defined below so the complete project remains structured from the beginning.

---

## Milestone -1 — Synthetic Matrix Prototype

### Goal
Validate the alarm-planning concept **without uploading or parsing real floorplans**.

Instead of starting from images or PDFs, create synthetic example matrices and semantic fixtures that represent residential layouts.

### Why this milestone exists
For a solo builder, the biggest early risk is spending time on floorplan reading before proving that the planner itself produces valuable outputs.

The first question to answer is:

**Can the planner generate good alarm device proposals from a valid matrix?**

### Deliverables
- hand-built example matrices
- JSON fixtures for sample residential layouts
- first version of `model.py` validation
- first version of `io_json.py`
- minimal planning engine prototype
- visual debug output for matrices and placements

### Suggested synthetic scenarios
Create at least these 8 cases over time:
1. studio apartment
2. 1-bedroom apartment
3. 2-bedroom apartment
4. small house with front and back door
5. house with many accessible windows
6. house with kitchen near circulation path
7. narrow corridor case
8. irregular-shaped house

### Recommended starting subset
Do not build all 8 first.
Start with these 3:
1. studio apartment
2. small house with front and back door
3. corridor-heavy 2-bedroom house

### Inputs for each fixture
Each fixture should support:
- walls
- indoor cells
- outdoor cells
- doors
- windows
- prohibited cells
- heat source
- cold source
- electric board
- rooms (optional initially, required later)

### Testing before sign-off
- load/save JSON fixtures
- verify matrix integrity
- verify indoor/outdoor separation
- verify door/window positions
- run planner for max / optimal / min security levels
- visually inspect output

### Exit criteria
Do not move on until:
- synthetic fixtures load consistently
- planner produces valid proposals
- no prohibited placements are generated
- basic red zones are covered
- outputs are explainable

### Estimated duration
1 to 2 weeks

---

## Milestone 0 — Solo MVP Definition

### Goal
Reduce the project to the smallest realistic MVP.

### Deliverables
- final MVP scope
- supported residential use cases
- supported device list
- security profile definitions
- clear acceptance criteria
- benchmark scenario definition

### MVP assumptions
Phase 1 should assume:
- residential floorplans only
- synthetic matrices first
- assisted real input later
- no full autonomous CV pipeline yet
- output is proposal JSON plus visual overlay/debug image

### Testing before sign-off
- review outputs from Milestone -1
- validate that generated proposals make sense technically and commercially
- freeze MVP scope

### Exit criteria
Do not continue until scope is fully constrained.

### Estimated duration
2 to 3 days

---

## Milestone 1 — Core Model and JSON Contract

### Goal
Stabilize the canonical backend contract.

### Deliverables
- finalized `model.py`
- JSON schema for planner objects
- `io_json.py`
- example fixtures and proposal outputs

### Core objects
- `GridMap`
- `Room`
- `Zone`
- `MapElement`
- `DevicePlacement`
- `InstallationProposal`

### Testing before sign-off
- serialization tests
- deserialization tests
- invalid schema tests
- fixture round-trip tests

### Exit criteria
The JSON contract is stable enough for all future modules.

### Estimated duration
3 to 5 days

---

## Milestone 2 — Grid Utilities and Scenario Builder

### Goal
Create the tooling needed to build and manipulate matrices quickly.

### Deliverables
- `grid_utils.py`
- helpers to generate synthetic layouts
- helpers to mark walls, doors, windows, prohibited cells
- room assignment helpers
- matrix renderer for debugging
- scenario builder script

### Why this matters
As a solo builder, speed of iteration matters more than elegance.
You should be able to create a new test case in minutes.

### Testing before sign-off
- matrix validation tests
- synthetic generation tests
- renderer output checks
- room labeling sanity tests

### Exit criteria
New scenarios can be created and debugged quickly.

### Estimated duration
1 week

---

## Milestone 3 — Zone Generation

### Goal
Transform matrix + elements into planning zones.

### Deliverables
- zone generation logic
- red zone generation
- gray zone generation
- prohibited zone expansion rules
- zone visualization/debug renderer

### Testing before sign-off
- door/window-driven red zone tests
- prohibited expansion tests around heat/cold sources
- corridor/open-plan edge case tests
- visual checks on synthetic fixtures

### Exit criteria
Zones are consistent, interpretable, and aligned with alarm logic.

### Estimated duration
1 week

---

## Milestone 4 — Alarm Placement Engine v1

### Goal
Generate deterministic installation proposals.

### Deliverables
- `engine_alarm.py`
- placement logic for panel
- placement logic for keyboard
- placement logic for magnetic contacts
- placement logic for PIR/PIRCAM
- placement logic for indoor and outdoor sirens
- reasons/explanations for each placement
- out-of-standard support

### Security levels
Support at least:
- `MAX`
- `OPTIMAL`
- `MIN`

### Testing before sign-off
- candidate generation tests
- hard-constraint tests
- prohibited placement tests
- coverage tests
- scenario comparisons across security levels

### Exit criteria
Do not move on until:
- proposals are coherent
- rules behave predictably
- device counts are sensible
- outputs are explainable

### Estimated duration
2 to 3 weeks

---

## Milestone 5 — Benchmark Harness and Regression Suite

### Goal
Protect the planner before introducing real floorplans.

### Deliverables
- benchmark runner
- expected outputs for core scenarios
- regression suite
- scorecard for:
  - coverage
  - rule violations
  - device count
  - unresolved issues

### Testing before sign-off
This milestone is mostly testing:
- rerun all scenarios automatically
- compare outputs to expected baseline
- verify no regressions after rule changes

### Exit criteria
Planner changes can be made safely without breaking prior behavior.

### Estimated duration
4 to 5 days

---

## Milestone 6 — Assisted Real Floorplan Input

### Goal
Add a first real-world input path without attempting full automation.

### Strategy
For a solo project, do not begin with full automatic floorplan recognition.

Phase 1 should support:
- upload image or PDF
- manually trace or confirm key items
- convert the assisted input into a matrix
- pass the matrix into the planner

### Deliverables
- basic image/PDF import
- simple assisted annotation flow
- matrix conversion from annotated floorplan
- planner reuse on real inputs

### Testing before sign-off
- 10 real plans manually converted
- compare proposals against expectations
- measure annotation time

### Exit criteria
Real floorplans can enter the existing planner pipeline reliably.

### Estimated duration
2 weeks

---

## Milestone 7 — Real Plan Validation

### Goal
Validate the planner on real residential cases.

### Deliverables
- 15 to 25 real examples
- comparison notes
- failure classification list
- improvement backlog for future automation

### Testing before sign-off
- end-to-end tests on real plans
- manual review of proposal usefulness
- measurement of first-pass quality

### Exit criteria
The system is useful on real plans even if assisted input is still required.

### Estimated duration
1 to 2 weeks

---

## Milestone 8 — Automation Upgrade Path

### Goal
Only after the planner is stable, begin automating floorplan interpretation.

### Deliverables
- wall detection prototype
- opening detection prototype
- OCR / room-label experiments
- confidence scoring
- fallback to manual correction

### Testing before sign-off
- compare auto-detected elements vs manually validated examples
- measure precision/recall on a small dataset

### Exit criteria
Automation can be added incrementally without destabilizing the planner.

### Estimated duration
Later phase / open-ended

---

# Milestone Dependencies

## Dependency flow
- **Milestone -1** proves the core concept on synthetic examples.
- **Milestone 0** freezes MVP scope using the learnings from -1.
- **Milestone 1** stabilizes the data contract.
- **Milestone 2** makes synthetic scenario creation fast.
- **Milestone 3** adds zone logic.
- **Milestone 4** produces real installation proposals.
- **Milestone 5** protects the planner with benchmarks and regression tests.
- **Milestone 6** introduces real floorplans in an assisted way.
- **Milestone 7** validates practical usefulness.
- **Milestone 8** automates more of the ingestion pipeline.

---

# Execution Model for One Person + Cursor

## Principle
Each milestone should be broken into small implementation loops.

### Recommended loop
1. define a very small task
2. ask Cursor to implement it
3. run tests immediately
4. inspect output visually if relevant
5. fix issues
6. commit to Git
7. move to the next small task

This is much more realistic than planning long phases without feedback.

---

## Recommended Weekly Rhythm

### Suggested cadence
- Day 1-2: implement
- Day 3: expand tests / fixtures
- Day 4: fix failures
- Day 5: freeze stable version
- Day 6-7: optional cleanup / documentation / backlog refinement

---

# Testing Strategy

## Rule
No milestone is complete until it has its own test gate.

## Test gate pattern for every milestone

### A. Build
Implement only the scope of the current milestone.

### B. Test
Run unit, integration, and scenario tests immediately.

### C. Review
Inspect visual/debug output manually.

### D. Freeze
Save:
- JSON fixtures
- screenshots
- expected outputs
- notes on limitations

### E. Commit
Create a Git commit before proceeding.

---

# Proposed Repository Structure

```text
project-root/
  docs/
    PROJECT_PLAN.md
    ARCHITECTURE.md
    TEST_STRATEGY.md
    MILESTONE_-1.md
    MILESTONE_0.md
    MILESTONE_1.md
    MILESTONE_2.md
    MILESTONE_3.md
    MILESTONE_4.md
    MILESTONE_5.md
    MILESTONE_6.md
    MILESTONE_7.md
    MILESTONE_8.md
  src/
    model.py
    io_json.py
    grid_utils.py
    zone_engine.py
    engine_alarm.py
  fixtures/
    synthetic/
      studio_apartment.json
      one_bedroom.json
      two_bedroom.json
      corridor_house.json
      open_plan_house.json
    real/
      README.md
  tests/
    test_model.py
    test_io_json.py
    test_grid_utils.py
    test_zones.py
    test_engine_alarm.py
    test_regression.py
  scripts/
    build_scenario.py
    render_matrix.py
    run_benchmarks.py
```

---

# Recommended Document Strategy

## Master document
Use this file as the master planning document:

- `docs/PROJECT_PLAN.md`

## Supporting milestone documents
Then create a dedicated file for each milestone, not only for Milestone -1:

- `docs/MILESTONE_-1.md`
- `docs/MILESTONE_0.md`
- `docs/MILESTONE_1.md`
- `docs/MILESTONE_2.md`
- `docs/MILESTONE_3.md`
- `docs/MILESTONE_4.md`
- `docs/MILESTONE_5.md`
- `docs/MILESTONE_6.md`
- `docs/MILESTONE_7.md`
- `docs/MILESTONE_8.md`

### Recommended usage
- `PROJECT_PLAN.md` = full roadmap and milestone overview
- each `MILESTONE_X.md` = detailed backlog, tasks, acceptance criteria, and notes for that milestone

That way the project structure is complete from the beginning, while your current implementation focus remains on Milestone -1.

---

# Recommended Immediate Next Steps

## First actions
1. add this file to the repo as `docs/PROJECT_PLAN.md`
2. create `docs/MILESTONE_-1.md` as the first execution file
3. keep the rest of the milestone files empty or with placeholders initially
4. create the first 3 synthetic fixtures
5. implement minimum `model.py`
6. implement JSON round-trip tests
7. implement a simple matrix renderer
8. only then start the first version of `engine_alarm.py`

---

# Final Note
This project plan is intentionally structured for the **complete project**, not only for the first milestone.

The current execution focus is Milestone -1, but the planning structure already includes the entire roadmap so Cursor can use it as a long-term project guide.
