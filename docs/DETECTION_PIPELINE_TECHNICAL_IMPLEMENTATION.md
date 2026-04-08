# DETECTION_PIPELINE_TECHNICAL_IMPLEMENTATION.md

## Title
Detection Pipeline — Technical Implementation Plan

## Purpose
This document translates `DETECTION_PIPELINE_SPEC.md` into a **technical implementation guide** for developers.

It is written from the perspective of a **technical analyst** and is intended to help a developer implement the detection segment step by step inside the project.

The goal is to turn this functional flow:

**PDF/image -> normalized image -> structural detection -> detection draft -> hybrid correction flow**

into:
- concrete modules
- concrete tools
- development stages
- test strategy
- acceptance criteria

---

# 1. Technical Objective

Build the first working version of the **detection pipeline** that can:

1. accept a PDF or image
2. normalize it into a working image
3. detect basic structural information
4. generate a `detection draft`
5. hand that draft to the next correction step

This implementation does **not** need to solve all floorplan understanding problems.
It only needs to produce a **useful, debuggable, testable draft**.

---

# 2. Technical Scope of the First Version

## In scope
- file ingestion
- PDF rendering
- image normalization
- wall candidate detection
- opening candidate detection
- rough indoor/outdoor estimation
- draft JSON export
- debug image export
- automated tests

## Out of scope
- OCR
- room label detection
- semantic symbol interpretation
- automatic electric board detection
- automatic heat source detection
- advanced ML models
- multi-floor support
- multi-page PDF support

---

# 3. Recommended Technical Stack

## Backend language
- Python

## Web/API layer
- FastAPI

## PDF rendering
- PyMuPDF

## Image processing
- OpenCV

## Geometry support
- Shapely (optional but recommended for cleanup and line consolidation)

## Data structures
- Python dataclasses or Pydantic models

## Testing
- pytest

## Debug/inspection artifacts
- PNG overlays
- JSON draft outputs

---

# 4. Proposed Code Architecture

The detection pipeline should be implemented as a dedicated subsystem.

## Suggested module structure

```text
src/
  detection/
    __init__.py
    models.py
    ingest.py
    normalize.py
    wall_detection.py
    opening_detection.py
    region_estimation.py
    draft_builder.py
    debug_render.py
    pipeline.py

scripts/
  detect_floorplan.py

tests/
  test_detection_ingest.py
  test_detection_normalize.py
  test_wall_detection.py
  test_opening_detection.py
  test_region_estimation.py
  test_detection_pipeline_e2e.py

data/
  fixtures/
    detection/
      ...
```

---

# 5. Responsibilities by Module

## 5.1 `models.py`
Defines internal typed structures.

### Suggested models
- `DetectionInput`
- `RenderedImage`
- `WallCandidate`
- `OpeningCandidate`
- `RegionDraft`
- `DetectionDraft`

### Why
This avoids passing raw dictionaries between processing steps.

---

## 5.2 `ingest.py`
Handles file input and rendering decisions.

### Responsibilities
- validate input extension
- detect if input is PDF or image
- render PDF first page to image
- load image into OpenCV-compatible format
- return normalized `RenderedImage`

### Suggested functions
- `load_input(path: str) -> DetectionInput`
- `render_pdf_first_page(path: str, dpi: int) -> RenderedImage`
- `load_raster_image(path: str) -> RenderedImage`

---

## 5.3 `normalize.py`
Prepares the image for downstream detection.

### Responsibilities
- grayscale conversion
- denoise if needed
- contrast normalization if needed
- thresholding / binarization
- optional inversion depending on image style

### Suggested functions
- `to_grayscale(image)`
- `normalize_contrast(image)`
- `binarize(image, config)`
- `prepare_working_image(rendered_image, config)`

---

## 5.4 `wall_detection.py`
Detects structural wall candidates.

### Responsibilities
- line extraction
- contour-based wall inference
- horizontal/vertical dominance detection
- candidate cleanup

