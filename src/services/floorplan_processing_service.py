from __future__ import annotations

from pathlib import Path
from typing import Callable

from domain.contracts import ProcessingResult
from domain.enums import ProcessingStatus
from infrastructure.artifact_store import ArtifactStore
from infrastructure.pipeline_runner import PipelineRunner
from services.workspace_service import SessionWorkspace, WorkspaceService

ProgressCallback = Callable[[float, str], None]


class FloorplanProcessingService:
    def __init__(
        self,
        workspace_service: WorkspaceService | None = None,
        pipeline_runner: PipelineRunner | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.workspace_service = workspace_service or WorkspaceService()
        self.pipeline_runner = pipeline_runner or PipelineRunner()
        self.artifact_store = artifact_store or ArtifactStore()

    def save_upload(self, workspace: SessionWorkspace, filename: str, raw_bytes: bytes) -> Path:
        return self.workspace_service.save_upload(workspace, filename, raw_bytes)

    def process_existing_upload(
        self,
        workspace: SessionWorkspace,
        upload_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> ProcessingResult:
        try:
            outputs = self.pipeline_runner.run_to_step04(
                workspace,
                upload_path=upload_path,
                progress_cb=progress_cb,
            )
            review_bundle_copy = self.artifact_store.copy_if_exists(
                outputs["review_bundle_path"],
                workspace.review_dir / "review_bundle.json",
            )
            preview_copy = self.artifact_store.copy_if_exists(
                outputs["preview_image_path"],
                workspace.review_dir / "floor_like_preview.png",
            )
            return ProcessingResult(
                session_id=workspace.session_id,
                workspace_path=str(workspace.root),
                upload_path=str(upload_path),
                base_image_path=str(preview_copy) if preview_copy else None,
                review_bundle_path=str(review_bundle_copy or outputs["review_bundle_path"]),
                preview_paths={
                    "review_preview": str(preview_copy or outputs["preview_image_path"]),
                },
                status=ProcessingStatus.SUCCEEDED,
                step04_dir=str(outputs["step04_dir"]),
            )
        except Exception as exc:  # noqa: BLE001
            return ProcessingResult(
                session_id=workspace.session_id,
                workspace_path=str(workspace.root),
                upload_path=str(upload_path),
                base_image_path=None,
                review_bundle_path=None,
                preview_paths={},
                status=ProcessingStatus.FAILED,
                error_message=str(exc),
            )
