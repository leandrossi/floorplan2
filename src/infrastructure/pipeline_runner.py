from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from pipeline_common import DEFAULT_CONFIG, PROJECT_ROOT
from review_bundle_io import write_review_bundle
from services.workspace_service import SessionWorkspace

ProgressCallback = Callable[[float, str], None]


class PipelineRunner:
    def _run_roboflow(self, image_path: Path, output_dir: Path) -> Path:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "run_workflow_final.py"),
            str(image_path),
            "--output-dir",
            str(output_dir),
        ]
        env = dict(os.environ)
        for key in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "SOCKS_PROXY",
            "SOCKS5_PROXY",
            "socks_proxy",
            "socks5_proxy",
            "GIT_HTTP_PROXY",
            "GIT_HTTPS_PROXY",
        ):
            env.pop(key, None)
        env["NO_PROXY"] = ",".join(
            x for x in [env.get("NO_PROXY", ""), "serverless.roboflow.com", ".roboflow.com"] if x
        )
        env["no_proxy"] = env["NO_PROXY"]

        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env=env,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip() or "Roboflow failed without a message."
            raise RuntimeError(err)
        json_path = output_dir / "result_workflow_final.json"
        if not json_path.is_file():
            raise RuntimeError(f"Roboflow finished without creating {json_path}")
        return json_path

    def run_to_step04(
        self,
        workspace: SessionWorkspace,
        upload_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> dict[str, Path]:
        def _progress(ratio: float, message: str) -> None:
            if progress_cb is not None:
                progress_cb(ratio, message)

        _progress(0.05, "Uploading floorplan for automatic interpretation...")
        json_path = self._run_roboflow(upload_path, workspace.roboflow_dir)

        from final_step01_parse_and_rasterize import run as run_step01
        from final_step02_classify_space import run as run_step02
        from final_step03_assign_rooms import run as run_step03
        from final_step04_build_matrix_csv import run as run_step04

        _progress(0.18, "Detecting walls and openings...")
        run_step01(json_path, workspace.step01_dir)

        _progress(0.40, "Separating indoor and outdoor areas...")
        run_step02(
            workspace.step01_dir / "structural_mask.npy",
            workspace.step01_dir / "room_polygons.npy",
            workspace.step02_dir,
        )

        _progress(0.62, "Organizing detected rooms...")
        run_step03(
            workspace.step02_dir / "space_classified.npy",
            workspace.step01_dir / "room_polygons.npy",
            workspace.step03_dir,
        )

        _progress(0.84, "Preparing visual review...")
        run_step04(
            workspace.step02_dir / "space_classified.npy",
            workspace.step03_dir / "room_id_matrix.npy",
            DEFAULT_CONFIG,
            workspace.step04_dir,
        )

        review_bundle_path = workspace.step04_dir / "review_bundle.json"
        if not review_bundle_path.is_file():
            write_review_bundle(workspace.step04_dir, DEFAULT_CONFIG)
        _progress(1.0, "Ready to review the floorplan.")
        return {
            "roboflow_json": json_path,
            "step04_dir": workspace.step04_dir,
            "review_bundle_path": review_bundle_path,
            "preview_image_path": workspace.step04_dir / "floor_like_preview.png",
        }

    def run_step05(
        self,
        workspace: SessionWorkspace,
        *,
        security_level: str,
        review_approved_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> dict[str, Path]:
        def _progress(ratio: float, message: str) -> None:
            if progress_cb is not None:
                progress_cb(ratio, message)

        from final_step05_plan_alarm import run as run_step05

        out_dir = workspace.proposal_level_dir(security_level)
        _progress(0.20, "Building the solution on your floorplan...")
        run_step05(
            workspace.step04_dir,
            DEFAULT_CONFIG,
            out_dir,
            security_level=security_level,
            review_path=review_approved_path,
        )
        _progress(1.0, "Solution generated.")
        return {
            "proposal_dir": out_dir,
            "proposal_path": out_dir / "installation_proposal.json",
            "report_path": out_dir / "alarm_plan_report.json",
            "final_grid_path": out_dir / "final_floorplan_grid.json",
        }
