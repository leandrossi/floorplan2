from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import streamlit as st

from domain.enums import ProcessingStatus, SecurityLevel, WizardScreen

STATE_KEY = "wizard_mvp_state"


@dataclass
class WizardSessionState:
    session_id: str | None = None
    current_screen: str = WizardScreen.INTRO.value
    workspace_path: str | None = None
    upload_path: str | None = None
    uploaded_file_name: str | None = None
    processing_status: str = ProcessingStatus.IDLE.value
    processing_message: str | None = None
    processing_requested: bool = False
    step04_dir: str | None = None
    review_bundle_path: str | None = None
    review_preview_path: str | None = None
    review_approved_path: str | None = None
    corrected_preview_path: str | None = None
    risk_overlay_path: str | None = None
    risk_summary_text: str | None = None
    proposal_level: str = SecurityLevel.RECOMMENDED.value
    proposal_paths_by_level: dict[str, str] = field(default_factory=dict)
    report_paths_by_level: dict[str, str] = field(default_factory=dict)
    overlay_paths_by_level: dict[str, str] = field(default_factory=dict)
    proposal_summaries_by_level: dict[str, str] = field(default_factory=dict)
    proposal_counts_by_level: dict[str, dict[str, int]] = field(default_factory=dict)
    kit_by_level: dict[str, dict[str, Any]] = field(default_factory=dict)
    main_entry: list[int] | None = None
    electric_board: list[int] | None = None
    struct_patch: list[dict[str, int]] = field(default_factory=list)
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WizardSessionState":
        if not data:
            return cls()
        allowed = {field_name for field_name in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


def load_wizard_state() -> WizardSessionState:
    return WizardSessionState.from_dict(st.session_state.get(STATE_KEY))


def save_wizard_state(state: WizardSessionState) -> WizardSessionState:
    st.session_state[STATE_KEY] = state.to_dict()
    return state


def clear_runtime_widget_state() -> None:
    for key in (
        "review_last_paint_dedupe",
        "review_last_grid_pick_dedupe",
        "review_img_click_sig",
    ):
        st.session_state.pop(key, None)


def reset_flow_state(state: WizardSessionState) -> WizardSessionState:
    current_session = state.session_id
    current_workspace = state.workspace_path
    new_state = WizardSessionState(
        session_id=current_session,
        workspace_path=current_workspace,
        current_screen=WizardScreen.UPLOAD.value,
    )
    clear_runtime_widget_state()
    return new_state
