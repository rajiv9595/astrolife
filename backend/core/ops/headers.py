"""
Phase 12 — security headers. Conservative defaults that do not break the
existing SPA (no restrictive CSP by default; documented exception).
"""
from __future__ import annotations

from typing import Dict

SECURITY_HEADERS: Dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "SAMEORIGIN",
    # Content-Security-Policy intentionally NOT set by default: the existing
    # Vite SPA uses inline module scripts; a restrictive CSP would break it.
    # Deployments may add a tailored CSP after verifying the built bundle.
}
