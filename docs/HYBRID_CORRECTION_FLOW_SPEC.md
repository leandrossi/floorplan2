# HYBRID_CORRECTION_FLOW_SPEC.md

## Title
Hybrid Correction Flow Specification — MVP Floorplan to Matrix

## Purpose
This document defines the **hybrid correction flow** for the MVP.

The product direction is:

**PDF/image -> automatic detection draft -> interpreted result shown to user -> user correction -> approved matrix -> JSON**

This means the user does **not** draw the floorplan from scratch.
The system first generates an interpretation, and the user then corrects it.

This is a hybrid between:
- automatic structural detection
- controlled human correction

---

# 1. Product Principle

The correction experience should feel like:

**“The system understood the plan enough to help me, and I only need to fix what is wrong.”**

It should not feel like:
- redrawing the plan from zero
- editing raw JSON
- painting a spreadsheet blindly

---

# 2. Hybrid Flow Summary

## Step 1 — Upload
The client uploads a PDF or image.

## Step 2 — Automatic interpretation
The system produces an initial structural draft.

## Step 3 — Review interpreted result
The client sees:
- original floorplan
- interpreted overlay
- optional matrix/grid preview

## Step 4 — Correct interpretation
The client adjusts the interpreted result.

## Step 5 — Confirm semantic markers
The client confirms:
- main entry
- electric board
- heat source

## Step 6 — Approve
The client approves the corrected result.

## Step 7 — Generate matrix and JSON
The approved structure becomes:
- matrix
- planner JSON

---

# 3. What the User Actually Corrects

The user should correct the **interpreted structure**, not the raw PDF and not a blank matrix.

## Objects the user corrects
- walls
- doors
- windows
- indoor/outdoor classification
- semantic markers

---

# 4. Recommended UI Representation

The correction screen should have at least 3 conceptual layers.

## Layer 1 — Original floorplan
The uploaded PDF/image rendered as background.

## Layer 2 — Interpreted overlay
The system’s detected result shown as editable structure:
- walls
- openings
- markers

## Layer 3 — Matrix/grid preview
An optional visible grid or matrix layer that can be toggled on or off.

---

## Recommended default view
Show:
- original image
- interpreted overlay

Allow optional toggles for:
- grid on/off
- original image on/off
- overlay on/off

This gives the user confidence while keeping the system understandable.

---

# 5. Why This Hybrid Is Better Than Two Extreme Options

## Better than full automatic
Because the system will not be perfectly accurate.

## Better than full manual matrix painting
Because the user should not start from nothing.

The hybrid approach gives:
- automation
- control
- faster correction
- higher trust

---

# 6. What the User Should NOT Have To Do

The user should not have to:
- recreate all walls manually
- type coordinates
- edit JSON directly
- classify every room from scratch
- redraw the plan from zero

The user should only fix what the system got wrong.

---

# 7. Correction Modes

The correction flow should be separated into modes or steps.

## Mode 1 — Structure correction
Correct:
- walls
- doors
- windows
- local indoor/outdoor interpretation

## Mode 2 — Semantic correction
Set or confirm:
- main entry
- electric board
- heat source

## Mode 3 — Approval
Review final result and generate matrix.

---

# 8. Editing Model

The user should not directly paint a raw matrix as the first interaction.

But the correction layer should still be compatible with matrix output.

## Recommended model
The user edits an **interpreted structural representation** that can later be rasterized into matrix form.

This means:
- visual correction first
- matrix generation second

---

# 9. Recommended Editing Actions

## Structural correction actions
- add wall
- remove wall
- adjust wall segment
- add door
- move door
- remove door
- add window
- move window
- remove window
- fix local indoor/outdoor classification if needed

## Semantic correction actions
- place main entry
- place electric board
- place heat source
- move them
- delete them

---

# 10. Matrix Preview Role

Even if the user is not directly editing the matrix first, the system should offer a matrix preview before final export.

## Why
Because the engine consumes matrix data.

The user should be able to verify:
- the discretization looks correct
- openings are represented correctly
- walls are continuous where expected
- interior/exterior separation makes sense

---

# 11. Recommended Approval Boundary

The final matrix should be generated **after** the correction step, not before final confirmation.

That means:

**detection draft -> correction -> approval -> matrix**

This ensures the planner only receives approved structure.

---

# 12. Intermediate Data Layers

The MVP should use at least these layers:

## Layer A — Detection Draft
Automatic result from the detector.

## Layer B — Corrected Overlay
User-adjusted interpretation.

## Layer C — Final Matrix
Rasterized approved structure.

## Layer D — Planner JSON
Final output compatible with the engine.

---

# 13. Suggested Corrected Overlay Contract

```json
{
  "document_id": "example_001",
  "image_width": 2400,
  "image_height": 1600,
  "status": "edited",
  "walls": [],
  "doors": [],
  "windows": [],
  "elements": []
}
```

This corrected overlay is what the user approves before matrix generation.

---

# 14. Usability Goals

The hybrid correction layer should aim for:

- low friction
- fast local corrections
- confidence in what the machine interpreted
- clear boundary between automatic guess and user-approved truth

---

# 15. Complexity / Usability / Wow

## Complexity
**Medium-high**

Because it combines automation and editing.

## Usability
**High**

Because the user corrects a proposal instead of starting from nothing.

## Wow
**High**

Because the system appears intelligent while still remaining controllable.

This is stronger than:
- pure automation with no correction
- pure manual matrix editing

---

# 16. Recommended Build Order

## Step 1
Show detected interpretation on top of uploaded floorplan

## Step 2
Allow structural correction

## Step 3
Allow semantic correction

## Step 4
Add matrix preview

## Step 5
Add approval

## Step 6
Export approved matrix JSON

---

# 17. Validation Rules Before Approval

Before final approval, the system should validate:

- structure is not obviously broken
- doors/windows are attached sensibly
- exactly one main entry exists
- electric board is set if known
- no unresolved critical warnings remain

---

# 18. What This Means for Product Design

The product should present itself as:

**AI-assisted floorplan interpretation with human validation**

That is a strong MVP positioning because it is:
- realistic
- trustworthy
- technically achievable

---

# 19. Final Recommendation

The MVP should use a hybrid correction flow where:

- the machine generates the first structural interpretation
- the client corrects that interpretation
- the corrected result becomes the approved matrix
- the approved matrix becomes the final JSON

This is the right product balance between:
- automation
- usability
- engineering practicality
- final planner reliability
