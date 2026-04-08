from __future__ import annotations

"""
Central configuration for alarm planning rules (Milestone -1).

This keeps per-device / per-profile parameters in one place so that
the core engine code stays readable and behaviour is easy to tweak.
"""

from dataclasses import dataclass
from typing import Dict

from .model import SecurityLevel


@dataclass(frozen=True)
class MagneticRules:
    """
    Rules controlling magnetic contacts on exterior openings.

    - protect_main_entry_only: when True, only main entry opening groups are protected.
    - protect_all_doors: protect all exterior doors (subject to other flags).
    - protect_windows: also protect exterior windows.
    - suppression_radius_m: radius in meters used to clear local red cells
      around covered openings.
    """

    protect_main_entry_only: bool
    protect_all_doors: bool
    protect_windows: bool
    suppression_radius_m: float


@dataclass(frozen=True)
class PirRules:
    """
    Rules controlling PIR / PIRCAM motion placement.

    - radius_m: nominal coverage radius in meters.
    - fov_deg: nominal FOV angle (kept for future orientation modelling).
    - protect_unmagnetized_doors: whether to force door-anchored PIRs for
      exterior doors that don't have magnetics.
    """

    radius_m: float
    fov_deg: float
    protect_unmagnetized_doors: bool


@dataclass(frozen=True)
class SirenRules:
    """
    Rules controlling siren placement.

    Siren placement is not yet implemented; this struct is here to make it
    easy to wire in later without changing the public contract.
    """

    place_indoor: bool
    place_outdoor: bool


ALARM_RULES: Dict[SecurityLevel, Dict[str, object]] = {
    SecurityLevel.MIN: {
        "magnetic": MagneticRules(
            protect_main_entry_only=True,
            protect_all_doors=False,
            protect_windows=False,
            suppression_radius_m=2.0,
        ),
        "pir": PirRules(
            radius_m=8.0,
            fov_deg=90.0,
            protect_unmagnetized_doors=True,
        ),
        "siren": SirenRules(
            place_indoor=True,
            place_outdoor=False,
        ),
    },
    SecurityLevel.OPTIMAL: {
        "magnetic": MagneticRules(
            protect_main_entry_only=False,
            protect_all_doors=True,
            protect_windows=False,
            suppression_radius_m=2.0,
        ),
        "pir": PirRules(
            radius_m=8.0,
            fov_deg=90.0,
            protect_unmagnetized_doors=True,
        ),
        "siren": SirenRules(
            place_indoor=True,
            place_outdoor=True,
        ),
    },
    SecurityLevel.MAX: {
        "magnetic": MagneticRules(
            protect_main_entry_only=False,
            protect_all_doors=True,
            protect_windows=True,
            suppression_radius_m=2.0,
        ),
        "pir": PirRules(
            radius_m=8.0,
            fov_deg=90.0,
            protect_unmagnetized_doors=False,
        ),
        "siren": SirenRules(
            place_indoor=True,
            place_outdoor=True,
        ),
    },
}

