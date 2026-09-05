"""
Phase 6C — Rule lifecycle state machine.

Defines legal state transitions and validates that no silent activation occurs.
All state changes are explicit and auditable.

Legal states:
  DRAFT, VALIDATED, TESTED, REVIEW_PENDING, ACTIVE,
  DISABLED, DEPRECATED, ARCHIVED, REJECTED

Legal transitions:
  DRAFT -> VALIDATED
  VALIDATED -> TESTED
  TESTED -> REVIEW_PENDING
  REVIEW_PENDING -> ACTIVE
  ACTIVE -> DISABLED
  ACTIVE -> DEPRECATED
  DISABLED -> ACTIVE
  DEPRECATED -> ARCHIVED
  REVIEW_PENDING -> REJECTED
  REJECTED -> DRAFT
  VALIDATED -> DRAFT
  TESTED -> DRAFT

Invalid transitions (raise LifecycleTransitionError):
  DRAFT -> ACTIVE (no direct activation without validation, test, and review)
  Any transition not in the legal set
"""
from __future__ import annotations

from typing import FrozenSet, Optional, Set, Tuple

# ——— Legal lifecycle states ———
LIFECYCLE_STATES: FrozenSet[str] = frozenset({
    "DRAFT",
    "VALIDATED",
    "TESTED",
    "REVIEW_PENDING",
    "ACTIVE",
    "DISABLED",
    "DEPRECATED",
    "ARCHIVED",
    "REJECTED",
})

# ——— Legal transition matrix ———
LEGAL_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset({
    ("DRAFT", "VALIDATED"),
    ("VALIDATED", "TESTED"),
    ("TESTED", "REVIEW_PENDING"),
    ("REVIEW_PENDING", "ACTIVE"),
    ("ACTIVE", "DISABLED"),
    ("ACTIVE", "DEPRECATED"),
    ("DISABLED", "ACTIVE"),
    ("DEPRECATED", "ARCHIVED"),
    ("REVIEW_PENDING", "REJECTED"),
    ("REJECTED", "DRAFT"),
    ("VALIDATED", "DRAFT"),
    ("TESTED", "DRAFT"),
})


class LifecycleTransitionError(ValueError):
    """Raised when an illegal lifecycle transition is attempted."""
    pass


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Check whether a state transition is legal."""
    if from_state not in LIFECYCLE_STATES or to_state not in LIFECYCLE_STATES:
        return False
    return (from_state, to_state) in LEGAL_TRANSITIONS


def validate_transition(from_state: str, to_state: str) -> None:
    """Raise LifecycleTransitionError if the transition is not legal."""
    if not is_valid_transition(from_state, to_state):
        legal = ", ".join(
            f"{f} -> {t}" for f, t in sorted(LEGAL_TRANSITIONS)
        )
        raise LifecycleTransitionError(
            f"Invalid lifecycle transition: {from_state} -> {to_state}. "
            f"Legal transitions: {legal}"
        )


class RuleLifecycleStateMachine:
    """State machine controller for rule lifecycle transitions."""

    def __init__(self, initial: str = "DRAFT") -> None:
        if initial not in LIFECYCLE_STATES:
            raise ValueError(f"Initial lifecycle status must be one of {sorted(LIFECYCLE_STATES)}, got {initial}")
        self.status: str = initial

    def transition(self, to_state: str) -> str:
        """Transition to a new state, validating the move."""
        validate_transition(self.status, to_state)
        self.status = to_state
        return self.status

    def can_reach(self, target: str, visited: Optional[Set[str]] = None) -> bool:
        """Check whether target state is reachable from current state via legal moves."""
        if visited is None:
            visited = set()
        if self.status == target:
            return True
        if self.status in visited:
            return False
        visited.add(self.status)

        current = self.status
        for next_state in LIFECYCLE_STATES:
            if is_valid_transition(current, next_state):
                self.status = next_state
                if self.can_reach(target, visited):
                    self.status = current
                    return True
                self.status = current
        return False