# Experiment 3 follow-up — position selection vs. budget and partition size

> **Full analysis of 23 configurations × 2 workloads × 7 methods (322 verified result rows).** Unlike the original short report, this document covers the full constant-BPK matrix, the fixed-256B supplementary experiments, projection ceilings, saturation, and comparative interpretation.

## 1. Question, scope, and methodology

**Question:** Do position sets chosen at the original Experiment 3 setting (P=8,000, budget=512B) remain competitive when **partition size** and **bits per key (BPK)** change? Does changing positions improve on the fixed `(0,1,-2,-1)` reference, and when can it exceed a full-key Optimized Bloom filter?

Dataset: **2,926,705 Shalla stored strings**; official **Uniform and Zipf** workloads, **10 million query occurrences each**. Partition shuffle seed **55**; common **fnv1a-mix-v1** hash mapping. All compared implementations have **zero observed false negatives**. Results use **overall query–partition pruning (%)**, where larger is better. `BPK = 8 × budget_bytes / partition_size` means **bits**, not bytes, per key. **Oracle** is exact full-key membership, *not* an equal-budget filter.

### Frozen candidate positions

| Method | Origin / selected workload | Positions |
| --- | ---: | ---: |
| ReferenceJointCM | Fixed baseline | `(0,1,-2,-1)` |
| AI_Uniform | AI A1_04 / Uniform | `(0,1,-5,-1)` |
| AI_Zipf | AI A1_03 / Zipf | `(0,4,-5,-1)` |
| Random_Uniform | Random R1_02 / Uniform | `(1,3,5,11)` |
| Random_Zipf | Random R1_06 / Zipf | `(6,7,-10,-5)` |

All **four** selected position combinations are evaluated against **both** query workloads across every setting; they are never retuned or reselected during the sweep.

### Benchmark matrix

Five partition sizes (**500, 2,000, 8,000, 32,000, 128,000**) × four constant BPK levels (**0.512, 1.024, 2.048, 4.096**) plus three extra **256B-per-partition** settings at P=8,000/32,000/128,000 = **23 configurations per workload**. Each configuration includes Oracle, Bloom, Reference CM, and the four selected maps. Nominal bitmap budget is identical for competing methods, but their serialized metadata includes small schema/header differences.

## 2. Main findings

1. **Uniform, low memory:** at **0.512 BPK**, at least one Joint CM outperforms Bloom at **all five** P values. As soon as BPK reaches **1.024**, **Bloom wins against all five tested Joint CMs for all five P values**; this remains true for 2.048 and 4.096 BPK.
2. **Zipf, selected random tuple:** `Random_Zipf` beats Bloom at **3/5** partition sizes for **0.512 BPK**, **3/5** for **1.024 BPK**, **2/5** for **2.048 BPK**, and **0/5** for **4.096 BPK**. Thus, its advantage is **not limited to the lowest BPK**.
3. **Largest measured advantage:** Zipf, **P=32,000, B=2,048B (0.512 BPK)**: `Random_Zipf` **32.06%** vs Bloom **14.97%** (**+17.09 pp**). At Zipf **P=8,000/1.024 BPK**, it achieves **48.37%** vs Bloom **37.43%** (**+10.94 pp**).
4. **Ceilings depend on positions:** at Zipf P=8,000, Reference CM's collision-free ceiling is **8.24%**, while `Random_Zipf` reaches **89.35%**; a single reference tuple cannot define the maximum achievable performance for all Joint CM variants.
5. **No demonstrated AI advantage:** the strongest Zipf tuple was a Random control, and candidates were picked post hoc using the same two workloads. This shows a position-selection opportunity, **not** that AI selection is superior.

## 3. Wins versus Optimized Bloom

A win requires a strictly larger `pruning_pct` under the same P, B and workload. Each entry below counts **wins / ties / losses**; tied zero-pruning results appear at extremely low budgets.

| Method | Uniform (23 configs) | Zipf (23 configs) |
| --- | ---: | ---: |
| ReferenceJointCM | 6 / 0 / 17 | 3 / 0 / 20 |
| AI_Uniform | 6 / 1 / 16 | 2 / 1 / 20 |
| AI_Zipf | 6 / 1 / 16 | 2 / 1 / 20 |
| Random_Uniform | 7 / 1 / 15 | 2 / 1 / 20 |
| Random_Zipf | 7 / 1 / 15 | 10 / 1 / 12 |

