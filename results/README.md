# Experiment results

## Main results

| Results | Documentation | Scope |
| --- | --- | --- |
| [joint_cm_comparison.csv](joint_cm_comparison.csv) | [Comparison and data dictionary](joint_cm_comparison.md) | All Random and AI proposals, with Oracle and OptimizedBloom; fixed P=8000, budget=512B; 76 rows. |
| [joint_cm_sensitivity.csv](joint_cm_sensitivity.csv) | [Sensitivity analysis](joint_cm_sensitivity.md) | Frozen best solutions for each workload, plus three baselines; 23 configurations, 276 rows; no cross-workload evaluation. |

Both CSVs share the same 47-column schema, documented in [the data dictionary](joint_cm_comparison.md#data-dictionary). The comparison table covers all candidates at the original setting, whereas the sensitivity table varies partition size and budget for the selected winners.

## Figures

[Figure index and reproduction commands](figures/README.md): eight publication-ready figures, available as 300-dpi PNG files.

## Supporting results

| Directory | Contents |
| --- | --- |
| [non_character/](non_character/) | [Original position-budget sensitivity CSV](non_character/position_budget_sensitivity.csv) and [analysis](non_character/position_budget_sensitivity.md). |
| [referenced_JCM/](referenced_JCM/) | [Shalla pilot](referenced_JCM/shalla_pilot.csv) and [partition sensitivity](referenced_JCM/shalla_partition_sensitivity.csv). |
| [joint_profile/](joint_profile/) | Joint projection profiles, bitmap diagnostics, partition-level statistics and top tokens. |

## Reproducibility

- Fixed-configuration comparison: `python3 scripts/aggregate_results.py --check`
- Sensitivity results: `python3 scripts/joint_cm_sensitivity.py check`
- Full sensitivity experiment instructions: [experiments/joint_cm_sensitivity/README.md](../experiments/joint_cm_sensitivity/README.md).

Run commands from the repository root. The published CSVs can be verified without new AI calls or benchmark execution.
