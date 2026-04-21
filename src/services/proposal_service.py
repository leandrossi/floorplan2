from __future__ import annotations

from pathlib import Path
from typing import Callable

from domain.contracts import ProposalViewModel
from domain.enums import SecurityLevel
from infrastructure.alarm_engine_adapter import AlarmEngineAdapter
from infrastructure.artifact_store import ArtifactStore
from infrastructure.review_bundle_adapter import ReviewBundleAdapter
from review_bundle_io import apply_struct_patches, load_approved
from ui_components import render_proposal_views

ProgressCallback = Callable[[float, str], None]


class ProposalService:
    def __init__(
        self,
        adapter: AlarmEngineAdapter | None = None,
        review_adapter: ReviewBundleAdapter | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.adapter = adapter or AlarmEngineAdapter()
        self.review_adapter = review_adapter or ReviewBundleAdapter()
        self.artifact_store = artifact_store or ArtifactStore()

    def build(
        self,
        *,
        workspace,
        review_bundle_path: Path,
        review_approved_path: Path,
        level: SecurityLevel,
        progress_cb: ProgressCallback | None = None,
    ) -> ProposalViewModel:
        generated = self.adapter.generate_proposal(
            workspace,
            security_level=level.planner_code,
            review_approved_path=review_approved_path,
            progress_cb=progress_cb,
        )
        proposal = generated["proposal"]
        report = generated["report"]
        bundle = self.review_adapter.load(review_bundle_path)
        approved = load_approved(review_approved_path) or {}
        effective_struct = apply_struct_patches(bundle.struct, approved.get("struct_patch") or [])

        _, device_img, device_counts, _ = render_proposal_views(
            effective_struct,
            proposal=proposal,
            show_red_zones=False,
            show_devices=True,
            replace_base_with_devices=True,
        )
        overlay_path = self.artifact_store.write_rgb_image(
            workspace.proposal_level_dir(level.planner_code) / "devices_overlay.png",
            device_img,
        )
        counts = report.get("device_counts") or device_counts
        total_devices = sum(int(v) for v in counts.values())
        summary = (
            f"{level.label}: {total_devices} dispositivos distribuidos sobre el plano "
            "para cubrir accesos y circulación sin cambiar el diagnóstico base."
        )
        return ProposalViewModel(
            security_level=level.planner_code,
            devices=list(proposal.get("devices") or []),
            overlay_path=str(overlay_path),
            counts_by_type={str(k): int(v) for k, v in counts.items()},
            proposal_summary=summary,
            proposal_path=str(generated["paths"]["proposal_path"]),
            report_path=str(generated["paths"]["report_path"]),
        )
