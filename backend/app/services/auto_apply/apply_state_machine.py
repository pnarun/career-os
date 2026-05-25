"""Apply flow state machine — human-in-the-loop transitions."""

from __future__ import annotations

from app.models.auto_apply import ApplyState

TERMINAL_STATES: frozenset[ApplyState] = frozenset({
    "SUCCESS",
    "FAILED",
    "CAPTCHA_BLOCKED",
    "CANCELLED",
})

ALLOWED_TRANSITIONS: dict[ApplyState, frozenset[ApplyState]] = {
    "IDLE": frozenset({"OPENING_JOB", "FAILED", "CANCELLED"}),
    "OPENING_JOB": frozenset({"DETECTING_FORM", "FAILED", "CAPTCHA_BLOCKED", "CANCELLED"}),
    "DETECTING_FORM": frozenset({
        "UPLOADING_RESUME",
        "FILLING_FIELDS",
        "DETECTING_QUESTIONS",
        "FAILED",
        "CAPTCHA_BLOCKED",
        "CANCELLED",
    }),
    "UPLOADING_RESUME": frozenset({"FILLING_FIELDS", "DETECTING_QUESTIONS", "FAILED", "CANCELLED"}),
    "FILLING_FIELDS": frozenset({"DETECTING_QUESTIONS", "WAITING_CONFIRMATION", "FAILED", "CANCELLED"}),
    "DETECTING_QUESTIONS": frozenset({"WAITING_CONFIRMATION", "FAILED", "CANCELLED"}),
    "WAITING_CONFIRMATION": frozenset({"SUBMITTING", "CANCELLED", "FAILED"}),
    "SUBMITTING": frozenset({"SUCCESS", "FAILED", "CAPTCHA_BLOCKED"}),
    "SUCCESS": frozenset(),
    "FAILED": frozenset(),
    "CAPTCHA_BLOCKED": frozenset(),
    "CANCELLED": frozenset(),
}


class ApplyStateMachine:
    def __init__(self, initial: ApplyState = "IDLE") -> None:
        self.state = initial

    def can_transition(self, target: ApplyState) -> bool:
        return target in ALLOWED_TRANSITIONS.get(self.state, frozenset())

    def transition(self, target: ApplyState) -> ApplyState:
        if not self.can_transition(target):
            raise ValueError(f"Invalid transition: {self.state} → {target}")
        self.state = target
        return self.state

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES
