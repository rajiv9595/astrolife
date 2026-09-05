"""
Phase 5G-H — Sign sequence strategies. Profile-aware direction rules.
Pure index arithmetic; no astro.
"""
from __future__ import annotations
from typing import List, Union, Optional

from ..arudha import SIGNS
from ..rashi_drishti import SIGN_TYPES
from .profile import (
    JaiminiDashaProfile,
    direction_for_start_sign as profile_direction_for_start_sign,
)

FORWARD = "FORWARD"
REVERSE = "REVERSE"


# Default profile for backward compatibility (Convention A)
_DEFAULT_PROFILE = JaiminiDashaProfile(
    method="CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL"
)


def direction_for_start_sign(
    arg1: Union[JaiminiDashaProfile, str],
    arg2: Optional[str] = None
) -> str:
    """
    Get direction for start sign under the given profile.
    
    Supports two call signatures for backward compatibility:
    1. direction_for_start_sign(profile, start_sign) - new profile-aware
    2. direction_for_start_sign(start_sign) - legacy, uses default Convention A
    """
    if isinstance(arg1, JaiminiDashaProfile) and arg2 is not None:
        return profile_direction_for_start_sign(arg1, arg2)
    elif isinstance(arg1, str) and arg2 is None:
        # Legacy call: direction_for_start_sign(start_sign)
        return profile_direction_for_start_sign(_DEFAULT_PROFILE, arg1)
    else:
        raise TypeError(
            "direction_for_start_sign expects either (profile, start_sign) "
            "or (start_sign) for legacy compatibility"
        )


def step(sign: str, direction: str, n: int = 1) -> str:
    idx = SIGNS.index(sign)
    delta = n if direction == FORWARD else -n
    return SIGNS[(idx + delta) % 12]


def full_cycle(start_sign: str, direction: str) -> List[str]:
    """All 12 signs exactly once from the start sign in sequence direction."""
    seq = [start_sign]
    cur = start_sign
    for _ in range(11):
        cur = step(cur, direction)
        seq.append(cur)
    return seq