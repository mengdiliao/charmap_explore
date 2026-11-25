# Experiment 3 — published stage results

This directory is the completed full-data run with hash version **fnv1a-mix-v1**. It contains the original AI response and frozen AI/random designs, evaluated using the same hash mapping for Bloom and Joint CM. No new AI call was made for the unified run.

## Results

P=8000, 366 partitions, 512 bytes per partition, nominal BPK=0.512. Both workloads have 10M query occurrences. All 54 benchmark rows (27 algorithms × 2 workloads) have zero false negatives.

| Workload | Method/group | Mean pruning | Best pruning | Above Bloom |
| --- | --- | ---: | ---: | ---: |
| Uniform | Optimized Bloom | 14.1506% | — | — |
| Uniform | Reference Joint CM | 14.4001% | — | — |
| Uniform | AI (12) | 14.8116% | 18.3266% | 6/12 |
| Uniform | Random (12) | 14.9342% | 19.0296% | 9/12 |
| Zipfian | Optimized Bloom | 14.5181% | — | — |
| Zipfian | Reference Joint CM | 4.6455% | — | — |
| Zipfian | AI (12) | 6.0322% | 9.0480% | 0/12 |
| Zipfian | Random (12) | 11.3581% | 22.0971% | 2/12 |

Oracle: 99.7953% Uniform, 99.7420% Zipfian (exact membership, no comparable metadata budget). The serialized Bloom is 187,468 bytes; the AI/random maps range from 187,463 to 187,470 bytes, with the same bitmap payload.

| Candidate | Positions | Uniform pruning | Zipfian pruning |
| --- | --- | ---: | ---: |
| R1_02 (best Uniform) | [1,3,5,11] | 19.0296% | 12.9448% |
| R1_06 (best Zipfian) | [6,7,-10,-5] | 14.5168% | 22.0971% |
| R1_12 | [12,13,15,-5,-3] | 17.0291% | 18.8073% |
| A1_04 (best AI Uniform) | [0,1,-5,-1] | 18.3266% | 6.1549% |
| A1_03 (best AI Zipfian) | [0,4,-5,-1] | 16.3150% | 9.0480% |

R1_06 and R1_12 beat Bloom on both workloads. The maximum observed gain over Bloom is 4.8790 percentage points (Uniform) and 7.5790 percentage points (Zipfian). AI and random averages exceed Bloom slightly on Uniform; neither group's mean exceeds Bloom on Zipfian. The sampled AI designs do not outperform the random controls overall. These are descriptive, post-hoc results from one AI response and one random seed, with no held-out workload.

## File guide

| File | Contents |
| --- | --- |
| [report.md](report.md) | Generated group summary and baseline scores. |
| [proposal_results.csv](proposal_results.csv) | All 48 proposal/workload rows, positions, AI reasons where applicable, exact diagnostics and deltas vs Bloom/reference. |
| [benchmark/results.csv](benchmark/results.csv) | All 54 benchmark rows, including Bloom, reference and Oracle. |
| [designs.tsv](designs.tsv) | Evaluated design IDs and canonical positions. |
| [frozen.json](frozen.json) | Frozen experiment configuration, AI and random proposals, and unique design mapping. |
| [prompt.md](prompt.md), [examples.json](examples.json) | Original prompt and structural samples (historical mapping retained for provenance). |
| [response_1.json](response_1.json), [api_raw_1.json](api_raw_1.json) | Original AI output and API metadata (model and token usage). |
| [config.json](config.json), [runtime.json](runtime.json), [replay.json](replay.json) | Data hashes, settings, source/build hashes, runtime information and replay provenance. |
| benchmark/*.bin | Serialized physical metadata for each non-Oracle method. |
| legacy_results.csv, legacy_runtime.json, hash_comparison.csv | Original hashing ablation artifacts retained solely for traceability; not used in the main result comparison above. |

The numerical values above derive from the published CSVs. See [methodology](../../docs/experiment3-level1.md) for metric definitions and [reproduction instructions](../../docs/experiment3-level1.md#7-reproduce) to rerun in a separate directory without changing the published snapshot.