### Wins at each fixed BPK (out of 5 partition sizes)

**Uniform**

| Method | 0.512 | 1.024 | 2.048 | 4.096 |
| --- | ---: | ---: | ---: | ---: |
| ReferenceJointCM | 3/5 | 0/5 | 0/5 | 0/5 |
| AI_Uniform | 4/5 | 0/5 | 0/5 | 0/5 |
| AI_Zipf | 4/5 | 0/5 | 0/5 | 0/5 |
| Random_Uniform | 5/5 | 0/5 | 0/5 | 0/5 |
| Random_Zipf | 5/5 | 0/5 | 0/5 | 0/5 |

**Zipf**

| Method | 0.512 | 1.024 | 2.048 | 4.096 |
| --- | ---: | ---: | ---: | ---: |
| ReferenceJointCM | 0/5 | 0/5 | 0/5 | 0/5 |
| AI_Uniform | 0/5 | 0/5 | 0/5 | 0/5 |
| AI_Zipf | 0/5 | 0/5 | 0/5 | 0/5 |
| Random_Uniform | 0/5 | 0/5 | 0/5 | 0/5 |
| Random_Zipf | 3/5 | 3/5 | 2/5 | 0/5 |

The 23-configuration totals include the three **fixed-256B** supplemental configurations, which are **not** included in the fixed-BPK win tables.

## 4. Complete fixed-BPK results — Uniform

All reported values are **overall pruning rate (%)**. `AI-U/Z` and `Random-U/Z` refer to the tuple chosen as best on the indicated original workload.

| P | Budget B | BPK | Bloom | Reference | AI-U | AI-Z | Random-U | Random-Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 32 | 0.512 | 14.08 | 17.82 | 17.23 | 14.53 | 15.38 | 14.22 |
| 500 | 64 | 1.024 | 37.58 | 30.00 | 35.06 | 36.28 | 35.52 | 37.45 |
| 500 | 128 | 2.048 | 61.33 | 39.17 | 50.06 | 57.10 | 54.00 | 60.75 |
| 500 | 256 | 4.096 | 85.98 | 45.21 | 59.98 | 71.66 | 66.43 | 77.47 |
| 2000 | 128 | 0.512 | 14.18 | 16.59 | 18.32 | 15.50 | 17.28 | 14.27 |
| 2000 | 256 | 1.024 | 37.66 | 25.23 | 33.32 | 34.73 | 35.08 | 36.91 |
| 2000 | 512 | 2.048 | 61.34 | 30.44 | 45.11 | 51.99 | 49.99 | 59.15 |
| 2000 | 1024 | 4.096 | 85.96 | 33.46 | 52.40 | 63.56 | 59.63 | 75.01 |
| 8000 | 512 | 0.512 | 14.15 | 14.40 | 18.33 | 16.31 | 19.03 | 14.52 |
| 8000 | 1024 | 1.024 | 37.62 | 18.90 | 29.51 | 31.55 | 34.47 | 35.02 |
| 8000 | 2048 | 2.048 | 61.25 | 21.66 | 37.30 | 43.86 | 46.36 | 54.57 |
| 8000 | 4096 | 4.096 | 85.84 | 23.27 | 41.83 | 51.59 | 53.77 | 67.99 |
| 32000 | 2048 | 0.512 | 14.36 | 9.85 | 16.94 | 16.19 | 19.53 | 15.28 |
| 32000 | 4096 | 1.024 | 37.64 | 11.65 | 23.41 | 25.99 | 31.48 | 31.42 |
| 32000 | 8192 | 2.048 | 61.07 | 12.64 | 27.60 | 32.98 | 40.00 | 44.99 |
| 32000 | 16384 | 4.096 | 85.42 | 13.22 | 29.96 | 37.20 | 45.07 | 53.93 |
| 128000 | 8192 | 0.512 | 13.91 | 6.24 | 13.49 | 13.27 | 17.76 | 14.52 |
| 128000 | 16384 | 1.024 | 36.67 | 6.80 | 16.73 | 18.08 | 25.17 | 24.20 |
| 128000 | 32768 | 2.048 | 59.54 | 7.10 | 18.63 | 21.04 | 29.94 | 31.24 |
| 128000 | 65536 | 4.096 | 83.36 | 7.23 | 19.66 | 22.74 | 32.69 | 35.54 |

