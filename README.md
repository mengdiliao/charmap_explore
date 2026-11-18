# Character Map Exploration

Dataset preparation for equality-based partition pruning over real strings. The four P0 datasets are Shalla, Reddit usernames, GeoNames, and US addresses. See [data preparation](docs/data-preparation.md) for sources, exact workload provenance, and commands. Raw datasets and generated query files are not tracked in Git.

## Java build and experiment tasks

Use JDK 21 and the committed Gradle Wrapper (`./gradlew build`, `./gradlew test`). See [Gradle quick start](docs/gradle.md) and [Experiment 3](docs/experiment3-level1.md). No standalone Gradle installation is necessary.

## Java source organization

- `hashing/`: shared hash functions and unsigned bucket mapping.
- `encoding/`: character extraction and joint-token encoding.
- `data/`: `DatasetLoader` reads existing input files; `LoadedData` holds in-memory keys and query counts; `PartitionLayout` handles reproducible shuffle and partition IDs. This package does not download or generate datasets.
- `serialization/`: binary metadata serialization.
- `statistics/`: existing bitmap statistics and shared transposed bitmap storage.
- `evaluation/`: construction and evaluation, joint diagnostics, and CSV utilities. The legacy truncated MinMax remains in Evaluator; no new statistic is introduced.
- `experiments/`: the four existing experiment entry points.

The Gradle task names, data paths, hash algorithms, partition layout, metadata format, and experiment parameters remain unchanged. See [code organization](docs/code-organization.md).
