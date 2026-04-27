from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pipeline_common import PROJECT_ROOT

APP_WORKSPACES_ROOT_ENV = "APP_WORKSPACES_ROOT"
DEFAULT_WORKSPACES_ROOT = PROJECT_ROOT / "workspaces"


def resolve_workspaces_root() -> Path:
    configured = os.environ.get(APP_WORKSPACES_ROOT_ENV, "").strip()
    if not configured:
        return DEFAULT_WORKSPACES_ROOT
    return Path(configured).expanduser().resolve()


def _safe_name(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return cleaned or "floorplan"


@dataclass(frozen=True)
class SessionWorkspace:
    session_id: str
    root: Path
    input_dir: Path
    processing_dir: Path
    review_dir: Path
    proposal_dir: Path
    exports_dir: Path

    @property
    def step01_dir(self) -> Path:
        return self.processing_dir / "step01"

    @property
    def step02_dir(self) -> Path:
        return self.processing_dir / "step02"

    @property
    def step03_dir(self) -> Path:
        return self.processing_dir / "step03"

    @property
    def step04_dir(self) -> Path:
        return self.processing_dir / "step04"

    @property
    def roboflow_dir(self) -> Path:
        return self.processing_dir / "roboflow"

    def proposal_level_dir(self, planner_code: str) -> Path:
        return self.proposal_dir / planner_code

    def upload_path(self, filename: str) -> Path:
        return self.input_dir / _safe_name(filename)


class WorkspaceService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or resolve_workspaces_root()

    def create_session_id(self) -> str:
        return uuid4().hex

    def get_or_create(self, session_id: str | None = None) -> SessionWorkspace:
        sid = session_id or self.create_session_id()
        root = self.root / f"session_{sid}"
        input_dir = root / "input"
        processing_dir = root / "processing"
        review_dir = root / "review"
        proposal_dir = root / "proposal"
        exports_dir = root / "exports"
        for path in (input_dir, processing_dir, review_dir, proposal_dir, exports_dir):
            path.mkdir(parents=True, exist_ok=True)
        return SessionWorkspace(
            session_id=sid,
            root=root,
            input_dir=input_dir,
            processing_dir=processing_dir,
            review_dir=review_dir,
            proposal_dir=proposal_dir,
            exports_dir=exports_dir,
        )

    def save_upload(self, workspace: SessionWorkspace, filename: str, raw_bytes: bytes) -> Path:
        out_path = workspace.upload_path(filename)
        out_path.write_bytes(raw_bytes)
        return out_path
