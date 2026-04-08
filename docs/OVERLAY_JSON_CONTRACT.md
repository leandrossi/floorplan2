# Overlay JSON contract (MVP)

This document defines the **overlay layer** JSON schema used as input to the floorplan-to-matrix converter. The overlay represents the **client-approved editable structure** (walls, doors, windows, semantic markers) in **image coordinates**.

## Purpose

- **Overlay JSON**: UI state, editable geometry, user corrections (output of the overlay editor or detection + correction flow).
- **Matrix JSON**: Planner input, produced by `overlay_to_matrix()` from an approved overlay.

See [NEXT_DEFINITIONS_MVP_FLOORPLAN_TO_MATRIX.md](NEXT_DEFINITIONS_MVP_FLOORPLAN_TO_MATRIX.md) for the product flow.

## Coordinate system

- **Image space**: Origin at **top-left**. **x** increases to the right, **y** increases downward (typical image coordinates).
- **Units**: All overlay coordinates are in **pixels** (same scale as the source image).
- **Grid mapping**: Converter maps image `(x, y)` to matrix cell `(r, c)` with **r = row (y)**, **c = column (x)**. Matrix `cells[r][c]` is row-major.

## Required fields

| Field           | Type   | Description                          |
|----------------|--------|--------------------------------------|
| `document_id`  | string | Identifier for the document/session  |
| `image_width`  | number | Width of the source image (pixels)   |
| `image_height` | number | Height of the source image (pixels)  |
| `walls`        | array  | List of wall segments (see below)   |

## Optional fields

| Field      | Type   | Description                                      |
|-----------|--------|--------------------------------------------------|
| `status`  | string | e.g. `"approved"` (informational)                |
| `doors`   | array  | List of door openings (default: `[]`)           |
| `windows` | array  | List of window openings (default: `[]`)          |
| `elements`| array  | Semantic markers (default: `[]`)                 |

## Wall segment

Each item in `walls` is an object:

| Field | Type   | Description           |
|-------|--------|-----------------------|
| `id`  | string | Unique identifier     |
| `x1`  | number | Start x (pixels)      |
| `y1`  | number | Start y (pixels)      |
| `x2`  | number | End x (pixels)        |
| `y2`  | number | End y (pixels)        |

Walls are rasterized as lines; they define the boundary between indoor and outdoor. The converter adds a one-cell outdoor border so exterior can be flood-filled.

## Door / window opening

Each item in `doors` or `windows` is an object:

| Field         | Type   | Description                              |
|---------------|--------|------------------------------------------|
| `id`          | string | Unique identifier                        |
| `x`           | number | Top-left x (pixels)                      |
| `y`           | number | Top-left y (pixels)                      |
| `width`       | number | Length of the opening (along main axis)  |
| `orientation` | string | `"horizontal"` or `"vertical"`           |

- **Horizontal**: opening extends along x; short extent in y.
- **Vertical**: opening extends along y; short extent in x.

The converter draws a small rectangle (with fixed pixel thickness for the perpendicular dimension) and marks those cells as `door` or `window`.

## Semantic element

Each item in `elements` is an object:

| Field  | Type   | Description                    |
|--------|--------|--------------------------------|
| `type` | string | One of: `main_entry`, `electric_board`, `heat_source`, `cold_source` |
| `x`    | number | Position x (pixels)            |
| `y`    | number | Position y (pixels)            |

- **main_entry**: Must lie on a **door** cell (the door rectangle in the overlay should include this point).
- **electric_board**: Must lie on an **indoor** (or heat/cold) cell.
- **heat_source** / **cold_source**: Must not lie on **outdoor** or **wall**; the cell is marked as `heat_source` / `cold_source` in the matrix.

## Scale parameters (converter input)

The overlay does not store scale. The converter requires:

- **`cell_size_m`**: Physical size of one grid cell side (meters).
- **`pixels_per_meter`**: Image scale (pixels per real-world meter).

Grid dimensions are derived as:

- `extent_m_x = image_width / pixels_per_meter`
- `extent_m_y = image_height / pixels_per_meter`
- `interior_width = round(extent_m_x / cell_size_m)`, `interior_height = round(extent_m_y / cell_size_m)`
- The output matrix adds a one-cell outdoor border: `width = interior_width + 2`, `height = interior_height + 2`.

## Example (minimal)

```json
{
  "document_id": "example_001",
  "image_width": 200,
  "image_height": 160,
  "status": "approved",
  "walls": [
    {"id": "w1", "x1": 0, "y1": 0, "x2": 80, "y2": 0},
    {"id": "w2", "x1": 120, "y1": 0, "x2": 200, "y2": 0},
    {"id": "w3", "x1": 0, "y1": 0, "x2": 0, "y2": 160},
    {"id": "w4", "x1": 200, "y1": 0, "x2": 200, "y2": 60},
    {"id": "w5", "x1": 200, "y1": 100, "x2": 200, "y2": 160},
    {"id": "w6", "x1": 0, "y1": 160, "x2": 200, "y2": 160}
  ],
  "doors": [
    {"id": "door_1", "x": 80, "y": 0, "width": 40, "orientation": "horizontal"}
  ],
  "windows": [
    {"id": "window_1", "x": 192, "y": 60, "width": 40, "orientation": "vertical"}
  ],
  "elements": [
    {"type": "main_entry", "x": 100, "y": 4},
    {"type": "electric_board", "x": 40, "y": 80},
    {"type": "heat_source", "x": 100, "y": 100}
  ]
}
```

## Validation

Use `acala_core.overlay_to_matrix.validate_overlay(overlay: dict)` to validate before conversion. It raises `ValueError` on missing required fields, invalid types, or disallowed element types.

## Related

- Conversion: `acala_core.overlay_to_matrix.overlay_to_matrix()` and `overlay_to_matrix_json()`.
- Script: `python -m scripts.overlay_to_matrix <overlay.json> --cell-size 0.5 --pixels-per-meter 50`.
- Matrix schema: fixture JSON loadable by `io_json.load_fixture()` (see [ARCHITECTURE.md](ARCHITECTURE.md)).
