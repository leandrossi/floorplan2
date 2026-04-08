#!/usr/bin/env python3
"""Step 01: parse structure + rooms Roboflow JSON (schema A or B), normalize."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from pipeline_common import (
    DEFAULT_CONFIG,
    DEFAULT_ROOMS_JSON,
    DEFAULT_STRUCTURE_JSON,
    PROJECT_ROOT,
    collect_image_size_from_structure,
    detect_schema,
    iter_schema_a,
    iter_schema_b,
    load_config,
    load_json,
    normalize_detection,
    save_json,
)


def parse_file(
    path: Path,
    *,
    source_type: str,
    cfg: dict,
    inherited_size: tuple[int, int] | None,
) -> tuple[list[dict], int, int]:
    data = load_json(path)
    schema = detect_schema(data)
    if source_type == "structure":
        iw, ih = collect_image_size_from_structure(data, schema)
    else:
        if inherited_size:
            iw, ih = inherited_size
        else:
            iw, ih = collect_image_size_from_structure(data, schema)

    if schema == "A":
        triples = list(iter_schema_a(data))
    else:
        triples = list(iter_schema_b(data))

    out: list[dict] = []
    for _w, _h, p in triples:
        d = normalize_detection(p, source_type=source_type, image_w=iw, image_h=ih, cfg=cfg)
        if d is not None:
            out.append(d)

    return out, iw, ih


def run(
    *,
    structure_json: Path,
    rooms_json: Path,
    config_path: Path,
    out_dir: Path,
) -> None:
    cfg = load_config(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    struct_detections, sw, sh = parse_file(structure_json, source_type="structure", cfg=cfg, inherited_size=None)
    rooms_detections, rw, rh = parse_file(
        rooms_json,
        source_type="rooms",
        cfg=cfg,
        inherited_size=(sw, sh),
    )

    if (sw, sh) != (rw, rh):
        raise ValueError(
            f"Tamaño imagen distinto: estructura {sw}x{sh} vs habitaciones {rw}x{rh}"
        )

    save_json(
        out_dir / "normalized_structure.json",
        {"meta": {"image_width": sw, "image_height": sh, "source": "structure"}, "detections": struct_detections},
    )
    save_json(
        out_dir / "normalized_rooms.json",
        {"meta": {"image_width": rw, "image_height": rh, "source": "rooms"}, "detections": rooms_detections},
    )

    # summary.txt
    lines = [
        f"image_size: {sw}x{sh}",
        "",
        "=== structure ===",
    ]
    cr = Counter(d["class_raw"] for d in struct_detections)
    cn = Counter(d["class_norm"] for d in struct_detections)
    lines.append(f"counts_raw: {dict(cr)}")
    lines.append(f"counts_norm: {dict(cn)}")
    acc = [d for d in struct_detections if d.get("passes_threshold")]
    lines.append(f"total: {len(struct_detections)} accepted_passes_threshold: {len(acc)}")
    unk = [d for d in struct_detections if d["class_norm"] == "unknown"]
    lines.append(f"unknown_class: {len(unk)}")
    for u in unk[:20]:
        lines.append(f"  - raw={u['class_raw']!r} id={u.get('detection_id')}")
    if len(unk) > 20:
        lines.append("  ...")

    lines.extend(["", "=== rooms ==="])
    cr2 = Counter(d["class_raw"] for d in rooms_detections)
    cn2 = Counter(d["class_norm"] for d in rooms_detections)
    lines.append(f"counts_raw: {dict(cr2)}")
    lines.append(f"counts_norm: {dict(cn2)}")
    acc2 = [d for d in rooms_detections if d.get("passes_threshold")]
    lines.append(f"total: {len(rooms_detections)} accepted_passes_threshold: {len(acc2)}")

    (out_dir / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Step01 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure-json", type=Path, default=DEFAULT_STRUCTURE_JSON)
    ap.add_argument("--rooms-json", type=Path, default=DEFAULT_ROOMS_JSON)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step01")
    args = ap.parse_args()
    run(structure_json=args.structure_json, rooms_json=args.rooms_json, config_path=args.config, out_dir=args.out)


if __name__ == "__main__":
    main()
