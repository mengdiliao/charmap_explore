# Unified hashing ablation

Base: 9a3d9ad3c2a32b6b1c24f2d77bea8c5f937f44ee (refactor/code-organization). Hash version: fnv1a-mix-v1.

Bloom hashes the full ASCII key with FNV-1a. Joint CM hashes the ordered projected character sequence with the exact same FNV-1a update operation, including symbol 128 for missing positions. Both then apply one SplitMix64-style finalizer to the raw FNV hash plus j times 0x9e3779b97f4a7c15 and unsigned modulo m. At P=8000, B=512, Bloom k=1 and Joint CM k=1. Bloom still uses theoretically optimized k for other configurations. Pair, tuple4 and general joint mappings are all updated. Base-256/257 exact encodings remain only for lossless token identity and diagnostics. JointProfile translates encoded tokens back to the same character sequence before hashing. Fixed character and length maps are unchanged.

## Replay the original AI and Random candidates (no AI call)

From the repository root with JDK 21, Python 3.10+, existing Shalla input files, and the original run directory:

    ./gradlew clean test
    python3 scripts/experiment3.py replay --from-run runs/experiment3_level1 --out runs/experiment3_unified_hashing

If the original run is elsewhere, replace --from-run; use --data /path/to/shalla if needed. The old directory must contain config.json, prompt.md, response_1.json and frozen.json. Replay copies these unchanged, verifies data and prompt/response digests, and runs evaluate/report with the original P, B, seed, candidate IDs, AI positions and random positions. No prepare/generate/freeze step or API key is required. The output must be separate and empty. If the original benchmark/results.csv is present, it is copied as legacy_results.csv and paired with the new results to produce hash_comparison.csv. The comparison verifies identical query counts, oracle, projection ceiling, NDV, payload and other invariants. Source run files are not changed.

Outputs: benchmark/results.csv (all methods), proposal_results.csv (AI/random positions and deltas vs new Bloom and reference), report.md, hash_comparison.csv (if old results are available), runtime.json and replay.json. The original prompt's historical hash instructions and scores remain untouched in the replay for provenance, not as instructions for a new AI call. No held-out evaluation is added.

The bitmap payload is unchanged. Serialized hash-based component schemas now identify the new hash version, adding small shared schema overhead; metadata_total_bytes includes that overhead. Exact projection and partition metrics should not change. Actual hash-dependent pruning, saturation, collisions, serialized bitmaps and BPK may differ.

Other Gradle tasks retain their names and arguments, but default outputs now use java_unified_* / experiment3_unified_hashing. Legacy full-result parity CI is intended for main/refactor only; the unified-hashing CI tests matching shared bit mappings, missing positions, zero false negatives, frozen replay and full Shalla reference/profile consistency. No historical CSV is overwritten.