### Suggested functions
- `detect_wall_candidates(image, config) -> list[WallCandidate]`
- `merge_collinear_walls(candidates) -> list[WallCandidate]`
- `filter_small_wall_candidates(candidates, config)`

---

## 5.5 `opening_detection.py`
Detects possible doors and windows.

### Responsibilities
- search for interruptions in wall continuity
- identify likely opening spans
- classify opening candidates conservatively
- return uncertain candidates if needed

### Suggested functions
- `detect_opening_candidates(image, wall_candidates, config) -> list[OpeningCandidate]`
- `classify_opening_candidate(candidate, context)`

---

## 5.6 `region_estimation.py`
Builds rough indoor/outdoor estimation.

### Responsibilities
- estimate exterior reachability
- estimate interior contiguous space
- create masks or cell-like draft segmentation

### Suggested functions
- `estimate_indoor_outdoor(image, wall_candidates, opening_candidates, config) -> RegionDraft`

---

## 5.7 `draft_builder.py`
Builds the output contract for the next stage.

### Responsibilities
- convert detection objects to serializable draft
- inject metadata
- include confidence if available
- keep output stable and debuggable

### Suggested functions
- `build_detection_draft(input_data, rendered_image, walls, openings, regions, config) -> DetectionDraft`
- `draft_to_dict(draft) -> dict`

---

## 5.8 `debug_render.py`
Generates visual artifacts for inspection.

### Responsibilities
- overlay walls on source image
- overlay openings on source image
- render indoor/outdoor preview
- save debug PNG files

### Suggested functions
- `render_wall_debug(...)`
- `render_opening_debug(...)`
- `render_region_debug(...)`
- `render_detection_summary(...)`

---

## 5.9 `pipeline.py`
Orchestrates the whole detection flow.

### Responsibilities
- call all stages in sequence
- manage config
- return draft
- optionally write debug outputs

### Suggested function
- `run_detection_pipeline(input_path, config) -> DetectionDraft`

---

# 6. Suggested Processing Pipeline

## Step 1 — Ingestion
Input:
- PDF or image path

Output:
- rendered image object

## Step 2 — Normalization
Input:
- rendered image

Output:
- processed working image

## Step 3 — Wall detection
Input:
- normalized image

Output:
- wall candidates

## Step 4 — Opening detection
Input:
- normalized image + walls

Output:
- opening candidates

## Step 5 — Region estimation
Input:
- normalized image + walls + openings

Output:
- indoor/outdoor draft

## Step 6 — Draft building
Input:
- all prior outputs

Output:
- detection draft JSON structure

## Step 7 — Debug export
Input:
- draft + source image

Output:
- PNG debug assets

---

# 7. Development Stages

The code should not be developed all at once.
It should be built in phases with tests after each phase.

---

## Stage A — File ingestion and rendering
### Build
- support PDF and image input
- render first PDF page
- load raster image
- expose image metadata

### Tools
- PyMuPDF
- OpenCV

### Deliverables
- `ingest.py`
- `models.py` basic input/output models
- first CLI script

### Tests
- load JPG successfully
- load PNG successfully
- render first page of PDF successfully
- reject unsupported file type
- validate output width/height

### Acceptance criteria
Developer can run a command and obtain:
- image dimensions
- rendered preview object
- no downstream processing yet

---

## Stage B — Normalization
### Build
- grayscale conversion
- thresholding
- optional denoise
- optional inversion

### Tools
- OpenCV

### Deliverables
- `normalize.py`
- normalized debug PNG output

### Tests
- grayscale output shape correct
- binary image contains expected value range
- thresholding works on fixture images
- normalization does not crash on PDF-rendered image

### Acceptance criteria
Developer can generate a normalized image from each supported fixture.

---

## Stage C — Wall candidate detection
### Build
- line extraction strategy
- morphological enhancement
- candidate merging
- filtering of noise

### Tools
- OpenCV
- optional Shapely

### Deliverables
- `wall_detection.py`
- wall candidate model
- wall debug render

