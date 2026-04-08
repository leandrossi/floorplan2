# ARCHITECTURE.md

## Title
MVP Architecture — Home Alarm Installation Planner

## Purpose
This document defines the **technical architecture for the MVP** of the home alarm installation planner.

The goal of the MVP is **not** to build a production-grade platform.

The goal is to build the **smallest architecture that can prove the core value**:

> Given a valid matrix representation of a home layout, can the system generate a coherent alarm installation proposal?

This architecture is intentionally simple so it can be built and maintained by **one person using Cursor as an AI coding assistant**.

---

## MVP Philosophy

This project should be built with the following principles:

1. **Keep the architecture small**
2. **Prefer files over infrastructure**
3. **Prefer deterministic rules over AI**
4. **Prefer debug visibility over elegance**
5. **Prefer a working planner over a complete platform**
6. **Do not build production complexity too early**

This means:

- no microservices
- no distributed systems
- no event bus
- no queue system
- no cloud deployment assumptions
- no database for Milestone -1
- no frontend application for Milestone -1
- no automatic floorplan understanding yet

---

## High-Level Architecture

The MVP architecture is made of only **two major parts**:

### 1. Planner Core
This is the actual product logic.

It takes a structured input and produces:
- zones
- device placements
- reasons
- warnings
- proposal output

### 2. Input Adapter
This converts external input into the structured format that the planner needs.

For **Milestone -1**, the input adapter is:
- JSON fixture loader (`io_json.load_fixture`)
- **Overlay-to-matrix converter** (`acala_core.overlay_to_matrix`): converts approved overlay JSON (walls, doors, windows, semantic markers in image coordinates) into planner-ready matrix JSON. See **`docs/OVERLAY_JSON_CONTRACT.md`** for the overlay schema and **`docs/NEXT_DEFINITIONS_MVP_FLOORPLAN_TO_MATRIX.md`** for the product flow.

For later milestones, the input adapter may also include:
- assisted floorplan annotation tool (editor UI)
- structural detection (image → first-draft overlay)

---

## System Diagram

```text
Synthetic Fixture JSON
        ↓
     io_json.py
        ↓
   Scenario Model
        ↓
   grid_utils.py
        ↓
      zones.py
        ↓
  engine_alarm.py
        ↓
 InstallationProposal
        ↓
 debug_render.py / JSON output
```

This is the full MVP pipeline.

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
│  ├─ fixtures/
│  │  └─ synthetic/
│  └─ expected/
├─ src/
│  ├─ model.py
│  ├─ io_json.py
│  ├─ grid_utils.py
│  ├─ zones.py
│  ├─ engine_alarm.py
│  ├─ debug_render.py
│  └─ main.py
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

This is enough for the MVP.

---

## Architectural Layers

## 1. Domain Model Layer
### File
`src/model.py`

### Responsibility
This is the central contract of the system.

It defines the internal objects used by all modules:
- scenario
- grid
- room
- semantic element
- zone
- device placement
- installation proposal

### Why it matters
This is the most important part of the architecture.

If the domain model is stable, the input method can change later without breaking the planning engine.

### Design rule
All other modules should depend on this model.
The model should not depend on the rest of the application.

---

## 2. Input/Output Layer
### File
`src/io_json.py`

### Responsibility
This module reads and writes structured JSON files.

Its job is to:
- load synthetic fixtures
- validate input shape
- convert raw JSON into model objects
- save proposal outputs
- save summary/debug metadata if needed

### MVP decision
Use JSON files only.
Do not add a database in Milestone -1.

### Why
File-based workflows are:
- faster to build
- easier to inspect
- easier to version with Git
- simpler for Cursor-driven development

---

## 3. Grid Utility Layer
### File
`src/grid_utils.py`

### Responsibility
This module provides low-level helpers for matrix and spatial logic.

Examples:
- bounds checking
- neighborhood lookup
- distance calculations
- indoor/outdoor adjacency
- line-of-sight helpers
- wall collision checks
- radius expansion helpers

### Design rule
This module should not know business rules about alarm devices.
It should only provide reusable geometry and grid logic.

---

## 4. Zone Generation Layer
### File
`src/zones.py`

### Responsibility
This module transforms structure into planning zones.

It should generate:
- red zones
- gray zones
- prohibited zones

### Why separate it
This stage makes the planner easier to debug.

