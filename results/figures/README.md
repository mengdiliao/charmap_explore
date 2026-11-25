# Joint CM thesis figures

Generated from the two published CSVs, not from manually entered values. All files are available as SVG (editable vector), PDF (LaTeX), and PNG (300 dpi). No AI API calls, original datasets, or Java benchmarks are needed.

## Reproduce

From the repository root (Python 3.10–3.13 recommended):

```bash
python3 -m pip install -r requirements-plotting.txt
python3 scripts/plot_joint_cm_comparison.py
python3 scripts/plot_joint_cm_sensitivity.py
```

Both scripts support `--input PATH`, `--out PATH`, and `--formats svg pdf png` (all three by default).

## Comparison (all 12 candidates per group)

| Figure | SVG | PDF | PNG |
| --- | --- | --- | --- |
| A1 — Pruning distribution | [SVG](comparison/pruning_distribution.svg) | [PDF](comparison/pruning_distribution.pdf) | [PNG](comparison/pruning_distribution.png) |
| A2 — Positive vs. negative pruning | [SVG](comparison/positive_negative_pruning.svg) | [PDF](comparison/positive_negative_pruning.pdf) | [PNG](comparison/positive_negative_pruning.png) |
| A3 — Discrimination vs. saturation | [SVG](comparison/discrimination_saturation.svg) | [PDF](comparison/discrimination_saturation.pdf) | [PNG](comparison/discrimination_saturation.png) |
| A4 — Position frequency | [SVG](comparison/position_frequency.svg) | [PDF](comparison/position_frequency.pdf) | [PNG](comparison/position_frequency.png) |

A1 shows descriptive candidate distributions, not confidence intervals or independent AI runs. Oracle is omitted from the main axes to preserve readable differences among budget-limited methods; the original CSV retains Oracle. A4 counts shared Random and unprofiled AI designs once, not twice.

## Sensitivity (fixed winners)

| Figure | SVG | PDF | PNG |
| --- | --- | --- | --- |
| B1 — Pruning vs. BPK | [SVG](sensitivity/pruning_vs_bpk.svg) | [PDF](sensitivity/pruning_vs_bpk.pdf) | [PNG](sensitivity/pruning_vs_bpk.png) |
| B2 — Pruning vs. partition size | [SVG](sensitivity/pruning_vs_partition_size.svg) | [PDF](sensitivity/pruning_vs_partition_size.pdf) | [PNG](sensitivity/pruning_vs_partition_size.png) |
| B3 — Performance delta | [SVG](sensitivity/performance_delta.svg) | [PDF](sensitivity/performance_delta.pdf) | [PNG](sensitivity/performance_delta.png) |
| B4 — Exact pruning ceiling | [SVG](sensitivity/exact_pruning_ceiling.svg) | [PDF](sensitivity/exact_pruning_ceiling.pdf) | [PNG](sensitivity/exact_pruning_ceiling.png) |

B1–B3 use the 20 constant-BPK settings for each workload; the three supplemental fixed-256B cases remain in the CSV. B4 includes the extra 0.256-BPK point at P=8000. Configured BPK = 8 × budget_bytes / partition_size (not actual serialized bpk). All plotted winners were frozen at P=8000, B=512B and evaluated only on their matching workload. The exact ceiling belongs to a particular projection and partition layout, not Joint CM in general.
