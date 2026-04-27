from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image

from application.navigation import can_enter, previous_screen
from application.wizard_state import (
    WizardSessionState,
    clear_runtime_widget_state,
    load_wizard_state,
    reset_flow_state,
    save_wizard_state,
)
from domain.contracts import KitViewModel, ProposalViewModel, ReviewResult, RiskViewModel
from domain.enums import ProcessingStatus, SecurityLevel, WizardScreen
from infrastructure.artifact_store import ArtifactStore
from services.floorplan_processing_service import FloorplanProcessingService
from services.kit_service import KitService
from services.proposal_service import ProposalService
from services.review_service import ReviewService
from services.risk_service import RiskService
from services.workspace_service import SessionWorkspace, WorkspaceService

ProgressCallback = Callable[[float, str], None]
MIN_RISK_RENDER_WIDTH = 1000
MIN_PROPOSAL_RENDER_WIDTH = 1000
PROPOSAL_OVERLAY_BASENAME = "devices_overlay_v3.png"


class WizardController:
    def __init__(
        self,
        workspace_service: WorkspaceService | None = None,
        processing_service: FloorplanProcessingService | None = None,
        review_service: ReviewService | None = None,
        risk_service: RiskService | None = None,
        proposal_service: ProposalService | None = None,
        kit_service: KitService | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.workspace_service = workspace_service or WorkspaceService()
        self.processing_service = processing_service or FloorplanProcessingService(self.workspace_service)
        self.review_service = review_service or ReviewService()
        self.risk_service = risk_service or RiskService()
        self.proposal_service = proposal_service or ProposalService()
        self.kit_service = kit_service or KitService()
        self.artifact_store = artifact_store or ArtifactStore()

    def state(self) -> WizardSessionState:
        state = load_wizard_state()
        if state.session_id is None or state.workspace_path is None:
            workspace = self.workspace_service.get_or_create(state.session_id)
            state.session_id = workspace.session_id
            state.workspace_path = str(workspace.root)
            save_wizard_state(state)
        return state

    def _workspace(self, state: WizardSessionState | None = None) -> SessionWorkspace:
        current = state or self.state()
        return self.workspace_service.get_or_create(current.session_id)

    def persist(self, state: WizardSessionState) -> WizardSessionState:
        return save_wizard_state(state)

    def start_flow(self) -> WizardSessionState:
        state = reset_flow_state(self.state())
        state.current_screen = WizardScreen.UPLOAD.value
        return self.persist(state)

    def back(self) -> WizardSessionState:
        state = self.state()
        prev_screen = previous_screen(state.current_screen)
        while prev_screen is WizardScreen.PROCESSING:
            prev_screen = previous_screen(prev_screen)
        if can_enter(prev_screen, state):
            state.current_screen = prev_screen.value
        return self.persist(state)

    def go_to(self, screen: WizardScreen) -> WizardSessionState:
        state = self.state()
        if can_enter(screen, state):
            state.current_screen = screen.value
        return self.persist(state)

    def reset_all(self) -> WizardSessionState:
        state = WizardSessionState()
        clear_runtime_widget_state()
        return self.persist(state)

    def save_upload(self, filename: str, raw_bytes: bytes) -> WizardSessionState:
        state = reset_flow_state(self.state())
        workspace = self._workspace(state)
        upload_path = self.processing_service.save_upload(workspace, filename, raw_bytes)
        state.upload_path = str(upload_path)
        state.uploaded_file_name = filename
        state.processing_status = ProcessingStatus.QUEUED.value
        state.processing_message = "Plano cargado. Vamos a analizarlo."
        state.processing_requested = True
        state.current_screen = WizardScreen.PROCESSING.value
        return self.persist(state)

    def run_processing(self, progress_cb: ProgressCallback | None = None) -> WizardSessionState:
        state = self.state()
        if not state.upload_path:
            state.last_error = "Falta un plano cargado para iniciar el análisis."
            state.processing_status = ProcessingStatus.FAILED.value
            return self.persist(state)

        workspace = self._workspace(state)
        state.processing_status = ProcessingStatus.RUNNING.value
        state.processing_message = "Estamos interpretando el plano."
        self.persist(state)

        result = self.processing_service.process_existing_upload(
            workspace,
            Path(state.upload_path),
            progress_cb=progress_cb,
        )
        state.processing_requested = False
        state.processing_status = result.status.value
        state.processing_message = None
        state.last_error = result.error_message
        if result.status == ProcessingStatus.SUCCEEDED:
            state.step04_dir = result.step04_dir
            state.review_bundle_path = result.review_bundle_path
            state.review_preview_path = result.preview_paths.get("review_preview")
            state.current_screen = WizardScreen.REVIEW.value
        else:
            state.current_screen = WizardScreen.UPLOAD.value
        return self.persist(state)

    def get_review_validation(self, *, require_markers: bool = True) -> dict:
        state = self.state()
        if not state.review_bundle_path:
            raise RuntimeError("No hay datos de revisión cargados.")
        return self.review_service.build_validation_state(
            bundle_path=Path(state.review_bundle_path),
            struct_patch=state.struct_patch,
            main_entry=state.main_entry,
            electric_board=state.electric_board,
            require_markers=require_markers,
        )

    def update_review_draft(
        self,
        *,
        struct_patch: list[dict[str, int]],
        main_entry: list[int] | None,
        electric_board: list[int] | None,
    ) -> WizardSessionState:
        state = self.state()
        state.struct_patch = struct_patch
        state.main_entry = main_entry
        state.electric_board = electric_board
        return self.persist(state)

    def approve_review(self) -> ReviewResult:
        state = self.state()
        if not state.review_bundle_path:
            raise RuntimeError("No hay bundle de revisión disponible.")
        workspace = self._workspace(state)
        result = self.review_service.approve(
            bundle_path=Path(state.review_bundle_path),
            review_dir=workspace.review_dir,
            struct_patch=state.struct_patch,
            main_entry=state.main_entry,
            electric_board=state.electric_board,
        )
        if result.approved:
            state.review_approved_path = result.review_approved_path
            state.corrected_preview_path = result.corrected_preview_path
            state.risk_overlay_path = None
            state.risk_summary_text = None
            state.proposal_paths_by_level = {}
            state.report_paths_by_level = {}
            state.overlay_paths_by_level = {}
            state.proposal_summaries_by_level = {}
            state.proposal_counts_by_level = {}
            state.kit_by_level = {}
            state.current_screen = WizardScreen.RISK.value
            self.persist(state)
        return result

    def ensure_risk_view(self) -> RiskViewModel:
        state = self.state()
        if not state.review_bundle_path or not state.review_approved_path:
            raise RuntimeError("Primero tenés que aprobar la revisión.")
        workspace = self._workspace(state)
        if state.risk_overlay_path and Path(state.risk_overlay_path).is_file():
            try:
                with Image.open(state.risk_overlay_path) as current_overlay:
                    if current_overlay.width < MIN_RISK_RENDER_WIDTH:
                        state.risk_overlay_path = None
                        self.persist(state)
                    else:
                        return RiskViewModel(
                            base_plan_path=str(workspace.review_dir / "risk_base_plan.png"),
                            risk_overlay_path=state.risk_overlay_path,
                            legend=[
                                {"label": "Baseline diagnosis", "color": "Translucent red"},
                                {"label": "Main entrance", "color": "Solid red"},
                                {"label": "Electrical board", "color": "Solid blue"},
                            ],
                            summary_text=state.risk_summary_text or "",
                            details=[],
                        )
            except OSError:
                state.risk_overlay_path = None
                self.persist(state)
        if state.risk_overlay_path and Path(state.risk_overlay_path).is_file():
            return RiskViewModel(
                base_plan_path=str(workspace.review_dir / "risk_base_plan.png"),
                risk_overlay_path=state.risk_overlay_path,
                legend=[
                    {"label": "Baseline diagnosis", "color": "Translucent red"},
                    {"label": "Main entrance", "color": "Solid red"},
                    {"label": "Electrical board", "color": "Solid blue"},
                ],
                summary_text=state.risk_summary_text or "",
                details=[],
            )
        risk_view = self.risk_service.build(
            review_bundle_path=Path(state.review_bundle_path),
            review_approved_path=Path(state.review_approved_path),
            output_path=workspace.review_dir / "risk_overlay.png",
        )
        state.risk_overlay_path = risk_view.risk_overlay_path
        state.risk_summary_text = risk_view.summary_text
        self.persist(state)
        return risk_view

    def set_proposal_level(self, level: SecurityLevel) -> WizardSessionState:
        state = self.state()
        state.proposal_level = level.value
        return self.persist(state)

    def _proposal_from_cache(self, state: WizardSessionState, level: SecurityLevel) -> ProposalViewModel | None:
        proposal_path = state.proposal_paths_by_level.get(level.value)
        if not proposal_path:
            return None
        overlay_path = state.overlay_paths_by_level.get(level.value)
        if overlay_path and Path(overlay_path).is_file():
            try:
                if Path(overlay_path).name != PROPOSAL_OVERLAY_BASENAME:
                    return None
                with Image.open(overlay_path) as overlay_image:
                    if overlay_image.width < MIN_PROPOSAL_RENDER_WIDTH:
                        return None
            except OSError:
                return None
        devices: list = []
        if Path(proposal_path).is_file():
            devices = list((self.artifact_store.read_json(Path(proposal_path)).get("devices") or []))
        if state.review_bundle_path and state.review_approved_path and devices:
            devices, grid_h, grid_w = self.proposal_service.resolve_devices_for_overlay(
                review_bundle_path=Path(state.review_bundle_path),
                review_approved_path=Path(state.review_approved_path),
                proposal_devices=devices,
            )
        else:
            grid_h, grid_w = 0, 0
        return ProposalViewModel(
            security_level=level.planner_code,
            devices=devices,
            overlay_path=overlay_path,
            counts_by_type=state.proposal_counts_by_level.get(level.value, {}),
            proposal_summary=state.proposal_summaries_by_level.get(level.value, ""),
            proposal_path=proposal_path,
            report_path=state.report_paths_by_level.get(level.value),
            grid_h=grid_h,
            grid_w=grid_w,
        )

    def ensure_proposal_view(self, progress_cb: ProgressCallback | None = None) -> ProposalViewModel:
        state = self.state()
        if not state.review_bundle_path or not state.review_approved_path:
            raise RuntimeError("La propuesta necesita una revisión aprobada.")
        level = SecurityLevel(state.proposal_level)
        cached = self._proposal_from_cache(state, level)
        if cached is not None:
            return cached

        workspace = self._workspace(state)
        proposal_view = self.proposal_service.build(
            workspace=workspace,
            review_bundle_path=Path(state.review_bundle_path),
            review_approved_path=Path(state.review_approved_path),
            level=level,
            progress_cb=progress_cb,
        )
        state.proposal_paths_by_level[level.value] = proposal_view.proposal_path or ""
        state.report_paths_by_level[level.value] = proposal_view.report_path or ""
        state.overlay_paths_by_level[level.value] = proposal_view.overlay_path or ""
        state.proposal_summaries_by_level[level.value] = proposal_view.proposal_summary
        state.proposal_counts_by_level[level.value] = proposal_view.counts_by_type
        self.persist(state)
        return proposal_view

    def get_kit_view(self) -> KitViewModel:
        state = self.state()
        level = SecurityLevel(state.proposal_level)
        cached = state.kit_by_level.get(level.value)
        if cached:
            return KitViewModel(
                items=list(cached.get("items") or []),
                hero_summary=str(cached.get("hero_summary") or ""),
                cta_payload=dict(cached.get("cta_payload") or {}),
                level_label=str(cached.get("level_label") or level.label),
            )
        proposal = self.ensure_proposal_view()
        kit = self.kit_service.build(proposal)
        state.kit_by_level[level.value] = kit.to_dict()
        self.persist(state)
        return kit
