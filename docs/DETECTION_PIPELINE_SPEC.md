# DETECTION_PIPELINE_SPEC.md

## Title
Detection Pipeline Specification — MVP Floorplan to Matrix

## Purpose
This document defines the MVP detection pipeline for transforming a **PDF/image floorplan** into an initial machine-readable structural draft.

This draft is **not final**.
It is an automatically generated interpretation that will later be shown to the client for correction and approval.

The pipeline target is:

**PDF/image -> normalized image -> structural detection -> detection draft -> hybrid correction flow**

---

# 1. Detection Philosophy

The MVP detection layer does **not** need to understand the floorplan perfectly.

Its role is to produce a **useful first draft** that:
- gives the client a strong starting point
- reduces manual work
- preserves enough structure to allow correction
- can later be converted into matrix form

The detection layer should therefore optimize for:
- useful structure
- explainable output
- fast iteration
- compatibility with correction UI

It should **not** optimize for full automation in the first version.

---

# 2. Input Types

The MVP should accept:

- PDF
- PNG
- JPG / JPEG

---

# 3. Detection Pipeline Stages

The recommended MVP detection pipeline is:

1. file ingestion
2. normalization
3. structural image preprocessing
4. wall candidate detection
5. opening candidate detection
6. interior/exterior estimation
7. draft generation
8. handoff to correction layer

---

# 4. Stage 1 — File Ingestion

## 4.1 Accepted input
- single-page PDF
- image files

## 4.2 MVP constraints
For the first version:
- assume one floorplan per upload
- assume one page per PDF
- ignore multi-page architectural sets

## 4.3 Output of ingestion
A normalized input object with:
- source type
- file name
- rendered image path
- image width
- image height

---

# 5. Stage 2 — Normalization

The uploaded document should be converted into a working image representation.

## 5.1 PDF rendering
PDF should be rendered to image at a reasonable working resolution.

## 5.2 Image normalization
Apply:
- grayscale conversion
- optional contrast normalization
- optional denoising
- optional thresholding / binarization

## 5.3 Goal
Create a stable working image for structural detection.

---

# 6. Stage 3 — Structural Image Preprocessing

This stage prepares the image for line and contour extraction.

## Recommended operations
- thresholding
- morphology
- line enhancement
- contour cleanup
- noise suppression

## Goal
Make walls and major structural strokes more prominent.

---

# 7. Stage 4 — Wall Candidate Detection

This is the first essential detection objective.

## MVP objective
Detect:
- dominant wall lines
- wall boundaries
- likely room separators
- outer boundary candidates

## Expected output
A set of **wall candidates**, not necessarily final walls.

## Representation
Wall candidates should be represented as structured objects, for example:
- start point
- end point
- confidence
- source = detected

---

# 8. Stage 5 — Opening Candidate Detection

The next goal is to identify likely openings in walls.

## MVP objective
Detect likely:
- door candidates
- window candidates

## Important note
These are only candidates.
The user will confirm or correct them later.

## Representation
Each candidate should include at least:
- type guess (`door` or `window`)
- position
- approximate span
- orientation
- confidence

---

# 9. Stage 6 — Interior/Exterior Estimation

The system should produce an approximate spatial interpretation.

## MVP objective
Estimate:
- likely indoor area
- likely outdoor area
- boundary separation

## Why this matters
Even if imperfect, this gives the correction layer a meaningful first interpretation.

---

# 10. Stage 7 — Detection Draft Output

The output of the detection layer should **not** go directly to final matrix JSON.

It should generate a **Detection Draft**.

## Detection Draft contents
Suggested fields:
- document metadata
- rendered image size
- wall candidates
- opening candidates
- indoor/outdoor draft mask
- optional confidence fields
- status = detected

---

# 11. Recommended Detection Draft Shape

```json
{
  "document_id": "draft_001",
  "image_width": 2400,
  "image_height": 1600,
  "status": "detected",
  "walls": [
    {
      "id": "wall_1",
      "x1": 120,
      "y1": 200,
      "x2": 820,
      "y2": 200,
      "confidence": 0.91,
      "source": "detected"
    }
  ],
  "doors": [
    {
      "id": "door_1",
      "x": 260,
      "y": 200,
      "width": 60,
      "orientation": "horizontal",
      "confidence": 0.68,
      "source": "detected"
    }
  ],
  "windows": [],
  "regions": {
    "indoor_mask": "reference_or_path",
    "outdoor_mask": "reference_or_path"
  }
}
```

This is only a directional example.

---

# 12. What the MVP Should Detect Automatically

## Yes
- main walls
- secondary wall separators if clear
- likely openings
- rough indoor/outdoor separation

## No
Do not try to detect automatically in the first version:
- room names
- room types
- electric board
- heat source
- true main entry
- furniture
- text semantics
- full symbol legend interpretation

Those should be user-confirmed later.

---

# 13. Confidence Handling

The MVP does not need sophisticated confidence UX, but the detection system should internally distinguish between:
- strong candidates
- weak candidates

## Suggested use
Low-confidence objects can still be shown, but visually marked as uncertain in the correction layer.

---

# 14. Conversion Boundary

The detection stage should end at:
**Detection Draft**

It should not:
- generate final planner JSON
- auto-approve structure
- bypass user correction

This is critical for MVP safety.

---

# 15. Recommended Technical Stack

## Backend / processing
- FastAPI
- PyMuPDF for PDF rendering
- OpenCV for preprocessing and structural extraction
- optional Shapely for geometry cleanup

## Why
This stack is realistic, available, and well aligned with the current Python-based project.

---

# 16. Complexity / Usability / Wow

## Complexity
**Medium**

Because the MVP only aims for structural draft generation, not semantic understanding.

## Usability
**High**, if the draft is good enough to reduce manual correction.

## Wow
**High**
because the user uploads a plan and immediately sees a machine-generated structural interpretation.

---

# 17. Build Order Recommendation

## Step 1
PDF/image ingestion

## Step 2
Image normalization

## Step 3
Wall detection

## Step 4
Opening candidates

## Step 5
Indoor/outdoor draft

## Step 6
Detection Draft JSON export

## Step 7
Handoff to correction layer

---

# 18. Definition of Done

This detection spec is fulfilled when the system can:

- accept PDF/image
- normalize the input
- produce structural wall candidates
- produce opening candidates
- estimate indoor/outdoor draft
- export a detection draft
- pass that draft into the correction workflow

---

# 19. Final Recommendation

The detection layer should be treated as a **draft generator**, not a final truth generator.

The MVP wins if:
- the draft is useful
- the correction step is simple
- the final approved matrix is reliable

That is the correct balance between automation and control.
