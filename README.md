# Experiment 4 — Simple Statistical Profiling 

This branch adds workload-specific offline profiling and prompts. See [Experiment 4 instructions](docs/experiment4-simple-profiling.md) for the eight characteristics, file-selection flags, matched control, full-workload profiling, raw dot-count categories and tests. The prepare command is offline; generate makes one explicit AI API call for a selected prompt arm. The evaluate command runs the four-group comparison for one full workload using the existing profiled response, without any API call.

---

# Experiment 3 — AI-guided Joint Character Maps

Stage results for equality-based partition pruning on the Shalla dataset.

**Research question:** Can an AI model select character-position combinations that prune more partitions than random selection and an optimized full-key Bloom filter, under the same metadata payload budget?

## Experiment at a glance

| Setting | Value |
| --- | --- |
| Stored keys | 2,926,705 unique ASCII strings (Shalla) |
| Workloads | 10M Uniform + 10M Zipfian (exponent 1.5) |
| Partition layout | Seed 55; 8,000 keys per partition; 366 partitions |
| Payload | 512 bytes per partition (4,096 bits; nominal 0.512 bits/key) |
| AI / random | 12 frozen AI candidates / 12 length-matched random candidates |
| Baselines | Optimized Bloom (k=1), reference Joint CM [0,1,-2,-1], exact Oracle |
| Hash mapping | Shared FNV-1a, one mix, unsigned modulo; fnv1a-mix-v1 |
| Correctness | Zero false negatives in all 54 benchmark rows |

### Main findings

| Workload | Bloom | AI mean / best | Random mean / best |
| --- | ---: | ---: | ---: |
| Uniform | 14.15% | 14.81% / 18.33% | 14.93% / 19.03% |
| Zipfian | 14.52% | 6.03% / 9.05% | 11.36% / 22.10% |

Joint CM can outperform Bloom at this budget, but the single AI response does not outperform the random group overall. Two random candidates beat Bloom on both workloads. These are exploratory results, not evidence of generalization to held-out workloads.

## Start here

- [Experimental design and methodology](docs/experiment3-level1.md): candidate selection, shared hashing, metrics, correctness, limitations and reproducibility.
- [Shalla data and workload preparation](docs/data-preparation.md): source, exact data counts and how to obtain the input files.
- [Published results and artifact guide](runs/experiment3_unified_hashing/README.md): main findings, candidate positions and where to find the raw results.
- [Full benchmark CSV](runs/experiment3_unified_hashing/results.csv) and [candidate-level CSV](runs/experiment3_unified_hashing/proposal_results.csv).
- [Original AI prompt](runs/experiment3_unified_hashing/prompt.md), [response](runs/experiment3_unified_hashing/response_1.json) and [frozen designs](runs/experiment3_unified_hashing/frozen.json).

## Reproduce the published result

Install Python 3.10+ and JDK 21; use the committed Gradle wrapper. Obtain the three Shalla text files using the [data guide](docs/data-preparation.md). From the repository root:

```bash
./gradlew clean test

src=runs/experiment3_unified_hashing
dst=runs/experiment3_reproduced
mkdir "$dst" &&
  cp "$src"/{config.json,prompt.md,response_1.json,frozen.json} "$dst/" &&
  python3 scripts/experiment3.py evaluate --out "$dst"
```

This uses the already frozen AI/random candidates, verifies the input hashes, and writes new results without overwriting the published run. No AI API key or new AI call is needed. Use a new output directory for each rerun.

## Source code

All Java packages below have a local README explaining their files.

| Package | Responsibility |
| --- | --- |
| [data](src/main/java/charmap/data/README.md) | Read prepared inputs and assign partitions |
| [encoding](src/main/java/charmap/encoding/README.md) | Project characters and represent exact tokens |
| [hashing](src/main/java/charmap/hashing/README.md) | Shared hash and bit mapping |
| [statistics](src/main/java/charmap/statistics/README.md) | Bloom, Joint CM and shared bitmap representation |
| [evaluation](src/main/java/charmap/evaluation/README.md) | Build/evaluate statistics, diagnostics and CSVs |
| [serialization](src/main/java/charmap/serialization/README.md) | Write actual metadata bytes |
| [experiments](src/main/java/charmap/experiments/README.md) | Experiment entry points |
| [scripts](scripts/README.md) | Python orchestration and input preparation |
| [tests](src/test/java/charmap/README.md) | Correctness and reproducibility checks |

The Experiment 3 entry point is PositionEvaluator.java. Earlier experiment code and reference CSVs remain for reproducibility and CI; they are not part of the stage-result comparison.
