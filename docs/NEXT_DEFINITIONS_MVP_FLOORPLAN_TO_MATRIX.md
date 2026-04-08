# NEXT_DEFINITIONS_MVP_FLOORPLAN_TO_MATRIX.md

## Title
Next Definitions — MVP Floorplan to Matrix

## Purpose
This document defines the **next product and technical decisions** for the MVP pipeline:

**PDF/image -> basic structural detection -> editable overlay -> client validation -> matrix -> JSON**

The goal is to move from a high-level architecture decision into a **clear implementation direction** that can be executed in Cursor.

This document does **not** define the final production system.
It defines the **next concrete MVP decisions**.

---

# 1. Current Product Direction

We have already chosen the following MVP path:

**PDF/image -> basic structural detection -> editable overlay -> client validation -> matrix -> JSON**

This means the system does not need to interpret the floorplan perfectly.
It only needs to:

1. generate a useful first structural draft
2. allow the client to correct it easily
3. convert the approved result into a clean matrix and JSON

The editable overlay is therefore a **core part of the MVP**, not a fallback.

---

# 2. Main Product Principle

## The MVP is not an “automatic floorplan reader”
The MVP is a **human-in-the-loop floorplan interpreter**.

That means:
- automatic detection gives a first draft
- the client validates and adjusts it
- only the approved result is used to build the matrix

This should shape all product decisions.

---

# 3. The Next Decisions We Need To Freeze

The next implementation decisions should be defined in this order:

1. what the editable overlay represents
2. what the client is allowed to edit
3. what the user flow looks like
4. what the intermediate data structure is before matrix generation
5. when the matrix is generated
6. what the output JSON contains

---

# 4. Decision 1 — What the Editable Overlay Represents

This is the most important design decision after choosing the MVP direction.

We have 3 conceptual options:

## Option A — Edit directly on the original image
The client sees the original PDF/image and edits directly on top of it.

### Pros
- natural and intuitive
- visually close to the source plan

### Cons
- harder to maintain a clean internal structure
- harder to keep geometry consistent
- harder to convert to matrix cleanly

---

## Option B — Edit a simplified structural overlay on top of the original image
The client sees:
- the original floorplan as background
- an editable structural layer on top

The overlay contains:
- walls
- doors
- windows
- semantic markers

### Pros
- best balance for MVP
- user still sees the original image
- internal representation stays structured
- easier conversion to matrix

### Cons
- slightly more work than image-only editing

---

## Option C — Edit directly in a matrix/grid editor
The client edits cells instead of geometry.

### Pros
- very easy to convert to JSON
- technically simple after matrix exists

### Cons
- poor user experience for first interaction
- too abstract for floorplan correction
- low wow factor

---

## Recommended decision
### Choose **Option B**
The client should edit a **structured overlay on top of the original image**.

This is the best MVP choice because it offers:
- good usability
- good internal consistency
- reasonable implementation cost
- strong visual confidence

---

# 5. Decision 2 — What the Overlay Contains

For the MVP, the overlay should contain only the minimum objects needed to generate the planner input.

## Overlay objects for MVP

### Structural
- wall segments
- door openings
- window openings

### Semantic
- main entry
- electric board
- heat source

### Optional later
- room labels
- cold source
- stairs
- restricted areas

---

## Important modeling rule
The overlay should distinguish between:

### Topology
Objects that define physical structure:
- walls
- doors
- windows

### Semantic markers
Objects that define planning meaning:
- main entry
- electric board
- heat source

This matches the schema rule already chosen:
- topology goes into `cells`
- semantic markers go into `elements`

---

# 6. Decision 3 — What the Client Can Edit

The client should not be allowed to do everything.
The MVP should expose only the tools needed to correct the first draft.

## Minimum editing actions for MVP

### Walls
- add wall segment
- move wall segment
- delete wall segment

### Doors
- add door
- move door
- delete door

### Windows
- add window
- move window
- delete window

### Semantic markers
- set main entry
- set electric board
- set heat source
- move those markers
- delete those markers

### Approval action
- approve overlay and continue

---

## What the client should NOT edit in MVP
Avoid exposing:
- room classification editing
- free polygon drawing for all objects
- arbitrary CAD-like tools
- complex rotation/orientation tools
- multi-floor navigation
- advanced snapping rules in first version

These would increase complexity too much.

---

# 7. Decision 4 — User Flow

The user experience should be simple and step-based.

## Recommended MVP flow

### Step 1 — Upload
The client uploads:
- PDF
- JPG
- PNG

### Step 2 — Automatic first draft
The system generates:
- image preview
- basic structural overlay

### Step 3 — Review structure
The client corrects:
- walls
- doors
- windows

### Step 4 — Review semantic markers
The client defines or confirms:
- main entry
- electric board
- heat source

### Step 5 — Approve
The client clicks approve.

### Step 6 — Generate matrix + JSON
The system converts the approved overlay into:
- matrix
- elements
- JSON

---

## Why this flow is good
It reduces cognitive load by separating:
- structure
- semantics
- final approval

This is better than showing everything at once.

---

# 8. Decision 5 — Intermediate Representation Before Matrix

This is the most important technical definition after the overlay choice.

Before generating the matrix, we should not work directly from raw pixels.
We should first create a **structured intermediate representation**.

