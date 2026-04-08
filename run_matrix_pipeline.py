#!/usr/bin/env python3
"""Ejecuta step01 → step07 en orden (desde la raíz del repo)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
STEPS = [
    "step01_parse_and_normalize_inputs.py",
    "step02_rasterize_structure.py",
    "step03_repair_wall_topology.py",
    "step04_build_structural_mask.py",
    "step04b_seal_structural_envelope.py",
    "step05_classify_exterior_interior.py",
    "step06_assign_rooms.py",
    "step07_build_final_outputs.py",
    "step08_combine_structure_rooms.py",
    "step09_export_floor_like_csv.py",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--ignore-threshold",
        action="store_true",
        help="Step02, Step05 (room proposals) y Step06 sin filtrar por passes_threshold",
    )
    ap.add_argument(
        "--step05-variants",
        action="store_true",
        help="Tras el pipeline, genera output/step05_variants (4 alternativas en paralelo; struct base step04)",
    )
    ap.add_argument(
        "--variants-struct",
        type=Path,
        default=None,
        help="NPY estructural para variantes (default: output/step04/structural_mask.npy)",
    )
    ap.add_argument(
        "--variants-jobs",
        type=int,
        default=4,
        help="Workers para step05_variants (1–4)",
    )
    args = ap.parse_args()
    extra_step02 = ["--ignore-threshold"] if args.ignore_threshold else []
    extra_step05 = ["--ignore-threshold"] if args.ignore_threshold else []
    extra_step06 = ["--ignore-threshold"] if args.ignore_threshold else []

    for s in STEPS:
        script = SRC / s
        print(f"\n>>> {s}", flush=True)
        extra: list[str] = []
        if s == "step02_rasterize_structure.py":
            extra = extra_step02
        elif s == "step05_classify_exterior_interior.py":
            extra = extra_step05
        elif s == "step06_assign_rooms.py":
            extra = extra_step06
        r = subprocess.run([sys.executable, str(script), *extra], check=False)
        if r.returncode != 0:
            print(f"Fallo en {s} (exit {r.returncode})", file=sys.stderr)
            sys.exit(r.returncode)
    if args.step05_variants:
        root = Path(__file__).resolve().parent
        struct = args.variants_struct or (root / "output" / "step04" / "structural_mask.npy")
        vcmd = [
            sys.executable,
            str(root / "src" / "step05_variants_exterior_interior.py"),
            "--struct",
            str(struct),
            "--jobs",
            str(max(1, min(4, int(args.variants_jobs)))),
        ]
        if args.ignore_threshold:
            vcmd.append("--ignore-threshold")
        print("\n>>> step05_variants_exterior_interior.py", flush=True)
        rv = subprocess.run(vcmd, check=False)
        if rv.returncode != 0:
            print(f"Fallo en step05_variants (exit {rv.returncode})", file=sys.stderr)
            sys.exit(rv.returncode)
    print("\nPipeline matriz OK -> output/step01 … step07", flush=True)


if __name__ == "__main__":
    main()
