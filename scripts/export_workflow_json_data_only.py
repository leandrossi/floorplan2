#!/usr/bin/env python3
"""
Extrae del resultado Roboflow (workflow) un JSON solo con datos útiles:
sin output_image, sin ruta al JPG con plano de fondo.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def strip_for_simple_view(doc: dict) -> dict:
    out = copy.deepcopy(doc)
    for run in out.get("runs") or []:
        if isinstance(run, dict):
            run.pop("visualization_relative", None)
            wo = run.get("workflow_output")
            if isinstance(wo, list):
                for block in wo:
                    if isinstance(block, dict):
                        block.pop("output_image", None)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent.parent
    ap.add_argument(
        "--in",
        dest="inp",
        type=Path,
        default=root / "output" / "result_workflow2.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=root / "output" / "result_workflow2.data_only.json",
    )
    args = ap.parse_args()
    doc = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    lean = strip_for_simple_view(doc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(lean, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito: {args.out}", flush=True)


if __name__ == "__main__":
    main()