Instead of going directly from matrix to placement, the system goes through a meaningful intermediate layer:
- matrix
- zones
- placements

That makes failures easier to isolate.

### MVP approach
Zone logic should be deterministic and readable.

---

## 5. Alarm Planning Engine
### File
`src/engine_alarm.py`

### Responsibility
This is the core business logic.

It should:
- read the validated scenario
- apply hard constraints
- generate candidate positions
- score candidates
- choose final placements
- generate the final proposal

### Device scope for MVP
- Panel
- Keyboard
- Magnetic sensor
- PIR
- PIRCam
- Indoor siren
- Outdoor siren

**Exact behaviour** (zones, magnetics, PIRs, sirens, profile matrix) is documented in **`docs/alarm_engine.md`**.

### Design rule
This module should be deterministic.
Given the same input, it should return the same output.

### MVP approach
Use:
- readable heuristics
- hard constraints
- simple candidate scoring
- greedy or straightforward selection

Avoid:
- machine learning
- search-heavy optimization
- probabilistic reasoning
- solver-heavy architecture

---

## 6. Debug Rendering Layer
### File
`src/debug_render.py`

### Responsibility
This module renders intermediate and final states for inspection.

It may render:
- matrix layout
- room layout
- zone map
- final placements
- optional text summary

### Why it matters
For this MVP, visualization is one of the fastest debugging tools.

It is much easier to inspect:
- wrong zones
- wrong candidate placement
- wall collisions
- bad entry assumptions

when the output is visible.

### MVP decision
A simple renderer is enough:
- ASCII
- simple image output
- simple color-coded map

Do not build a polished UI yet.

---

## 7. Thin Entrypoint
### File
`src/main.py`

### Responsibility
This module should only orchestrate the pipeline.

Its role is:
- load input
- call planner
- save results
- optionally trigger debug render

### Design rule
No business logic here.

---

## Core Data Flow

The MVP should follow this exact flow:

### Step 1 — Load fixture
A synthetic JSON fixture is loaded from disk.

### Step 2 — Validate and parse
The fixture is validated and converted into internal model objects.

### Step 3 — Build grid context
Grid helpers prepare the matrix and spatial interpretation.

### Step 4 — Build zones
The system generates red/gray/prohibited zones.

### Step 5 — Plan devices
The engine places:
- panel
- keyboard
- magnetics
- motion devices
- sirens

### Step 6 — Produce proposal
The planner returns an `InstallationProposal`.

### Step 7 — Render and export
The result is written to JSON and optionally rendered visually.

---

## Internal Contract

The core internal contract should be stable and small.

### Minimum objects
The architecture should support at least these concepts:

- Scenario
- Grid / cells
- Room
- Element
- Zone
- DevicePlacement
- InstallationProposal

### Why this matters
This contract is the boundary between:
- input adaptation
- planning logic
- output rendering

It allows the system to stay modular without becoming complex.

---

## Suggested Module Responsibilities

## `model.py`
Should contain:
- enums
- dataclasses or Pydantic models
- scenario structure
- proposal structure

Should not contain:
- planner logic
- file I/O
- rendering

---

## `io_json.py`
Should contain:
- fixture loading
- fixture validation
- proposal export

Should not contain:
- placement logic
- zone logic

---

## `grid_utils.py`
Should contain:
- spatial helper functions
- coordinate helpers
- adjacency logic
- collision checks

Should not contain:
- security business rules

---

## `zones.py`
Should contain:
- functions to create red zones
- functions to create prohibited zones
- optional gray zone generation

Should not contain:
- final device selection

---

## `engine_alarm.py`
Should contain:
- device placement logic
- candidate scoring
- hard constraints
- final proposal assembly

Should not contain:
- direct file loading
- rendering logic

---

## `debug_render.py`
Should contain:
- matrix rendering
- zone rendering
- placement rendering

Should not contain:
- planner logic

---

## Simple Runtime Modes

The MVP only needs a few runtime modes.

### Mode 1 — Run one fixture
Input:
- one synthetic fixture

Output:
- one proposal
- one debug render

### Mode 2 — Render one fixture
Input:
- one synthetic fixture

Output:
- visual artifact for inspection

### Mode 3 — Benchmark synthetic suite
Input:
- all synthetic fixtures

Output:
- all proposals
- summary metrics
- regression comparison

That is enough for Milestone -1.

---

## Why No Database Yet

A database is unnecessary for Milestone -1 because:

