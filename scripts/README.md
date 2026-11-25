# Experiment scripts

## Experiment 4 — offline profiling

[experiment4.py](experiment4.py) generates descriptive profiles, a matched control prompt and a profiled prompt for one selected full workload (uniform or zipf), with raw prefix/dot-count categories and no external classification file. [test_experiment4.py](test_experiment4.py) provides offline fixture tests. Run instructions: [Experiment 4](../docs/experiment4-simple-profiling.md). The prepare command is offline; generate calls the Anthropic API for the chosen arm. The evaluate command invokes the selected-workload Java evaluator, compares Oracle, optimized Bloom, historical best AI and all 12 profiled proposals, and writes CSV/JSON/Markdown results. Control and random generation are not required.

## Experiment 3

| File | Responsibility |
| --- | --- |
| [experiment3.py](experiment3.py) | Prepare the AI prompt, collect and validate a response, freeze designs, evaluate with Gradle, and report results. Also supports replay of an original legacy run with unified hashing. |
| [prepare_shalla.py](prepare_shalla.py) | Obtain the pinned Shalla data and reproduce both official-generator workloads. |
| [prepare_lits.py](prepare_lits.py) | Earlier dataset-preparation utility; not used for the reported run. |
| [verify_java_parity.py](verify_java_parity.py) | Earlier migration verification utility; retained for historical reproducibility. |

## Main commands

The [published run](../runs/experiment3_unified_hashing/README.md) already includes the AI response and frozen random controls. Follow the [Experiment 3 reproduction instructions](../docs/experiment3-level1.md#7-reproduce) to reproduce it with evaluate only.

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

## Results and figures

| File | Responsibility |
| --- | --- |
| [aggregate_results.py](aggregate_results.py) | Rebuild the 76-row comparison from published run artifacts. |
| [joint_cm_sensitivity.py](joint_cm_sensitivity.py) | Evaluate frozen matching-workload winners and merge the 276-row sensitivity table. |
| [position_budget_sensitivity.py](position_budget_sensitivity.py) | Original Experiment 3 sensitivity sweep; retained for reproducibility. |
| [plot_joint_cm_comparison.py](plot_joint_cm_comparison.py) | Plot four fixed-configuration comparison figures. |
| [plot_joint_cm_sensitivity.py](plot_joint_cm_sensitivity.py) | Plot four sensitivity figures. |
| [joint_cm_plotting.py](joint_cm_plotting.py) | Shared plotting conventions and PNG export. |

See the [results index](../results/README.md) and [figure instructions](../results/figures/README.md).
