"""
Phase 5H — Profile Isolation Guard.

Ensures that evaluations from different Jaimini Dasha profiles are never
merged. Each profile's candidates are kept strictly separate.

This is a structural constraint, not a suggestion. Violations are
reported as validation errors.
"""
from __future__ import annotations

from typing import Dict, List, Set

from core.jaimini.candidates import JaiminiEventCandidate


class ProfileIsolationGuard:
    """Enforces profile isolation across candidate sets.

    Usage:
        guard = ProfileIsolationGuard()
        guard.register("PROFILE_A", candidates_a)
        guard.register("PROFILE_B", candidates_b)
        violations = guard.check_isolation()
    """

    def __init__(self) -> None:
        self._profile_candidates: Dict[str, List[JaiminiEventCandidate]] = {}
        self._profile_ids: Set[str] = set()

    def register(
        self, profile_id: str, candidates: List[JaiminiEventCandidate]
    ) -> None:
        """Register candidates for a profile."""
        self._profile_candidates[profile_id] = list(candidates)
        self._profile_ids.add(profile_id)

    def check_isolation(self) -> List[str]:
        """Verify no candidate is shared across profiles.

        Returns list of violations (empty = clean).
        """
        violations: List[str] = []
        seen_candidate_ids: Dict[str, str] = {}

        for profile_id in sorted(self._profile_ids):
            for c in self._profile_candidates.get(profile_id, []):
                if c.candidate_id in seen_candidate_ids:
                    other_profile = seen_candidate_ids[c.candidate_id]
                    violations.append(
                        f"Candidate {c.candidate_id} registered under both "
                        f"'{other_profile}' and '{profile_id}'."
                    )
                else:
                    seen_candidate_ids[c.candidate_id] = profile_id

        return violations

    def get_candidates(self, profile_id: str) -> List[JaiminiEventCandidate]:
        """Get candidates for a specific profile."""
        return list(self._profile_candidates.get(profile_id, []))

    def all_profiles(self) -> List[str]:
        """List all registered profiles."""
        return sorted(self._profile_ids)

    def merge_profiles(self) -> Dict[str, List[JaiminiEventCandidate]]:
        """Return per-profile candidate lists (never merged)."""
        return {
            pid: list(cands)
            for pid, cands in sorted(self._profile_candidates.items())
        }
