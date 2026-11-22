# Experiment 3 follow-up — selected positions across partition sizes and budgets

## Purpose

Measure whether the *specific* position selections that ranked best in Experiment 3
continue to perform well when partition size and budget change. This is a **fixed-design
sensitivity test**, not new AI generation or a claim that AI is superior to random.

Base branch: `experiment/unified-hashing`. Same dataset, query workloads,
partition shuffle seed (55), full-key Bloom implementation, one-hash Joint CM
implementation, MISSING encoding and zero-false-negative check.

## Frozen candidates (selected from the published P=8000, B=512B run)

| Method | Group | Best on | Proposal | Positions | Original pruning |
|---|---|---|---|---|---|
| AI_Uniform | AI | Uniform | A1_04 | [0,1,-5,-1] | 18.3266% Uniform |
| AI_Zipf | AI | Zipf | A1_03 | [0,4,-5,-1] | 9.0480% Zipf |
| Random_Uniform | Random | Uniform | R1_02 | [1,3,5,11] | 19.0296% Uniform |
| Random_Zipf | Random | Zipf | R1_06 | [6,7,-10,-5] | 22.0971% Zipf |
| ReferenceJointCM | Reference | — | — | [0,1,-2,-1] | 14.4001% Uniform / 4.6455% Zipf |

Comparators: `OptimizedBloom` (full-key), exact `Oracle` (unbudgeted).
All four selected designs are evaluated against **both** Uniform and Zipf workloads
at each budget/partition setting. Positions are NOT reselected per configuration.

## Experiment matrix

Replicates the **same 23 configurations** in `results/shalla_partition_sensitivity.csv`:

| Partition size P | Budgets (bytes per partition) |
|---:|---|
| 500 | 32, 64, 128, 256 |
| 2,000 | 128, 256, 512, 1,024 |
| 8,000 | 256, 512, 1,024, 2,048, 4,096 |
| 32,000 | 256, 2,048, 4,096, 8,192, 16,384 |
| 128,000 | 256, 8,192, 16,384, 32,768, 65,536 |

Full Shalla: 2,926,705 unique stored keys; 10M queries for **each** official workload.
Two workloads × 23 configurations × (Oracle + Bloom + Reference + four selected maps)
= **322 result rows**, in a single CSV with the same core metric columns as
`results/shalla_partition_sensitivity.csv`, plus position diagnostics and provenance.

`nominal_bpk` means **bits per key**, not bytes per key: 8 * B / P.
For `P=128000, B=256`, nominal BPK is 0.016 bits/key.

## Running

The dedicated workflow `.github/workflows/position-budget-sensitivity.yml` runs
the full matrix in five parallel partition-size jobs, using the same pinned
GitHub Actions Shalla dataset/workload artifact as the earlier full-data verification.
An aggregation job validates all rows and reproduces the published
P=8000/B=512 values, uploads a combined artifact, and attempts to commit:

- `results/position_budget_sensitivity.csv` — all validated rows
- `results/position_budget_sensitivity.md` — compact win counts and anchor comparison

To run locally with prepared full Shalla files:

```bash
python3 scripts/position_budget_sensitivity.py validate
python3 scripts/position_budget_sensitivity.py run --partition-size 8000 --data data/shalla --out /tmp/sweep-p8000
# Repeat for P=500,2000,32000,128000, using different --out paths.
mkdir -p /tmp/sweep-all
cp /tmp/sweep-p*/p*.csv /tmp/sweep-all/
python3 scripts/position_budget_sensitivity.py merge --source-dir /tmp/sweep-all --output results/position_budget_sensitivity.csv
```

The suite enforces: unique matching rows, no false negatives, memory budget,
each position map's exact (collision-free) pruning ceiling, and exact reproduction
of the original Experiment 3 numbers at P=8000, B=512B.

**Interpretation:** The best candidates were selected *post hoc* on the same
Uniform/Zipf workloads and at P=8000. Different partition sizes/budgets provide
a useful robustness check, but this does not constitute independent validation
on a held-out workload. No inference about all possible joint character maps
should be drawn from these four selected combinations.
