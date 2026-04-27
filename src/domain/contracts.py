from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from domain.enums import ProcessingStatus


@dataclass
class ProcessingResult:
    session_id: str
    workspace_path: str
    upload_path: str
    base_image_path: str | None
    review_bundle_path: str | None
    preview_paths: dict[str, str] = field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.IDLE
    step04_dir: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class ReviewResult:
    approved: bool
    review_bundle_path: str
    review_approved_path: str | None
    main_entry: list[int] | None
    electric_board: list[int] | None
    corrected_preview_path: str | None
    blocking_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checklist: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskViewModel:
    base_plan_path: str | None
    risk_overlay_path: str | None
    legend: list[dict[str, str]]
    summary_text: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProposalViewModel:
    security_level: str
    devices: list[dict[str, Any]]
    overlay_path: str | None
    counts_by_type: dict[str, int]
    proposal_summary: str
    proposal_path: str | None = None
    report_path: str | None = None
    grid_h: int = 0
    grid_w: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KitViewModel:
    items: list[dict[str, Any]]
    hero_summary: str
    cta_payload: dict[str, str] = field(default_factory=dict)
    level_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
