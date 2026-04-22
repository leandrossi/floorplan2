from __future__ import annotations

from application.wizard_state import WizardSessionState
from domain.enums import WizardScreen

SCREEN_ORDER: tuple[WizardScreen, ...] = (
    WizardScreen.INTRO,
    WizardScreen.UPLOAD,
    WizardScreen.PROCESSING,
    WizardScreen.REVIEW,
    WizardScreen.RISK,
    WizardScreen.PROPOSAL,
    WizardScreen.KIT,
)


def get_screen(screen_name: str | WizardScreen) -> WizardScreen:
    if isinstance(screen_name, WizardScreen):
        return screen_name
    try:
        return WizardScreen(str(screen_name))
    except ValueError:
        return WizardScreen.KIT


def next_screen(screen_name: str | WizardScreen) -> WizardScreen:
    screen = get_screen(screen_name)
    idx = SCREEN_ORDER.index(screen)
    return SCREEN_ORDER[min(idx + 1, len(SCREEN_ORDER) - 1)]


def previous_screen(screen_name: str | WizardScreen) -> WizardScreen:
    screen = get_screen(screen_name)
    idx = SCREEN_ORDER.index(screen)
    return SCREEN_ORDER[max(idx - 1, 0)]


def can_enter(screen_name: str | WizardScreen, state: WizardSessionState) -> bool:
    screen = get_screen(screen_name)
    if screen is WizardScreen.INTRO:
        return True
    if screen is WizardScreen.UPLOAD:
        return True
    if screen is WizardScreen.PROCESSING:
        return bool(state.upload_path)
    if screen is WizardScreen.REVIEW:
        return bool(state.review_bundle_path)
    if screen is WizardScreen.RISK:
        return bool(state.review_approved_path)
    if screen is WizardScreen.PROPOSAL:
        return bool(state.review_approved_path and state.risk_overlay_path)
    if screen is WizardScreen.KIT:
        return bool(state.proposal_paths_by_level.get(state.proposal_level))
    return False


def available_screens(state: WizardSessionState) -> list[WizardScreen]:
    return [screen for screen in SCREEN_ORDER if can_enter(screen, state)]