- fixtures are hand-authored
- outputs are small
- version control is enough
- debugging is easier with files
- schema changes will happen frequently

A database can be added later if the project reaches:
- many real plans
- user corrections
- historical comparisons
- annotation workflows

But for the MVP, files are the correct choice.

---

## Why No API Yet

An API is not needed in Milestone -1 because:
- the system is not being consumed by multiple clients
- the workflow can run locally from scripts
- the priority is core planner validation

If needed later, a thin API can be added on top of the planner core.
It should not influence the MVP architecture now.

---

## Why No Frontend Yet

A frontend app would slow down the MVP.

For Milestone -1, the goal is:
- validate planner behavior
- inspect outputs
- tune rules

That can be done using:
- fixture files
- scripts
- rendered debug images

A frontend only becomes important when:
- real-floorplan annotation starts
- non-technical users need interaction
- correction workflows must be tested

---

## Decision: Deterministic Planner First

The MVP planner should be deterministic.

### Why
Because the main value is:
- reasoning about coverage
- applying clear security rules
- producing inspectable results

Deterministic logic is better for this phase because it is:
- easier to test
- easier to debug
- easier to explain
- easier to modify with Cursor

### Future possibility
Machine learning may later assist:
- floorplan recognition
- room classification
- symbol detection

But the planning core should remain mostly rule-based.

---

## Suggested Design Principles

### 1. Single source of truth
All modules should operate on the same internal model.

### 2. Clear stage boundaries
Each stage should have one responsibility.

### 3. Easy debugging
Intermediate outputs should always be inspectable.

### 4. Small files, small modules
Keep modules focused and readable.

### 5. No premature abstraction
Do not invent generic frameworks too early.

### 6. Keep business logic visible
Alarm rules should remain easy to inspect and edit.

---

## MVP Error Handling Strategy

Keep error handling simple.

### Input errors
Reject invalid fixtures clearly.

### Planner errors
Fail fast with readable messages.

### Rendering errors
Do not block proposal creation if rendering fails.

### Goal
The system should always make it obvious:
- what failed
- in which stage
- on which fixture

---

## Recommended Output Artifacts

For each fixture run, the system should produce:

- proposal JSON
- optional summary JSON
- optional rendered PNG or text output
- optional benchmark row

This makes manual review easy.

---

## Example MVP Command Flow

```bash
python scripts/run_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/render_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/benchmark_synthetic.py
pytest tests/
```

These commands are enough to support the milestone.

---

## Future Extension Path

Only after the planner core is stable, the architecture may expand.

### Likely next extension
Add an assisted real-floorplan input layer.

This could become:
- `floorplan_adapter.py`
- `annotate_floorplan.py`

Its job would be to convert real plans into the same internal scenario model.

### Important rule
The planner core should not need major redesign when this happens.

That is why the internal contract is so important.

---

## What This MVP Architecture Explicitly Avoids

This architecture intentionally avoids:

- microservices
- cloud-native design
- distributed architecture
- message queues
- background workers
- user authentication
- web dashboard
- database-backed persistence
- full production observability stack
- automatic floorplan AI pipeline

All of those would add complexity without helping Milestone -1 succeed.

---

## Final Recommendation

The MVP architecture should stay extremely simple:

```text
Fixture JSON
   ↓
Loader
   ↓
Scenario Model
   ↓
Zone Builder
   ↓
Alarm Engine
   ↓
Proposal JSON + Debug Render
```

That is the right architecture for this stage because it is:

- fast to build
- easy to test
- easy to understand
- easy to evolve
- realistic for one person using Cursor

---

## Architecture Decision Summary

### Keep
- one Python codebase
- file-based workflow
- small focused modules
- deterministic planner
- separate zone generation
- debug rendering

### Avoid
- production platform patterns
- infrastructure-heavy decisions
- large UI investment
- ML in the planner core
- premature automation of floorplan parsing

---

## Current Scope Alignment
This architecture is aligned with:

- `PROJECT_PLAN.md`
- `MILESTONE_-1.md`

Specifically:
- Milestone -1 uses only synthetic fixtures
- the planner is the core product
- floorplan ingestion comes later
- the implementation is optimized for one-person development

---

## Next Recommended Document
After this architecture file, the most useful next document is:

**TEST_STRATEGY.md**

That file should define:
- unit test scope
- scenario test scope
- regression strategy
- acceptance criteria by milestone
