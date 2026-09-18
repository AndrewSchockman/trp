"""Backward-compatible shim.

The evaluator moved to the installable `trp` package. This file keeps
`from tools.evaluate import ...` working for existing scripts and CI.
New code should import from `trp` directly.
"""

from trp.evaluate import *  # noqa: F401,F403
from trp.evaluate import DriftDetector, Profile, evaluate, generate_sample, load_profile  # noqa: F401

if __name__ == "__main__":
    from trp.cli import main
    main()
