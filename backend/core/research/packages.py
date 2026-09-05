"""
Phase 9 — research packages: isolated research namespace, deterministic
fingerprints, JSON-serializable, versioned, schema-validated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import canonical_json, fingerprint_of
from . import validation as _validation

_STORE: Dict[str, Dict[str, Any]] = {}


def _key(package_id: str, package_version: str) -> str:
    return f"{package_id}@{package_version}"


def package_fingerprint(pkg: Dict[str, Any]) -> str:
    slim = {k: v for k, v in pkg.items() if k != "fingerprint"}
    return fingerprint_of(slim)


def create_research_package(package_id: str, package_version: str = "0.1.0",
                            author: str = "", description: str = "",
                            profiles: Optional[List[str]] = None,
                            **extra: Any) -> Dict[str, Any]:
    pkg: Dict[str, Any] = {
        "package_id": package_id,
        "package_version": package_version,
        "author": author,
        "author_email": extra.get("author_email", ""),
        "description": description,
        "rules": list(extra.get("rules", [])),
        "sources": list(extra.get("sources", [])),
        "claims": list(extra.get("claims", [])),
        "evidence": list(extra.get("evidence", [])),
        "dependencies": dict(extra.get("dependencies", {})),
        "fixtures": list(extra.get("fixtures", [])),
        "profiles": list(profiles or extra.get("profiles", ["PARASHARI_CLASSICAL"])),
        "experiments": list(extra.get("experiments", [])),
        "review": dict(extra.get("review", {})),
        "lifecycle": extra.get("lifecycle", "EXPERIMENTAL"),
    }
    pkg["fingerprint"] = package_fingerprint(pkg)
    _STORE[_key(package_id, package_version)] = pkg
    return pkg


def validate_research_package(pkg: Dict[str, Any]) -> Dict[str, Any]:
    ok, errors, warnings = _validation.validate_research_package(pkg)
    return {"valid": ok, "errors": errors, "warnings": warnings,
            "fingerprint": package_fingerprint(pkg)}


def get_research_package(package_id: str, package_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if package_version:
        return _STORE.get(_key(package_id, package_version))
    cands = [v for k, v in _STORE.items() if k.startswith(package_id + "@")]
    if not cands:
        return None
    return sorted(cands, key=lambda p: p.get("package_version", ""))[-1]


def list_research_packages() -> List[Dict[str, Any]]:
    return sorted(_STORE.values(), key=lambda p: (p.get("package_id", ""), p.get("package_version", "")))


def export_package(pkg: Dict[str, Any]) -> str:
    return canonical_json(pkg)


def import_package(payload: str) -> Dict[str, Any]:
    import json
    obj = json.loads(payload)
    if not isinstance(obj, dict) or "package_id" not in obj:
        raise ValueError("invalid research package payload")
    ok, errors, _ = _validation.validate_research_package(obj)
    if not ok:
        raise ValueError(f"package schema invalid: {errors}")
    _STORE[_key(obj["package_id"], obj.get("package_version", "0.1.0"))] = obj
    return obj


def clear_store() -> None:
    _STORE.clear()
