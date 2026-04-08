#!/usr/bin/env python3
"""
Lógica compartida: ejecutar workflows Roboflow serverless, guardar JSON y JPG.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

API_URL = "https://serverless.roboflow.com"
WORKSPACE_NAME = "basura-basura-s-workspace"
IMAGE_INPUT_KEY = "image"

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_TEST_IMAGE = PROJECT_ROOT / "Floorplan2.png"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_VIS_SUBDIR = "visualizations"


@dataclass(frozen=True)
class WorkflowScriptConfig:
    workflow_id: str
    description: str
    default_json_name: str
    default_vis_suffix: str
    default_output_dir: Path = DEFAULT_OUTPUT_DIR


def _path_relative_to_project(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_client() -> InferenceHTTPClient:
    # Siempre el .env junto al proyecto (subprocess/IDE a veces usan otro cwd).
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if not api_key:
        print(
            "Falta ROBOFLOW_API_KEY. Copia .env.example a .env y pega tu API key.",
            file=sys.stderr,
        )
        sys.exit(1)
    return InferenceHTTPClient(api_url=API_URL, api_key=api_key)


def run_one(
    client: InferenceHTTPClient,
    workflow_id: str,
    image_path: Path,
    use_cache: bool,
) -> object:
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    return client.run_workflow(
        workspace_name=WORKSPACE_NAME,
        workflow_id=workflow_id,
        images={IMAGE_INPUT_KEY: str(image_path.resolve())},
        use_cache=use_cache,
    )


def _workflow_blocks(raw: object) -> list[dict]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def _output_image_to_bytes(oi: object) -> bytes | None:
    b64: str | None = None
    if isinstance(oi, dict) and oi.get("type") == "base64":
        v = oi.get("value")
        b64 = v if isinstance(v, str) else None
    elif isinstance(oi, str) and oi.strip():
        b64 = oi
    if not b64:
        return None
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[-1]
    try:
        return base64.b64decode(b64, validate=False)
    except (ValueError, binascii.Error):
        return None


def _extract_image_bytes_from_block(block: dict) -> bytes | None:
    """
    Compat con distintos nombres de salida de workflows:
    - output_image (histórico)
    - final_image (workflow final)
    - image
    """
    for key in ("output_image", "final_image", "image"):
        data = _output_image_to_bytes(block.get(key))
        if data:
            return data
    return None


def _save_base64_output_image(block: dict, dest: Path) -> bool:
    data = _extract_image_bytes_from_block(block)
    if not data:
        return False
    dest = dest.with_suffix(".jpg") if dest.suffix.lower() not in {".jpg", ".jpeg"} else dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def extract_images_from_result_json(args: argparse.Namespace) -> None:
    src = args.from_json.expanduser().resolve()
    if not src.is_file():
        print(f"No existe: {src}", file=sys.stderr)
        sys.exit(1)
    doc = json.loads(src.read_text(encoding="utf-8"))
    runs = doc.get("runs")
    if not isinstance(runs, list):
        print("JSON sin lista 'runs'", file=sys.stderr)
        sys.exit(1)

    out_dir = args.output_dir.expanduser().resolve()
    vis_dir = out_dir / DEFAULT_VIS_SUBDIR

    for run in runs:
        if not isinstance(run, dict):
            continue
        inp = run.get("input_image")
        wo = run.get("workflow_output")
        if not isinstance(inp, str):
            continue
        stem = Path(inp).stem
        vis_path = vis_dir / f"{stem}{args.vis_suffix}.jpg"
        saved = False
        for block in _workflow_blocks(wo):
            if _save_base64_output_image(block, vis_path):
                saved = True
                print(f"Visualización guardada: {vis_path}", file=sys.stderr)
                break
        if not saved:
            print(f"Sin imagen base64 decodificable para {inp}", file=sys.stderr)


def _summarize_json_for_print(obj: object) -> object:
    if isinstance(obj, list):
        return [_summarize_json_for_print(x) for x in obj]
    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            if k in {"output_image", "final_image", "image"}:
                if isinstance(v, dict) and v.get("type") == "base64":
                    vv = deepcopy(v)
                    raw = vv.get("value")
                    if isinstance(raw, str) and len(raw) > 80:
                        vv["value"] = (
                            f"<base64 omitido, {len(raw)} caracteres — guardado en archivo>"
                        )
                    out[k] = vv
                elif isinstance(v, str) and len(v) > 80:
                    out[k] = f"<base64 omitido, {len(v)} caracteres — guardado en archivo>"
                else:
                    out[k] = v
            else:
                out[k] = _summarize_json_for_print(v)
        return out
    return obj


def build_parser(config: WorkflowScriptConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=config.description)
    parser.add_argument(
        "images",
        nargs="*",
        type=Path,
        help=(
            "Rutas a imágenes (default: Floorplan2.png en la raíz del proyecto; "
            "si no existe, ./images/*)"
        ),
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Desactiva cache del serverless",
    )
    parser.add_argument(
        "--no-save-vis",
        action="store_true",
        help="No guardar imagen base64 (output_image/final_image) como JPG",
    )
    parser.add_argument(
        "--vis-suffix",
        default=config.default_vis_suffix,
        help=(
            f"Sufijo antes de .jpg en {DEFAULT_VIS_SUBDIR}/ "
            f"(default: {config.default_vis_suffix})"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.default_output_dir,
        help=f"Carpeta para JSON e imágenes (default: {config.default_output_dir})",
    )
    parser.add_argument(
        "--json-file",
        default=config.default_json_name,
        help=f"Nombre del JSON dentro de --output-dir (default: {config.default_json_name})",
    )
    parser.add_argument(
        "--from-json",
        type=Path,
        metavar="RESULT.json",
        help="No llama a la API; lee un result.json y escribe los JPG desde output_image/final_image",
    )
    return parser


def main_entry(config: WorkflowScriptConfig, argv: list[str] | None = None) -> None:
    args = build_parser(config).parse_args(argv)

    if args.from_json:
        extract_images_from_result_json(args)
        return

    client = build_client()
    use_cache = not args.no_cache

    roots_dir = PROJECT_ROOT / "images"
    if args.images:
        paths = args.images
    elif DEFAULT_TEST_IMAGE.is_file():
        paths = [DEFAULT_TEST_IMAGE]
    else:
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        paths = sorted(
            p for p in roots_dir.iterdir() if p.suffix.lower() in exts
        )
        if not paths:
            print(
                f"No está {DEFAULT_TEST_IMAGE.name} ni hay imágenes en {roots_dir}. "
                "Coloca Floorplan2.png en el proyecto o pasa rutas de imagen.",
                file=sys.stderr,
            )
            sys.exit(1)

    out_dir = args.output_dir.expanduser().resolve()
    vis_dir = out_dir / DEFAULT_VIS_SUBDIR
    json_path = out_dir / args.json_file

    runs: list[dict] = []
    for p in paths:
        out = run_one(client, config.workflow_id, p, use_cache=use_cache)
        vis_saved: str | None = None

        if not args.no_save_vis:
            vis_path = vis_dir / f"{p.stem}{args.vis_suffix}.jpg"
            for block in _workflow_blocks(out):
                if _save_base64_output_image(block, vis_path):
                    vis_saved = _path_relative_to_project(vis_path)
                    print(f"Visualización guardada: {vis_path}", file=sys.stderr)
                    break

        runs.append(
            {
                "input_image": str(p.resolve()),
                "visualization_relative": vis_saved,
                "workflow_output": out,
            }
        )

    document = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": API_URL,
        "workspace_name": WORKSPACE_NAME,
        "workflow_id": config.workflow_id,
        "output_dir": _path_relative_to_project(out_dir),
        "runs": runs,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    # Raw JSON (con base64 intacto para debug/re-extract)
    json_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"JSON guardado: {json_path}", file=sys.stderr)
    # Console output: versión resumida (sin base64 largo)
    print(json.dumps(_summarize_json_for_print(document), indent=2, ensure_ascii=False))