### Tests
- simple synthetic rectangle returns 4 dominant boundary candidates
- noisy fixture still returns non-empty walls
- very small artifacts are filtered
- merging reduces duplicate segments

### Acceptance criteria
The system can detect meaningful wall candidates on synthetic fixtures and example plans.

---

## Stage D — Opening candidate detection
### Build
- identify likely wall interruptions
- propose doors/windows
- assign orientation
- attach confidence

### Tools
- OpenCV
- geometry logic

### Deliverables
- `opening_detection.py`
- opening candidate model
- opening debug render

### Tests
- simple wall with known gap yields opening candidate
- horizontal and vertical openings both supported
- false positives limited on basic fixtures
- output schema valid

### Acceptance criteria
The system produces plausible opening candidates on test images.

---

## Stage E — Indoor/outdoor estimation
### Build
- estimate reachable exterior
- estimate interior space
- prepare masks or region summaries

### Tools
- OpenCV flood fill / segmentation logic
- optional Shapely

### Deliverables
- `region_estimation.py`
- region debug render

### Tests
- closed boundary yields indoor region
- exterior stays exterior
- disconnected noise does not dominate classification

### Acceptance criteria
System produces a rough but coherent indoor/outdoor interpretation.

---

## Stage F — Detection draft builder
### Build
- serializable detection draft
- metadata fields
- stable JSON structure

### Tools
- dataclasses / Pydantic
- json module

### Deliverables
- `draft_builder.py`
- draft export utility

### Tests
- output contains required fields
- walls serialize correctly
- openings serialize correctly
- region data serialize correctly
- contract remains stable

### Acceptance criteria
Developer can produce a detection draft JSON from one command.

---

## Stage G — End-to-end pipeline
### Build
- orchestrator
- CLI
- debug artifact generation

### Tools
- Python
- existing detection modules

### Deliverables
- `pipeline.py`
- `scripts/detect_floorplan.py`

### Tests
- full pipeline runs on image fixture
- full pipeline runs on PDF fixture
- draft JSON written
- debug PNGs written
- no exception on supported sample set

### Acceptance criteria
One command generates:
- detection draft JSON
- wall/opening/region debug images

---

# 8. CLI Recommendation

Provide one script for development and debugging.

## Suggested command

```bash
PYTHONPATH=src python -m scripts.detect_floorplan input/sample.pdf --output-dir outputs/detection/sample_001
```

## Suggested outputs
- `draft.json`
- `source.png`
- `normalized.png`
- `walls.png`
- `openings.png`
- `regions.png`
- `summary.png`

This will accelerate iteration significantly.

---

# 9. Configuration Strategy

The detection pipeline should not hardcode all thresholds.

## Recommended config areas
- PDF render DPI
- thresholding mode
- blur / denoise parameters
- minimum wall length
- opening minimum span
- merge distance tolerance
- region estimation sensitivity

## Recommendation
Use a dedicated config object or YAML/JSON config later.
For MVP, a Python config dataclass is enough.

---

# 10. Test Strategy

The testing approach should be layered.

## 10.1 Unit tests
Test each module in isolation.

### Examples
- PDF render dimensions
- threshold output type
- line merge logic
- opening classifier behavior

---

## 10.2 Synthetic fixture tests
Use simple generated images where expected structure is known.

### Examples
- rectangle room
- single wall with one gap
- two-room split
- outer boundary with clear exterior

This is critical because synthetic fixtures make assertions stable.

---

## 10.3 Regression tests with saved assets
Keep a small set of sample PDFs/images and compare:
- candidate counts
- expected draft fields
- output not empty
- visual diff if needed later

---

## 10.4 End-to-end tests
Run the whole pipeline from input file to detection draft.

### Examples
- sample PDF -> draft JSON
- sample image -> draft JSON
- debug files created
- contract remains valid

---

# 11. Recommended Test File Breakdown

```text
tests/
  test_detection_ingest.py
  test_detection_normalize.py
  test_wall_detection.py
  test_opening_detection.py
  test_region_estimation.py
  test_detection_draft_builder.py
  test_detection_pipeline_e2e.py
```

