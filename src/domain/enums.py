from __future__ import annotations

from enum import Enum


class WizardScreen(str, Enum):
    INTRO = "intro"
    UPLOAD = "upload"
    PROCESSING = "processing"
    REVIEW = "review"
    RISK = "risk"
    PROPOSAL = "proposal"
    KIT = "kit"

    @property
    def label(self) -> str:
        return {
            WizardScreen.INTRO: "Inicio",
            WizardScreen.UPLOAD: "Plano",
            WizardScreen.PROCESSING: "Análisis",
            WizardScreen.REVIEW: "Revisión",
            WizardScreen.RISK: "Diagnóstico",
            WizardScreen.PROPOSAL: "Solución",
            WizardScreen.KIT: "Kit",
        }[self]


class SecurityLevel(str, Enum):
    BASIC = "basic"
    RECOMMENDED = "recommended"
    MAXIMUM = "maximum"

    @property
    def label(self) -> str:
        return {
            SecurityLevel.BASIC: "Básico",
            SecurityLevel.RECOMMENDED: "Recomendado",
            SecurityLevel.MAXIMUM: "Máximo",
        }[self]

    @property
    def planner_code(self) -> str:
        return {
            SecurityLevel.BASIC: "min",
            SecurityLevel.RECOMMENDED: "optimal",
            SecurityLevel.MAXIMUM: "max",
        }[self]

    @classmethod
    def from_planner_code(cls, value: str) -> "SecurityLevel":
        normalized = str(value).strip().lower()
        mapping = {
            "min": cls.BASIC,
            "optimal": cls.RECOMMENDED,
            "max": cls.MAXIMUM,
            "basic": cls.BASIC,
            "recommended": cls.RECOMMENDED,
            "maximum": cls.MAXIMUM,
        }
        return mapping.get(normalized, cls.RECOMMENDED)


class ProcessingStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
