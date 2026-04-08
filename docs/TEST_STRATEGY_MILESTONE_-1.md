# TEST_STRATEGY_MILESTONE_-1.md

## Title
Test Strategy — Milestone -1

## Scope
This document defines the testing strategy for **Milestone -1: Synthetic Matrix Prototype**.

Milestone -1 is the first executable validation phase of the project.
Its purpose is to prove that the core planning engine can generate a useful alarm installation proposal from a **synthetic structured matrix**, without any real floorplan ingestion.

This test strategy is intentionally simple and practical for:
- one person
- local development
- Cursor-assisted implementation
- fast iteration
- low overhead

---

## Main Objective of Testing
The objective of testing in this milestone is not to prove production readiness.

The objective is to answer these questions:

1. can synthetic fixtures be loaded reliably?
2. can the system build a valid internal scenario from them?
3. can zones be generated consistently?
4. can the planner produce coherent outputs?
5. can regressions be detected quickly after rule changes?

---

## What We Are Testing
Milestone -1 covers the following components:

- fixture loading
- fixture validation
- internal scenario/model creation
- grid utilities
- zone generation
- alarm placement engine
- debug rendering
- synthetic benchmark runner

---

## What We Are Not Testing Yet
The following are out of scope for this milestone test strategy:

- image upload
- PDF parsing
- OCR
- automatic wall detection
- room detection from floorplan images
- frontend UI workflows
- API integration
- cloud deployment
- performance at scale
- multi-user concurrency
- production monitoring

---

## Test Philosophy
This milestone should follow these rules:

1. **test small parts first**
2. **run tests often**
3. **prefer simple assertions over complicated frameworks**
4. **use synthetic fixtures as the main integration test layer**
5. **save baseline outputs before changing rules**
6. **make regressions visible quickly**

Because this is a one-person MVP, the test strategy should optimize for:
- fast feedback
- low ceremony
- easy maintenance
- confidence during rule iteration

---

## Test Layers

## Layer 1 — Unit Tests
### Goal
Validate small isolated behaviors.

### Modules covered
- `model.py`
- `io_json.py`
- `grid_utils.py`
- `zones.py`
- selected parts of `engine_alarm.py`

### Examples
- invalid enum values are rejected
- fixture dimensions match cell array dimensions
- coordinates outside grid are rejected
- neighborhood lookup behaves correctly
- opening adjacent to outdoor is correctly identified
- prohibited radius expansion behaves as expected

### Purpose
Unit tests should catch low-level bugs early before they appear in full scenario runs.

---

## Layer 2 — Scenario Tests
### Goal
Validate that a full synthetic fixture produces a complete and sane result.

### Scope
For each synthetic fixture:
- load fixture
- build scenario
- generate zones
- run planner
- inspect final proposal object

### Assertions
At minimum:
- no crash
- valid proposal object returned
- at least expected device families exist
- no placement inside walls
- no placement outside the grid
- no placement in outdoor cells
- no placement in prohibited cells unless explicitly flagged

### Purpose
Scenario tests are the main integration tests of this milestone.

---

## Layer 3 — Visual Debug Review
### Goal
Catch errors that are easier to see than to assert.

### Scope
For each synthetic fixture and security profile:
- render matrix
- render zones
- render final placements

### Human review questions
- do red zones appear where expected?
- do prohibited zones appear around problem areas?
- is the panel placed in a reasonable location?
- is the keyboard near the main entry?
- are motion sensors placed in useful positions?
- are sirens in obviously wrong places?
- do placements look commercially sensible?

### Purpose
Visual review is essential in this milestone because many spatial mistakes are obvious visually but hard to encode at first.

---

## Layer 4 — Regression Tests
### Goal
Detect unwanted behavior changes after rule updates.

### Scope
For each synthetic fixture, store a baseline summary such as:
- device count by type
- warning count
- out-of-standard count
- estimated red-zone coverage
- number of prohibited violations
- selected high-level placement checks

### Important note
Exact coordinates do not need to be frozen too early if scoring is still evolving.
Instead, freeze **stable behavior metrics** first.

### Purpose
Regression tests protect the project from accidental degradation while rules evolve.

---

## Synthetic Fixture Coverage Plan

The synthetic benchmark set should include at least these fixtures:

