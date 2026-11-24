# Experiment scripts

## Experiment 4 — offline profiling

[experiment4.py](experiment4.py) generates descriptive profiles, a matched control prompt and a profiled prompt for one selected full workload (uniform or zipf), with raw prefix/dot-count categories and no external classification file. [test_experiment4.py](test_experiment4.py) provides offline fixture tests. Run instructions: [Experiment 4](../docs/experiment4-simple-profiling.md). This script does not call AI or run Gradle; keep Experiment 3 commands separate.

## Experiment 3

| File | Responsibility |
| --- | --- |
| [experiment3.py](experiment3.py) | Prepare the AI prompt, collect and validate a response, freeze designs, evaluate with Gradle, and report results. Also supports replay of an original legacy run with unified hashing. |
| [prepare_shalla.py](prepare_shalla.py) | Obtain the pinned Shalla data and reproduce both official-generator workloads. |
| [prepare_lits.py](prepare_lits.py) | Earlier dataset-preparation utility; not used for the reported run. |
| [verify_java_parity.py](verify_java_parity.py) | Earlier migration verification utility; retained for historical reproducibility. |

## Main commands

The [published run](../runs/experiment3_unified_hashing/README.md) already includes the AI response and frozen random controls. Follow the [root instructions](../README.md#reproduce-the-published-result) to reproduce it with evaluate only.

For a genuinely new independent Level 1 run, choose a fresh directory and use the same --out value for all steps:

```bash
python3 scripts/experiment3.py prepare --out runs/experiment3_new
# Optional new paid AI call: configure ANTHROPIC_API_KEY locally first.
python3 scripts/experiment3.py generate --out runs/experiment3_new
python3 scripts/experiment3.py freeze --out runs/experiment3_new
python3 scripts/experiment3.py evaluate --out runs/experiment3_new
```

Alternatively, supply the unedited JSON in response_1.json before freeze. The generate command is the only AI API call. Keep credentials out of Git. The run is not a reproduction of the published AI sample if generate is executed again.

The replay command is designed to take an **original legacy-hashing** frozen run and evaluate it with unified hashing. It copies input/provenance files and, if an earlier benchmark CSV is present, produces a paired hash comparison. To reproduce the already unified published run, use evaluate on a fresh copy of the four frozen inputs instead (not replay against itself).
