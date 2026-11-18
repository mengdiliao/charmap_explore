# Behavior-preserving code organization

Base commit: 5f4d35b4a9722f08d238091207b030b6e07f5a35.

This refactor separates existing code, rather than adding or tuning a statistic. See the README for packages. 

- HashUtils preserves FNV-1a and both original mixing stages for Bloom; CharacterEncoding preserves base-257 tuples, legacy base-256 pairs and MISSING=128.
- BitmapStatistic preserves transposed postings and the exact method/component schema strings. The four subclasses only specialize the bit mapping. Hybrid methods still compose components. The truncated MinMax implementation remains in Evaluator for historical compatibility.
- Dataset and PartitionLayout preserve the pinned MT19937-64 shuffle and query multiplicities. MetadataSerializer preserves CMP1 bytes and shared schema accounting.
- JointDiagnostics preserves the original NDV, occupancy and exact projection metrics. ResultWriter preserves CSV formatting. Experiment class names move into experiments; Gradle task names and CLI arguments stay the same.
- Experiment 3 now recursively hashes Java sources and records repo-relative paths, so runtime provenance still covers every Java file after package moves. The experiment's prompt, candidates, workload and scoring are unchanged.

Verification: run `./gradlew test`, plus the existing full Shalla workflows that compare against archived CSV results. Historical output files are not regenerated or changed by this refactor.