1. `studio_apartment.json`
2. `apartment_1br.json`
3. `apartment_2br.json`
4. `house_small_front_back.json`
5. `house_window_heavy.json`
6. `house_open_plan.json`
7. `house_corridor.json`
8. `house_irregular.json`

These should cover:
- small footprint layouts
- multiple rooms
- multiple openings
- corridor logic
- open-plan logic
- perimeter-heavy logic
- irregular geometry

---

## Security Profile Coverage
Every fixture should be tested in all 3 profiles:

- `min`
- `optimal`
- `max`

### Why
Because profile-specific logic is part of the product value.

At minimum, the tests should confirm:
- `min` produces fewer devices than `optimal` or `max`
- `max` does not reduce essential coverage
- profile changes actually influence the proposal

---

## Test Categories by Component

## 1. Fixture Loading Tests
### Purpose
Ensure fixture files are structurally valid.

### Test cases
- valid fixture loads successfully
- missing required field fails
- invalid cell category fails
- invalid security profile fails
- mismatched width/height vs cell matrix fails
- invalid element coordinates fail

### Pass condition
Loader must reject bad inputs clearly and consistently.

---

## 2. Model Validation Tests
### Purpose
Ensure internal objects are valid and safe to use.

### Test cases
- device placement requires valid coordinates
- zone type must be one of allowed values
- installation proposal requires placement list
- unsupported enum values fail
- optional fields default cleanly if designed to do so

### Pass condition
The internal model should prevent invalid planner state as early as possible.

---

## 3. Grid Utility Tests
### Purpose
Ensure matrix operations are trustworthy.

### Test cases
- inside/outside bounds checks
- neighbor calculation for center cells
- neighbor calculation for edge cells
- radius expansion behavior
- wall blocking behavior
- exterior opening identification
- coordinate conversion consistency

### Pass condition
Spatial helper functions return predictable results for normal and edge cases.

---

## 4. Zone Generation Tests
### Purpose
Ensure the planner has meaningful intermediate zones.

### Test cases
- red zones generated from accessible doors
- red zones generated from accessible windows
- prohibited zones generated around heat source
- prohibited zones generated around cold source if applicable
- prohibited zones stay within sensible area
- zones do not get placed outside grid bounds

### Pass condition
Zones are coherent and stable for all synthetic fixtures.

---

## 5. Alarm Placement Tests
### Purpose
Ensure device placement logic is reasonable and constrained.

### Test cases
- panel is placed in a permitted area
- keyboard is placed near main entry
- magnetic sensors are added to relevant openings
- motion devices avoid prohibited areas
- motion devices are not placed in walls
- indoor siren is placed in a sensible indoor position
- outdoor siren is placed in a sensible perimeter position if supported
- device count changes by security level

### Pass condition
Placements should be valid, explainable, and profile-sensitive.

---

## 6. Proposal Consistency Tests
### Purpose
Ensure the final output is coherent.

### Test cases
- proposal contains placements list
- each placement includes a device type
- each placement includes a reason
- warnings are list-like and serializable
- proposal can be exported to JSON

### Pass condition
Proposal outputs should be machine-readable and human-reviewable.

---

## 7. Debug Rendering Tests
### Purpose
Ensure visual outputs are generated reliably.

### Test cases
- matrix render completes without error
- zone render completes without error
- proposal render completes without error
- output file exists after render
- render does not mutate scenario data

### Pass condition
Rendering supports debugging and does not interfere with planning logic.

---

## Minimal Acceptance Assertions Per Fixture
For every fixture/profile combination, assert at least:

- fixture loads successfully
- planner returns a proposal
- proposal contains at least one placement
- no placement is outside grid bounds
- no placement is on a wall
- no placement is on outdoor cells
- keyboard exists if the scenario has a main entry
- panel exists unless the scenario explicitly blocks it
- at least one detection strategy exists for intrusion paths in normal scenarios

---

## Manual Review Checklist
For visual/manual review, use this checklist:

### Structure
- walls look correct
- indoor/outdoor split looks correct
- entry points are visible
- windows are correctly represented

### Zones
- red zones align with accessible openings
- prohibited zones appear around hazard areas
- gray zones, if used, are sensible

### Placements
- panel location is plausible
- keyboard is close to entry
- motion devices face useful directions
- motion devices are not blocked by walls
- device count is not obviously excessive
- proposal seems installable in real life

### Output quality
- reasons are understandable
- warnings are useful
- out-of-standard flags are used correctly