**Interpretation:** At 0.512 BPK the best map changes with P: Reference at P=500, AI-U at P=2,000, and Random-U at P≥8,000. At **1.024 BPK** and above **no tested Joint CM wins against Bloom** on Uniform. For example, P=128,000 / 4.096 BPK gives **83.36% Bloom vs 35.54% best Joint CM** (Random-Z).

## 5. Complete fixed-BPK results — Zipf

| P | Budget B | BPK | Bloom | Reference | AI-U | AI-Z | Random-U | Random-Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 32 | 0.512 | 14.21 | 7.23 | 9.06 | 12.04 | 12.30 | 13.59 |
| 500 | 64 | 1.024 | 37.22 | 15.43 | 19.96 | 31.31 | 23.57 | 34.22 |
| 500 | 128 | 2.048 | 60.85 | 20.73 | 27.17 | 50.87 | 33.17 | 57.65 |
| 500 | 256 | 4.096 | 85.93 | 22.95 | 30.97 | 62.18 | 50.27 | 74.85 |
| 2000 | 128 | 0.512 | 13.75 | 8.21 | 9.57 | 9.28 | 5.03 | 11.96 |
| 2000 | 256 | 1.024 | 37.66 | 11.57 | 15.09 | 20.82 | 20.15 | 32.75 |
| 2000 | 512 | 2.048 | 61.65 | 14.66 | 19.91 | 37.04 | 28.84 | 65.79 |
| 2000 | 1024 | 4.096 | 85.76 | 16.07 | 24.68 | 42.29 | 32.82 | 81.31 |
| 8000 | 512 | 0.512 | 14.52 | 4.65 | 6.15 | 9.05 | 12.94 | 22.10 |
| 8000 | 1024 | 1.024 | 37.43 | 5.82 | 12.30 | 15.56 | 20.62 | 48.37 |
| 8000 | 2048 | 2.048 | 62.02 | 6.24 | 14.91 | 19.78 | 24.91 | 67.88 |
| 8000 | 4096 | 4.096 | 83.47 | 7.16 | 16.66 | 22.48 | 28.25 | 78.68 |
| 32000 | 2048 | 0.512 | 14.97 | 2.41 | 6.81 | 7.49 | 10.41 | 32.06 |
| 32000 | 4096 | 1.024 | 38.16 | 3.12 | 9.61 | 10.55 | 15.87 | 50.93 |
| 32000 | 8192 | 2.048 | 62.63 | 4.08 | 10.87 | 12.11 | 20.93 | 59.64 |
| 32000 | 16384 | 4.096 | 83.12 | 4.12 | 11.67 | 12.93 | 23.07 | 72.31 |
| 128000 | 8192 | 0.512 | 18.00 | 2.08 | 4.68 | 4.65 | 9.25 | 26.37 |
| 128000 | 16384 | 1.024 | 38.00 | 2.13 | 5.75 | 5.92 | 11.16 | 46.83 |
| 128000 | 32768 | 2.048 | 56.70 | 2.66 | 6.91 | 6.49 | 12.02 | 52.23 |
| 128000 | 65536 | 4.096 | 84.83 | 2.69 | 7.26 | 6.99 | 12.40 | 56.58 |

**Interpretation:** `Random_Zipf` beats Bloom at P=8,000 and 32,000 for **1.024 BPK**, and at P=2,000 and 8,000 for **2.048 BPK**. It also beats Bloom at P=128,000 / 1.024 BPK. The advantage disappears everywhere by **4.096 BPK**, where Bloom can make more effective use of additional bits.

## 6. Supplemental fixed-256B cases

These are **not** 0.512-BPK cases. Nominal BPK is 0.256 at P=8,000, 0.064 at P=32,000, and 0.016 at P=128,000.

