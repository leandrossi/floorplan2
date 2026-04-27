from __future__ import annotations

from domain.contracts import KitViewModel, ProposalViewModel
from domain.enums import SecurityLevel

DEVICE_COPY: dict[str, tuple[str, str]] = {
    "panel": ("Central panel", "Coordinates the whole alarm system."),
    "keyboard": ("Keypad", "Arm and disarm the system."),
    "magnetic": ("Magnetic contact", "Protects openings such as doors and windows."),
    "pir": ("Motion sensor", "Covers movement in hallways and rooms."),
    "pircam": ("Camera sensor", "Detects movement with visual verification."),
    "siren_indoor": ("Indoor siren", "Alerts inside the home."),
    "siren_outdoor": ("Outdoor siren", "Makes the alarm visible and audible outside."),
}


class KitService:
    def build(self, proposal: ProposalViewModel) -> KitViewModel:
        items: list[dict[str, str | int]] = []
        for device_type, qty in sorted(proposal.counts_by_type.items()):
            friendly_name, purpose = DEVICE_COPY.get(
                device_type,
                (device_type.replace("_", " ").title(), "Included in this recommendation."),
            )
            items.append(
                {
                    "device_type": device_type,
                    "name": friendly_name,
                    "quantity": int(qty),
                    "purpose": purpose,
                }
            )

        level = SecurityLevel.from_planner_code(proposal.security_level)
        hero_summary = (
            f"{level.label} kit: a clear parts list to install the setup you reviewed on your floorplan."
        )
        return KitViewModel(
            items=items,
            hero_summary=hero_summary,
            cta_payload={"primary": "Start another floorplan", "secondary": "Back to solution"},
            level_label=level.label,
        )
