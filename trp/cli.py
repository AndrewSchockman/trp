"""Command line interface for the Trust Requirements Profile.

Designed so that a new user goes from install to a working evaluation in one
command:

    pip install trp
    trp demo
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from . import SPEC_VERSION, __version__
from .evaluate import DriftDetector, evaluate, generate_sample, load_profile

# --- output helpers ---------------------------------------------------------

OK = "\033[32m"
WARN = "\033[33m"
ERR = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
END = "\033[0m"


def _color(enabled: bool):
    if enabled and sys.stdout.isatty():
        return OK, WARN, ERR, DIM, BOLD, END
    return "", "", "", "", "", ""


def _bundled(name: str) -> Path:
    """Return a path to a file bundled inside the installed package."""
    return Path(str(resources.files("trp").joinpath(name)))


def _load_json(path: Path) -> Any:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {path}: {e}", file=sys.stderr)
        raise SystemExit(2)


def _strip_meta(data: dict) -> dict:
    """Drop underscore-prefixed test annotations from evidence files."""
    return {k: v for k, v in data.items() if not k.startswith("_")}


# --- commands ---------------------------------------------------------------

def cmd_demo(args: argparse.Namespace) -> int:
    """Run a complete evaluation using a bundled profile. No arguments needed."""
    g, w, e, d, b, x = _color(not args.no_color)

    profile_path = _bundled("profiles/manufacturing-safety.json")
    profile = load_profile(profile_path)

    print(f"\n{b}Trust Requirements Profile{x} {d}spec {SPEC_VERSION} / package {__version__}{x}\n")
    print(f"{d}Profile:{x} manufacturing safety (bundled example)")
    print(f"{d}Source: {profile_path}{x}\n")

    healthy = generate_sample(profile)
    scenarios = [("Healthy system", healthy)]

    # Push one signal past its critical threshold, in the direction that is unsafe
    # for that signal. Falls back to a large multiplier if no threshold is set.
    degraded = dict(healthy)
    for sig in profile.scored_signals:
        if sig.signal not in degraded:
            continue
        value = degraded[sig.signal]
        if not isinstance(value, (int, float)):
            continue
        threshold = sig.critical_threshold if sig.critical_threshold is not None else None
        if sig.direction == "higher_is_unsafe":
            degraded[sig.signal] = (threshold * 1.5) if threshold else value * 10
        elif sig.direction == "lower_is_unsafe":
            degraded[sig.signal] = (threshold * 0.5) if threshold else value / 10
        else:
            continue
        degraded["_degraded_signal"] = sig.signal
        break
    degraded_signal = degraded.pop("_degraded_signal", "a signal")
    scenarios.append((f"Degraded: {degraded_signal}", degraded))

    # Drop everything but the first signal, to show missing-evidence handling
    first = next(iter(healthy), None)
    partial = {first: healthy[first]} if first else {}
    scenarios.append(("Missing evidence", partial))

    for label, evidence in scenarios:
        drift = None
        if profile.drift_window > 0:
            drift = DriftDetector(profile.drift_window, profile.drift_signals)
        result = evaluate(profile, evidence, drift)
        standing = result.get("standing", "unknown")
        color = g if standing in ("full", "satisfied") else (w if standing else e)
        print(f"  {label:28} {color}{standing:12}{x}{d}{result.get('response', '')}{x}")

    print(f"\n{d}Full result for the healthy case:{x}\n")
    drift = DriftDetector(profile.drift_window, profile.drift_signals) if profile.drift_window > 0 else None
    print(json.dumps(evaluate(profile, scenarios[0][1], drift), indent=2))

    print(f"\n{b}Next steps{x}")
    print("  trp init manufacturing > my-profile.json   scaffold your own profile")
    print("  trp validate my-profile.json               check it against the schema")
    print("  trp sample my-profile.json > evidence.json generate sample evidence")
    print("  trp evaluate my-profile.json evidence.json evaluate it\n")
    print(f"{d}Specification: https://doi.org/10.5281/zenodo.22099403{x}\n")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Print a starter profile to stdout."""
    available = {
        "manufacturing": "profiles/manufacturing-safety.json",
        "healthcare": "profiles/healthcare-data-governance.json",
    }
    if args.template not in available:
        print(
            f"Unknown template '{args.template}'. Available: {', '.join(sorted(available))}",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(_load_json(_bundled(available[args.template])), indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a profile against the TRP JSON Schema."""
    g, w, e, d, b, x = _color(not args.no_color)
    try:
        import jsonschema
    except ImportError:
        print("jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
        return 2

    schema = _load_json(_bundled("schema/trp.schema.json"))
    instance = _load_json(args.profile)

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda x: list(x.path))

    if not errors:
        print(f"{g}VALID{x}  {args.profile}")
        print(f"{d}  spec_version: {instance.get('spec_version', 'unset')}{x}")
        signals = instance.get("scored_signals", [])
        rules = instance.get("hard_rules", [])
        print(f"{d}  {len(signals)} scored signal(s), {len(rules)} hard rule(s){x}")
        return 0

    print(f"{e}INVALID{x}  {args.profile}   {len(errors)} error(s)\n")
    for err in errors:
        loc = ".".join(str(p) for p in err.path) or "(root)"
        print(f"  {e}{loc}{x}")
        print(f"    {err.message}")
    return 1


def cmd_sample(args: argparse.Namespace) -> int:
    """Generate sample evidence for a profile."""
    print(json.dumps(generate_sample(load_profile(args.profile)), indent=2))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate evidence against a profile."""
    profile = load_profile(args.profile)
    evidence = _strip_meta(_load_json(args.evidence))
    drift = None
    if profile.drift_window > 0:
        drift = DriftDetector(profile.drift_window, profile.drift_signals)
    result = evaluate(profile, evidence, drift)
    print(json.dumps(result, indent=2))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(f"trp {__version__}")
    print(f"specification {SPEC_VERSION}")
    print("https://doi.org/10.5281/zenodo.22099403")
    return 0


# --- entry point ------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trp",
        description="Trust Requirements Profile: state and verify the trust "
                    "requirements of AI and autonomous systems.",
        epilog="Start with: trp demo",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colored output.")
    sub = p.add_subparsers(dest="command")

    d = sub.add_parser("demo", help="Run a complete example. No arguments needed.")
    d.set_defaults(func=cmd_demo)

    i = sub.add_parser("init", help="Print a starter profile to stdout.")
    i.add_argument("template", nargs="?", default="manufacturing",
                   help="manufacturing or healthcare (default: manufacturing)")
    i.set_defaults(func=cmd_init)

    v = sub.add_parser("validate", help="Validate a profile against the schema.")
    v.add_argument("profile", type=Path)
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("sample", help="Generate sample evidence for a profile.")
    s.add_argument("profile", type=Path)
    s.set_defaults(func=cmd_sample)

    e = sub.add_parser("evaluate", help="Evaluate evidence against a profile.")
    e.add_argument("profile", type=Path)
    e.add_argument("evidence", type=Path)
    e.set_defaults(func=cmd_evaluate)

    ver = sub.add_parser("version", help="Print version information.")
    ver.set_defaults(func=cmd_version)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        print("\nStart with: trp demo\n")
        raise SystemExit(0)
    try:
        raise SystemExit(args.func(args))
    except BrokenPipeError:
        # Output was piped into something that closed early, such as head.
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
