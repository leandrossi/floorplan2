# Testing and Debug Rules

## Main rule
Every step must generate something a human can inspect.

That means:
- image preview,
- overlay,
- report,
- matrix file,
- or all of them.

## Debug strategy
Prefer visual debugging over silent assumptions.

Examples:
- overlay masks on original image,
- save intermediate walls before/after repair,
- export conflict reports,
- export room matching reports.

## Required CLI style
Each step should be directly executable, for example:

```bash
python src/step01_parse_and_normalize_inputs.py
python src/step02_rasterize_structure.py
python src/step03_repair_wall_topology.py
python src/step04_build_structural_mask.py
python src/step05_classify_exterior_interior.py
python src/step06_assign_rooms.py
python src/step07_build_final_outputs.py
```

## Manual review checklist
### After Step 02
- Are walls roughly aligned with the floorplan?
- Are windows and doors in the expected places?
- Are diagonal walls preserved?

### After Step 03
- Are obvious wall gaps reduced?
- Did we preserve real diagonal walls?
- Did the repair avoid absurd closure artifacts?

### After Step 04
- Are windows/doors embedded in structure rather than floating?
- Does the structure still define plausible enclosed regions?

### After Step 05
- Are closed spaces classified as interior?
- Does the exterior flood fill stay outside where expected?

### After Step 06
- Does each real room receive a stable room id?
- Are door connections prevented from merging adjacent rooms?
- Do room-model proposals improve room labeling rather than break it?

### After Step 07
- Are final matrices aligned with previews?
- Is metadata correct and explicit about scale mode?

## Recommendation for testing
Implement and validate sequentially.
Do not jump to Step 06 before Step 05 behaves correctly.