---

# 12. Fixture Strategy

Create a dedicated detection fixture set.

## Suggested fixture categories

### Synthetic simple
- one rectangular room
- corridor
- two-room split
- known openings

### Realistic simplified
- exported floorplan PNGs
- rendered PDF pages
- scanned plan examples

### Edge cases
- noisy scan
- low contrast PDF
- thick walls
- very narrow doors/windows

---

# 13. Debug Strategy

Detection work is much easier if every stage can be inspected visually.

## Always generate debug images during development
At least:
- normalized image
- wall candidates over source
- openings over source
- indoor/outdoor estimation
- combined summary

Without this, debugging will be much slower.

---

# 14. Definition of Done per Stage

Each stage is complete only when it has:

- code implemented
- dedicated tests
- at least one debug output
- one CLI-visible result
- no silent failures

---

# 15. Integration with Next Steps

The output of this pipeline should later feed the correction layer.

Therefore the detection implementation must preserve:
- stable IDs where useful
- geometry in image coordinates
- enough structure to be editable later

Do not optimize output only for internal experiments.
Optimize it for the **next UI step** as well.

---

# 16. Risks and Mitigations

## Risk 1 — Detection too weak
### Mitigation
Treat output as draft only and rely on correction layer.

## Risk 2 — Overfitting to synthetic fixtures
### Mitigation
Add a small but diverse real-image fixture set early.

## Risk 3 — Noisy results impossible to debug
### Mitigation
Require debug renders at each stage.

## Risk 4 — Contract drift
### Mitigation
Freeze draft builder tests early.

---

# 17. Recommended First Sprint

If the developer has to start now, the first sprint should include only:

1. input ingestion
2. PDF rendering
3. normalization
4. wall detection baseline
5. debug image export
6. basic tests

Do not start with openings and semantic complexity immediately.

That will reduce risk.

---

# 18. Recommended Second Sprint

1. opening candidate detection
2. indoor/outdoor estimation
3. detection draft export
4. end-to-end pipeline
5. more fixtures
6. regression tests

---

# 19. Final Technical Recommendation

The developer should implement the detection subsystem as a **modular, debuggable, test-driven pipeline**.

The first success criterion is not “perfect floorplan understanding”.
It is:

- stable ingestion
- meaningful structural draft
- reproducible debug outputs
- contract-ready handoff to the correction layer

That is the correct technical interpretation of the MVP.

#Adding here in Cursor.

# Detection Pipeline Refactor — Checkpoints

## Step 0 — Baseline

- [ ] `python -m scripts.run_detection data/fixtures/detection/simple_plan.jpg -o outputs/detection_drafts/simple_plan.json`
- [ ] `python -m scripts.render_detection_draft outputs/detection_drafts/simple_plan.json --width 80 --height 24`
- [ ] `PYTHONPATH=src pytest tests/ -q`

Keep this output as reference before refactor.

---

## Step 1 — Models and typing

**Goal**: Introduce typed models in `src/detection/models.py` without changing external behaviour.

- [ ] Create `src/detection/models.py` with:
  - [ ] `RenderedImage(path: Path, image: np.ndarray, width: int, height: int, source_type: str)`
  - [ ] `WallCandidate`
  - [ ] `OpeningCandidate`
  - [ ] `RegionDraft`
  - [ ] `DetectionDraft`
- [ ] Update `src/detection/ingest.py` to return `RenderedImage` instead of a loose tuple.
- [ ] Update `src/detection/normalize.py` and `src/detection/walls.py` signatures to accept/return these models internally.
- [ ] Keep `run_detection_pipeline` returning the same Detection Draft JSON.

**Checks**

- [ ] `PYTHONPATH=src pytest tests/test_detection_ingest.py` (new simple test).
- [ ] Baseline commands from Step 0 still produce the same JSON/ASCII.

---

## Step 2 — Module structure alignment

**Goal**: Match `DETECTION_PIPELINE_TECHNICAL_IMPLEMENTATION.md` module names via thin wrappers.