## Recommended intermediate model

### DocumentImage
- source file reference
- rendered preview image size
- scale metadata if available

### OverlayModel
- walls
- doors
- windows
- semantic markers

### ApprovalState
- draft
- edited
- approved

This means the matrix should be generated from:
**approved overlay model**, not directly from the uploaded image.

---

## Why this matters
If the matrix is generated directly from image processing output:
- every detection error propagates immediately
- corrections become harder to reason about

If the matrix is generated from an approved overlay:
- conversion is deterministic
- geometry is much cleaner
- debugging is easier

---

# 9. Decision 6 — When the Matrix Is Generated

There are two possible strategies.

## Strategy A — Generate matrix early, then edit matrix
### Not recommended
This makes correction hard and too abstract.

## Strategy B — Generate matrix only after overlay approval
### Recommended
This keeps the user working in a meaningful visual mode.

---

## Final recommendation
The matrix should be generated **after client approval**.

That means:

**upload -> detect -> edit overlay -> approve -> matrix**

This is the cleanest flow.

---

# 10. Decision 7 — JSON Layers We Need

We should not jump directly from image to final planner JSON.
The MVP should use at least 2 JSON levels.

## Level 1 — Overlay JSON
Represents the client-approved editable structure.

Suggested contents:
- file reference
- canvas size
- walls
- doors
- windows
- semantic markers
- approval status

## Level 2 — Matrix JSON
Represents the planner-ready grid.

Suggested contents:
- width
- height
- cell_size_m
- cells
- elements
- optional openings
- metadata

---

## Why use two levels
Because they solve different problems.

### Overlay JSON
- UI state
- editable geometry
- user corrections

### Matrix JSON
- planner input
- normalized structure
- stable logic layer

This separation will make the system easier to extend later.

---

# 11. Recommended Data Contract for the Overlay Layer

For MVP, the overlay JSON should be kept very simple.

## Suggested shape

```json
{
  "document_id": "example_001",
  "image_width": 2400,
  "image_height": 1600,
  "status": "approved",
  "walls": [
    {
      "id": "wall_1",
      "x1": 100,
      "y1": 120,
      "x2": 600,
      "y2": 120
    }
  ],
  "doors": [
    {
      "id": "door_1",
      "x": 220,
      "y": 120,
      "width": 40,
      "orientation": "horizontal"
    }
  ],
  "windows": [
    {
      "id": "window_1",
      "x": 530,
      "y": 120,
      "width": 60,
      "orientation": "horizontal"
    }
  ],
  "elements": [
    {
      "type": "main_entry",
      "x": 220,
      "y": 120
    },
    {
      "type": "electric_board",
      "x": 420,
      "y": 900
    },
    {
      "type": "heat_source",
      "x": 650,
      "y": 980
    }
  ]
}
```

This is only a directional example, not a frozen final schema.

---

# 12. Recommended Matrix Generation Strategy

Once the overlay is approved, the system should:

1. normalize geometry
2. convert walls/openings into a structured planar layer
3. rasterize to grid
4. assign cell types
5. inject semantic markers into `elements`
6. export matrix JSON

---

## Resulting matrix JSON
The matrix JSON should follow the rule already established:

### `cells`
- outdoor
- wall
- indoor
- door
- window

### `elements`
- main_entry
- electric_board
- heat_source

### Optional
- openings spans
- rooms
- metadata

---

# 13. Interface Design Recommendation

For MVP, the editor should not try to behave like AutoCAD.

## Interface recommendation

### Main canvas
- original floorplan image as background
- editable overlay on top

### Tool panel
- wall tool
- door tool
- window tool
- main entry tool
- electric board tool
- heat source tool
- delete tool

### Action panel
- reset draft
- save progress
- approve and generate matrix

---

## Why this is enough
This keeps the interface:
- understandable
- fast to build
- good enough for validation

That is what the MVP needs.

---

# 14. Product Evaluation of This Direction

## Complexity
**Medium-high**

Not trivial, but still realistic for an MVP if the feature set stays small.

## Usability
**High**

Because the user sees:
- the original plan
- a visual interpretation
- simple correction tools

## Wow effect
**High**

Because the product feels intelligent:
- it reads the floorplan
- suggests a structure
- allows easy correction
- turns it into a machine-usable format

---

# 15. Implementation Priorities

The next implementation work should be split like this:

## Priority 1
Define overlay JSON contract

## Priority 2
Define frontend editing tools and exact interaction model

## Priority 3
Define geometry normalization and rasterization rules

## Priority 4
Define matrix JSON export contract

---

# 16. What We Should Define Next

The next logical document after this one should be:

## `OVERLAY_EDITOR_SPEC.md`

That document should define:
- exact tools
- exact object types
- exact user interactions
- snap behavior
- selection behavior
- approval behavior
- save/load behavior

That would make the frontend/editor implementation much more concrete.

---

# 17. Final Recommendation

The right MVP path is still:

**PDF/image -> basic structural detection -> editable overlay -> client validation -> matrix -> JSON**

And the next thing to freeze is not the detection algorithm.
It is the **overlay editing model**.

That is the layer that connects:
- automatic reading
- user correction
- planner-ready structure

If that layer is well defined, the rest of the pipeline becomes much easier to implement and evolve.
