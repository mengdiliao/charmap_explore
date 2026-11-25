# Experiment results

## Master Joint CM comparison

[joint_cm_comparison.csv](joint_cm_comparison.csv) is the consolidated analysis table. One row represents one solution evaluated on one workload, not one AI generation. It contains 76 rows (38 per workload) at the fixed Shalla configuration: partition size 8,000, payload budget 512 bytes, seed 55, unified FNV-1a/mix hashing.

| Method | Uniform | Zipf | Definition |
| --- | ---: | ---: | --- |
| Oracle | 1 | 1 | Exact partition membership upper bound on pruning |
| OptimizedBloom | 1 | 1 | Full-key Bloom filter with optimized hash count |
| Random | 12 | 12 | Original randomly selected position combinations |
| AI_NoCharacteristics | 12 | 12 | AI given task description and representative samples, without the additional statistical profile |
| AI_HumanCharacteristics | 12 | 12 | AI given task description, representative samples and human-selected dataset/workload characteristics |

The original Random and AI_NoCharacteristics solutions were evaluated on both workloads. AI_HumanCharacteristics solutions were generated and evaluated separately for Uniform and Zipf. These groups therefore differ in both profiling input and optimization scope; the comparison alone does not isolate the causal contribution of the added profile. All evaluations are in-sample.

## Reproduce

From the repository root:

```bash
python3 scripts/aggregate_results.py
python3 scripts/aggregate_results.py --check
```

The first command regenerates the master CSV deterministically from published run artifacts; the second verifies exact byte-for-byte equality. Neither calls an AI API nor runs a benchmark. The script validates group counts, solution identity, experimental configuration, dataset/query hashes in the recorded configs, duplicate baseline results, frozen profiled proposals, and zero false negatives. Original result files are not modified.

Sources:

- [Original benchmark](../runs/experiment3_unified_hashing/results.csv): Oracle and OptimizedBloom; ReferenceJointCM is used only to calculate a reference delta.
- [Original proposals](../runs/experiment3_unified_hashing/proposal_results.csv): all original AI and Random results.
- [Uniform profiled results](../runs/experiment4_uniform/evaluation/profiled/call_1/results.csv): all twelve profiled AI results.
- [Zipf profiled results](../runs/experiment4_zipf/evaluation/profiled/call_1/results.csv): all twelve profiled AI results.
- Corresponding configuration, runtime and generation metadata supply provenance.

Repeated baselines and historical-best replay rows are omitted. The original historical AI rows are authoritative, including metadata sizes (renaming a statistic during replay changes its serialized description length). Identical positions from different generations are retained as distinct proposals. No ReferenceJointCM row, sensitivity sweeps, or optional AI control runs are included.

## Data dictionary

### Solution identification

| Column | Meaning |
| --- | --- |
| method | Method group listed above |
| solution_id | Stable solution identifier; combine with workload for a unique evaluation row |
| workload | Actual evaluated query distribution: uniform or zipf |
| positions | Ordered, semicolon-delimited character indices; negative indices count from the end |
| position_count | Number of selected positions, derived from positions |
| reason | Original AI explanation, preserved verbatim; blank for non-AI methods |

### Pruning and diagnostics

| Column | Meaning |
| --- | --- |
| pruning_pct | Percentage of all query-partition pairs pruned |
| positive_pruning_pct | Percentage of query-partition pairs pruned for globally positive queries; derived from recorded rates and query counts |
| negative_pruning_pct | Percentage of query-partition pairs pruned for globally negative queries |
| exact_joint_pruning_pct | Pruning using exact projected tuples, without hashing collisions |
| oracle_capture_pct | Percentage of the Oracle's prunable pairs captured |
| partition_fpr_pct | False positive pairs as a percentage of pairs that should be prunable |
| false_negatives | Count of incorrectly pruned true membership pairs; must be zero |
| retained_rows_pct | Percentage of data rows retained across queries, weighted by actual partition sizes |
| delta_bloom_pp | Pruning rate minus OptimizedBloom rate, in percentage points |
| delta_reference_pp | Pruning rate minus the original ReferenceJointCM rate, in percentage points |
| delta_ai_no_characteristics_best_pp | Pruning rate minus the best AI_NoCharacteristics rate for the same workload, in percentage points |
| mean_token_ndv | Mean number of distinct tokens per partition |
| mean_saturation_pct | Mean percentage of occupied bitmap bits per partition |
| collision_excess_pct | Percentage of distinct-token counts lost to occupied-bit collisions |
| bloom_k | Number of Bloom hash functions; blank if not applicable |
| metadata_total_bytes | Actual serialized metadata size in bytes, including serialization overhead |
| payload_used_bytes | Bitmap payload bytes per partition |
| bpk | Actual bits per stored key (8 × metadata_total_bytes / dataset_rows) |
| query_partition_pairs | Total query-partition pairs |
| oracle_retained | Number of pairs retained by Oracle |
| retained | Number of pairs retained by the evaluated statistic |
| false_positive_pairs | Retained pairs minus oracle_retained |

Positive pruning is calculated as (pruning_pct × queries − negative_pruning_pct × global_negative) / global_positive. It is blank when no globally positive queries exist. Derived percentages and deltas are rounded to nine decimal places. Oracle has zero reported metadata bytes because its exact membership structure is not charged by the evaluator; this is not a claim that Oracle requires no storage.

### Experimental configuration

| Column | Meaning |
| --- | --- |
| dataset | Dataset name |
| dataset_rows | Total dataset rows |
| unique_stored | Distinct stored keys |
| nonascii_rows | Number of non-ASCII rows |
| partition_size | Configured maximum keys per partition |
| partitions | Number of partitions |
| budget_bytes | Configured payload budget per partition, including for baseline comparisons |
| queries | Query occurrences |
| global_positive | Globally positive query occurrences |
| global_negative | Globally negative query occurrences |
| partition_seed | Partition layout seed |
| hash_version | Hash implementation version |

Nominal BPK is not stored redundantly; calculate it as 8 × budget_bytes / partition_size if needed.

### Provenance

| Column | Meaning |
| --- | --- |
| model | Actual returned AI model; blank for non-AI methods |
| generation_id | Stable ID shared by proposals from one AI call; use it when joining generation-level costs to avoid double counting |
| call | Source call number; for Random this identifies the matched original batch, not an AI call |
| source_proposal_id | Original proposal identifier |
| algorithm | Original evaluator algorithm identifier |
| components | Original evaluator component descriptor |
| source_file | Repository-relative path of authoritative source CSV |

Blank values denote unavailable or inapplicable fields, not measured zeros. The master CSV contains measured evaluation data plus explicitly derived metrics and provenance, not duplicated generation-level token totals.

## Other results

- [Position and budget sensitivity](position_budget_sensitivity.csv) and [analysis](position_budget_sensitivity.md)
- [Shalla partition sensitivity](shalla_partition_sensitivity.csv)
- [Shalla pilot](shalla_pilot.csv)
- [Joint profile](joint_profile/)