---

## Pass/Fail Gates for Milestone -1

## Gate A — Fixture Integrity Gate
This gate passes when:
- at least 2 initial fixtures load successfully
- invalid fixtures are rejected cleanly
- core schema is stable enough to continue

Do not proceed to broad planner work before this gate passes.

---

## Gate B — Zone Logic Gate
This gate passes when:
- red zones and prohibited zones are generated on the initial fixtures
- visual review shows expected behavior
- no obvious zone generation bugs remain

Do not proceed to full placement work before this gate passes.

---

## Gate C — Planner Coherence Gate
This gate passes when:
- the planner returns coherent proposals on the initial fixtures
- no major invalid placements occur
- security profiles produce different outputs

Do not scale to all fixtures before this gate passes.

---

## Gate D — Synthetic Suite Gate
This gate passes when:
- all 8 fixtures run successfully
- all 3 profiles run successfully
- baseline metrics are recorded
- no critical regression remains open

This is the main completion gate for Milestone -1.

---

## Metrics to Track
For Milestone -1, the metrics should stay simple.

Track at least:
- number of fixtures passing
- number of fixture/profile combinations passing
- device count by type
- warning count
- out-of-standard count
- estimated red-zone coverage
- prohibited placement count
- runtime per scenario, only as an informational metric

These metrics should be saved in benchmark summaries.

---

## Baseline Strategy
When the planner becomes stable enough, save a baseline for every fixture/profile combination.

### Suggested baseline contents
- fixture name
- security profile
- placement counts by device type
- warnings count
- out-of-standard count
- red-zone coverage estimate
- notes

### Why
This allows rule changes to be evaluated against previous behavior without freezing every exact coordinate too early.

---

## Failure Classification
When a test fails, classify it into one of these buckets:

### Category 1 — Input/schema failure
Examples:
- malformed fixture
- invalid enum
- coordinate mismatch

### Category 2 — Spatial logic failure
Examples:
- zone outside grid
- neighbor logic broken
- invalid wall crossing

### Category 3 — Planner failure
Examples:
- no panel placed
- keyboard missing near entry
- motion sensor placed in prohibited cell

### Category 4 — Output/render failure
Examples:
- export fails
- render file not generated
- summary malformed

This helps prioritize fixes quickly.

---

## Recommended Test Commands
These are placeholders and can be adapted.

```bash
pytest tests/test_model.py
pytest tests/test_io_json.py
pytest tests/test_grid_utils.py
pytest tests/test_zones.py
pytest tests/test_engine_alarm.py
pytest tests/test_regression_synthetic.py
python scripts/run_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/render_fixture.py data/fixtures/synthetic/studio_apartment.json
python scripts/benchmark_synthetic.py
```

---

## Suggested Test Execution Rhythm

### During daily development
Run:
- focused unit tests for the module being edited
- one or two fixture runs
- one visual render for the changed scenario

### Before committing
Run:
- all unit tests
- scenario tests for affected fixtures
- synthetic benchmark for at least the main fixtures

### Before marking Milestone -1 complete
Run:
- full test suite
- full synthetic benchmark
- full visual/manual review on all base fixtures
- save/update benchmark baseline

---

## Recommended First Test Backlog

### Step 1
Create fixture validation tests.

### Step 2
Create grid bounds and adjacency tests.

### Step 3
Create zone-generation tests for 2 initial fixtures.

### Step 4
Create first planner scenario tests.

### Step 5
Create render smoke tests.

### Step 6
Create benchmark/regression summary output.

This order keeps testing aligned with implementation order.

---

## Definition of Done for Testing
The test strategy for Milestone -1 is considered successfully executed when:

- the core modules have unit coverage for critical logic
- every synthetic fixture can be run end to end
- every fixture/profile combination has at least basic assertions
- visual review has been performed on all base fixtures
- a baseline benchmark summary exists
- rule changes can be validated without guesswork

---

## Final Recommendation
For this milestone, the test strategy should stay simple and practical:

- unit tests for low-level logic
- scenario tests for full fixture behavior
- visual review for spatial sanity
- regression summaries for safe iteration

That is enough to support a strong MVP without turning the project into a heavy QA process.

---

## Related Documents
This file should be used together with:

- `PROJECT_PLAN.md`
- `MILESTONE_-1.md`
- `ARCHITECTURE.md`