| Workload | P | Budget B | BPK | Bloom | Reference | AI-U | AI-Z | Random-U | Random-Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform | 8000 | 256 | 0.256 | 2.0131 | 8.3819 | 7.0837 | 4.3886 | 5.7787 | 2.5114 |
| uniform | 32000 | 256 | 0.064 | 0.0000 | 0.9317 | 0.1721 | 0.0261 | 0.0299 | 0.0022 |
| uniform | 128000 | 256 | 0.016 | 0.0000 | 0.0274 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| zipf | 8000 | 256 | 0.256 | 1.7363 | 2.0633 | 2.4427 | 2.3285 | 4.8409 | 2.1410 |
| zipf | 32000 | 256 | 0.064 | 0.0000 | 0.1487 | 0.0570 | 0.0547 | 0.0117 | 0.0154 |
| zipf | 128000 | 256 | 0.016 | 0.0000 | 0.0025 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

At these extreme settings, Bloom sometimes has approximately **0%** overall pruning; a CM can technically win while still pruning very little in absolute terms. Do not equate a positive *percentage-point difference* here with useful end-to-end performance.

## 7. Representation ceiling: why position selection matters

`exact_joint_pruning_pct` is a **collision-free projected-tuple pruning ceiling** for a *particular* position set; it is **not** the complete-key Oracle and it is **not** constrained by the deployed bitmap budget. At a fixed P and workload, changing bitmap bytes reduces hash collisions but **cannot increase the exact tuple ceiling**.

### Uniform — collision-free pruning ceiling (%)

| P | ReferenceJointCM | AI_Uniform | AI_Zipf | Random_Uniform | Random_Zipf |
| --- | ---: | ---: | ---: | ---: | ---: |
| 500 | 51.65 | 71.63 | 89.90 | 82.03 | 98.62 |
| 2000 | 37.00 | 60.68 | 77.77 | 71.18 | 94.98 |
| 8000 | 25.01 | 46.97 | 60.80 | 62.32 | 84.55 |
| 32000 | 13.80 | 32.56 | 41.87 | 50.85 | 64.64 |
| 128000 | 7.42 | 20.76 | 24.53 | 35.71 | 40.38 |

### Zipf — collision-free pruning ceiling (%)

| P | ReferenceJointCM | AI_Uniform | AI_Zipf | Random_Uniform | Random_Zipf |
| --- | ---: | ---: | ---: | ---: | ---: |
| 500 | 28.17 | 36.54 | 78.45 | 63.49 | 99.00 |
| 2000 | 17.57 | 27.86 | 48.83 | 38.42 | 96.34 |
| 8000 | 8.24 | 18.14 | 25.72 | 31.98 | 89.35 |
| 32000 | 4.71 | 13.02 | 15.27 | 24.35 | 78.21 |
| 128000 | 2.70 | 7.60 | 9.34 | 13.35 | 59.69 |

Across growing P, the reference's Zipf ceiling falls from **28.17%** (P=500) to **2.70%** (P=128,000). The Random-Zipf tuple's ceiling also declines with P, but stays much higher (**99.00% → 59.69%**). This shows why the reference's ceiling must not be presented as a universal Joint CM ceiling.

## 8. Bitmap saturation and the budget–partition interaction

Mean bitmap saturation is a *construction/data statistic* and therefore is identical for Uniform and Zipf at the same P, budget and method; query-weighted pruning is not identical. The table shows `mean_saturation_pct` at **0.512 BPK**.

| P | Bloom | Reference | AI-U | AI-Z | Random-U | Random-Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 85.92 | 65.97 | 75.79 | 84.00 | 81.29 | 85.61 |
| 2000 | 85.82 | 54.55 | 69.57 | 80.06 | 75.88 | 84.99 |
| 8000 | 85.82 | 42.36 | 60.95 | 73.26 | 69.67 | 82.84 |
| 32000 | 85.52 | 28.32 | 48.52 | 61.58 | 61.77 | 76.73 |
| 128000 | 85.62 | 15.73 | 34.91 | 45.92 | 50.31 | 64.20 |

For `Random_Zipf`, saturation falls from **85.61%** at P=500 to **76.73%** at P=32,000 (0.512 BPK), while its **Zipf representation ceiling decreases** from about **99.00% to 78.21%**. Its *observed* Zipf pruning nevertheless grows from **13.59% to 32.06%**. This illustrates competing effects: projected-token reuse can lower bitmap occupancy, even as more partitions contain the same frequently queried projected tuples.

