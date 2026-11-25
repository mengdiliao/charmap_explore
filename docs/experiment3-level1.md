# Experiment 3 — AI without Characteristics (Level 1)

## 1. Objective

Test whether a single AI-generated set of position combinations can outperform length-matched random selection and an optimized full-key Bloom filter for equality queries. This experiment evaluates a single joint bitmap per partition, not a hybrid or an iterative AI optimization loop.

## 2. Setup

| Parameter | Value |
| --- | --- |
| Dataset | Shalla; 2,926,705 unique ASCII stored keys |
| Queries | Both complete official-generator workloads; 10,000,000 queries each |
| Partition size / count | 8,000 / 366 (last: 6,705 keys) |
| Partition seed | 55; deterministic MT19937-64 shuffle |
| Payload | 512 bytes per partition; nominal BPK = 8 × 512 / 8,000 = 0.512 |
| Candidate lengths | 2–6 distinct positions from 0..15 and -16..-1 |
| AI configuration | claude-opus-5-5; high effort; max_tokens=16000; one response |
| Random controls | Seed 155; one length-matched random combination per AI proposal |
| Baselines | OptimizedBloom, ReferenceJointCM and exact full-key Oracle |

See [data preparation](data-preparation.md) for the source, workload distribution and checksums. The same partition layout, workload and payload apply to every evaluated design.

## 3. Design and selection

The original AI prompt contained the task, dataset/workload description, structural sample strings and historical baseline scores. It requested 12 unique combinations, exactly eight of length four and four of other allowed lengths. The observed response contains eight four-position tuples, three triples and one five-position tuple. Positions are canonicalized (nonnegative ascending, then negative ascending). Random combinations match each corresponding AI tuple's length and are unique within the random group, excluding the reference. The evaluator deduplicates identical designs if needed; this run has 25 unique joint maps including the reference.

The [recorded prompt](../runs/experiment3_unified_hashing/prompt.md), [AI response](../runs/experiment3_unified_hashing/response_1.json), [raw API response](../runs/experiment3_unified_hashing/api_raw_1.json), [frozen candidate list](../runs/experiment3_unified_hashing/frozen.json) and [configuration](../runs/experiment3_unified_hashing/config.json) are retained. No candidate was chosen using evaluation feedback. The reported run reuses the original designs with unified hashing rather than generating a second AI response. Consequently, the original prompt describes the older mapping and its historical scores; it is provenance, not a description of the current implementation. The new scoring uses only the current unified implementation.

## 4. Statistics and shared hashing

- **Optimized Bloom:** hash the entire key; choose integer k in 1..16 minimizing the standard Bloom FPR approximation using nominal partition size and bitmap budget. Here k=1.
- **Joint Character Map:** extract one ordered tuple from the selected positions. Positive indices count from the start (zero-based), negative indices from the end. An out-of-range position is symbol 128 (MISSING), distinct from ASCII 0–127. For example, [0,1,-2,-1] projects www.example.com to wwom.
- **Reference Joint CM:** a fixed candidate using [0,1,-2,-1].
- **Oracle:** exact full-key membership per partition, an upper bound without a comparable metadata budget.

Both Bloom and Joint CM use the same 64-bit FNV-1a update over their input symbols. For raw FNV result h, bit index j is unsigned_remainder(mix(h + j × 0x9e3779b97f4a7c15), m), with 64-bit wraparound and m=4096. Each index uses one SplitMix64-style finalizer; both methods use j=0 in this run. Insertion sets the bit; querying an unset bit safely excludes a partition. The only structural difference at k=1 is full-key versus projected-key input. In this sense, Joint CM is a single-hash Bloom-style bitmap over projected keys.

Base-257 token encoding does NOT determine the deployed joint bitmap index. It is a lossless representation of a fixed-length projected tuple (up to six ASCII/MISSING symbols here) for diagnostics. Projection collisions arise when different full strings share a token; bitmap collisions arise when different tokens map to the same bit. The [encoding](../src/main/java/charmap/encoding/README.md), [hashing](../src/main/java/charmap/hashing/README.md) and [statistics](../src/main/java/charmap/statistics/README.md) package guides explain these operations.

## 5. Evaluation

Each query occurrence is evaluated against all partitions. Let Q be the number of query occurrences, N the number of partitions, R the number of retained query–partition pairs, and O the exact Oracle-retained pairs. Duplicate query values are evaluated once and weighted by their multiplicities; this preserves full-workload counts. Both globally positive and negative queries contribute to overall pruning.

