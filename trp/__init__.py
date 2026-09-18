"""Trust Requirements Profile (TRP).

An open standard for stating and verifying the trust requirements of AI and
autonomous systems.

Specification version 0.5. Published under Apache License 2.0 and stewarded by
the AI Trust Alliance.

Basic use:

    from trp import load_profile, evaluate

    profile = load_profile("trp.json")
    result = evaluate(profile, {"vibration_rms_g": 0.4, "temperature_C": 62})
    print(result["standing"])

Command line:

    trp demo                      run a complete example end to end
    trp init manufacturing        scaffold a new profile from a starter
    trp validate trp.json         check a profile against the schema
    trp sample trp.json           generate sample evidence for a profile
    trp evaluate trp.json ev.json evaluate evidence against a profile
"""

from __future__ import annotations

from .evaluate import (
    DriftDetector,
    HardRule,
    Profile,
    ScoredSignal,
    StandingBand,
    evaluate,
    generate_sample,
    load_profile,
)

__version__ = "0.5.1"
SPEC_VERSION = "0.5"

__all__ = [
    "DriftDetector",
    "HardRule",
    "Profile",
    "ScoredSignal",
    "StandingBand",
    "evaluate",
    "generate_sample",
    "load_profile",
    "SPEC_VERSION",
    "__version__",
]
