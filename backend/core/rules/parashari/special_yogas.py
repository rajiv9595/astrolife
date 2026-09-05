"""
Phase 5B — special/small yogas that do not fit other files.
Currently: Yogakaraka placement is in raja_yoga; this module is reserved
for future clearly-sourced additions. Kept intentionally small per
"fewer correct yogas" rule.
"""
from __future__ import annotations

# No additional yogas promoted in Phase 5B. This module documents that
# Vesi/Vasi/Ubhayachari, Sakata, Kahala, Chamara, Matsya/Kurma/Parvata,
# Brahma/Vishnu/Shiva complexes, Pushkala, Kalpadruma, Akhanda Samrajya and
# similar legacy-JSON names were audited and deliberately NOT promoted
# (see SOURCE_AUDIT §Omitted). Importing this module must not register rules.

FORMATION_EVALUATORS = {}


def build_extra_rules():
    """Return [] — no extra rules promoted in Phase 5B."""
    return []