| Metric | Definition |
| --- | --- |
| Pruning rate (%) | 100 × (Q × N − R) / (Q × N) |
| False-positive pairs | R − O, provided there are no false negatives |
| Partition FPR (%) | 100 × (R − O) / (Q × N − O) |
| False negatives | Query occurrences whose true containing partition is pruned |
| Negative pruning (%) | Fraction of pairs pruned only among globally absent query keys |
| Oracle capture (%) | 100 × (Q × N − R) / (Q × N − O) |
| Mean token NDV | Mean number of distinct exact projected tokens per partition |
| Mean saturation (%) | Total occupied bits / total bitmap bits × 100 |
| Collision excess (%) | (Sum of per-partition token NDVs − sum of occupied bits) / sum of token NDVs × 100 |
| Exact joint pruning (%) | Pruning if each partition stored an exact set of projected tokens (no bitmap collision) |
| Metadata size / actual BPK | Serialized file bytes; 8 × bytes / stored keys |
| Delta vs Bloom (pp) | Candidate pruning rate minus same-workload Bloom pruning rate |

Exact joint pruning is a ceiling for that position combination, not the full-key Oracle. It is calculated offline, not stored inside the 512-byte metadata. All actual statistics are subject to zero false negatives. Physical metadata includes fixed header and shared schema, so actual BPK is slightly above nominal. Transposed postings and frequency aggregation are benchmark accelerations, not claims about production query latency.

## 6. Results and limitations

| Workload | Bloom | AI mean / best | Random mean / best |
| --- | ---: | ---: | ---: |
| Uniform | 14.15% | 14.81% / 18.33% | 14.93% / 19.03% |
| Zipfian | 14.52% | 6.03% / 9.05% | 11.36% / 22.10% |

Joint CM can outperform Bloom at this budget, but the single AI response does not outperform the random group overall. Two random candidates beat Bloom on both workloads. These are exploratory results, not evidence of generalization to held-out workloads.

See the [published result guide](../runs/experiment3_unified_hashing/README.md) for full numerical results, candidate positions and raw files. The [full benchmark CSV](../runs/experiment3_unified_hashing/results.csv) and [candidate-level CSV](../runs/experiment3_unified_hashing/proposal_results.csv) are also included in the repository. The consolidated comparison with Experiment 4 is available in [joint_cm_comparison.csv](../results/joint_cm_comparison.csv). One AI response, one random seed, one partition seed and one hash configuration were tested. Both workloads are fully evaluated, with no holdout and no iteration or detailed profiling fed to the AI. The best candidate is identified post hoc; this is a stage result, not a statistically validated claim that AI improves selection or that the best design generalizes.

## 7. Reproduce

Install Python 3.10+ and JDK 21; use the committed Gradle wrapper. Obtain the three Shalla text files using the [data guide](data-preparation.md). From the repository root:

```bash
./gradlew clean test

src=runs/experiment3_unified_hashing
dst=runs/experiment3_reproduced
mkdir "$dst" &&
  cp "$src"/{config.json,prompt.md,response_1.json,frozen.json} "$dst/" &&
  python3 scripts/experiment3.py evaluate --out "$dst"
```

This uses the already frozen AI/random candidates, verifies the input hashes, and writes new results without overwriting the published run. No AI API key or new AI call is needed. Use a new output directory for each rerun.

Python verifies the source data and prompt/response hashes, writes designs.tsv and runtime.json, invokes the Gradle positionEvaluator task, then writes proposal_results.csv and report.md. The source run is not modified. JDK 21 and Python 3.10+ are sufficient for evaluation; Gradle 8.14.3 and JUnit dependencies are fetched when required. Set JAVA_HEAP=6g if more heap is needed; the default is 4g. The original data-generation dependencies are separate. For additional independent AI experiments, see [scripts](../scripts/README.md); these are not needed for this result.

Verification: `./gradlew clean test`. The [unified verification workflow](../.github/workflows/unified-hashing.yml) tests shared hashing, replay and full Shalla reference/profiling consistency. Historical CSVs used by those checks are not part of the main experiment results.

## 8. Source code

All Java packages below have a local README explaining their files.

| Package | Responsibility |
| --- | --- |
| [data](../src/main/java/charmap/data/README.md) | Read prepared inputs and assign partitions |
| [encoding](../src/main/java/charmap/encoding/README.md) | Project characters and represent exact tokens |
| [hashing](../src/main/java/charmap/hashing/README.md) | Shared hash and bit mapping |
| [statistics](../src/main/java/charmap/statistics/README.md) | Bloom, Joint CM and shared bitmap representation |
| [evaluation](../src/main/java/charmap/evaluation/README.md) | Build/evaluate statistics, diagnostics and CSVs |
| [serialization](../src/main/java/charmap/serialization/README.md) | Write actual metadata bytes |
| [experiments](../src/main/java/charmap/experiments/README.md) | Experiment entry points |
| [scripts](../scripts/README.md) | Python orchestration and input preparation |
| [tests](../src/test/java/charmap/README.md) | Correctness and reproducibility checks |

The Experiment 3 entry point is [PositionEvaluator.java](../src/main/java/charmap/experiments/PositionEvaluator.java). Earlier experiment code and reference CSVs remain for reproducibility and CI; they are not part of the stage-result comparison.

[Back to project overview](../README.md)
