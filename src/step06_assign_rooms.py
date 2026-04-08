#!/usr/bin/env python3
"""
Step 06: room_id_matrix a partir de space_interior_room_proposal.npy (step05).

La partición 1..K coincide con el orden de detecciones `room` en normalized_rooms.json
(misma política que step05: ignore_threshold alineado con run del pipeline).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from pipeline_common import PROJECT_ROOT, load_json, save_json


def room_detections_list(doc: dict, *, ignore_threshold: bool) -> list[dict]:
    out: list[dict] = []
    for d in doc.get("detections", []):
        if d.get("exclude_reason"):
            continue
        if not ignore_threshold and not d.get("passes_threshold"):
            continue
        if d.get("class_norm") != "room":
            continue
        pts = d.get("points") or []
        if len(pts) < 3:
            continue
        out.append(d)
    return out


def run(
    room_proposal_npy: Path,
    rooms_json: Path,
    space_npy: Path,
    out_dir: Path,
    *,
    ignore_threshold: bool = False,
) -> None:
    proposal = np.load(room_proposal_npy).astype(np.int32)
    h, w = proposal.shape[:2]

    space = np.load(space_npy)
    if space.shape != proposal.shape:
        raise ValueError(
            f"shape room_proposal {proposal.shape} != space_classified {space.shape}"
        )

    interior = space == 4
    doc = load_json(rooms_json)
    room_dets = room_detections_list(doc, ignore_threshold=ignore_threshold)

    room_id_img = proposal.copy()
    ids_present = sorted(int(x) for x in np.unique(room_id_img) if x > 0)
    k_expected = len(room_dets)

    meta_rooms: list[dict] = []
    report_lines: list[str] = [
        "Fuente: space_interior_room_proposal.npy (step05).",
        f"room_detections_en_json: {k_expected}",
        f"ids_en_matriz: {ids_present}",
        "",
    ]
    if ids_present and max(ids_present) != k_expected:
        report_lines.append(
            f"AVISO: max id ({max(ids_present)}) != len(room_dets) ({k_expected}); "
            "revisa mismo --ignore-threshold que step05."
        )
        report_lines.append("")

    for rid in ids_present:
        mask = room_id_img == rid
        area = int(mask.sum())
        ov = int((mask & interior).sum())
        det = room_dets[rid - 1] if 0 < rid <= len(room_dets) else None
        did = det.get("detection_id") if det else None
        conf = float(det["confidence"]) if det else None
        meta_rooms.append(
            {
                "room_id": rid,
                "source": "room_proposal_step05",
                "detection_index": rid - 1,
                "detection_id": did,
                "confidence": conf,
                "pixel_area": area,
                "overlap_struct_interior_class4": ov,
            }
        )
        report_lines.append(
            f"room_id={rid} area={area} overlap_interior(4)={ov} det_id={did} conf={conf}"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "room_id_matrix.npy", room_id_img)
    np.savetxt(
        out_dir / "room_id_matrix.csv",
        room_id_img,
        fmt="%d",
        delimiter=",",
    )

    prev = np.zeros((h, w, 3), dtype=np.uint8)
    rng = np.random.default_rng(42)
    mx = int(room_id_img.max())
    for i in range(1, mx + 1):
        prev[room_id_img == i] = tuple(int(x) for x in rng.integers(80, 255, size=3))
    cv2.imwrite(str(out_dir / "room_id_preview.png"), prev)

    save_json(out_dir / "rooms_metadata.json", {"rooms": meta_rooms, "source_matrix": str(room_proposal_npy)})
    (out_dir / "rooms_match_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Step06 OK -> {out_dir}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--room-proposal",
        type=Path,
        default=PROJECT_ROOT / "output" / "step05" / "space_interior_room_proposal.npy",
    )
    ap.add_argument(
        "--rooms-json",
        type=Path,
        default=PROJECT_ROOT / "output" / "step01" / "normalized_rooms.json",
    )
    ap.add_argument("--space", type=Path, default=PROJECT_ROOT / "output" / "step05" / "space_classified.npy")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "output" / "step06")
    ap.add_argument(
        "--ignore-threshold",
        action="store_true",
        help="Misma lista room que step05 (incluye bajo umbral)",
    )
    args = ap.parse_args()
    run(
        args.room_proposal,
        args.rooms_json,
        args.space,
        args.out,
        ignore_threshold=bool(args.ignore_threshold),
    )


if __name__ == "__main__":
    main()
