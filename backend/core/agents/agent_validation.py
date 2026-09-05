"""
Phase 7 — validation gates: context validation, applicability pre-check,
capability/tradition checks, provenance + conflict + unknown validation.

Validation never mutates. Every gate returns sorted string notes; empty means
pass. Missing prerequisites yield UNKNOWN/PARTIAL, never silent substitution.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .agent_contract import AgentContract
from .agent_models import UNKNOWN as UNKNOWN_FINDING


def _section_present(context: Any, section: str) -> bool:
    value = getattr(context, section, None)
    if value is None:
        return False
    if isinstance(value, (dict, list)):
        return len(value) > 0
    return True


def validate_context(context: Any, contract: AgentContract) -> List[str]:
    """Required sections present and non-empty; returns missing section names."""
    return sorted(s for s in contract.required_inputs if not _section_present(context, s))


def validate_traditions(context: Any, contract: AgentContract) -> List[str]:
    """At least one context tradition must be within the agent's allowed set.

    Overlap (not subset) semantics: a multi-tradition chart context is usable
    by every agent whose own tradition is represented; agents only ever read
    their in-scope sections. No silent conversion occurs."""
    allowed = set(contract.allowed_traditions)
    requested = set(context.allowed_traditions or [])
    if not requested:
        return []
    if requested & allowed:
        return []
    return sorted(f"no overlap: context {sorted(requested)} vs "
                  f"{contract.agent_id} allows {sorted(allowed)}")


def validate_profile(profile: str, contract: AgentContract) -> List[str]:
    """Profiles constrain only agents that declare supported_profiles."""
    if not contract.supported_profiles:
        return []
    if not profile:
        return []
    if profile in contract.supported_profiles:
        return []
    return [f"profile {profile!r} unsupported by {contract.agent_id}"]


def validate_capability(contract: AgentContract, sections: List[str]) -> List[str]:
    """All read sections must be declared in accepted_inputs."""
    return sorted(f"section {s!r} outside capability" for s in sections
                  if not contract.can_read(s))


def applicability_gate(context: Any, contract: AgentContract) -> Dict[str, Any]:
    """Phase 6E-style pre-check: required inputs, tradition, lifecycle-of-inputs.

    Returns a verdict dict; agents map it to UNKNOWN/PARTIAL/INVALID.
    """
    missing = validate_context(context, contract)
    tradition_notes = validate_traditions(context, contract)
    profile_notes = validate_profile(context.profile, contract)
    gate_notes = sorted(tradition_notes + profile_notes)
    if gate_notes:
        return {"verdict": "INVALID", "missing": missing,
                "tradition_notes": gate_notes}
    if missing:
        return {"verdict": "UNKNOWN", "missing": missing, "tradition_notes": []}
    optional_missing = sorted(s for s in contract.optional_inputs
                              if not _section_present(context, s))
    if optional_missing:
        return {"verdict": "PARTIAL", "missing": [], "optional_missing": optional_missing,
                "tradition_notes": []}
    return {"verdict": "OK", "missing": [], "tradition_notes": []}


def validate_provenance(result: Any, context: Any) -> List[str]:
    """Every substantive conclusion must chain to supplied inputs. (§9)"""
    notes = []
    known_facts = set(context.known_fact_keys())
    known_rules = set(context.known_rule_ids())
    known_evidence = set(context.evidence_ids)
    for finding in result.findings:
        if finding.type in ("RULE_RESULT", "INTERPRETATION"):
            if not finding.supporting_inputs:
                notes.append(f"{finding.finding_id}: no supporting inputs")
                continue
            for key in finding.supporting_inputs:
                if key not in known_facts and key not in known_rules:
                    notes.append(f"{finding.finding_id}: unsupported input {key!r}")
            for eid in finding.evidence_ids:
                if eid not in known_evidence:
                    notes.append(f"{finding.finding_id}: unknown evidence {eid!r}")
    if result.provenance.input_fingerprint != context.fingerprint():
        notes.append("provenance input fingerprint mismatch")
    return sorted(notes)


def validate_conflicts(result: Any, context: Any,
                       rule_ids: List[str] | None = None) -> List[str]:
    """Supplied conflicts relevant to the agent's used rules must surface.

    Only conflicts touching the agent's domain (its used rule ids) are
    required to propagate; catalogue conflicts from other systems must not
    force every agent to CONFLICTED. (§11)"""
    notes = []
    scope = set(rule_ids if rule_ids is not None else result.rule_results_used)
    relevant = {c.conflict_id for c in context.conflicts
                if c.rule_a in scope or c.rule_b in scope}
    reported = set(result.conflicts)
    if relevant and result.status != "CONFLICTED":
        notes.append("relevant conflicts supplied but status is not CONFLICTED")
    for cid in sorted(relevant):
        if cid not in reported:
            notes.append(f"supplied conflict {cid!r} not propagated")
    return sorted(notes)


def validate_unknowns(result: Any, gate: Dict[str, Any]) -> List[str]:
    """Missing inputs must propagate as UNKNOWN findings/unknowns. (§12)"""
    notes = []
    for missing in gate.get("missing", []):
        if missing not in result.unknowns and not any(
                missing in f.supporting_inputs or missing in f.statement
                for f in result.findings if f.type == UNKNOWN_FINDING):
            notes.append(f"missing input {missing!r} not propagated as UNKNOWN")
    return sorted(notes)
