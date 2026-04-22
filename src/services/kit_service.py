from __future__ import annotations

from domain.contracts import KitViewModel, ProposalViewModel
from domain.enums import SecurityLevel

DEVICE_COPY: dict[str, tuple[str, str]] = {
    "panel": ("Panel central", "Coordina todo el sistema de alarma."),
    "keyboard": ("Teclado", "Permite activar y desactivar la alarma."),
    "magnetic": ("Sensor magnético", "Protege accesos como puertas y ventanas."),
    "pir": ("Sensor de movimiento", "Cubre áreas de paso dentro de la casa."),
    "pircam": ("Sensor con cámara", "Detecta movimiento y agrega verificación visual."),
    "siren_indoor": ("Sirena interior", "Alerta dentro de la vivienda."),
    "siren_outdoor": ("Sirena exterior", "Hace visible y audible la alarma desde afuera."),
}


class KitService:
    def build(self, proposal: ProposalViewModel) -> KitViewModel:
        items: list[dict[str, str | int]] = []
        for device_type, qty in sorted(proposal.counts_by_type.items()):
            friendly_name, purpose = DEVICE_COPY.get(
                device_type,
                (device_type.replace("_", " ").title(), "Componente incluido en la solución."),
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
            f"Kit {level.label}: una selección clara de componentes para instalar la propuesta "
            "que viste sobre tu plano."
        )
        return KitViewModel(
            items=items,
            hero_summary=hero_summary,
            cta_payload={"primary": "Empezar otro plano", "secondary": "Volver a la solución"},
            level_label=level.label,
        )
