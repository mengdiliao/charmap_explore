# Correctness tests

[CorrectnessTest.java](CorrectnessTest.java) uses JUnit 5 to test character extraction including MISSING, hash vectors, shared full/projected bit mapping, optimized Bloom k, deterministic shuffle, query multiplicities, metadata and zero false negatives on a small fixture including short/empty keys.

Run from repository root:

```bash
./gradlew clean test
```

Fixtures are synthetic and not research results. The [unified hashing verification workflow](../../../../.github/workflows/unified-hashing.yml) additionally tests frozen replay and full Shalla reference/profiling consistency, without paid AI calls. Existing historical CSVs are used by those invariance checks.
