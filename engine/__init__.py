"""Manifold Landscape computation engine.

A verification-backed engine for the geometry of continuous mathematics. Every quantity
it produces carries a provenance (which deterministic routine computed it) and a
verification (an independent confirmation that it is correct); nothing unverified, and
nothing model-sourced, is allowed to surface. See ``result.py`` for that mechanism and
constraint C-VERIFIED-MATH for why it exists.
"""

from .result import (
    Quantity,
    Solution,
    Verification,
    UnverifiedResultError,
    ALLOWED_PROVENANCE,
    MODEL_PROVENANCE,
)

__all__ = [
    "Quantity",
    "Solution",
    "Verification",
    "UnverifiedResultError",
    "ALLOWED_PROVENANCE",
    "MODEL_PROVENANCE",
]