- [ ] Add:
  - [ ] `src/detection/wall_detection.py` importing from `walls.py`.
  - [ ] `src/detection/opening_detection.py` importing from `openings.py`.
  - [ ] `src/detection/region_estimation.py` importing from `regions.py`.
  - [ ] `src/detection/draft_builder.py` importing from `draft.py`.
  - [ ] `src/detection/pipeline.py` exposing `run_detection_pipeline`.
- [ ] Update `src/detection/__init__.py` and `scripts/run_detection.py` to use `detection.pipeline`.

**Checks**

- [ ] `PYTHONPATH=src pytest tests/test_detection_pipeline.py -q`
- [ ] Baseline commands from Step 0 still behave the same.

---

## Step 3 — Wall mask and indoor/outdoor masks

**Goal**: Build robust wall and indoor/outdoor masks.

- [ ] In `wall_detection.py`:
  - [ ] Implement `build_wall_mask(RenderedImage, list[WallCandidate], config) -> np.ndarray`.
  - [ ] Implement `close_outer_boundary(mask, config) -> np.ndarray` (morphology close).
  - [ ] (Optional) `skeletonize_wall_mask(mask) -> np.ndarray` for 1‑px walls.
- [ ] In `region_estimation.py`:
  - [ ] Implement `estimate_indoor_outdoor(wall_mask, config) -> RegionDraft` using flood‑fill from corners.
- [ ] Store masks in `RegionDraft` (full size or downsampled).

**Checks**

- [ ] `PYTHONPATH=src pytest tests/test_wall_detection.py -q` (new).
- [ ] `PYTHONPATH=src pytest tests/test_region_estimation.py -q` (new).
- [ ] Re‑run Step 0 commands: walls should be continuous and closed around the outer rectangle.

---

## Step 4 — Mask‑aware opening detection

**Goal**: Ensure doors/windows sit on real boundaries, not in the middle of rooms.

- [ ] In `opening_detection.py`:
  - [ ] Use `wall_mask` and `RegionDraft.indoor/outdoor` as inputs.
  - [ ] For each color‑based candidate:
    - [ ] Center must be on a wall pixel of the skeletonized wall mask.
    - [ ] Sampling along normal:
      - [ ] Window: one side indoor, other outdoor.
      - [ ] Interior door: indoor/indoor.
      - [ ] Main door: indoor/outdoor.
  - [ ] Snap candidate centerline onto the wall skeleton.

**Checks**

- [ ] `PYTHONPATH=src pytest tests/test_opening_detection.py -q` (new; uses `simple_plan.jpg`).
- [ ] ASCII render: no `D`/`W` in the middle of rooms; all openings aligned to `#`.

---

## Step 5 — Draft builder + debug rendering

**Goal**: Clean contract + visual debugging.

- [ ] Implement `build_detection_draft(...) -> DetectionDraft` and `draft_to_dict(...)` in `draft_builder.py`.
- [ ] Ensure `run_detection_pipeline` uses these and still returns same JSON shape.
- [ ] Implement `debug_render.py`:
  - [ ] wall overlay PNG,
  - [ ] opening overlay PNG,
  - [ ] region (indoor/outdoor) overlay PNG.

**Checks**

- [ ] `PYTHONPATH=src pytest tests/test_detection_pipeline_e2e.py -q`.
- [ ] Manually inspect PNG debug overlays for `simple_plan.jpg`.

---

## Step 6 — Final verification on simple and real plans

**Goal**: Confirm behaviour is robust beyond `simple_plan`.

- [ ] Add at least one more test image under `data/fixtures/detection/` (slightly more realistic).
- [ ] Run full suite:
  - [ ] `PYTHONPATH=src pytest tests/ -q`
- [ ] For each fixture (including new one), run:
  - [ ] `python -m scripts.run_detection ...`
  - [ ] `python -m scripts.render_detection_draft ...`
  - [ ] Visually confirm: closed outer walls, openings only on boundaries.
