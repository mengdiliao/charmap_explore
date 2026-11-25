# AI-guided Joint Character Maps

Research on AI-designed statistics for equality-based partition pruning of string identifiers.

## Research questions

- Can AI select character-position combinations that outperform random selection and an optimized Bloom filter?
- Does providing dataset and workload characteristics improve AI-generated designs?
- How sensitive are the selected designs to partition size and metadata budget?

## Experimental setup

The experiments use the Shalla dataset (2,926,705 unique ASCII keys) and two full query workloads: Uniform and Zipfian (10 million query occurrences each). The main comparison uses 8,000 keys per partition and a 512-byte bitmap budget (configured BPK = 0.512). All methods must produce zero false negatives.

## Experiments

| Experiment | Description | Documentation |
| --- | --- | --- |
| Experiment 3 — AI without characteristics | One AI response with task description and samples; 12 AI and 12 length-matched random combinations, evaluated on both workloads. | [Design, methodology and reproduction](docs/experiment3-level1.md) |
| Experiment 4 — AI with human-selected characteristics | Eight additional dataset/workload characteristics; 12 AI combinations generated and evaluated separately for each workload. | [Profiling, generation and evaluation](docs/experiment4-simple-profiling.md) |
| Joint CM sensitivity | Freeze the best Random and AI designs at the original setting, then evaluate each on its matching workload under 23 partition-size/budget configurations. | [Design and reproduction](experiments/joint_cm_sensitivity/README.md) |

## Results

| Result | Data | Explanation |
| --- | --- | --- |
| Fixed-configuration comparison (76 rows) | [CSV](results/joint_cm_comparison.csv) | [Method definitions and data dictionary](results/joint_cm_comparison.md) |
| Sensitivity analysis (276 rows) | [CSV](results/joint_cm_sensitivity.csv) | [Results and analysis](results/joint_cm_sensitivity.md) |

See the [results index](results/README.md) and [figures](results/figures/README.md) for all eight plots and reproduction commands.

The additional characteristics improve average AI pruning on Zipf, but not on Uniform at the original setting. Random still finds the best individual solution on both workloads at that setting. The profiled AI designs have higher exact-projection pruning potential, although the limited bitmap budget restricts actual pruning. These are exploratory, in-sample results, not evidence of consistent AI superiority.

## Repository guide

| Directory | Contents |
| --- | --- |
| [docs/](docs/) | Experimental methodology and [data preparation](docs/data-preparation.md) |
| [scripts/](scripts/README.md) | Data preparation, AI generation, evaluation, aggregation and plotting |
| [src/main/java/charmap/](src/main/java/charmap/) | Statistics, shared hashing, evaluation and serialization; each package has its own guide |
| [experiments/](experiments/) | Frozen sensitivity selections and configurations |
| [runs/](runs/) | Published prompts, responses, profiles and raw evaluation artifacts |
| [results/](results/README.md) | Consolidated CSVs, analyses and figures |

For reproduction, follow the experiment-specific documentation above. Evaluation of the existing frozen designs does not require new AI calls.
