from __future__ import annotations

from enum import Enum


class WizardScreen(str, Enum):
    INTRO = "intro"
    UPLOAD = "upload"
    PROCESSING = "processing"
    REVIEW = "review"
    REVIEW_MARKERS = "review_markers"
    RISK = "risk"
    PROPOSAL = "proposal"
    KIT = "kit"

    @property
    def label(self) -> str:
        return {
            WizardScreen.INTRO: "Welcome",
            WizardScreen.UPLOAD: "Floor plan",
            WizardScreen.PROCESSING: "Analysis",
            WizardScreen.REVIEW: "Review",
            WizardScreen.REVIEW_MARKERS: "References",
            WizardScreen.RISK: "Diagnosis",
            WizardScreen.PROPOSAL: "Solution",
            WizardScreen.KIT: "Kit",
        }[self]


class SecurityLevel(str, Enum):
    BASIC = "basic"
    RECOMMENDED = "recommended"
    MAXIMUM = "maximum"

    @property
    def label(self) -> str:
        return {
            SecurityLevel.BASIC: "Basic",
            SecurityLevel.RECOMMENDED: "Recommended",
            SecurityLevel.MAXIMUM: "Maximum",
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
