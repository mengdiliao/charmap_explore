# Character Map Exploration

Dataset preparation for equality-based partition pruning over real strings. The four P0 datasets are Shalla, Reddit usernames, GeoNames, and US addresses. See [data preparation](docs/data-preparation.md) for sources, exact workload provenance, and commands. Raw datasets and generated query files are not tracked in Git.

## Java build and experiment tasks

Use JDK 21 and the committed Gradle Wrapper (`./gradlew build`, `./gradlew test`). See [Gradle quick start](docs/gradle.md) and [Experiment 3](docs/experiment3-level1.md). No standalone Gradle installation is necessary.
