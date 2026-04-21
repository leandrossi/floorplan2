from __future__ import annotations

from pathlib import Path
from typing import Callable

from infrastructure.artifact_store import ArtifactStore
from infrastructure.pipeline_runner import PipelineRunner
from services.workspace_service import SessionWorkspace

ProgressCallback = Callable[[float, str], None]


class AlarmEngineAdapter:
    def __init__(
        self,
        pipeline_runner: PipelineRunner | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.pipeline_runner = pipeline_runner or PipelineRunner()
        self.artifact_store = artifact_store or ArtifactStore()

    def generate_proposal(
        self,
        workspace: SessionWorkspace,
        *,
        security_level: str,
        review_approved_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> dict:
        paths = self.pipeline_runner.run_step05(
            workspace,
            security_level=security_level,
            review_approved_path=review_approved_path,
            progress_cb=progress_cb,
        )
        proposal = self.artifact_store.read_json(paths["proposal_path"])
        report = self.artifact_store.read_json(paths["report_path"])
        return {
            "paths": paths,
            "proposal": proposal,
            "report": report,
        }
