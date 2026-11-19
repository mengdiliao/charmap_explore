# Shared hashing

[HashUtils.java](HashUtils.java) implements the unified hash version fnv1a-mix-v1.

| Method / field | Responsibility |
| --- | --- |
| FNV_OFFSET | Initial 64-bit FNV-1a state. |
| fnv1aStep(h,symbol) | XOR the next symbol and multiply by the FNV prime with 64-bit wraparound. |
| fnv1a(s) | Apply fnv1aStep to the whole character sequence, without mixing. |
| mix(x) | SplitMix64-style finalizer, applied once for each bit index. |
| hashToBit(h,j,m) | Mix h + j × HASH_STEP and take the unsigned remainder modulo m; returns an index in [0,m-1]. |
| VERSION | Identifies the mapping in serialized hash-based statistic schemas. |

Bloom feeds the full key to FNV-1a. Joint CM streams the selected symbols through the same fnv1aStep, avoiding temporary strings. Both call hashToBit. In Experiment 3, m=4096 and j=0 for both methods. Modulo is included in hashToBit; there is no separate bucket() function.

The integer tuple encoding used by exact diagnostics is not part of this hash mapping. See [encoding](../encoding/README.md) and [statistics](../statistics/README.md).
