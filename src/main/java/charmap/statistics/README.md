# Partition statistics

The Experiment 3 comparison uses OptimizedBloom and one JointCharacterMap per evaluated position combination.

| File | Responsibility |
| --- | --- |
| [BitmapStatistic.java](BitmapStatistic.java) | Shared bitmap component abstraction, bit-setting logic, transposed partition postings, schema and diagnostic counters. |
| [BloomFilter.java](BloomFilter.java) | Hashes the complete key; optimalK searches k=1..16 using the standard Bloom FPR approximation. Uses shared hashToBit for each hash position. |
| [JointCharacterMap.java](JointCharacterMap.java) | Projects selected positions (including MISSING), hashes the resulting sequence via shared FNV-1a, and sets/tests one bit per key. Also supports earlier pair/tuple4 variants. |
| [CharacterMap.java](CharacterMap.java) | Independent single-position bitmap using ch(s,p) modulo 128. Retained for prior fixed/prefix/suffix methods; not evaluated in Experiment 3. |
| [LengthMap.java](LengthMap.java) | Bitmap of string lengths, with an overflow bucket. Retained for prior methods; not evaluated in Experiment 3. |

Inserts set bits and never clear them. Queries retain a partition if all required bits are set; otherwise it can be safely pruned. Bloom and Joint CM both use a 512-byte payload and one bit per projected/full key (k=1) in the reported experiment. Full-key Oracle membership is handled by the evaluator, not by a statistic class.

The transposed representation stores, for each bit position, which partitions have that bit set. This accelerates offline evaluation. Serialization reconstructs partition-local bytes; JVM memory is not the actual metadata size.

See [hashing](../hashing/README.md), [serialization](../serialization/README.md) and [evaluation](../evaluation/README.md).