A high ceiling alone does not ensure high pruning: e.g., `Random_Zipf` has an approximately **99%** Zipf ceiling at P=500, yet achieves only **13.59%** at 0.512 BPK owing to collisions/saturation. Likewise, low bitmap saturation does not rescue a low-ceiling representation.

## 9. Key budget crossovers

The following examples isolate the regions where the best selected tuple beats Bloom as BPK increases (Δ is candidate minus Bloom in **percentage points**).

| Workload | P | BPK | Bloom % | Candidate | Candidate % | Δ pp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform | 8000 | 0.512 | 14.15 | Random_Uniform | 19.03 | +4.88 |
| uniform | 8000 | 1.024 | 37.62 | Random_Uniform | 34.47 | -3.15 |
| uniform | 32000 | 0.512 | 14.36 | Random_Uniform | 19.53 | +5.17 |
| uniform | 128000 | 1.024 | 36.67 | Random_Uniform | 25.17 | -11.50 |
| zipf | 2000 | 2.048 | 61.65 | Random_Zipf | 65.79 | +4.14 |
| zipf | 8000 | 0.512 | 14.52 | Random_Zipf | 22.10 | +7.58 |
| zipf | 8000 | 1.024 | 37.43 | Random_Zipf | 48.37 | +10.94 |
| zipf | 8000 | 2.048 | 62.02 | Random_Zipf | 67.88 | +5.86 |
| zipf | 8000 | 4.096 | 83.47 | Random_Zipf | 78.68 | -4.79 |
| zipf | 32000 | 0.512 | 14.97 | Random_Zipf | 32.06 | +17.09 |
| zipf | 32000 | 1.024 | 38.16 | Random_Zipf | 50.93 | +12.78 |
| zipf | 128000 | 1.024 | 38.00 | Random_Zipf | 46.83 | +8.83 |

**Interpretation:** Under intermediate budgets, the best Zipf-selected tuple can outperform full-key Bloom. At high BPK, Bloom rapidly reduces its full-key hash false positives; the projected tuple is still bounded by its position-specific collision-free ceiling. This explains the **crossover by 4.096 BPK** without implying that *every* conceivable character-based statistic has the same limitation.

## 10. Validity and limitations

- **Post-hoc selection and no held-out validation.** Candidates were chosen from the same Uniform/Zipf benchmark at P=8,000/B=512B; this sensitivity sweep does not prove they generalize to unseen queries or data.
- **One AI response, one Random seed, one dataset, one partition shuffle seed.** Do not infer statistical dominance of Random search or the global optimality of `[6,7,-10,-5]` from four finalists.
- **Only single projected-tuple bitmap maps were compared.** No general comparison of all Character Maps, adaptive per-partition designs, combined maps, or hybrids is warranted.
- **Zero observed false negatives** were verified; this is not a proof of correctness for arbitrary future changes.
- **Full-key Bloom has an optimized number of hashes**, whereas each deployed Joint CM uses one hash. The metadata payload budget is equal, but physical serialized size includes small header/schema differences.
- **The pruning rate is query–partition pair based**, not database execution time. Full-key Oracle and collision-free tuple ceilings are analytical diagnostics and are not memory-matched baselines.
- **Useful next step:** Analyze the position features that let Random-Zipf achieve high Zipf ceiling with manageable saturation; evaluate a simple profiled-selection heuristic and AI against independent query/workload samples to determine whether AI adds measurable value.

## 11. Data, methods and reproduction

- Full 322-row dataset: [`position_budget_sensitivity.csv`](position_budget_sensitivity.csv).
- Frozen winner definitions: [`selected.tsv`](../experiments/position_budget_sensitivity/selected.tsv).
- Experiment specification: [`experiments/position_budget_sensitivity/README.md`](../experiments/position_budget_sensitivity/README.md).
- Evaluator / merge validation: [`scripts/position_budget_sensitivity.py`](../scripts/position_budget_sensitivity.py).
- Original Experiment 3 selection source: [`runs/experiment3_unified_hashing/proposal_results.csv`](../runs/experiment3_unified_hashing/proposal_results.csv).

**Conclusion:** The original reference's Partition Size limitations are real but **representation-specific**. Position selection can meaningfully improve pruning in selected workload/BPK regimes, particularly Zipf, while Bloom dominates at higher memory budgets. This demonstrates a position-selection problem worth studying, **not an established advantage for AI**.
