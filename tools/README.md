# Reference Evaluator

A minimal reference implementation that loads a TRP profile and evaluates a data sample against it. Demonstrates that TRP profiles are machine-actionable: any conforming evaluator reading the same profile and evidence reaches the same result.

This is a reference tool for testing and development, not a production evaluation source.

## What It Does

1. **Loads a TRP profile** from JSON and validates its structure.
2. **Checks hard rules** first. If any hard rule triggers (e.g., emergency stop active, safety certification expired), the system is placed in the worst standing band regardless of scores.
3. **Evaluates scored signals** against their warning and critical thresholds, computing severity and weighted penalty for each.
4. **Assigns a standing band** from the profile's declared bands based on the evaluation.
5. **Tracks drift** when configured, maintaining a moving average over the profile's declared window.
6. **Outputs a JSON result** with the standing, response, all signal evidence, triggered rules, and drift state.

## Quick Start

No dependencies beyond Python 3.10+ and `jsonschema` (for optional schema validation).

```bash
# Generate a sample with safe default values for a profile
python3 evaluate.py ../../examples/manufacturing-safety/trp.json --generate-sample > sample.json

# Evaluate the sample against the profile
python3 evaluate.py ../../examples/manufacturing-safety/trp.json sample.json
```

## Example Output

```json
{
  "trp_id": "manufacturing-safety",
  "trp_version": "1.0.0",
  "hard_rules_triggered": [],
  "trust_score": 100.0,
  "signal_results": [
    {
      "signal": "human_distance_m",
      "value": 1.8,
      "unit": "m",
      "severity": 0.0,
      "penalty": 0.0,
      "in_warning": false,
      "in_critical": false
    }
  ],
  "missing_signals": [],
  "standing": "good",
  "hard_override": false,
  "response": "full"
}
```

## How It Maps to the Specification

| Spec Concept | Evaluator Behavior |
|---|---|
| Scored signals with direction and thresholds | Severity computed per signal using the spec's directional threshold model |
| Hard rules with conditions and actions | Checked before scoring; any trigger overrides the standing |
| On-missing policy | Missing signals handled per their declared policy (critical, incomplete, or ignore) |
| Standing bands with severity order | Bands sorted by severity; assignment based on worst active condition |
| Required standing and response bands | Response action mapped from the assigned band |
| Drift over a window | Moving average tracked per signal across consecutive evaluations |

## Limitations

This evaluator is intentionally simple. It demonstrates that the TRP format is machine-actionable, not that this particular implementation is optimal. Production evaluation sources may use different scoring algorithms, richer drift models, or additional verification logic. The specification permits all of these because it defines the profile format, not the evaluation method.
